from flask_restx import Api, Resource, fields, Namespace
from flask import request
from app import app
from models import Trip, User
from chat_advisor import get_chat_response
from weather import WeatherAPI
from flask_login import current_user, login_required

# Initialize Flask-RESTX
api = Api(
    app,
    version='1.0',
    title='AI Travel Planner API',
    description='API documentation for the AI Travel Planner application',
    doc='/api/docs'
)

# Create namespaces for different API categories
trips_ns = Namespace('trips', description='Trip operations')
chat_ns = Namespace('chat', description='AI Chat operations')
weather_ns = Namespace('weather', description='Weather forecast operations')
api.add_namespace(trips_ns, path='/api/trips')
api.add_namespace(chat_ns, path='/api/chat')
api.add_namespace(weather_ns, path='/api/weather')

# Define models for request/response documentation
trip_model = api.model('Trip', {
    'id': fields.Integer(readonly=True, description='Trip identifier'),
    'destination': fields.String(required=True, description='Trip destination'),
    'num_days': fields.Integer(required=True, description='Number of days'),
    'travel_type': fields.String(required=True, description='Type of travel'),
    'num_people': fields.Integer(required=True, description='Number of people'),
    'itinerary': fields.Raw(description='Trip itinerary'),
    'shared_with': fields.Raw(description='Users the trip is shared with')
})

chat_request = api.model('ChatRequest', {
    'message': fields.String(required=True, description='User message'),
    'context': fields.String(description='Optional context for the conversation')
})

weather_params = api.model('WeatherParams', {
    'location': fields.String(required=True, description='City name'),
    'num_days': fields.Integer(description='Number of days (1-14)'),
    'start_date': fields.Date(description='Start date (YYYY-MM-DD)'),
    'end_date': fields.Date(description='End date (YYYY-MM-DD)')
})

# Trip endpoints
@trips_ns.route('/')
class TripList(Resource):
    @trips_ns.doc('list_trips')
    @trips_ns.marshal_list_with(trip_model)
    @login_required
    def get(self):
        """List all trips for the current user"""
        return Trip.query.filter_by(user_id=current_user.id).all()

    @trips_ns.doc('create_trip')
    @trips_ns.expect(trip_model)
    @trips_ns.marshal_with(trip_model)
    @login_required
    def post(self):
        """Create a new trip"""
        data = request.json
        trip = Trip(
            user_id=current_user.id,
            destination=data['destination'],
            num_days=data['num_days'],
            travel_type=data['travel_type'],
            num_people=data['num_people'],
            itinerary=data.get('itinerary')
        )
        db.session.add(trip)
        db.session.commit()
        return trip

@trips_ns.route('/<int:id>')
@trips_ns.param('id', 'Trip identifier')
class TripResource(Resource):
    @trips_ns.doc('get_trip')
    @trips_ns.marshal_with(trip_model)
    @login_required
    def get(self, id):
        """Get a specific trip"""
        trip = Trip.query.get_or_404(id)
        if trip.user_id != current_user.id and str(current_user.id) not in (trip.shared_with or []):
            api.abort(403, "Not authorized to view this trip")
        return trip

    @trips_ns.doc('update_trip')
    @trips_ns.expect(trip_model)
    @trips_ns.marshal_with(trip_model)
    @login_required
    def put(self, id):
        """Update a trip"""
        trip = Trip.query.get_or_404(id)
        if trip.user_id != current_user.id:
            api.abort(403, "Not authorized to modify this trip")
        data = request.json
        for key, value in data.items():
            setattr(trip, key, value)
        db.session.commit()
        return trip

    @trips_ns.doc('delete_trip')
    @login_required
    def delete(self, id):
        """Delete a trip"""
        trip = Trip.query.get_or_404(id)
        if trip.user_id != current_user.id:
            api.abort(403, "Not authorized to delete this trip")
        db.session.delete(trip)
        db.session.commit()
        return '', 204

# Chat endpoints
@chat_ns.route('/')
class ChatResource(Resource):
    @chat_ns.doc('chat_with_ai')
    @chat_ns.expect(chat_request)
    @login_required
    def post(self):
        """Get AI chat response"""
        data = request.json
        response = get_chat_response(
            message=data['message'],
            context=data.get('context'),
            is_trip_suggestion='trip_suggestion' in data
        )
        return {'response': response}

# Weather endpoints
weather_api = WeatherAPI()

@weather_ns.route('/')
class WeatherResource(Resource):
    @weather_ns.doc('get_weather')
    @weather_ns.expect(weather_params)
    def get(self):
        """Get weather forecast"""
        location = request.args.get('location')
        num_days = request.args.get('num_days', type=int)
        start_date = request.args.get('start_date')
        end_date = request.args.get('end_date')
        
        if not location:
            api.abort(400, "Location parameter is required")
            
        try:
            if start_date and end_date:
                forecast = weather_api.get_forecast_by_dates(location, start_date, end_date)
            else:
                forecast = weather_api.get_forecast(location, num_days or 7)
            return forecast
        except Exception as e:
            api.abort(500, str(e))
