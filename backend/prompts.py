"""Centralized prompt constants for AI-assisted features."""

AI_SOLUTION_PROMPT = """You are an expert veterinary assistant for Karnataka, India farmers.
A farmer has reported an issue:
- Animal Type: {animal_type}
- Symptoms: {symptoms}
- Description: {description}

Provide IMMEDIATE temporary measures (5-6 bullet points) the farmer can take BEFORE the veterinarian arrives.
Write in simple English and Kannada (dual language).
Include a disclaimer that this is temporary advice only."""

VOICE_ADVISORY_PROMPT = "A farmer reported: '{transcription}'. Give a short 2-sentence first aid tip."

FALLBACK_AI_SOLUTIONS = {
    "poultry": [
        "1. Immediately isolate sick birds from the flock.",
        "2. Disinfect the shed with phenol-based disinfectant.",
        "3. Ensure proper ventilation and reduce overcrowding.",
        "4. Provide electrolyte solution in drinking water.",
        "5. Contact veterinarian immediately if mortality exceeds 2%."
    ],
    "pig": [
        "1. Isolate affected pigs immediately.",
        "2. Strict biosecurity - no visitors, dedicated footwear.",
        "3. Disinfect premises with 2% sodium hydroxide or iodine.",
        "4. Do not move pigs to other farms or markets.",
        "5. Report to nearest veterinary officer within 24 hours."
    ],
    "cattle": [
        "1. Separate sick animals from healthy herd.",
        "2. Check temperature and provide shade/cool water.",
        "3. Do not share equipment between sick and healthy animals.",
        "4. Clean and disinfect feeding/watering troughs daily.",
        "5. Note: This is temporary advice. Vet visit is mandatory."
    ],
    "goat": [
        "1. Isolate affected goats immediately.",
        "2. Disinfect shed with lime powder and phenol.",
        "3. Provide clean drinking water with oral rehydration salts.",
        "4. Check for ticks and apply acaricides if needed.",
        "5. Contact veterinarian for PPR/ET vaccination if not done."
    ]
}
