import os

def process_farmer_voice(audio_file_path):
    """
    Safely processes audio without external API recursion errors.
    """
    transcription = "Audio recording attached by farmer."
    advisory = "Emergency report submitted. Please keep the affected animals isolated and monitored until a veterinarian connects with you."

    try:
        # Check if Sarvam API key exists
        sarvam_key = os.getenv("SARVAM_API_KEY")
        if sarvam_key and audio_file_path and os.path.exists(audio_file_path):
            from sarvamai import SarvamAI
            client = SarvamAI(api_key=sarvam_key)
            with open(audio_file_path, "rb") as audio_file:
                res = client.speech_to_text.transcribe(file=audio_file, model="saaras:v1")
                if hasattr(res, "transcript") and res.transcript:
                    transcription = str(res.transcript)
    except Exception as err:
        # Avoid printing full object 'err' to prevent maximum recursion depth errors
        print("Voice STT Notice: API call skipped or encountered connection issue.")

    try:
        # Check if Gemini API key exists
        gemini_key = os.getenv("GEMINI_API_KEY")
        if gemini_key:
            from google import genai
            g_client = genai.Client(api_key=gemini_key)
            prompt = f"A farmer reported: '{transcription}'. Give a short 2-sentence first aid tip."
            response = g_client.models.generate_content(model="gemini-2.5-flash", contents=prompt)
            if response and hasattr(response, "text") and response.text:
                advisory = str(response.text).strip()
    except Exception as err:
        print("Voice Advisory Notice: AI generation skipped or encountered connection issue.")

    return {
        "transcription": transcription,
        "advisory": advisory
    }