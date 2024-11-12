import os
import json
from openai import OpenAI
from typing import Optional, Dict, List
import logging
from models import TripTemplate
from app import db
import random

logger = logging.getLogger(__name__)


def initialize_openai_client():
    """Initialize OpenAI client with proper error handling."""
    api_key = os.environ.get("OPENAI_API_KEY")
    if not api_key:
        logger.error("OpenAI API key not configured")
        return None

    try:
        return OpenAI(api_key=api_key)
    except Exception as e:
        logger.error(f"Failed to initialize OpenAI client: {str(e)}")
        return None


def get_fallback_template(destination: str, num_days: int,
                          travel_type: str) -> Optional[Dict]:
    """Get a suitable template based on parameters."""
    try:
        # Try to find a template with exact match
        template = TripTemplate.query.filter(
            TripTemplate.travel_type == travel_type,
            TripTemplate.num_days == num_days).first()

        # If no exact match, try to find a template with similar duration
        if not template:
            template = TripTemplate.query.filter(
                TripTemplate.travel_type == travel_type, TripTemplate.num_days
                <= num_days + 2, TripTemplate.num_days
                >= max(1, num_days - 2)).first()

        # If still no template, get any template with matching travel type
        if not template:
            template = TripTemplate.query.filter_by(
                travel_type=travel_type).first()

        # If no matching template at all, get any template
        if not template:
            template = TripTemplate.query.first()

        if not template:
            return None

        # Customize template for the requested destination and duration
        itinerary = customize_template(template.base_itinerary, destination,
                                       num_days)

        return {
            "destination": destination,
            "suggested_duration": num_days,
            "travel_type": travel_type,
            "recommended_group_size": template.suggested_group_size,
            "itinerary": itinerary
        }
    except Exception as e:
        logger.error(f"Error getting fallback template: {str(e)}")
        return None


def customize_template(base_itinerary: Dict, destination: str,
                       num_days: int) -> Dict:
    """Customize template itinerary for specific destination and duration."""
    try:
        # Get the number of days in the base itinerary
        base_days = len(base_itinerary)
        customized = {}

        # If requested days is less than template days, take first n days
        if num_days <= base_days:
            for day in range(1, num_days + 1):
                customized[str(day)] = [
                    activity.replace(
                        activity.split(': ')[1] if ': ' in activity else
                        activity, f"{destination} {activity.split(': ')[1]}"
                        if ': ' in activity else f"{destination} {activity}")
                    for activity in base_itinerary[str(day)][:3]
                ]
        else:
            # If more days needed, repeat the template with variations
            for day in range(1, num_days + 1):
                template_day = str(((day - 1) % base_days) + 1)
                customized[str(day)] = [
                    activity.replace(
                        activity.split(': ')[1] if ': ' in activity else
                        activity, f"{destination} {activity.split(': ')[1]}"
                        if ': ' in activity else f"{destination} {activity}")
                    for activity in base_itinerary[template_day][:3]
                ]

        return customized
    except Exception as e:
        logger.error(f"Error customizing template: {str(e)}")
        return {
            str(i):
            ["Morning activity", "Afternoon activity", "Evening activity"]
            for i in range(1, num_days + 1)
        }


def generate_trip_plan(destination: str,
                       num_days: int,
                       travel_type: str,
                       num_people: int,
                       alternatives: bool = False) -> Optional[List[Dict]]:
    """
    Generate a trip plan with optional alternatives.
    Returns a list of trip suggestions.
    """
    try:
        client = initialize_openai_client()
        if not client:
            raise ValueError("OpenAI client initialization failed")

        if alternatives:
            prompt = f'''Create exactly 3 alternative trip suggestions similar to {destination}. For each alternative:
1. Choose a different but related destination (nearby city, similar cultural experience, or comparable attraction type)
2. Include a detailed {num_days}-day itinerary with specific locations
3. Maintain the {travel_type} travel style but vary the experiences
4. Accommodate {num_people} people

Format each suggestion as valid JSON:
{{
    "destination": "City Name, Country",
    "suggested_duration": {num_days},
    "travel_type": "{travel_type}",
    "recommended_group_size": "X-Y",
    "itinerary": {{
        "1": [
            "Morning: [Specific activity/location]",
            "Afternoon: [Specific activity/location]",
            "Evening: [Specific activity/location]"
        ],
        ... (repeat for each day)
    }}
}}

Return an array of exactly 3 alternatives.'''
        else:
            prompt = f'''Create a detailed {num_days}-day trip itinerary for {destination} for {num_people} people. Travel type: {travel_type}.

Format as JSON with this exact structure:
{{
    "destination": "City Name, Country",
    "suggested_duration": days,
    "travel_type": "type",
    "recommended_group_size": "X-Y",
    "itinerary": {{
        "1": [
            "Morning: [Specific activity/location]",
            "Afternoon: [Specific activity/location]",
            "Evening: [Specific activity/location]"
        ]
    }}
}}

Rules:
1. Always use valid JSON with proper quotes
2. Each day must have exactly 3 activities (morning, afternoon, evening)
3. Use real, mappable location names
4. Travel type must be one of: cultural, adventure, relaxation, family, business
5. Include specific venue/location names'''

        max_retries = 3
        last_error = None

        for attempt in range(max_retries):
            try:
                response = client.chat.completions.create(
                    model="gpt-4o",  # Fixed model name
                    messages=[{
                        "role": "user",
                        "content": prompt
                    }],
                    temperature=0.7,
                    max_tokens=2000)

                if not response or not response.choices:
                    raise ValueError("No response generated")

                content = response.choices[0].message.content
                if not content:
                    raise ValueError("Empty response from API")

                try:
                    data = json.loads(content)
                    # Validate and normalize the response
                    if alternatives:
                        if not isinstance(data, list):
                            data = [data]
                        if len(data) < 3:
                            logger.warning(
                                f"Got {len(data)} suggestions, expected 3")
                            continue
                        return data[:
                                    3]  # Ensure we return exactly 3 alternatives
                    return [data]  # Return single suggestion as a list

                except json.JSONDecodeError as e:
                    last_error = f"Invalid JSON response: {str(e)}"
                    logger.warning(last_error)
                    if attempt < max_retries - 1:  # Only continue if we have more retries
                        continue
                    raise ValueError(last_error)

            except Exception as e:
                last_error = str(e)
                logger.warning(
                    f"Retry {attempt + 1} after error: {last_error}")
                if attempt == max_retries - 1:
                    break
                continue

        # If AI generation fails, try to use template as fallback
        template_plan = get_fallback_template(destination, num_days,
                                              travel_type)
        if template_plan:
            logger.info("Using template-based fallback plan")
            if alternatives:
                # For alternatives, modify the template slightly to create variations
                variations = []
                base_template = template_plan.copy()
                for i in range(3):
                    variation = base_template.copy()
                    variation["itinerary"] = customize_template(
                        base_template["itinerary"], destination, num_days)
                    variations.append(variation)
                return variations
            return [template_plan]

        # If both AI and template fallback fail, return error message
        raise ValueError(
            f"Failed to generate trip plan after {max_retries} attempts: {last_error}"
        )

    except Exception as e:
        error_message = str(e)
        logger.error(f"Error generating trip plan: {error_message}")
        return [{
            "destination": "Error",
            "suggested_duration": num_days,
            "travel_type": travel_type,
            "recommended_group_size": f"1-{num_people}",
            "itinerary": {
                "1": [
                    f"Error generating trip plan: {error_message}",
                    "Please try again with different parameters",
                    "Or contact support if the issue persists"
                ]
            }
        }]
