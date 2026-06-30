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
        
        # En cas de paramètre manquant, on renvoie une structure vide pour éviter le crash JS
        if not search_query:
            self.wfile.write(json.dumps([])).encode()
            return

        if not VOTRE_API_KEY_APIFY:
            self.wfile.write(json.dumps([])).encode()
            return
            
        client = ApifyClient(VOTRE_API_KEY_APIFY)
        run_input = {
            "searchStrings": [search_query], 
            "maxCrawledPlacesPerSearch": 15, 
            "language": "fr"
        }
        
        try:
            # Lance le robot instantanément en tâche de fond (prend moins d'une seconde sur Vercel)
            client.actor("scrapers/google-maps-scraper").start(run_input=run_input)
            
            # Formatage d'une fausse ligne sous forme de tableau (liste) pour satisfaire le JS
            reponse_valide = [{
                "title": "🤖 ROBOT DÉMARRÉ AVEC SUCCÈS !",
                "phone": "Vérifie Apify",
                "website": "https://console.apify.com",
                "address": "Les résultats arrivent sur ton tableau de bord Apify d'ici 1 à 2 min.",
                "NOM_DU_PATRON": "APIFY"
            }]
            
            self.wfile.write(json.dumps(reponse_valide).encode())
            
        except Exception as e:
            # En cas de plantage d'Apify, renvoie un tableau vide pour ne pas bloquer l'interface
            self.wfile.write(json.dumps([])).encode()
        
        return