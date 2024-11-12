from datetime import datetime
from app import db
from flask_login import UserMixin
from sqlalchemy import Index, UniqueConstraint
from sqlalchemy.orm import relationship

class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(64), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(256))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Add relationships with cascade rules
    trips = relationship('Trip', backref='owner', lazy=True, cascade='all, delete-orphan')
    preferences = relationship('UserPreference', backref='user', uselist=False, cascade='all, delete-orphan')
    reviews = relationship('Review', backref='user', lazy=True, cascade='all, delete-orphan')
    
    # Add indexes for better query performance
    __table_args__ = (
        Index('ix_user_email_lower', db.text('lower(email)')),
        Index('ix_user_username_lower', db.text('lower(username)')),
        UniqueConstraint('email', name='uq_user_email'),
    )

class Trip(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id', ondelete='CASCADE'), nullable=False)
    destination = db.Column(db.String(200), nullable=False)
    num_days = db.Column(db.Integer, nullable=False)
    travel_type = db.Column(db.String(50), nullable=False)
    num_people = db.Column(db.Integer, nullable=False)
    itinerary = db.Column(db.JSON, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    shared_with = db.Column(db.JSON, default=lambda: '[]')
    weather_data = db.Column(db.JSON)
    route_data = db.Column(db.JSON)
    template_id = db.Column(db.Integer, db.ForeignKey('trip_template.id', ondelete='SET NULL'), nullable=True)
    reviews = relationship('Review', backref='trip', lazy=True, cascade='all, delete-orphan')

class Review(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    trip_id = db.Column(db.Integer, db.ForeignKey('trip.id', ondelete='CASCADE'), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id', ondelete='CASCADE'), nullable=False)
    rating = db.Column(db.Integer, nullable=False)
    comment = db.Column(db.Text)
    photo_path = db.Column(db.String(255))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

class TripTemplate(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text, nullable=False)
    destination = db.Column(db.String(200), nullable=False)
    num_days = db.Column(db.Integer, nullable=False)
    travel_type = db.Column(db.String(50), nullable=False)
    suggested_group_size = db.Column(db.String(50), nullable=False)
    base_itinerary = db.Column(db.JSON, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    trips = relationship('Trip', backref='template', lazy=True)

class UserPreference(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id', ondelete='CASCADE'), nullable=False, unique=True)
    preferred_travel_types = db.Column(db.JSON, default=lambda: '[]')
    preferred_destinations = db.Column(db.JSON, default=lambda: '[]')
    preferred_trip_length = db.Column(db.Integer, default=3)  # Set default to 3 days
    preferred_group_size = db.Column(db.Integer, default=2)   # Set default to 2 people
    budget_range = db.Column(db.String(50))
    interests = db.Column(db.JSON, default=lambda: '[]')
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

class ItineraryCache(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    query_hash = db.Column(db.String(64), unique=True, nullable=False)
    destination = db.Column(db.String(200), nullable=False)
    num_days = db.Column(db.Integer, nullable=False)
    travel_type = db.Column(db.String(50), nullable=False)
    num_people = db.Column(db.Integer, nullable=False)
    response_data = db.Column(db.JSON, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    expires_at = db.Column(db.DateTime, nullable=False)
    
    __table_args__ = (
        Index('ix_itinerary_cache_query', 'destination', 'num_days', 'travel_type', 'num_people'),
    )
