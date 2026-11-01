import os
import json
import google.generativeai as genai

class SynthesizerEngine:
    def __init__(self):
        self.name = "LLM Synthesis Engine"
        
        # Pulls the API key from your Render environment variables
        api_key = os.getenv("GEMINI_API_KEY")
        if api_key:
            genai.configure(api_key=api_key)
            # Using Gemini 1.5 Flash: It is incredibly fast and free for up to 15 RPM
            self.model = genai.GenerativeModel('gemini-1.5-flash')
        else:
            self.model = None

    def analyze(self, raw_data: dict, math_data: dict, vision_data: dict, text_data: dict) -> dict:
        """Merges all engine outputs and uses Gemini to deduce the final persona."""
        if not self.model:
            return {"error": "GEMINI_API_KEY not found in environment variables."}

        profile = raw_data.get("profile", {})
        
        # 1. Build the Intelligence Prompt
        prompt = f"""
        You are an OSINT behavioral analyst. Analyze this Instagram profile data and generate a structured dossier.
        
        Target: @{profile.get('username')} ({profile.get('full_name')})
        Bio (Decoded): {text_data.get('decoded_bio')}
        Account Category: {profile.get('business_category', 'Unknown')}
        
        Behavioral Metrics:
        - Engagement Rate: {math_data.get('engagement_rate_pct')}%
        - Chronotype: {math_data.get('chronotype')}
        - Content Formats: {math_data.get('format_strategy')}
        
        Visual & Content Intelligence:
        - Dominant Image Colors: {vision_data.get('aesthetic_palette')}
        - Text found inside their images (via OCR): {vision_data.get('in_image_text_snippets')}
        - Top Hashtags Used: {text_data.get('top_hashtags')}
        - Frequent Collaborators/Mentions: {text_data.get('top_collaborators')}
        
        Based STRICTLY on this data (do not hallucinate outside information), return a JSON object with exactly these keys:
        - "inferred_hobbies": (List of strings. Concrete hobbies or activities detected)
        - "aesthetic_vibe": (A 1-sentence description of their visual style)
        - "inferred_skills": (List of strings. Technical, creative, or physical skills demonstrated)
        - "executive_summary": (A sharp 2-sentence summary of who this person is and how they behave online)
        """

        try:
            # 2. Call Gemini API and force JSON output
            response = self.model.generate_content(
                prompt,
                generation_config={"response_mime_type": "application/json"}
            )
            
            # 3. Parse and return the dossier
            dossier = json.loads(response.text)
            return dossier
            
        except Exception as e:
            print(f"[!] Synthesis Error: {e}")
            return {
                "inferred_hobbies": ["Error analyzing hobbies"],
                "aesthetic_vibe": "Error analyzing vibe.",
                "inferred_skills": ["Unknown"],
                "executive_summary": "Could not generate summary due to API error."
            }
