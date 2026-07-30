from backend.app import normalize_analysis_payload

payload = {
    'title': 'Fowl Pox Detected',
    'advice': 'Isolate the flock and consult a vet.',
    'animal_type': 'Poultry',
    'severity': 'High'
}

print(normalize_analysis_payload(payload))
