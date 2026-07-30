import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from backend.app import normalize_analysis_payload


def test_normalize_analysis_payload_uses_kaggle_response_fields():
    payload = {
        'title': 'Fowl Pox Detected',
        'advice': 'Isolate the flock and consult a vet.',
        'animal_type': 'Poultry',
        'severity': 'High'
    }

    normalized = normalize_analysis_payload(payload)

    assert normalized['issue_title'] == 'Fowl Pox Detected'
    assert normalized['description'] == 'Isolate the flock and consult a vet.'
    assert normalized['animal_type'] == 'Poultry'
    assert normalized['severity'] == 'High'
