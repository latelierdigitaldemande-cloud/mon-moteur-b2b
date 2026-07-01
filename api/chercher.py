from http.server import BaseHTTPRequestHandler
from urllib.parse import urlparse, parse_qs
import json
import os
from apify_client import ApifyClient

# Récupération de ta clé configurée sur Vercel
VOTRE_API_KEY_APIFY = os.environ.get("APIFY_API_KEY")

class handler(BaseHTTPRequestHandler):
    def do_GET(self):
        # Configuration des entêtes requis pour Vercel et ton HTML
        self.send_response(200)
        self.send_header('Content-type', 'application/json')
        self.end_headers()
        
        query_components = parse_qs(urlparse(self.path).query)
        search_query = query_components.get('q', [''])[0]
        
        # Si la recherche ou la clé est manquante, on renvoie une liste vide pour éviter le bug JS
        if not search_query or not VOTRE_API_KEY_APIFY:
            self.wfile.write(json.dumps([])).encode()
            return
            
        client = ApifyClient(VOTRE_API_KEY_APIFY)
        run_input = {
            "searchStrings": [search_query], 
            "maxCrawledPlacesPerSearch": 15, 
            "language": "fr"
        }
        
        try:
            # Lance le robot instantanément en tâche de fond (Prend 1 seconde, évite le timeout)
            client.actor("scrapers/google-maps-scraper").start(run_input=run_input)
            
            # Formatage d'une fausse ligne d'entreprise lue par ton index.html
            reponse_pour_html = [{
                "title": "🤖 ROBOT DÉMARRÉ AVEC SUCCÈS !",
                "phone": "Vérifie Apify",
                "website": "https://console.apify.com",
                "address": "Les données arrivent sur ton compte Apify d'ici 1 à 2 min.",
                "NOM_DU_PATRON": "APIFY"
            }]
            
            self.wfile.write(json.dumps(reponse_pour_html).encode())
            
        except Exception as e:
            # Si Apify crash au lancement, on renvoie une liste vide pour clore la recherche proprement
            self.wfile.write(json.dumps([])).encode()
        
        return