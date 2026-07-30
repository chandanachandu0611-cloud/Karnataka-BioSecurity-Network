from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime, timedelta, timezone
import json

db = SQLAlchemy()

def get_ist():
    """Helper to get current time in Indian Standard Time (IST) as naive datetime"""
    return (datetime.now(timezone(timedelta(hours=5, minutes=30)))).replace(tzinfo=None)

class User(UserMixin, db.Model):
    __tablename__ = 'users'
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(256), nullable=False)
    role = db.Column(db.String(20), nullable=False)  # farmer, vet, district_head, state_head
    phone = db.Column(db.String(15))
    language = db.Column(db.String(5), default='en')  # en or kn
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=get_ist)

    # Relationships
    farmer_profile = db.relationship('FarmerProfile', backref='user', uselist=False)
    vet_profile = db.relationship('VetProfile', backref='user', uselist=False)
    district_profile = db.relationship('DistrictHeadProfile', backref='user', uselist=False)
    state_profile = db.relationship('StateHeadProfile', backref='user', uselist=False)

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

    def get_role_display(self):
        roles = {
            'farmer': 'Farmer / ರೈತ',
            'vet': 'Veterinarian / ಪಶುವೈದ್ಯ',
            'district_head': 'District Head / ಜಿಲ್ಲಾ ಮುಖ್ಯಸ್ಥ',
            'state_head': 'State Head / ರಾಜ್ಯ ಮುಖ್ಯಸ್ಥ'
        }
        return roles.get(self.role, self.role)

class District(db.Model):
    __tablename__ = 'districts'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50), nullable=False)
    name_kn = db.Column(db.String(50))  # Kannada name
    total_villages = db.Column(db.Integer, default=0)
    total_livestock = db.Column(db.Integer, default=0)
    total_poultry = db.Column(db.Integer, default=0)
    total_pigs = db.Column(db.Integer, default=0)
    risk_level = db.Column(db.String(10), default='green')  # green, yellow, red
    latitude = db.Column(db.Float)
    longitude = db.Column(db.Float)
    vet_count = db.Column(db.Integer, default=0)
    farmer_count = db.Column(db.Integer, default=0)
    vaccination_coverage = db.Column(db.Float, default=0.0)

    # Relationships
    farmers = db.relationship('FarmerProfile', backref='district', lazy=True)
    vets = db.relationship('VetProfile', backref='district', lazy=True)
    incidents = db.relationship('Incident', backref='district', lazy=True)

class FarmerProfile(db.Model):
    __tablename__ = 'farmer_profiles'
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    farm_name = db.Column(db.String(100))
    village = db.Column(db.String(100))
    taluka = db.Column(db.String(100))
    district_id = db.Column(db.Integer, db.ForeignKey('districts.id'))
    farm_size = db.Column(db.Float)  # in acres
    livestock_type = db.Column(db.String(50))  # poultry, pig, cattle, mixed
    animal_count = db.Column(db.Integer, default=0)
    latitude = db.Column(db.Float)
    longitude = db.Column(db.Float)
    is_biosecure = db.Column(db.Boolean, default=False)

    # Relationships
    incidents = db.relationship('Incident', backref='farmer', lazy=True)
    vaccinations = db.relationship('VaccinationRecord', backref='farmer', lazy=True)

class VetProfile(db.Model):
    __tablename__ = 'vet_profiles'
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    registration_number = db.Column(db.String(50), unique=True)
    qualification = db.Column(db.String(100))
    specialization = db.Column(db.String(50))
    district_id = db.Column(db.Integer, db.ForeignKey('districts.id'))
    taluka = db.Column(db.String(100))
    is_verified = db.Column(db.Boolean, default=False)

    # Relationships
    assigned_incidents = db.relationship('Incident', backref='assigned_vet', lazy=True)
    schedules = db.relationship('VetSchedule', backref='vet', lazy=True)

class DistrictHeadProfile(db.Model):
    __tablename__ = 'district_head_profiles'
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    district_id = db.Column(db.Integer, db.ForeignKey('districts.id'))
    phone_office = db.Column(db.String(15))
    office_address = db.Column(db.Text)

class StateHeadProfile(db.Model):
    __tablename__ = 'state_head_profiles'
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    state_name = db.Column(db.String(50), default='Karnataka')
    phone_office = db.Column(db.String(15))
    office_address = db.Column(db.Text)

class Incident(db.Model):
    __tablename__ = 'incidents'
    id = db.Column(db.Integer, primary_key=True)
    farmer_id = db.Column(db.Integer, db.ForeignKey('farmer_profiles.id'), nullable=False)
    vet_id = db.Column(db.Integer, db.ForeignKey('vet_profiles.id'))
    district_id = db.Column(db.Integer, db.ForeignKey('districts.id'))
    title = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text)
    symptoms = db.Column(db.Text)
    animal_type = db.Column(db.String(50))  # poultry, pig, cattle
    affected_count = db.Column(db.Integer, default=1)
    severity = db.Column(db.String(20), default='medium')  # low, medium, high, critical
    images = db.Column(db.Text)  # JSON list of image filenames
    status = db.Column(db.String(20), default='pending')  # pending, assigned, in_progress, resolved
    ai_solution = db.Column(db.Text)
    vet_notes = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=get_ist)
    resolved_at = db.Column(db.DateTime)
    village = db.Column(db.String(100))
    taluka = db.Column(db.String(100))
    voice_url = db.Column(db.String(255), nullable=True)
    voice_transcription = db.Column(db.Text, nullable=True)

    def get_images_list(self):
        if self.images:
            return json.loads(self.images)
        return []

    def set_images_list(self, images_list):
        self.images = json.dumps(images_list)

class VetSchedule(db.Model):
    __tablename__ = 'vet_schedules'
    id = db.Column(db.Integer, primary_key=True)
    vet_id = db.Column(db.Integer, db.ForeignKey('vet_profiles.id'), nullable=False)
    incident_id = db.Column(db.Integer, db.ForeignKey('incidents.id'))
    scheduled_date = db.Column(db.DateTime, nullable=False)
    status = db.Column(db.String(20), default='scheduled')  # scheduled, completed, cancelled
    notes = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=get_ist)

class Message(db.Model):
    __tablename__ = 'messages'
    id = db.Column(db.Integer, primary_key=True)
    sender_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    recipient_id = db.Column(db.Integer, db.ForeignKey('users.id'))
    recipient_role = db.Column(db.String(20))  # farmer, vet, district_head, state_head, all
    district_id = db.Column(db.Integer, db.ForeignKey('districts.id'))
    title = db.Column(db.String(200))
    content = db.Column(db.Text, nullable=False)
    created_at = db.Column(db.DateTime, default=get_ist)
    is_read = db.Column(db.Boolean, default=False)
    message_type = db.Column(db.String(20), default='general')  # general, alert, emergency

    sender = db.relationship('User', foreign_keys=[sender_id], backref='sent_messages')
    recipient = db.relationship('User', foreign_keys=[recipient_id], backref='received_messages')

class VaccinationRecord(db.Model):
    __tablename__ = 'vaccination_records'
    id = db.Column(db.Integer, primary_key=True)
    farmer_id = db.Column(db.Integer, db.ForeignKey('farmer_profiles.id'), nullable=False)
    animal_type = db.Column(db.String(50), nullable=False)
    vaccine_name = db.Column(db.String(100), nullable=False)
    date_given = db.Column(db.Date, nullable=False)
    next_due_date = db.Column(db.Date)
    vet_id = db.Column(db.Integer, db.ForeignKey('vet_profiles.id'))
    district_id = db.Column(db.Integer, db.ForeignKey('districts.id'))
    notes = db.Column(db.Text)
    status = db.Column(db.String(20), default='completed')  # completed, pending, overdue
