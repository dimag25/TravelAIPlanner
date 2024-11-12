import os
import json
from openai import OpenAI
from openai.types.chat import ChatCompletion, ChatCompletionMessageParam
from typing import Dict, List, Union, Optional
from functools import lru_cache
from app import app, logger


def initialize_openai_client():
    """Initialize the OpenAI client with proper error handling."""
    api_key = os.environ.get("OPENAI_API_KEY")
    if not api_key:
        logger.error("OpenAI API key not configured")
        return None

    try:
        return OpenAI(api_key=api_key)
    except Exception as e:
        logger.error(f"Failed to initialize OpenAI client: {str(e)}")
        return None


# Initialize OpenAI client
client = initialize_openai_client()

TRIP_SYSTEM_PROMPT = '''You are an AI travel advisor helping users plan their trips. Always respond with valid JSON following this format:
{
    "destination": "City Name, Country",
    "suggested_duration": 3,
    "travel_type": "cultural",
    "recommended_group_size": "2-4",
    "itinerary": {
        "1": [
            "Morning: Visit specific attraction name",
            "Afternoon: Visit specific location name",
            "Evening: Dinner at specific restaurant or area name"
        ]
    }
}

For alternative suggestions, return an array of exactly 3 suggestions.

Rules:
1. Always use valid JSON with proper quotes
2. Each suggestion must include at least 3 activities per day
3. Use real, mappable location names
4. Travel type must be one of: cultural, adventure, relaxation, family, business
5. Format group size as "X-Y" where X and Y are numbers
6. Include specific venue/location names for all activities'''

CHAT_SYSTEM_PROMPT = '''You are a helpful AI travel advisor. Provide concise but informative responses about:
- Destination recommendations
- Travel tips and local customs
- Activity suggestions
- Transportation and logistics
- Safety and health considerations
- Budget planning and cost estimates

Keep responses friendly and practical. If unsure, acknowledge limitations and suggest alternatives.'''


def check_api_key() -> bool:
    """Check if OpenAI API key is properly configured."""
    return bool(client)


def reinitialize_client() -> None:
    """Attempt to reinitialize the OpenAI client."""
    global client
    client = initialize_openai_client()


def extract_json_from_text(content: str) -> str:
    """Extract JSON content from a text that might contain markdown or other formatting."""
    try:
        # Find the first occurrence of '{' or '['
        json_start = min((content.find('{'), content.find('[')),
                         key=lambda x: float('inf') if x == -1 else x)

        if json_start == float('inf'):
            raise ValueError("No JSON structure found in content")

        # Find the matching closing bracket
        stack = []
        in_string = False
        escape_char = False

        for i in range(json_start, len(content)):
            char = content[i]

            if char == '\\' and not escape_char:
                escape_char = True
                continue

            if char == '"' and not escape_char:
                in_string = not in_string

            if not in_string:
                if char in '{[':
                    stack.append(char)
                elif char in '}]':
                    if not stack:
                        raise ValueError("Unmatched closing bracket")
                    if (char == '}'
                            and stack[-1] == '{') or (char == ']'
                                                      and stack[-1] == '['):
                        stack.pop()
                        if not stack:  # Found complete JSON structure
                            return content[json_start:i + 1]

            escape_char = False

        raise ValueError("Incomplete JSON structure")
    except Exception as e:
        logger.error(f"Error extracting JSON: {str(e)}")
        raise ValueError(f"Failed to extract JSON: {str(e)}")


@lru_cache(maxsize=100)
def parse_trip_suggestion(content: str) -> Optional[List[Dict]]:
    """Parse and validate trip suggestions from API response."""
    try:
        if not content or not isinstance(content, str):
            raise ValueError("Invalid content type or empty content")

        # Extract JSON content from the response
        try:
            json_content = extract_json_from_text(content.strip())
            data = json.loads(json_content)
        except (json.JSONDecodeError, ValueError) as e:
            logger.error(
                f"JSON parsing error: {str(e)}\nContent: {content[:200]}...")
            raise ValueError(f"Invalid JSON format: {str(e)}")

        # Convert single suggestion to list format
        suggestions = [data] if isinstance(data, dict) else data
        if not isinstance(suggestions, list):
            raise ValueError(
                "Invalid suggestion format: must be an object or array")

        valid_suggestions = []
        for suggestion in suggestions:
            try:
                # Validate required fields
                required_fields = [
                    "destination", "suggested_duration", "travel_type",
                    "recommended_group_size", "itinerary"
                ]
                missing = [
                    field for field in required_fields
                    if field not in suggestion
                ]
                if missing:
                    raise ValueError(
                        f"Missing required fields: {', '.join(missing)}")

                # Validate field types and values
                if not isinstance(
                        suggestion["destination"],
                        str) or not suggestion["destination"].strip():
                    raise ValueError(
                        "Invalid destination: must be a non-empty string")

                # Convert duration to integer
                try:
                    suggestion["suggested_duration"] = int(
                        float(str(suggestion["suggested_duration"])))
                    if suggestion["suggested_duration"] < 1:
                        raise ValueError("Duration must be positive")
                except (ValueError, TypeError):
                    raise ValueError(
                        "Invalid duration: must be a positive number")

                # Validate travel type
                if suggestion["travel_type"].lower() not in [
                        "cultural", "adventure", "relaxation", "family",
                        "business"
                ]:
                    raise ValueError("Invalid travel type")
                suggestion["travel_type"] = suggestion["travel_type"].lower()

                # Validate group size format
                if not isinstance(
                        suggestion["recommended_group_size"], str
                ) or '-' not in suggestion["recommended_group_size"]:
                    suggestion[
                        "recommended_group_size"] = "2-4"  # Default value

                # Validate itinerary
                itinerary = suggestion.get("itinerary", {})
                if not isinstance(itinerary, dict) or not itinerary:
                    raise ValueError(
                        "Invalid itinerary: must be a non-empty object")

                cleaned_itinerary = {}
                for day, activities in itinerary.items():
                    if not isinstance(activities, list):
                        continue
                    if len(activities) < 3:
                        continue
                    cleaned_activities = []
                    for activity in activities[:
                                               3]:  # Limit to 3 activities per day
                        if isinstance(activity, str) and activity.strip():
                            cleaned_activities.append(activity.strip())
                    if len(cleaned_activities) == 3:
                        cleaned_itinerary[str(day)] = cleaned_activities

                if not cleaned_itinerary:
                    raise ValueError("No valid activities found in itinerary")

                suggestion["itinerary"] = cleaned_itinerary
                valid_suggestions.append(suggestion)

            except ValueError as e:
                logger.warning(f"Skipping invalid suggestion: {str(e)}")
                continue

        if not valid_suggestions:
            raise ValueError("No valid suggestions after parsing")

        # Return at most 3 suggestions
        return valid_suggestions[:3]

    except Exception as e:
        logger.error(f"Error parsing suggestion: {str(e)}")
        return None


def get_chat_response(
        message: str,
        context: Optional[str] = None,
        is_trip_suggestion: bool = False) -> Union[str, List[Dict]]:
    """Get response from OpenAI API for chat or trip suggestions."""
    try:
        if not check_api_key():
            # Try to reinitialize the client once
            reinitialize_client()
            if not check_api_key():
                raise ValueError(
                    "OpenAI API key not configured or invalid. Please configure the API key first."
                )

        if not message.strip():
            raise ValueError("Empty message provided")

        # Prepare messages for the API
        messages: List[ChatCompletionMessageParam] = [{
            "role":
            "system",
            "content":
            TRIP_SYSTEM_PROMPT if is_trip_suggestion else CHAT_SYSTEM_PROMPT
        }]

        # Add context if provided
        if context:
            try:
                context_data = json.loads(context)
                context_prompt = f"Consider these user preferences: {json.dumps(context_data, indent=2)}"
                messages.append({"role": "system", "content": context_prompt})
            except json.JSONDecodeError:
                logger.warning("Failed to parse context data")

        messages.append({"role": "user", "content": message})

        # Make API call with retries
        max_retries = 3
        response = None
        last_error = None

        for attempt in range(max_retries):
            try:
                if not client:
                    raise ValueError("OpenAI client is not initialized")

                response = client.chat.completions.create(
                    model=
                    "gpt-4o",  # Fixed model name to match trip_generator.py
                    messages=messages,
                    temperature=0.7,
                    max_tokens=2000,
                    presence_penalty=0.6,
                    frequency_penalty=0.3)
                break
            except Exception as e:
                last_error = str(e)
                logger.warning(
                    f"Retry {attempt + 1} after error: {last_error}")
                if attempt == max_retries - 1:
                    raise ValueError(
                        f"Failed to get response after {max_retries} attempts: {last_error}"
                    )

        if not response or not response.choices:
            raise ValueError("No response generated")

        content = response.choices[0].message.content
        if not content:
            raise ValueError("Empty response from API")

        # Handle trip suggestions
        if is_trip_suggestion:
            suggestions = parse_trip_suggestion(content)
            if not suggestions:
                raise ValueError("Failed to parse trip suggestions")
            return suggestions

        return content

    except Exception as e:
        error_message = str(e)
        logger.error(f"Chat response error: {error_message}")

        if is_trip_suggestion:
            return [{
                "destination": "Error",
                "suggested_duration": 3,
                "travel_type": "cultural",
                "recommended_group_size": "2-4",
                "itinerary": {
                    "1": [
                        f"Error: {error_message}",
                        "Please try again with more specific details.",
                        "Ensure you provide destination and preferences."
                    ]
                }
            }]
        return f"I apologize, but I encountered an error: {error_message}. Please try again with more specific details."
