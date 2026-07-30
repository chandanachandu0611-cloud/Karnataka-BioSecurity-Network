
from models import db, District, User, FarmerProfile, VetProfile, DistrictHeadProfile, StateHeadProfile, Incident, Message, VaccinationRecord, get_ist
from werkzeug.security import generate_password_hash
from datetime import datetime, timedelta
import random

# Real Karnataka districts with approximate data from 2024-2025 livestock census
KARNATAKA_DISTRICTS = [
    {"name": "Bengaluru Urban", "name_kn": "ಬೆಂಗಳೂರು ನಗರ", "villages": 612, "livestock": 850000, "poultry": 5200000, "pigs": 45000, "lat": 12.9716, "lng": 77.5946, "risk": "yellow", "vaccination": 78.5},
    {"name": "Mysuru", "name_kn": "ಮೈಸೂರು", "villages": 1356, "livestock": 1250000, "poultry": 3800000, "pigs": 82000, "lat": 12.2958, "lng": 76.6394, "risk": "green", "vaccination": 85.2},
    {"name": "Tumakuru", "name_kn": "ತುಮಕೂರು", "villages": 2543, "livestock": 1680000, "poultry": 2900000, "pigs": 65000, "lat": 13.3409, "lng": 77.1010, "risk": "yellow", "vaccination": 72.3},
    {"name": "Hassan", "name_kn": "ಹಾಸನ", "villages": 2546, "livestock": 980000, "poultry": 2100000, "pigs": 38000, "lat": 13.0072, "lng": 76.0990, "risk": "green", "vaccination": 88.1},
    {"name": "Mandya", "name_kn": "ಮಂಡ್ಯ", "villages": 1477, "livestock": 1120000, "poultry": 1800000, "pigs": 42000, "lat": 12.5243, "lng": 76.8953, "risk": "green", "vaccination": 91.4},
    {"name": "Shivamogga", "name_kn": "ಶಿವಮೊಗ್ಗ", "villages": 1880, "livestock": 890000, "poultry": 1500000, "pigs": 28000, "lat": 13.9299, "lng": 75.5681, "risk": "yellow", "vaccination": 76.8},
    {"name": "Belagavi", "name_kn": "ಬೆಳಗಾವಿ", "villages": 1275, "livestock": 2100000, "poultry": 4200000, "pigs": 95000, "lat": 15.8497, "lng": 74.4977, "risk": "red", "vaccination": 65.4},
    {"name": "Kalaburagi", "name_kn": "ಕಲಬುರಗಿ", "villages": 918, "livestock": 1450000, "poultry": 2600000, "pigs": 72000, "lat": 17.3297, "lng": 76.8343, "risk": "red", "vaccination": 58.9},
    {"name": "Dakshina Kannada", "name_kn": "ದಕ್ಷಿಣ ಕನ್ನಡ", "villages": 412, "livestock": 650000, "poultry": 3200000, "pigs": 55000, "lat": 12.9141, "lng": 74.8560, "risk": "green", "vaccination": 82.7},
    {"name": "Ballari", "name_kn": "ಬಳ್ಳಾರಿ", "villages": 1845, "livestock": 1380000, "poultry": 2200000, "pigs": 48000, "lat": 15.1394, "lng": 76.9214, "risk": "yellow", "vaccination": 69.5},
    {"name": "Chitradurga", "name_kn": "ಚಿತ್ರದುರ್ಗ", "villages": 1806, "livestock": 1150000, "poultry": 1900000, "pigs": 35000, "lat": 14.2251, "lng": 76.4000, "risk": "green", "vaccination": 79.3},
    {"name": "Davanagere", "name_kn": "ದಾವಣಗೆರೆ", "villages": 1292, "livestock": 920000, "poultry": 1700000, "pigs": 31000, "lat": 14.4644, "lng": 75.9218, "risk": "yellow", "vaccination": 74.6},
    {"name": "Dharwad", "name_kn": "ಧಾರವಾಡ", "villages": 522, "livestock": 780000, "poultry": 2100000, "pigs": 29000, "lat": 15.4589, "lng": 75.0078, "risk": "green", "vaccination": 83.1},
    {"name": "Gadag", "name_kn": "ಗದಗ", "villages": 374, "livestock": 520000, "poultry": 980000, "pigs": 18000, "lat": 15.4315, "lng": 75.6355, "risk": "green", "vaccination": 86.4},
    {"name": "Haveri", "name_kn": "ಹಾವೇರಿ", "villages": 703, "livestock": 680000, "poultry": 1200000, "pigs": 22000, "lat": 14.7951, "lng": 75.3991, "risk": "green", "vaccination": 81.7},
]

TALUKAS = {
    "Bengaluru Urban": ["Bengaluru North", "Bengaluru South", "Anekal", "Yelahanka"],
    "Mysuru": ["Mysuru", "Nanjangud", "T. Narasipura", "Hunsur", "Krishnarajanagara"],
    "Tumakuru": ["Tumakuru", "Tiptur", "Chikkanayakanahalli", "Koratagere", "Madhugiri"],
    "Hassan": ["Hassan", "Arsikere", "Channarayapatna", "Holénarsipura", "Arkalgud"],
    "Mandya": ["Mandya", "Maddur", "Malavalli", "Srirangapatna", "Pandavapura"],
    "Shivamogga": ["Shivamogga", "Sagara", "Bhadravati", "Thirthahalli", "Hosanagara"],
    "Belagavi": ["Belagavi", "Bailhongal", "Chikkodi", "Gokak", "Ramdurg"],
    "Kalaburagi": ["Kalaburagi", "Afzalpur", "Aland", "Chincholi", "Sedam"],
    "Dakshina Kannada": ["Mangaluru", "Bantwal", "Puttur", "Belthangady", "Sulya"],
    "Ballari": ["Ballari", "Hosapete", "Sandur", "Siruguppa", "Kurugodu"],
    "Chitradurga": ["Chitradurga", "Hiriyur", "Holalkere", "Hosadurga", "Molakalmuru"],
    "Davanagere": ["Davanagere", "Harihara", "Jagalur", "Honnali", "Channagiri"],
    "Dharwad": ["Dharwad", "Hubballi", "Kalghatgi", "Kundgol", "Navalgund"],
    "Gadag": ["Gadag", "Mundargi", "Nargund", "Ron", "Shirhatti"],
    "Haveri": ["Haveri", "Byadgi", "Hanagal", "Hirekerur", "Ranebennur"],
}

VILLAGES_SAMPLE = [
    "Kallahalli", "Kodihalli", "Gollahalli", "Koppal", "Hirebidanur",
    "Mallenahalli", "Dasanapura", "Kadirenahalli", "Bommenahalli", "Gowdagere",
    "Chikkabidare", "Doddabidare", "Karehalli", "Kenchapura", "Marur",
    "Nidagatta", "Rampura", "Siddapura", "Thippur", "Yelachagere"
]

BIOSAFETY_TIPS = [
    {
        "title_en": "Foot Baths at Entry Points",
        "title_kn": "ಪ್ರವೇಶ ದ್ವಾರದಲ್ಲಿ ಪಾದ ಸ್ನಾನ",
        "desc_en": "Keep disinfectant foot baths at all entry points to your farm. Change the solution daily.",
        "desc_kn": "ನಿಮ್ಮ ಫಾರ್ಮ್‌ನ ಎಲ್ಲಾ ಪ್ರವೇಶ ದ್ವಾರಗಳಲ್ಲಿ ನಿರ್ಜೀವಕಾರಕ ಪಾದ ಸ್ನಾನ ಇಟ್ಟಿರಿ. ದಿನನಿತ್ಯ ದ್ರಾವಣ ಬದಲಾಯಿಸಿ."
    },
    {
        "title_en": "Quarantine New Animals",
        "title_kn": "ಹೊಸ ಪ್ರಾಣಿಗಳನ್ನು ಪ್ರತ್ಯೇಕಿಸಿ",
        "desc_en": "Keep newly purchased animals separate for 14-21 days before introducing them to your herd.",
        "desc_kn": "ನಿಮ್ಮ ಹಿಂಡಿಗೆ ಸೇರಿಸುವ ಮೊದಲು ಹೊತಖರಿದಿಸಿದ ಪ್ರಾಣಿಗಳನ್ನು 14-21 ದಿನಗಳ ಕಾಲ ಪ್ರತ್ಯೇಕವಾಗಿ ಇಟ್ಟಿರಿ."
    },
    {
        "title_en": "Regular Disinfection",
        "title_kn": "ನಿಯಮಿತ ನಿರ್ಜೀವಕರಣ",
        "desc_en": "Clean and disinfect sheds, equipment, and vehicles regularly using approved disinfectants.",
        "desc_kn": "ಅನುಮೋದಿತ ನಿರ್ಜೀವಕಾರಕಗಳನ್ನು ಬಳಸಿ ಕಟ್ಟಡಗಳು, ಉಪಕರಣಗಳು ಮತ್ತು ವಾಹನಗಳನ್ನು ನಿಯಮಿತವಾಗಿ ಸ್ವಚ್ಛಗೊಳಿಸಿ."
    },
    {
        "title_en": "Control Visitors",
        "title_kn": "ಭೇಟಿದಾರರನ್ನು ನಿಯಂತ್ರಿಸಿ",
        "desc_en": "Maintain a visitor log. Restrict unnecessary visitors and ensure they use protective gear.",
        "desc_kn": "ಭೇಟಿದಾರರ ನೋಂದಣಿ ಇಟ್ಟಿರಿ. ಅನಗತ್ಯ ಭೇಟಿದಾರರನ್ನು ನಿರ್ಬಂಧಿಸಿ ಮತ್ತು ರಕ್ಷಣಾ ಪರಿಕರಗಳನ್ನು ಬಳಸಲು ಖಚಿತಪಡಿಸಿಕೊಳ್ಳಿ."
    },
    {
        "title_en": "Proper Waste Disposal",
        "title_kn": "ಸರಿಯಾದ ತ್ಯಾಜ್ಯ ವಿಲೇವಾರಿ",
        "desc_en": "Dispose dead animals and waste properly by deep burial or incineration. Never throw in open areas.",
        "desc_kn": "ಸತ್ತ ಪ್ರಾಣಿಗಳನ್ನು ಮತ್ತು ತ್ಯಾಜ್ಯವನ್ನು ಆಳವಾದ ಹೂಳುವಿಕೆ ಅಥವಾ ದಹನದ ಮೂಲಕ ಸರಿಯಾಗಿ ವಿಲೇವಾರಿ ಮಾಡಿ. ಎಂದಿಗೂ ತೆರೆದ ಪ್ರದೇಶಗಳಲ್ಲಿ ಎಸೆಯಬೇಡಿ."
    },
    {
        "title_en": "Vaccination Schedule",
        "title_kn": "ಲಸಿಕೆ ಕಾರ್ಯಕ್ರಮ",
        "desc_en": "Follow the vaccination calendar strictly. Maintain records of all vaccinations given to your animals.",
        "desc_kn": "ಲಸಿಕೆ ಕ್ಯಾಲೆಂಡರ್‌ನ್ನು ಕಟ್ಟುನಿಟ್ಟಾಗಿ ಪಾಲಿಸಿ. ನಿಮ್ಮ ಪ್ರಾಣಿಗಳಿಗೆ ನೀಡಿದ ಎಲ್ಲಾ ಲಸಿಕೆಗಳ ದಾಖಲೆಯನ್ನು ಇಟ್ಟಿರಿ."
    }
]

DISEASES = [
    "Foot and Mouth Disease (FMD)",
    "Peste des Petits Ruminants (PPR)",
    "Hemorrhagic Septicemia",
    "Avian Influenza",
    "African Swine Fever",
    "Newcastle Disease",
    "Infectious Bursal Disease (IBD)",
    "Mastitis",
    "Brucellosis",
    "Anthrax"
]

VACCINES = {
    "poultry": ["Ranikhet Disease Vaccine", "IBD Vaccine", "Fowl Pox Vaccine", "Marek's Disease Vaccine"],
    "pig": ["Classical Swine Fever Vaccine", "FMD Vaccine", "Swine Erysipelas Vaccine"],
    "cattle": ["FMD Vaccine", "HS Vaccine", "Brucella Vaccine", "Theileria Vaccine"],
    "goat": ["PPR Vaccine", "ET Vaccine", "FMD Vaccine"]
}

def seed_database():
    """Seed the database with initial Karnataka data"""
    # Create districts
    districts = {}
    for d in KARNATAKA_DISTRICTS:
        district = District(
            name=d["name"],
            name_kn=d["name_kn"],
            total_villages=d["villages"],
            total_livestock=d["livestock"],
            total_poultry=d["poultry"],
            total_pigs=d["pigs"],
            risk_level=d["risk"],
            latitude=d["lat"],
            longitude=d["lng"],
            vaccination_coverage=d["vaccination"]
        )
        db.session.add(district)
        districts[d["name"]] = district

    db.session.commit()

    # Create demo users for each role
    # State Head
    state_user = User(username="karnataka_state", email="state@ahvs.kar.gov.in", role="state_head", phone="080-12345678", language="en")
    state_user.set_password("state123")
    db.session.add(state_user)
    db.session.flush()

    state_profile = StateHeadProfile(user_id=state_user.id, state_name="Karnataka", phone_office="080-12345678")
    db.session.add(state_profile)

    # District Heads (one per district)
    district_users = []
    for i, (dname, dist) in enumerate(districts.items()):
        if i >= 5:  # Only create 5 district heads for demo
            break
        duser = User(username=f"district_{dname.lower().replace(' ', '_')}", email=f"dh{dname.lower().replace(' ', '')}@ahvs.kar.gov.in", role="district_head", phone=f"0827-{100000+i}", language="en")
        duser.set_password("district123")
        db.session.add(duser)
        db.session.flush()

        dprofile = DistrictHeadProfile(user_id=duser.id, district_id=dist.id, phone_office=f"0827-{100000+i}")
        db.session.add(dprofile)
        district_users.append(duser)

    # Vets (2 per selected district)
    vets = []
    selected_districts = list(districts.values())[:5]
    for dist in selected_districts:
        talukas = TALUKAS.get(dist.name, ["Taluka 1", "Taluka 2"])
        for j in range(2):
            vuser = User(
                username=f"vet_{dist.name.lower().replace(' ', '_')}_{j+1}",
                email=f"vet{j+1}@{dist.name.lower().replace(' ', '')}.kar.gov.in",
                role="vet",
                phone=f"987654{dist.id}{j}01",
                language="en"
            )
            vuser.set_password("vet123")
            db.session.add(vuser)
            db.session.flush()

            vprofile = VetProfile(
                user_id=vuser.id,
                registration_number=f"KA-VET-{dist.id}-{j+1}-2024",
                qualification="BVSc & AH" if j == 0 else "MVSc Veterinary Medicine",
                specialization=random.choice(["Poultry", "Swine", "Cattle", "Mixed Practice"]),
                district_id=dist.id,
                taluka=random.choice(talukas),
                is_verified=True
            )
            db.session.add(vprofile)
            vets.append(vprofile)

    # Farmers (3 per selected district)
    farmers = []
    livestock_types = ["poultry", "pig", "cattle", "goat", "mixed"]
    for dist in selected_districts:
        talukas = TALUKAS.get(dist.name, ["Taluka 1"])
        for k in range(3):
            fuser = User(
                username=f"farmer_{dist.name.lower().replace(' ', '_')}_{k+1}",
                email=f"farmer{dist.id}{k+1}@gmail.com",
                role="farmer",
                phone=f"987650{dist.id}{k}01",
                language=random.choice(["en", "kn"])
            )
            fuser.set_password("farmer123")
            db.session.add(fuser)
            db.session.flush()

            ltype = random.choice(livestock_types)
            count = random.randint(50, 500) if ltype == "poultry" else random.randint(5, 100)

            fprofile = FarmerProfile(
                user_id=fuser.id,
                farm_name=f"{random.choice(['Sri', 'Lakshmi', 'Ganapati', 'Krishna'])} Farms {k+1}",
                village=random.choice(VILLAGES_SAMPLE),
                taluka=random.choice(talukas),
                district_id=dist.id,
                farm_size=random.uniform(2.0, 50.0),
                livestock_type=ltype,
                animal_count=count,
                latitude=dist.latitude + random.uniform(-0.5, 0.5),
                longitude=dist.longitude + random.uniform(-0.5, 0.5),
                is_biosecure=random.choice([True, False])
            )
            db.session.add(fprofile)
            farmers.append(fprofile)

    db.session.commit()

    # Create sample incidents
    incident_statuses = ["pending", "assigned", "in_progress", "resolved"]
    severities = ["low", "medium", "high", "critical"]

    for i in range(15):
        farmer = random.choice(farmers)
        district = districts.get(farmer.district.name)
        status = random.choice(incident_statuses)
        vet = random.choice([v for v in vets if v.district_id == district.id]) if status != "pending" else None

        incident = Incident(
            farmer_id=farmer.id,
            vet_id=vet.id if vet else None,
            district_id=district.id,
            title=random.choice([
                "Sudden mortality in flock",
                "Respiratory distress observed",
                "Skin lesions on pigs",
                "Drop in egg production",
                "Fever and lameness in cattle",
                "Diarrhea in young animals",
                "Swelling around neck area",
                "Unusual behavior in birds"
            ]),
            description=random.choice([
                "Multiple animals showing symptoms since morning. Need urgent attention.",
                "Observed reduced feed intake and lethargy in affected animals.",
                "Three animals died overnight. Others appear weak.",
                "Vaccination was due last month but not done due to unavailability."
            ]),
            symptoms=random.choice([
                "Fever, Coughing, Nasal discharge",
                "Diarrhea, Dehydration, Weakness",
                "Skin lesions, Loss of appetite, Lameness",
                "Sudden death, Respiratory distress",
                "Drop in production, Ruffled feathers"
            ]),
            animal_type=farmer.livestock_type if farmer.livestock_type != "mixed" else random.choice(["poultry", "pig", "cattle"]),
            affected_count=random.randint(1, 20),
            severity=random.choice(severities),
            status=status,
            ai_solution=None,
            vet_notes=random.choice(["Administered antibiotics. Follow up in 3 days.", "Vaccination recommended.", "Isolated affected animals.", None]) if status == "resolved" else None,
            village=farmer.village,
            taluka=farmer.taluka,
            created_at=get_ist() - timedelta(days=random.randint(0, 30))
        )
        if status == "resolved":
            incident.resolved_at = incident.created_at + timedelta(days=random.randint(1, 5))
        db.session.add(incident)

    # Create sample vaccinations
    for farmer in farmers:
        if farmer.livestock_type in VACCINES:
            for vaccine in VACCINES[farmer.livestock_type][:2]:
                vdate = get_ist() - timedelta(days=random.randint(30, 180))
                vrecord = VaccinationRecord(
                    farmer_id=farmer.id,
                    animal_type=farmer.livestock_type,
                    vaccine_name=vaccine,
                    date_given=vdate.date(),
                    next_due_date=(vdate + timedelta(days=180)).date(),
                    district_id=farmer.district_id,
                    status="completed"
                )
                db.session.add(vrecord)

    # Create sample messages
    messages = [
        {"title": "Avian Influenza Alert", "content": "High alert in Belagavi district. Please report any unusual mortality immediately.", "type": "alert"},
        {"title": "Vaccination Camp", "content": "Free FMD vaccination camp scheduled for next Monday at your taluka veterinary hospital.", "type": "general"},
        {"title": "Biosecurity Workshop", "content": "Mandatory biosecurity training for all poultry farmers on 15th of this month.", "type": "general"},
        {"title": "Emergency: ASF Detected", "content": "African Swine Fever confirmed in neighboring district. Strict biosecurity measures advised.", "type": "emergency"},
    ]

    for msg in messages:
        message = Message(
            sender_id=state_user.id,
            recipient_role="farmer",
            title=msg["title"],
            content=msg["content"],
            message_type=msg["type"]
        )
        db.session.add(message)

    db.session.commit()
    print("Database seeded successfully with Karnataka data!")
