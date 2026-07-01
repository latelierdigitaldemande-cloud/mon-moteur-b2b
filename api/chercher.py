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
        
        # Correction de la syntaxe de l'encodage en octets (.encode() englobe tout le texte)
        if not search_query or not VOTRE_API_KEY_APIFY:
            self.wfile.write(json.dumps([]).encode('utf-8'))
            return
            
        client = ApifyClient(VOTRE_API_KEY_APIFY)
        run_input = {
            "searchStrings": [search_query], 
            "maxCrawledPlacesPerSearch": 15, 
            "language": "fr"
        }
        
        try:
            client.actor("scrapers/google-maps-scraper").start(run_input=run_input)
            
            reponse_valide = [{
                "title": "🤖 ROBOT DÉMARRÉ AVEC SUCCÈS !",
                "phone": "Vérifie Apify",
                "website": "https://console.apify.com",
                "address": "Les résultats arrivent sur ton compte Apify d'ici 1 à 2 min.",
                "NOM_DU_PATRON": "APIFY"
            }]
            self.wfile.write(json.dumps(reponse_valide).encode('utf-8'))
        except Exception as e:
            self.wfile.write(json.dumps([]).encode('utf-8'))
        
        return
