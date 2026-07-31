"""
Lambda "declencheur" attache au meme VPC qu'app-server.
Ne fait qu'un seul appel HTTP interne (IP privee) vers l'API deja demarree
(par la regle EventBridge Scheduler "nappecast-start-instances" a 5h50 Paris).

Aucune dependance externe (urllib, deja dans le runtime Lambda).

Variables d'environnement attendues :
- APP_PRIVATE_IP     : IP privee d'app-server (ex: "172.31.32.79")
- PIPELINE_SECRET     : meme valeur que celle configuree cote API (docker-compose.yml)
- PIPELINE_PATH       : chemin de l'endpoint (defaut "/data")
- PORT                : port de l'API (defaut "8000")
"""

import json
import os
import urllib.error
import urllib.request

APP_PRIVATE_IP = os.environ["APP_PRIVATE_IP"]
PIPELINE_SECRET = os.environ["PIPELINE_SECRET"]
PIPELINE_PATH = "/data"
PORT = os.environ.get("PORT", "8000")


def lambda_handler(event, context):
    url = f"http://{APP_PRIVATE_IP}:{PORT}{PIPELINE_PATH}"
    req = urllib.request.Request(
        url,
        method="POST",
        headers={"X-Pipeline-Secret": PIPELINE_SECRET},
    )
    try:
        with urllib.request.urlopen(req, timeout=120) as resp:
            body = resp.read().decode("utf-8")
            print("Reponse API :", resp.status, body)
            return {"statusCode": resp.status, "body": body}
    except urllib.error.HTTPError as e:
        print("Erreur HTTP :", e.code, e.read().decode("utf-8"))
        raise
    except urllib.error.URLError as e:
        print("Erreur reseau (app-server pas encore pret ?) :", e.reason)
        raise
