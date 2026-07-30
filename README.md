# Karnataka Biosecurity Network

A complete community-driven biosecurity management system for Karnataka, India connecting farmers, veterinarians, district heads, and state heads for rapid disease response.

## Features

### Farmer Dashboard
- Simple, multilingual dashboard (English + Kannada)
- Biosecurity awareness tips
- Emergency reporting with image upload
- AI-generated temporary solutions (Gemini API integration)
- Vaccination record tracking
- Message/alerts inbox

### Veterinarian Dashboard
- View and accept pending cases in district
- Schedule farm visits
- Mark cases as resolved with notes
- Direct messaging to farmers
- Case management

### District Head Dashboard
- Key metrics summary (farms, cases, vets)
- Active disease cases tracking
- Incidents menu with status monitoring
- Vaccination coverage pie charts
- Send alerts to farmers and vets

### State Head Dashboard
- State-wide summary with charts
- District performance comparison
- Risk zone map (Red/Yellow/Green)
- AI-powered insights
- State-wide alert broadcasting
- Biosecurity status tracking

## Real Karnataka Data
The system is seeded with authentic data:
- 15 districts with real livestock census data
- Actual villages and talukas
- Priority diseases: FMD, PPR, HS, Avian Influenza, ASF
- Vaccination coverage statistics
- Risk zones based on outbreak patterns

## Tech Stack
- **Frontend:** HTML, CSS, JavaScript, Bootstrap 5, Chart.js, Leaflet Maps
- **Backend:** Flask, SQLAlchemy, Flask-Login
- **AI:** Google Gemini API (optional - falls back to rule-based system)
- **Database:** SQLite (can be upgraded to PostgreSQL)

## Setup Instructions

### 1. Install Dependencies
```bash
cd biosecurity_karnataka
pip install -r requirements.txt
```

### 2. Set Environment Variables (Optional - for AI)
```bash
export GEMINI_API_KEY="your_gemini_api_key_here"
```
Without API key, the system uses intelligent rule-based fallback suggestions.

### 3. Initialize Database
```bash
python app.py
```
The database will be automatically created and seeded with Karnataka data on first run.

### 4. Access the Application
Open browser: `http://localhost:5000`

## Demo Accounts

| Role | Username | Password |
|------|----------|----------|
| Farmer | farmer_bengaluru_urban_1 | farmer123 |
| Vet | vet_bengaluru_urban_1 | vet123 |
| District Head | district_bengaluru_urban | district123 |
| State Head | karnataka_state | state123 |

## Project Structure
```
biosecurity_karnataka/
├── app.py                 # Main Flask application
├── models.py              # Database models
├── data.py                # Karnataka seed data
├── requirements.txt       # Python dependencies
├── static/
│   ├── css/              # Stylesheets
│   ├── js/               # JavaScript files
│   ├── uploads/          # Uploaded incident images
│   └── images/           # Static images
└── templates/
    ├── base.html         # Base template
    ├── index.html        # Landing page
    ├── about.html        # About page
    ├── login.html        # Login page
    ├── signup.html       # Registration page
    ├── farmer_dashboard.html
    ├── vet_dashboard.html
    ├── district_dashboard.html
    ├── state_dashboard.html
    ├── report_emergency.html
    └── view_incident.html
```

## Key Features to Add in Production
1. **SMS Integration:** Twilio/Exotel for SMS alerts to farmers
2. **Push Notifications:** Firebase Cloud Messaging
3. **Mobile App:** React Native/Flutter companion app
4. **Blockchain:** Immutable vaccination records
5. **IoT Sensors:** Real-time temperature/humidity monitoring
6. **Multilingual:** Expand beyond Kannada to Telugu, Tamil, Marathi
7. **Offline Mode:** PWA for areas with poor connectivity
8. **Analytics:** Power BI/Tableau integration for advanced reporting

## License
This project is developed for the Animal Husbandry & Veterinary Services Department, Karnataka.
