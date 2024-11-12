# AI Travel Planner

A web-based travel planning application that generates personalized trip itineraries using AI assistance. The platform features an AI Trip Advisor with multi-day itinerary generation, interactive chat interface, and alternative trip suggestions, integrated with real-time weather forecasts and URL-based Google Maps directions.

## Features

- AI-powered trip planning with personalized itineraries
- Multi-day itinerary generation
- Interactive chat interface for travel advice
- Real-time weather forecasts
- URL-based Google Maps directions
- Email/password authentication
- User preferences management
- Trip sharing system with controlled access
- Pre-defined trip templates for popular destinations
- Photo upload for trip reviews

## Architecture

```mermaid
graph TB
    subgraph Frontend
        UI[User Interface]
        JS[JavaScript Client]
        Templates[Flask Templates]
    end

    subgraph Backend
        Flask[Flask Server]
        Auth[Authentication]
        TripGen[Trip Generator]
        WeatherServ[Weather Service]
        ChatAdv[Chat Advisor]
        Cache[ItineraryCache]
    end

    subgraph External_APIs
        OpenAI[OpenAI GPT-4]
        Weather[OpenWeatherMap]
        Maps[Google Maps]
    end

    subgraph Database
        PostgreSQL[(PostgreSQL)]
        Templates_DB[(Trip Templates)]
    end

    UI --> JS
    JS --> Templates
    Templates --> Flask
    Flask --> Auth
    Flask --> TripGen
    Flask --> WeatherServ
    Flask --> ChatAdv
    
    TripGen --> Cache
    TripGen --> OpenAI
    WeatherServ --> Weather
    ChatAdv --> OpenAI
    
    Flask --> PostgreSQL
    PostgreSQL --> Templates_DB
    
    classDef frontend fill:#f9f,stroke:#333,stroke-width:2px
    classDef backend fill:#bbf,stroke:#333,stroke-width:2px
    classDef external fill:#bfb,stroke:#333,stroke-width:2px
    classDef database fill:#fbb,stroke:#333,stroke-width:2px
    
    class UI,JS,Templates frontend
    class Flask,Auth,TripGen,WeatherServ,ChatAdv,Cache backend
    class OpenAI,Weather,Maps external
    class PostgreSQL,Templates_DB database
```

## Tech Stack

- Backend: Flask (Python)
- Frontend: JavaScript
- Database: PostgreSQL
- APIs:
  - OpenAI GPT-4 Integration
  - OpenWeatherMap API
  - URL-based Google Maps Integration

## Development Setup

### Prerequisites

1. Python 3.11 or higher
2. PostgreSQL database
3. Node.js 20.x or higher
4. Required API Keys:
   - OpenAI API key
   - OpenWeatherMap API key
   - Google Maps API key (optional)

### Local Development Setup

1. Clone the repository:
   ```bash
   git clone https://github.com/yourusername/ai-travel-planner.git
   cd ai-travel-planner
   ```

2. Install Python dependencies:
   ```bash
   pip install -r requirements.txt
   ```

3. Install Node.js dependencies:
   ```bash
   npm install
   ```

4. Set up environment variables:
   Create a `.env` file in the root directory with:
   ```
   OPENAI_API_KEY=your_openai_api_key
   OPENWEATHERMAP_API_KEY=your_openweather_api_key
   FLASK_SECRET_KEY=your_secret_key
   DATABASE_URL=postgresql://username:password@localhost:5432/travel_planner
   ```

5. Initialize the database:
   ```bash
   flask db upgrade
   python populate_templates.py
   ```

6. Start the development server:
   ```bash
   python main.py
   ```

### Docker Run Setup

 1. Start docker compose configuration
 ```bash
 docker compose up
 ```
 2. Open app in docker container
    ```http://localhost:5000/```
   

### Key Pages to Document

#### Homepage
![Homepage](static/screenshots/homepage.png)
The landing page showcases:
- Main hero section with travel imagery
- Key features and benefits
- Clear call-to-action buttons
- Navigation menu

#### Dashboard
![Dashboard](static/screenshots/dashboard.png)
The user dashboard displays:
- Overview of user's trips
- Filter and sort options
- Quick access to trip management
- Recommended trips section

#### Trip Creation
![Trip Creation](static/screenshots/trip_creation.png)
The trip creation interface includes:
- Destination search
- Trip details form
- AI suggestion interface
- Interactive itinerary builder

#### AI Chat Advisor
![Chat Advisor](static/screenshots/chat_advisor.png)
The chat interface features:
- Real-time AI responses
- Travel recommendations
- Context-aware suggestions
- Message history

#### Trip View
![Trip View](static/screenshots/trip_view.png)
The trip details page shows:
- Complete itinerary
- Weather forecast integration
- Map visualization
- Sharing controls

## Swagger API Documentation
![Api Docs](static/screenshots/api_docs.png)

```
http://localhost:5000/api/docs
```
### Authentication Routes
- `POST /auth/login` - User login
- `POST /auth/register` - User registration
- `GET /auth/logout` - User logout

### Trip Management
- `GET /api/trips` - List user trips
- `POST /api/trips` - Create new trip
- `GET /api/trips/<id>` - Get trip details
- `PUT /api/trips/<id>` - Update trip
- `DELETE /api/trips/<id>` - Delete trip

### AI Features
- `POST /api/chat` - Chat with AI advisor
- `POST /api/trip_advisor` - Get trip suggestions

### Weather API
- `GET /api/weather` - Get weather forecast
  - Query params:
    - `location`: City name
    - `num_days`: Number of days (1-14)
    - `start_date`: Start date (YYYY-MM-DD)
    - `end_date`: End date (YYYY-MM-DD)


## Error Handling

The application includes comprehensive error handling for:
- Database operations
- API integrations
- Authentication flows
- File uploads
- User input validation

## License

This project is licensed under the MIT License - see the LICENSE file for details.
