"""
Esegui una volta sola per ottenere il refresh token Google.
Apre il browser per autorizzare l'app, poi stampa le credenziali da salvare.
"""

import json
from google_auth_oauthlib.flow import InstalledAppFlow

SCOPES = [
    "https://www.googleapis.com/auth/spreadsheets",
    "https://www.googleapis.com/auth/drive.file",
]

CLIENT_SECRETS = "json google.json"

flow = InstalledAppFlow.from_client_secrets_file(CLIENT_SECRETS, scopes=SCOPES)

print("\nSe il browser non si apre automaticamente, copia questo URL nel browser:")
print("(apparirà tra un secondo)\n")

creds = flow.run_local_server(
    port=8080,
    open_browser=True,
    success_message="Autorizzazione completata! Puoi chiudere questa scheda.",
)

print("\n=== CREDENZIALI OTTENUTE ===")
print(f"GOOGLE_CLIENT_ID     = {creds.client_id}")
print(f"GOOGLE_CLIENT_SECRET = {creds.client_secret}")
print(f"GOOGLE_REFRESH_TOKEN = {creds.refresh_token}")
print("\nSalva questi tre valori come secrets su Fly.io.")
