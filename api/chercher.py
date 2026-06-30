from http.server import BaseHTTPRequestHandler
from urllib.parse import urlparse, parse_qs
import json
import os
from apify_client import ApifyClient

VOTRE_API_KEY_APIFY = os.environ.get("APIFY_API_KEY")

class handler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.send_header('Content-type', 'application/json')
        self.end_headers()
        
        query_components = parse_qs(urlparse(self.path).query)
        search_query = query_components.get('q', [''])[0]
        
        if not search_query:
            self.wfile.write(json.dumps({"error": "Parametre q manquant"}).encode())
            return

        if not VOTRE_API_KEY_APIFY:
            self.wfile.write(json.dumps({"error": "Cle APIFY_API_KEY manquante sur Vercel"}).encode())
            return
            
        client = ApifyClient(VOTRE_API_KEY_APIFY)
        run_input = {
            "searchStrings": [search_query], 
            "maxCrawledPlacesPerSearch": 15, 
            "language": "fr"
        }
        
        try:
            # .start() au lieu de .call() : Lance le robot en arrière-plan instantanément (prend 1 seconde)
            client.actor("scrapers/google-maps-scraper").start(run_input=run_input)
            
            # On renvoie un message de succès immédiat à l'application
            self.wfile.write(json.dumps({
                "status": "success", 
                "message": "Le robot Apify a ete lance avec succes ! Les resultats arrivent sur ton Dashboard Apify d'ici 1 a 2 minutes."
            }).encode())
        except Exception as e:
            self.wfile.write(json.dumps({"error": f"Erreur Apify: {str(e)}"}).encode())
        
        return