from app import app, db
from models import TripTemplate
import json

templates = [
    {
        "name": "Weekend City Break - New York",
        "description": "Perfect for a quick weekend getaway in the Big Apple. Experience the city's highlights in just 2 days.",
        "destination": "New York City, USA",
        "num_days": 2,
        "travel_type": "cultural",
        "suggested_group_size": "1-4",
        "base_itinerary": {
            "1": [
                "Morning: Visit Times Square and surrounding area",
                "Lunch: Try famous NY pizza",
                "Afternoon: Central Park exploration",
                "Evening: Broadway show and dinner in Theater District"
            ],
            "2": [
                "Morning: Visit Statue of Liberty and Ellis Island",
                "Lunch: Food tour in Lower Manhattan",
                "Afternoon: 9/11 Memorial and World Trade Center",
                "Evening: Rooftop bar with city views"
            ]
        }
    },
    {
        "name": "Cultural Discovery - London",
        "description": "Experience the best of British culture and history in London's most iconic locations.",
        "destination": "London, UK",
        "num_days": 4,
        "travel_type": "cultural",
        "suggested_group_size": "2-6",
        "base_itinerary": {
            "1": [
                "Morning: Tower of London tour",
                "Afternoon: Thames River cruise to Westminster",
                "Evening: London Eye experience at sunset"
            ],
            "2": [
                "Morning: British Museum exploration",
                "Afternoon: Shopping at Covent Garden",
                "Evening: West End theatre show"
            ],
            "3": [
                "Morning: Buckingham Palace and changing of the guard",
                "Afternoon: Hyde Park and Kensington Gardens",
                "Evening: Dinner at Borough Market"
            ],
            "4": [
                "Morning: St. Paul's Cathedral visit",
                "Afternoon: Tate Modern and Shakespeare's Globe",
                "Evening: Traditional pub dinner in Southwark"
            ]
        }
    },
    {
        "name": "Tel Aviv Beach & Culture",
        "description": "Discover the vibrant mix of Mediterranean beaches, rich history, and modern culture in Tel Aviv.",
        "destination": "Tel Aviv, Israel",
        "num_days": 3,
        "travel_type": "cultural",
        "suggested_group_size": "2-4",
        "base_itinerary": {
            "1": [
                "Morning: Jaffa Old City walking tour",
                "Afternoon: Relaxation at Gordon Beach",
                "Evening: Dinner at Carmel Market"
            ],
            "2": [
                "Morning: Bauhaus architecture tour in White City",
                "Afternoon: Visit Tel Aviv Museum of Art",
                "Evening: Nightlife at Rothschild Boulevard"
            ],
            "3": [
                "Morning: Breakfast at Sarona Market",
                "Afternoon: Shopping at Dizengoff Center",
                "Evening: Sunset at Tel Aviv Port"
            ]
        }
    },
    {
        "name": "Amsterdam Adventure",
        "description": "Experience the charm of Dutch canals, world-class museums, and cycling culture in Amsterdam.",
        "destination": "Amsterdam, Netherlands",
        "num_days": 3,
        "travel_type": "cultural",
        "suggested_group_size": "2-4",
        "base_itinerary": {
            "1": [
                "Morning: Van Gogh Museum visit",
                "Afternoon: Canal tour through historic center",
                "Evening: Dinner in Jordaan district"
            ],
            "2": [
                "Morning: Anne Frank House tour",
                "Afternoon: Bike ride through Vondelpark",
                "Evening: Visit to Royal Palace Amsterdam"
            ],
            "3": [
                "Morning: Rijksmuseum exploration",
                "Afternoon: Albert Cuyp Market visit",
                "Evening: Red Light District walking tour"
            ]
        }
    },
    {
        "name": "Berlin Historical Journey",
        "description": "Explore Berlin's rich history, vibrant art scene, and modern culture over 4 days.",
        "destination": "Berlin, Germany",
        "num_days": 4,
        "travel_type": "cultural",
        "suggested_group_size": "2-6",
        "base_itinerary": {
            "1": [
                "Morning: East Side Gallery visit",
                "Afternoon: Checkpoint Charlie Museum",
                "Evening: Dinner at Hackescher Markt"
            ],
            "2": [
                "Morning: Brandenburg Gate and Reichstag Building",
                "Afternoon: Holocaust Memorial",
                "Evening: Concert at Berliner Philharmonie"
            ],
            "3": [
                "Morning: Museum Island tour",
                "Afternoon: Berlin Wall Memorial",
                "Evening: Street food at Markthalle Neun"
            ],
            "4": [
                "Morning: Charlottenburg Palace visit",
                "Afternoon: Shopping at Kurfürstendamm",
                "Evening: Sunset at TV Tower"
            ]
        }
    },
    {
        "name": "Adventure Week - Costa Rica",
        "description": "A week-long adventure in Costa Rica's tropical paradise, perfect for nature and thrill-seekers.",
        "destination": "Costa Rica",
        "num_days": 7,
        "travel_type": "adventure",
        "suggested_group_size": "2-6",
        "base_itinerary": {
            "1": [
                "Arrival in San José",
                "Hotel check-in and orientation",
                "Evening: Local dinner and trip briefing"
            ],
            "2": [
                "Morning: Arenal Volcano hike",
                "Afternoon: Hot springs visit",
                "Evening: Wildlife night walk"
            ],
            "3": [
                "Full day: Zip-lining and canopy tours",
                "Evening: Traditional Costa Rican dinner"
            ],
            "4": [
                "Morning: Transfer to Manuel Antonio",
                "Afternoon: Beach time",
                "Evening: Sunset sailing trip"
            ],
            "5": [
                "Morning: Manuel Antonio National Park tour",
                "Afternoon: Surfing lesson",
                "Evening: Beach BBQ"
            ],
            "6": [
                "Morning: White water rafting",
                "Afternoon: Waterfall rappelling",
                "Evening: Farewell dinner"
            ],
            "7": [
                "Morning: Souvenir shopping",
                "Afternoon: Return flight from San José"
            ]
        }
    },
    {
        "name": "Relaxation Retreat - Bali",
        "description": "A peaceful 5-day retreat in Bali focusing on relaxation, wellness, and local culture.",
        "destination": "Bali, Indonesia",
        "num_days": 5,
        "travel_type": "relaxation",
        "suggested_group_size": "1-2",
        "base_itinerary": {
            "1": [
                "Morning: Arrival and spa treatment",
                "Afternoon: Hotel check-in and relaxation",
                "Evening: Welcome dinner at beach restaurant"
            ],
            "2": [
                "Morning: Yoga session",
                "Afternoon: Traditional massage",
                "Evening: Meditation class"
            ],
            "3": [
                "Morning: Visit to water temple",
                "Afternoon: Rice terrace walk",
                "Evening: Cooking class"
            ],
            "4": [
                "Morning: Beach yoga",
                "Afternoon: Spa treatment",
                "Evening: Sunset ceremony"
            ],
            "5": [
                "Morning: Final yoga session",
                "Afternoon: Departure"
            ]
        }
    }
]

def populate_templates():
    with app.app_context():
        # Clear existing templates
        TripTemplate.query.delete()
        
        # Add new templates
        for template_data in templates:
            template = TripTemplate(
                name=template_data["name"],
                description=template_data["description"],
                destination=template_data["destination"],
                num_days=template_data["num_days"],
                travel_type=template_data["travel_type"],
                suggested_group_size=template_data["suggested_group_size"],
                base_itinerary=template_data["base_itinerary"]
            )
            db.session.add(template)
        
        db.session.commit()
        print("Trip templates populated successfully!")

if __name__ == "__main__":
    populate_templates()
