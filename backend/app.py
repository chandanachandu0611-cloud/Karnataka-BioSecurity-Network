
import os
import json
import random
import sys
from datetime import datetime, timedelta
from pathlib import Path

import requests
from dotenv import load_dotenv
from flask import Flask, render_template, request, redirect, url_for, flash, jsonify, send_from_directory
from flask_login import LoginManager, login_user, logout_user, login_required, current_user
from werkzeug.utils import secure_filename

PROJECT_ROOT = Path(__file__).resolve().parent.parent
BACKEND_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(PROJECT_ROOT))
sys.path.insert(0, str(BACKEND_DIR))

from backend.models import db, User, District, FarmerProfile, VetProfile, DistrictHeadProfile, StateHeadProfile, Incident, VetSchedule, Message, VaccinationRecord, get_ist
from backend.data import seed_database, BIOSAFETY_TIPS, DISEASES, KARNATAKA_DISTRICTS
from backend.prompts import AI_SOLUTION_PROMPT, FALLBACK_AI_SOLUTIONS
from backend.gemma_service import analyze_image as analyze_image_with_gemini

KAGGLE_API_URL = "https://nativity-such-sheet.ngrok-free.dev"

# Load environment variables from .env file
load_dotenv(BACKEND_DIR / '.env')
load_dotenv(PROJECT_ROOT / '.env')

app = Flask(__name__, template_folder=str(PROJECT_ROOT / 'frontend' / 'templates'), static_folder=str(PROJECT_ROOT / 'frontend' / 'static'))
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'karnataka-biosecurity-2025-default-dev-key')
app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get('DATABASE_URL', f"sqlite:///{(PROJECT_ROOT / 'instance' / 'biosecurity_karnataka.db').as_posix()}")
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['UPLOAD_FOLDER'] = str(PROJECT_ROOT / 'frontend' / 'static' / 'uploads')
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB max file size

# Ensure upload directory exists
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

# Initialize extensions
db.init_app(app)
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'

ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


def get_uploaded_image(request_files):
    if 'image' in request_files:
        uploaded_file = request_files['image']
        if uploaded_file and getattr(uploaded_file, 'filename', ''):
            return uploaded_file

    if 'images' in request_files:
        files = request_files.getlist('images')
        for uploaded_file in files:
            if uploaded_file and getattr(uploaded_file, 'filename', ''):
                return uploaded_file

    return None


def first_non_empty(*values):
    for value in values:
        if value is None:
            continue
        if isinstance(value, str):
            stripped = value.strip()
            if stripped:
                return stripped
        elif value != '':
            return value
    return None


def normalize_analysis_payload(payload):
    if not isinstance(payload, dict):
        payload = {}

    nested_payload = payload.get('data') if isinstance(payload.get('data'), dict) else None
    if nested_payload:
        payload = {**nested_payload, **payload}

    title = first_non_empty(
        payload.get('issue_title'),
        payload.get('title'),
        payload.get('prediction'),
        payload.get('diagnosis'),
        payload.get('disease'),
        payload.get('name')
    )
    description = first_non_empty(
        payload.get('description'),
        payload.get('advice'),
        payload.get('message'),
        payload.get('recommendation'),
        payload.get('solution'),
        payload.get('details')
    )
    animal_type = first_non_empty(
        payload.get('animal_type'),
        payload.get('animal'),
        payload.get('livestock'),
        payload.get('species')
    )
    severity = first_non_empty(payload.get('severity'), payload.get('risk_level'), payload.get('risk'))

    symptoms = payload.get('symptoms')
    if isinstance(symptoms, str):
        symptoms_list = [item.strip() for item in symptoms.split(',') if item.strip()]
    elif isinstance(symptoms, (list, tuple, set)):
        symptoms_list = [str(item).strip() for item in symptoms if str(item).strip()]
    else:
        symptoms_list = []

    normalized_title = str(title or 'Pending Analysis').strip() or 'Pending Analysis'
    normalized_description = str(description or 'Pending Analysis').strip() or 'Pending Analysis'
    normalized_animal_type = str(animal_type or 'poultry').strip() or 'poultry'

    severity_value = 'medium'
    if severity:
        severity_text = str(severity).lower()
        if any(token in severity_text for token in ['high', 'severe', 'critical']):
            severity_value = 'high'
        elif any(token in severity_text for token in ['low', 'mild']):
            severity_value = 'low'

    return {
        'issue_title': normalized_title,
        'description': normalized_description,
        'animal_type': normalized_animal_type,
        'severity': severity_value,
        'symptoms': symptoms_list
    }


def analyze_image_with_kaggle(image_path, filename):
    if not image_path or not os.path.exists(image_path):
        return {
            'success': False,
            'data': {},
            'ai_disease': 'Pending Analysis',
            'ai_solution': 'Pending Analysis'
        }

    try:
        gemini_result = analyze_image_with_gemini(image_path)
        if gemini_result:
            analysis_data = normalize_analysis_payload(gemini_result)
            return {
                'success': True,
                'data': analysis_data,
                'ai_disease': analysis_data['issue_title'],
                'ai_solution': analysis_data['description']
            }

        with open(image_path, 'rb') as image_file:
            response = requests.post(
                KAGGLE_API_URL,
                files={'image': (filename, image_file, 'application/octet-stream')},
                headers={'ngrok-skip-browser-warning': 'true'},
                timeout=30
            )

        if response.status_code == 200:
            payload = {}
            try:
                payload = response.json() or {}
            except ValueError:
                payload = {}

            if not payload and response.text:
                try:
                    payload = json.loads(response.text)
                except ValueError:
                    payload = {'raw': response.text}

            analysis_data = normalize_analysis_payload(payload)
            title = analysis_data['issue_title']
            advice = analysis_data['description']

            return {
                'success': True,
                'data': analysis_data,
                'ai_disease': title,
                'ai_solution': advice
            }

        print(f"Kaggle analysis returned {response.status_code}: {response.text[:500]}")
        return {
            'success': False,
            'data': {},
            'ai_disease': 'Pending Analysis',
            'ai_solution': 'Pending Analysis'
        }
    except requests.exceptions.Timeout:
        print("Kaggle analysis timed out")
        return {
            'success': False,
            'data': {},
            'ai_disease': 'Pending Analysis',
            'ai_solution': 'Pending Analysis'
        }
    except Exception as exc:
        print(f"Kaggle analysis failed: {exc}")
        return {
            'success': False,
            'data': {},
            'ai_disease': 'Pending Analysis',
            'ai_solution': 'Pending Analysis'
        }


@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

# ============================================================
# AI SOLUTION GENERATOR (Gemini API Integration)
# ============================================================
def generate_ai_solution(description, symptoms, animal_type, images=None):
    """
    Generate temporary AI solution using Gemini API.
    In production, set GEMINI_API_KEY environment variable.
    Falls back to rule-based suggestions if API is not available.
    """
    api_key = os.environ.get('GEMINI_API_KEY')

    if not api_key:
        # Fallback rule-based system for demo
        solutions = FALLBACK_AI_SOLUTIONS

        base_solution = solutions.get(animal_type, solutions["cattle"])

        if "fever" in symptoms.lower() and "cough" in symptoms.lower():
            base_solution.append("⚠️ HIGH RISK: Respiratory symptoms with fever may indicate contagious disease. Immediate quarantine required.")
        if "diarrhea" in symptoms.lower() or "diarrhoea" in symptoms.lower():
            base_solution.append("💧 HYDRATION CRITICAL: Ensure oral electrolyte therapy continuously. Dehydration is the main cause of death.")
        if "sudden death" in symptoms.lower() or "mortality" in description.lower():
            base_solution.append("🚨 EMERGENCY: Multiple sudden deaths require immediate veterinary investigation and sample collection.")

        return "\n".join(base_solution)

    # Real Gemini API integration
    try:
        prompt = AI_SOLUTION_PROMPT.format(
            animal_type=animal_type,
            symptoms=symptoms,
            description=description,
        )

        url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-pro:generateContent?key={api_key}"
        headers = {"Content-Type": "application/json"}
        data = {
            "contents": [{"parts": [{"text": prompt}]}],
            "generationConfig": {"temperature": 0.3, "maxOutputTokens": 800}
        }

        response = requests.post(url, headers=headers, json=data, timeout=30)
        if response.status_code == 200:
            result = response.json()
            text = result["candidates"][0]["content"]["parts"][0]["text"]
            return text
        else:
            return generate_ai_solution(description, symptoms, animal_type)  # Fallback
    except Exception as e:
        print(f"AI API Error: {e}")
        return generate_ai_solution(description, symptoms, animal_type)  # Fallback

# ============================================================
# CONTEXT PROCESSORS
# ============================================================
@app.context_processor
def inject_globals():
    return {
        'now': get_ist(),
        'KARNATAKA_DISTRICTS': KARNATAKA_DISTRICTS
    }

# ============================================================
# LANDING & AUTH ROUTES
# ============================================================
@app.route('/')
def index():
    stats = {
        'total_farms': FarmerProfile.query.count(),
        'active_cases': Incident.query.filter(Incident.status.in_(['pending', 'assigned', 'in_progress'])).count(),
        'resolved_cases': Incident.query.filter_by(status='resolved').count(),
        'total_vets': VetProfile.query.count(),
        'districts_covered': District.query.count()
    }
    return render_template('index.html', stats=stats)

@app.route('/about')
def about():
    return render_template('about.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        user = User.query.filter_by(username=username).first()

        if user and user.check_password(password):
            login_user(user)
            flash('Login successful!', 'success')

            # Redirect based on role
            if user.role == 'farmer':
                return redirect(url_for('farmer_dashboard'))
            elif user.role == 'vet':
                return redirect(url_for('vet_dashboard'))
            elif user.role == 'district_head':
                return redirect(url_for('district_dashboard'))
            elif user.role == 'state_head':
                return redirect(url_for('state_dashboard'))
        else:
            flash('Invalid username or password', 'danger')

    return render_template('login.html')

@app.route('/signup', methods=['GET', 'POST'])
def signup():
    if request.method == 'POST':
        username = request.form.get('username')
        email = request.form.get('email')
        password = request.form.get('password')
        role = request.form.get('role')
        phone = request.form.get('phone')
        language = request.form.get('language', 'en')

        if User.query.filter((User.username == username) | (User.email == email)).first():
            flash('Username or email already exists', 'danger')
            return redirect(url_for('signup'))

        user = User(username=username, email=email, role=role, phone=phone, language=language)
        user.set_password(password)
        db.session.add(user)
        db.session.flush()

        # Create role-specific profile
        if role == 'farmer':
            district_id = request.form.get('district_id')
            profile = FarmerProfile(
                user_id=user.id,
                farm_name=request.form.get('farm_name'),
                village=request.form.get('village'),
                taluka=request.form.get('taluka'),
                district_id=district_id,
                farm_size = float(request.form.get('farm_size') or 0),
                livestock_type=request.form.get('livestock_type'),
                animal_count=int(request.form.get('animal_count', 0)),
                latitude=float(request.form.get('latitude', 0)),
                longitude=float(request.form.get('longitude', 0))
            )
            db.session.add(profile)

        elif role == 'vet':
            district_id = request.form.get('district_id')
            profile = VetProfile(
                user_id=user.id,
                registration_number=request.form.get('registration_number'),
                qualification=request.form.get('qualification'),
                specialization=request.form.get('specialization'),
                district_id=district_id,
                taluka=request.form.get('taluka'),
                is_verified=False
            )
            db.session.add(profile)

        elif role == 'district_head':
            district_id = request.form.get('district_id')
            profile = DistrictHeadProfile(
                user_id=user.id,
                district_id=district_id,
                phone_office=request.form.get('phone_office')
            )
            db.session.add(profile)

        elif role == 'state_head':
            profile = StateHeadProfile(
                user_id=user.id,
                state_name='Karnataka',
                phone_office=request.form.get('phone_office')
            )
            db.session.add(profile)

        db.session.commit()
        flash('Account created successfully! Please login.', 'success')
        return redirect(url_for('login'))

    districts = District.query.all()
    return render_template('signup.html', districts=districts)

@app.route('/logout')
@login_required
def logout():
    logout_user()
    flash('Logged out successfully', 'info')
    return redirect(url_for('index'))

# ============================================================
# FARMER ROUTES
# ============================================================
@app.route('/farmer/dashboard')
@login_required
def farmer_dashboard():
    if current_user.role != 'farmer':
        flash('Access denied', 'danger')
        return redirect(url_for('index'))

    profile = current_user.farmer_profile
    if not profile:
        flash('Profile not found', 'danger')
        return redirect(url_for('index'))

    incidents = Incident.query.filter_by(farmer_id=profile.id).order_by(Incident.created_at.desc()).all()
    vaccinations = VaccinationRecord.query.filter_by(farmer_id=profile.id).all()
    messages = Message.query.filter(
        (Message.recipient_role == 'farmer') | (Message.recipient_id == current_user.id)
    ).order_by(Message.created_at.desc()).limit(10).all()

    return render_template('farmer_dashboard.html', 
                         profile=profile, 
                         incidents=incidents, 
                         vaccinations=vaccinations,
                         messages=messages,
                         tips=BIOSAFETY_TIPS)

@app.route('/farmer/report-emergency', methods=['GET', 'POST'])
@login_required
def report_emergency():
    if request.method == 'POST':
        analyze_only = request.form.get('analyze_only') == '1'
        uploaded_file = get_uploaded_image(request.files)
        uploaded_image_path = None
        uploaded_image_filename = None

        if uploaded_file and getattr(uploaded_file, 'filename', ''):
            filename = secure_filename(uploaded_file.filename)
            upload_folder = app.config['UPLOAD_FOLDER']
            os.makedirs(upload_folder, exist_ok=True)
            uploaded_image_path = os.path.join(upload_folder, filename)
            uploaded_file.save(uploaded_image_path)
            uploaded_image_filename = filename

        analysis_result = analyze_image_with_kaggle(uploaded_image_path, uploaded_image_filename) if uploaded_image_path else {
            'success': False,
            'data': {},
            'ai_disease': 'Pending Analysis',
            'ai_solution': 'Pending Analysis'
        }

        if analyze_only:
            return jsonify(analysis_result)

        try:
            profile = getattr(current_user, 'farmer_profile', None)

            # Form Data
            title = request.form.get('title') or 'Emergency Report'
            animal_type = request.form.get('animal_type', 'Unspecified')
            affected_count = int(request.form.get('affected_count', 1) or 1)
            severity = request.form.get('severity', 'Medium')
            symptoms = request.form.get('symptoms', '')
            description = request.form.get('description', '')

            # If the farmer did not edit the fields, populate them from the Kaggle analysis.
            if analysis_result.get('data'):
                if not title or title == 'Emergency Report':
                    title = analysis_result['data'].get('issue_title') or title
                if not animal_type or animal_type == 'Unspecified':
                    animal_type = analysis_result['data'].get('animal_type') or animal_type
                if not severity or severity == 'Medium':
                    severity = analysis_result['data'].get('severity') or severity
                if not symptoms:
                    symptoms = ', '.join(analysis_result['data'].get('symptoms', []))
                if not description:
                    description = analysis_result['data'].get('description') or description

            # Upload Images & Format as JSON
            saved_image_names = []
            ai_disease = analysis_result.get('ai_disease', 'Pending Analysis')
            ai_solution = analysis_result.get('ai_solution', 'Pending Analysis')
            if uploaded_file and getattr(uploaded_file, 'filename', ''):
                filename = secure_filename(uploaded_file.filename)
                upload_folder = app.config['UPLOAD_FOLDER']
                os.makedirs(upload_folder, exist_ok=True)
                file_path = os.path.join(upload_folder, filename)
                if not os.path.exists(file_path):
                    uploaded_file.save(file_path)
                saved_image_names.append(filename)

            images_json = json.dumps(saved_image_names) if saved_image_names else "[]"

            # Process Voice File
            transcription = ""
            voice_filename = None
            voice_file = None

            if 'voice_file' in request.files:
                voice_file = request.files['voice_file']
            if voice_file and voice_file.filename != '':
                audio_filename = secure_filename(voice_file.filename)
                upload_folder = app.config['UPLOAD_FOLDER']
                os.makedirs(upload_folder, exist_ok=True)
                audio_path = os.path.join(upload_folder, audio_filename)
                voice_file.save(audio_path)
                voice_filename = audio_filename

                try:
                    from voice_service import process_farmer_voice
                    v_res = process_farmer_voice(audio_path)
                    transcription = v_res.get('transcription', '')
                    voice_advisory = v_res.get('advisory', '')
                    if ai_solution and ai_solution != 'Pending Analysis':
                        ai_solution = f"{voice_advisory}\n\nKaggle diagnosis: {ai_disease}\nAdvice: {ai_solution}" if voice_advisory else f"Kaggle diagnosis: {ai_disease}\nAdvice: {ai_solution}"
                    else:
                        ai_solution = voice_advisory or ai_solution
                except Exception as ve:
                    print(f"Voice Notice: {ve}")

            # Instantiate Incident matching models.py exact schema
            # Create Incident Record
            incident = Incident(
                farmer_id=profile.id if profile else None,
                district_id=profile.district_id if profile else None,
                title=title if title and title != 'Emergency Report' else ai_disease,
                description=description or ai_solution,
                symptoms=symptoms,
                animal_type=animal_type,
                affected_count=affected_count,
                severity=severity,
                images=images_json,
                status='pending',
                village=profile.village if profile else None,
                taluka=profile.taluka if profile else None,
                ai_solution=ai_solution
            )

            # Safely set voice attributes if they exist on the model
            

            if hasattr(incident, 'voice_url'):
                incident.voice_url = voice_filename
            elif hasattr(incident, 'audio_url'):
                incident.audio_url = voice_filename

            db.session.add(incident)
            db.session.commit()

            flash('Emergency report submitted successfully!', 'success')
            return redirect(url_for('farmer_dashboard'))

        except Exception as e:
            db.session.rollback()
            print(f"⚠️ Actual Submission Error: {e}")
            flash('Failed to submit report. Please try again.', 'danger')
            return redirect(url_for('report_emergency'))

    return render_template('report_emergency.html')


@app.route('/incident/<int:incident_id>')
@login_required
def view_incident(incident_id):
    incident = Incident.query.get_or_404(incident_id)
    return render_template('view_incident.html', incident=incident)


@app.route('/incident/<int:incident_id>/assign', methods=['POST'])
@login_required
def assign_incident(incident_id):
    incident = Incident.query.get_or_404(incident_id)
    profile = VetProfile.query.filter_by(user_id=current_user.id).first()

    if profile:
        incident.vet_id = profile.id
        incident.status = 'in_progress'
        db.session.commit()
        flash('Incident assigned to you successfully!', 'success')

    return redirect(url_for('vet_dashboard'))

# --- ADD THIS NEW ROUTE RIGHT HERE ---
@app.route('/incident/<int:incident_id>/resolve', methods=['POST'])
@login_required
def resolve_incident(incident_id):
    incident = Incident.query.get_or_404(incident_id)
    incident.status = 'resolved'
    db.session.commit()
    flash('Incident marked as resolved successfully!', 'success')
    return redirect(url_for('vet_dashboard'))


# --- ADDED ROUTE ---
@app.route('/incident/<int:incident_id>/schedule', methods=['POST'])
@login_required
def create_schedule(incident_id):
    incident = Incident.query.get_or_404(incident_id)
    visit_date = request.form.get('visit_date')
    notes = request.form.get('notes', '')
    
    flash('Visit scheduled successfully!', 'success')
    return redirect(url_for('view_incident', incident_id=incident.id))


@app.route('/uploads/<path:filename>')
def uploaded_file(filename):
    return send_from_directory(app.config['UPLOAD_FOLDER'], filename)
@app.route('/vet/dashboard')
@login_required
def vet_dashboard():
    profile = VetProfile.query.filter_by(user_id=current_user.id).first()
    
    # Fetch pending incidents (either matching district or all pending cases)
    if profile and profile.district_id:
        pending_incidents = Incident.query.filter(
            (Incident.district_id == profile.district_id) | (Incident.district_id == None),
            Incident.status == 'pending'
        ).all()
    else:
        pending_incidents = Incident.query.filter_by(status='pending').all()

    my_cases = Incident.query.filter_by(vet_id=profile.id if profile else None).all()
    
    return render_template('vet_dashboard.html', 
                           profile=profile, 
                           pending_incidents=pending_incidents,
                           incidents=pending_incidents,
                           my_cases=my_cases)
    


if __name__ == '__main__':
    app.run(host='0.0.0.0', debug=True, port=5000)