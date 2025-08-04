# Importerar nödvändiga bibliotek
from http.server import BaseHTTPRequestHandler
import json
import os
import google.generativeai as genai

# Läser in vår hemliga Google API-nyckel från Vercels "Environment Variables"
# Detta är ett säkert sätt att hantera nycklar på, istället för att klistra in dem i koden.
API_KEY = os.environ.get('GOOGLE_API_KEY')
genai.configure(api_key=API_KEY)

# Huvudklassen för vår serverless funktion
class handler(BaseHTTPRequestHandler):

    def do_POST(self):
        # Läs längden på inkommande data
        content_length = int(self.headers['Content-Length'])
        # Läs själva datan (den är i JSON-format)
        post_data = self.rfile.read(content_length)
        # Gör om JSON-texten till ett Python-objekt
        data = json.loads(post_data)

        # Hämta ut texten som ska analyseras från objektet
        text_att_analysera = data.get('medText', '')

        # Om texten är tom, skicka ett felmeddelande
        if not text_att_analysera:
            self.send_response(400)
            self.send_header('Content-type', 'application/json')
            self.end_headers()
            self.wfile.write(json.dumps({'error': 'Textrutan kan inte vara tom.'}).encode())
            return
        
        # Samma instruktion som förut - vår "hemliga sås"
        instruktion = f"""
        Du är en expert på medicinsk kommunikation. Analysera följande medicinska text i två delar.
        Text att analysera: "{text_att_analysera}"

        DEL 1: Översättaren.
        Agera som en pedagogisk läkare. Översätt texten till enkel, klar svenska. Förklara alla facktermer med enkla metaforer. Målgruppen är en orolig patient.

        DEL 2: Kritikern.
        Agera nu som en cynisk forskningskritiker. Analysera texten. Finns det några uppenbara "red flags"? Spekulera kring potentiella svagheter i en verklig studie för ett sådant här läkemedel.
        """

        # Anropa Gemini API
        try:
            model = genai.GenerativeModel('gemini-1.5-flash')
            response = model.generate_content(instruktion)
            
            # Försök att dela upp svaret i två delar
            full_text = response.text
            parts = full_text.split("DEL 2: Kritikern.")
            
            translation_part = parts[0].replace("DEL 1: Översättaren.", "").strip()
            critique_part = parts[1].strip() if len(parts) > 1 else "Kunde inte extrahera kritikerdelen."

            # Bygg upp vårt svarsobjekt
            response_data = {
                'translation': translation_part,
                'critique': critique_part
            }

            # Skicka ett lyckat svar (statuskod 200)
            self.send_response(200)
            self.send_header('Content-type', 'application/json')
            # Tillåt anrop från alla domäner (viktigt för Vercel)
            self.send_header('Access-Control-Allow-Origin', '*')
            self.end_headers()
            self.wfile.write(json.dumps(response_data).encode())

        except Exception as e:
            # Om något går fel med Gemini, skicka ett felmeddelande
            self.send_response(500)
            self.send_header('Content-type', 'application/json')
            self.end_headers()
            self.wfile.write(json.dumps({'error': f'Ett fel uppstod med AI-tjänsten: {e}'}).encode())
            
        return