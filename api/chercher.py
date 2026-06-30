from http.server import BaseHTTPRequestHandler
from urllib.parse import urlparse, parse_qs
import json
import pandas as pd
import requests
import time
import re
import os
from apify_client import ApifyClient

# Récupération sécurisée de la clé Apify configurée dans Vercel
VOTRE_API_KEY_APIFY = os.environ.get("APIFY_API_KEY")

class handler(BaseHTTPRequestHandler):
    def do_GET(self):
        # Configuration des entêtes de réponse JSON
        self.send_response(200)
        self.send_header('Content-type', 'application/json')
        self.end_headers()
        
        # Récupération du mot-clé envoyé par l'interface (ex: ?q=electricien lyon)
        query_components = parse_qs(urlparse(self.path).query)
        search_query = query_components.get('q', [''])[0]
        
        if not search_query:
            self.wfile.write(json.dumps({"error": "Paramètre de recherche 'q' manquant"}).encode())
            return

        if not VOTRE_API_KEY_APIFY:
            self.wfile.write(json.dumps({"error": "Clé APIFY_API_KEY introuvable dans les variables d'environnement Vercel"}).encode())
            return
            
        # 1. Lancement d'Apify avec bridage de sécurité pour tes tokens (15 résultats max)
        client = ApifyClient(VOTRE_API_KEY_APIFY)
        run_input = {
            "searchStrings": [search_query], 
            "maxCrawledPlacesPerSearch": 15, 
            "language": "fr"
        }
        
        try:
            run = client.actor("scrapers/google-maps-scraper").call(run_input=run_input)
            results = list(client.dataset(run["defaultDatasetId"]).list_items().items)
            df = pd.DataFrame(results)
        except Exception as e:
            self.wfile.write(json.dumps({"error": f"Erreur Apify: {str(e)}"}).encode())
            return

        if df.empty or 'phone' not in df.columns:
            self.wfile.write(json.dumps([]).encode())
            return

        # 2. Filtrage : On accepte tous les numéros français valides (fixes, portables 06/07, et les standards en 09)
        df['phone'] = df['phone'].astype(str)
        df_portables = df[df['phone'].str.contains(r'\+33\s*[1-79]', regex=True)].copy()

        if df_portables.empty:
            self.wfile.write(json.dumps([]).encode())
            return

        # 3. Enrichissement avec l'API du gouvernement (Recherche des dirigeants)
        noms_patrons = []
        for index, row in df_portables.iterrows():
            nom_boite = row.get('title', '')
            adresse = row.get('address', '')
            cp_match = re.search(r'\b\d{5}\b', str(adresse))
            cp = cp_match.group(0) if cp_match else ""
            
            url = f"https://recherche-entreprises.api.gouv.fr/search?q={nom_boite}&code_postal={cp}&per_page=1"
            try:
                res = requests.get(url, timeout=4).json()
                if res.get('results') and res['results'][0].get('dirigeants'):
                    d = res['results'][0]['dirigeants'][0]
                    noms_patrons.append(f"{d.get('prenom', '')} {d.get('nom', '')}".strip().upper())
                else:
                    noms_patrons.append("NON TROUVÉ")
            except:
                noms_patrons.append("NON TROUVÉ")
            time.sleep(0.1)

        df_portables['NOM_DU_PATRON'] = noms_patrons

        # 4. Nettoyage final et envoi des données au format JSON
        # On remplace les valeurs manquantes (comme l'absence de site web) par du texte vide pour éviter les bugs
        df_final = df_portables[['title', 'phone', 'website', 'address', 'NOM_DU_PATRON']].fillna('')
        donnees_finales = df_final.to_dict(orient='records')
        
        self.wfile.write(json.dumps(donnees_finales).encode())
        return