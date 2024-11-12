import os
import json
import requests
from datetime import datetime, timedelta
from flask import render_template, redirect, url_for, flash, request, jsonify
from flask_login import login_required, current_user
from werkzeug.utils import secure_filename
from sqlalchemy import or_, text
from app import app, db
from models import Trip, User, Review, TripTemplate, UserPreference
from utils.image_handler import save_image, allowed_file
from trip_generator import generate_trip_plan
from chat_advisor import get_chat_response
from weather import WeatherAPI

# Initialize WeatherAPI
weather_api = WeatherAPI()

# Add custom template filter for JSON
@app.template_filter('fromjson')
def fromjson_filter(value):
    try:
        return json.loads(value) if value else []
    except (TypeError, json.JSONDecodeError):
        return []

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/dashboard')
@login_required
def dashboard():
    # Get filter parameters
    search = request.args.get('search', '')
    travel_type = request.args.get('travel_type', '')
    duration = request.args.get('duration', '')
    sort = request.args.get('sort', 'newest')
    
    # Base query
    query = Trip.query.filter_by(user_id=current_user.id)
    
    # Apply filters
    if search:
        query = query.filter(Trip.destination.ilike(f'%{search}%'))
    if travel_type:
        query = query.filter_by(travel_type=travel_type)
    if duration:
        if duration == '1-3':
            query = query.filter(Trip.num_days.between(1, 3))
        elif duration == '4-7':
            query = query.filter(Trip.num_days.between(4, 7))
        elif duration == '8+':
            query = query.filter(Trip.num_days >= 8)
    
    # Apply sorting
    if sort == 'oldest':
        query = query.order_by(Trip.created_at.asc())
    elif sort == 'destination':
        query = query.order_by(Trip.destination.asc())
    else:  # newest
        query = query.order_by(Trip.created_at.desc())
    
    trips = query.all()
    
    # Get recommended trips based on user preferences
    recommended_trips = []
    if hasattr(current_user, 'preferences') and current_user.preferences:
        pref = current_user.preferences
        try:
            preferred_types = json.loads(pref.preferred_travel_types) if pref.preferred_travel_types else []
            if preferred_types and pref.preferred_trip_length:
                recommended_query = Trip.query.filter(
                    Trip.user_id != current_user.id,
                    Trip.travel_type.in_(preferred_types)
                )
                if pref.preferred_trip_length:
                    recommended_query = recommended_query.filter(
                        Trip.num_days.between(
                            max(1, pref.preferred_trip_length - 2),
                            min(30, pref.preferred_trip_length + 2)
                        )
                    )
                recommended_trips = recommended_query.limit(3).all()
        except (json.JSONDecodeError, TypeError) as e:
            app.logger.error(f"Error parsing user preferences: {str(e)}")
    
    return render_template('dashboard.html', 
                         trips=trips, 
                         recommended_trips=recommended_trips)

@app.route('/shared_trips')
@login_required
def shared_trips():
    # Get filter parameters
    search = request.args.get('search', '')
    travel_type = request.args.get('travel_type', '')
    duration = request.args.get('duration', '')
    sort = request.args.get('sort', 'newest')
    
    # Get base query for trips shared with current user
    query = Trip.query.filter(
        Trip.shared_with.cast(db.String).contains(str(current_user.id))
    )
    
    # Apply filters
    if search:
        search_terms = search.split()
        search_filters = []
        for term in search_terms:
            search_filters.append(Trip.destination.ilike(f'%{term}%'))
        query = query.filter(or_(*search_filters))

    if travel_type:
        query = query.filter(Trip.travel_type.ilike(f'%{travel_type}%'))

    if duration:
        if duration == '1-3':
            query = query.filter(Trip.num_days <= 3)
        elif duration == '4-7':
            query = query.filter(Trip.num_days > 3, Trip.num_days <= 7)
        elif duration == '8+':
            query = query.filter(Trip.num_days > 7)

    # Apply sorting
    if sort == 'oldest':
        query = query.order_by(Trip.created_at.asc())
    elif sort == 'destination':
        query = query.order_by(Trip.destination.asc())
    else:  # newest
        query = query.order_by(Trip.created_at.desc())

    trips = query.all()
    return render_template('shared_trips.html', trips=trips)

@app.route('/preferences', methods=['GET', 'POST'])
@login_required
def preferences():
    # Get or create user preferences
    user_prefs = UserPreference.query.filter_by(user_id=current_user.id).first()
    if not user_prefs:
        user_prefs = UserPreference(user_id=current_user.id)
        db.session.add(user_prefs)
        db.session.commit()
    
    if request.method == 'POST':
        try:
            # Handle travel types (checkboxes)
            travel_types = request.form.getlist('travel_types')
            user_prefs.preferred_travel_types = json.dumps(travel_types)
            
            # Handle destinations
            destinations = request.form.get('preferred_destinations', '').split(',')
            user_prefs.preferred_destinations = json.dumps([d.strip() for d in destinations if d.strip()])
            
            # Handle numeric fields
            user_prefs.preferred_trip_length = int(request.form.get('preferred_trip_length', 1))
            user_prefs.preferred_group_size = int(request.form.get('preferred_group_size', 1))
            
            # Handle budget range
            user_prefs.budget_range = request.form.get('budget_range')
            
            # Handle interests
            interests = request.form.get('interests', '').split(',')
            user_prefs.interests = json.dumps([i.strip() for i in interests if i.strip()])
            
            db.session.commit()
            flash('Preferences updated successfully!', 'success')
            return redirect(url_for('dashboard'))
            
        except Exception as e:
            db.session.rollback()
            app.logger.error(f"Error updating preferences: {str(e)}")
            flash('Error updating preferences. Please try again.', 'danger')
    
    return render_template('preferences.html', user_preferences=user_prefs)

@app.route('/trip/<int:trip_id>', methods=['GET', 'POST'])
@login_required
def view_trip(trip_id):
    trip = Trip.query.get_or_404(trip_id)
    
    # Check if user has permission to view this trip
    if trip.user_id != current_user.id and str(current_user.id) not in (trip.shared_with or []):
        flash('You do not have permission to view this trip.', 'danger')
        return redirect(url_for('dashboard'))
    
    if request.method == 'POST':
        # Handle sharing trip
        share_user_id = request.form.get('share_user_id')
        unshare = request.form.get('unshare')
        
        if share_user_id and trip.user_id == current_user.id:
            try:
                shared_with = json.loads(trip.shared_with) if trip.shared_with else []
                if share_user_id not in shared_with:
                    shared_with.append(share_user_id)
                    trip.shared_with = json.dumps(shared_with)
                    db.session.commit()
                    flash('Trip shared successfully!', 'success')
            except Exception as e:
                app.logger.error(f"Error sharing trip: {str(e)}")
                flash('Error sharing trip. Please try again.', 'danger')
                
        elif unshare and trip.user_id == current_user.id:
            try:
                shared_with = json.loads(trip.shared_with) if trip.shared_with else []
                if unshare in shared_with:
                    shared_with.remove(unshare)
                    trip.shared_with = json.dumps(shared_with)
                    db.session.commit()
                    flash('Sharing permission removed.', 'success')
            except Exception as e:
                app.logger.error(f"Error removing share permission: {str(e)}")
                flash('Error removing share permission. Please try again.', 'danger')
        
        # Handle review submission
        rating = request.form.get('rating')
        comment = request.form.get('comment')
        if rating and comment:
            try:
                # Handle photo upload if present
                photo_path = None
                if 'photo' in request.files:
                    photo = request.files['photo']
                    if photo and allowed_file(photo.filename):
                        photo_path = save_image(photo)
                
                review = Review(
                    trip_id=trip.id,
                    user_id=current_user.id,
                    rating=int(rating),
                    comment=comment,
                    photo_path=photo_path
                )
                db.session.add(review)
                db.session.commit()
                flash('Review submitted successfully!', 'success')
            except Exception as e:
                app.logger.error(f"Error submitting review: {str(e)}")
                flash('Error submitting review. Please try again.', 'danger')
                
        return redirect(url_for('view_trip', trip_id=trip.id))
    
    # Get reviews for the trip
    reviews = Review.query.filter_by(trip_id=trip.id).order_by(Review.created_at.desc()).all()
    
    # Get available users for sharing (exclude owner and already shared users)
    if trip.user_id == current_user.id:
        shared_with = json.loads(trip.shared_with) if trip.shared_with else []
        available_users = User.query.filter(
            User.id != current_user.id,
            ~User.id.in_([int(uid) for uid in shared_with])
        ).all()
        shared_users = User.query.filter(User.id.in_([int(uid) for uid in shared_with])).all()
    else:
        available_users = []
        shared_users = []

    return render_template('trip_view.html', 
                         trip=trip,
                         reviews=reviews,
                         is_owner=trip.user_id == current_user.id,
                         available_users=available_users,
                         shared_users=shared_users)

@app.route('/create_trip', methods=['GET', 'POST'])
@login_required
def create_trip():
    if request.method == 'POST':
        try:
            # Get form data
            destination = request.form.get('destination')
            num_days = int(request.form.get('num_days', 0))
            travel_type = request.form.get('travel_type')
            num_people = int(request.form.get('num_people', 0))
            itinerary_data = request.form.get('itinerary')
            
            # Validate required inputs
            if not all([destination, num_days, travel_type, num_people]):
                flash('Please fill in all required fields.', 'danger')
                return redirect(url_for('create_trip'))
            
            if num_days < 1 or num_days > 30:
                flash('Number of days must be between 1 and 30.', 'danger')
                return redirect(url_for('create_trip'))
            
            if num_people < 1:
                flash('Number of people must be at least 1.', 'danger')
                return redirect(url_for('create_trip'))
            
            # Handle itinerary
            itinerary = None
            if itinerary_data:
                try:
                    itinerary = json.loads(itinerary_data)
                except json.JSONDecodeError:
                    app.logger.warning("Invalid itinerary JSON provided")
                    itinerary = None
            
            # Generate itinerary if not provided or invalid
            if not itinerary:
                try:
                    generated_plans = generate_trip_plan(
                        destination=destination,
                        num_days=num_days,
                        travel_type=travel_type,
                        num_people=num_people
                    )
                    if generated_plans and len(generated_plans) > 0:
                        itinerary = generated_plans[0].get('itinerary')
                    if not itinerary:
                        flash('Failed to generate itinerary. Please try again or provide a manual itinerary.', 'warning')
                        return redirect(url_for('create_trip'))
                except Exception as e:
                    app.logger.error(f"Error generating itinerary: {str(e)}")
                    flash('Error generating itinerary. Please try again or provide a manual itinerary.', 'danger')
                    return redirect(url_for('create_trip'))
            
            # Create new trip
            trip = Trip(
                user_id=current_user.id,
                destination=destination,
                num_days=num_days,
                travel_type=travel_type,
                num_people=num_people,
                itinerary=itinerary
            )
            
            db.session.add(trip)
            db.session.commit()
            
            flash('Trip created successfully!', 'success')
            return redirect(url_for('view_trip', trip_id=trip.id))
            
        except ValueError as e:
            flash('Invalid numeric value provided.', 'danger')
            return redirect(url_for('create_trip'))
        except Exception as e:
            app.logger.error(f"Error creating trip: {str(e)}")
            flash('An error occurred while creating the trip.', 'danger')
            return redirect(url_for('create_trip'))
    
    return render_template('trip_create.html')

@app.route('/trip/<int:trip_id>/delete', methods=['POST'])
@login_required
def delete_trip(trip_id):
    trip = Trip.query.get_or_404(trip_id)
    
    if trip.user_id != current_user.id:
        flash('You do not have permission to delete this trip.', 'danger')
        return redirect(url_for('dashboard'))
    
    try:
        db.session.delete(trip)
        db.session.commit()
        flash('Trip deleted successfully.', 'success')
    except Exception as e:
        db.session.rollback()
        app.logger.error(f"Error deleting trip: {str(e)}")
        flash('Error deleting trip. Please try again.', 'danger')
    
    return redirect(url_for('dashboard'))

@app.route('/chat_advisor')
@login_required
def chat_advisor():
    return render_template('chat_advisor.html')

@app.route('/api/chat', methods=['POST'])
@login_required
def chat():
    try:
        data = request.get_json()
        if not data:
            return jsonify({'error': 'Invalid request data'}), 400
            
        message = data.get('message')
        if not message:
            return jsonify({'error': 'No message provided'}), 400
            
        response = get_chat_response(message)
        return jsonify({'response': response})
        
    except Exception as e:
        app.logger.error(f"Chat API error: {str(e)}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/trip_advisor', methods=['POST'])
@login_required
def get_trip_suggestions():
    try:
        data = request.get_json()
        if not data:
            return jsonify({'error': 'Invalid request data'}), 400
            
        description = data.get('description')
        if not description:
            return jsonify({'error': 'No description provided'}), 400
        
        # Include user preferences in the request if available
        if hasattr(current_user, 'preferences') and current_user.preferences:
            pref = current_user.preferences
            context = {
                'preferred_travel_types': json.loads(pref.preferred_travel_types) if pref.preferred_travel_types else [],
                'preferred_destinations': json.loads(pref.preferred_destinations) if pref.preferred_destinations else [],
                'preferred_trip_length': pref.preferred_trip_length,
                'preferred_group_size': pref.preferred_group_size,
                'budget_range': pref.budget_range,
                'interests': json.loads(pref.interests) if pref.interests else []
            }
            response = get_chat_response(description, context=json.dumps(context), is_trip_suggestion=True)
        else:
            response = get_chat_response(description, is_trip_suggestion=True)
            
        return jsonify(response)
            
    except Exception as e:
        app.logger.error(f"Trip advisor API error: {str(e)}")
        return jsonify({
            'error': str(e),
            'suggestions': None,
            'using_fallback': False,
            'generation_status': f'Error: {str(e)}'
        }), 500

@app.route('/api/weather')
def get_weather():
    """Get weather data for a location."""
    try:
        location = request.args.get('location')
        if not location:
            return jsonify({'error': 'Location is required'}), 400

        num_days = request.args.get('num_days')
        start_date = request.args.get('start_date')
        end_date = request.args.get('end_date')

        # Convert num_days to integer if provided
        if num_days:
            try:
                num_days = int(num_days)
                if num_days < 1 or num_days > 14:
                    return jsonify({'error': 'Number of days must be between 1 and 14'}), 400
            except ValueError:
                return jsonify({'error': 'Invalid number of days'}), 400

        # Validate date range if provided
        if start_date and end_date:
            try:
                start = datetime.strptime(start_date, '%Y-%m-%d')
                end = datetime.strptime(end_date, '%Y-%m-%d')
                if end < start:
                    return jsonify({'error': 'End date must be after start date'}), 400
                
                date_diff = (end - start).days
                if date_diff > 14:
                    return jsonify({'error': 'Date range cannot exceed 14 days'}), 400
            except ValueError:
                return jsonify({'error': 'Invalid date format'}), 400

        # Get weather data
        weather_data = weather_api.get_weather_data(
            location=location,
            num_days=num_days,
            start_date=start_date,
            end_date=end_date
        )
        
        return jsonify(weather_data)

    except ValueError as e:
        return jsonify({'error': str(e)}), 400
    except Exception as e:
        app.logger.error(f"Weather API error: {str(e)}")
        return jsonify({'error': 'Failed to fetch weather data'}), 500

def get_alert_severity(event, description):
    """Determine the severity of a weather alert based on its event type and description."""
    severe_keywords = ['severe', 'extreme', 'danger', 'warning', 'hurricane', 'tornado']
    moderate_keywords = ['watch', 'advisory', 'moderate']
    
    event_lower = event.lower()
    desc_lower = description.lower()
    
    # Check for severe conditions
    for keyword in severe_keywords:
        if keyword in event_lower or keyword in desc_lower:
            return 'Severe'
            
    # Check for moderate conditions
    for keyword in moderate_keywords:
        if keyword in event_lower or keyword in desc_lower:
            return 'Moderate'
            
    # Default to mild
    return 'Mild'

def get_active_alerts(alerts, timestamp):
    """Filter alerts that are active at the given timestamp."""
    active_alerts = []
    for alert in alerts:
        if alert['start'] <= timestamp <= alert['end']:
            active_alerts.append(alert)
    return active_alerts

@app.errorhandler(404)
def not_found_error(error):
    return render_template('errors/404.html'), 404

@app.errorhandler(500)
def internal_error(error):
    db.session.rollback()
    return render_template('errors/500.html'), 500