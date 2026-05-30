import os
from google_auth_oauthlib.flow import InstalledAppFlow
from youtube_upload import SCOPES

# Configure the secret file path (points to your client_secret_ytsimpletips.json)
CLIENT_SECRET_FILE = "client_secret_ytsimpletips.json"
TOKEN_FILE = "token.json"

def main():
    if not os.path.exists(CLIENT_SECRET_FILE):
        print(f"❌ Error: '{CLIENT_SECRET_FILE}' not found in the current directory.")
        print("Please ensure your client secret file is renamed or matching this filename.")
        return

    print("🚀 Starting local OAuth flow...")
    print("🌐 A browser window will open. Log in with jvijay1104@gmail.com and approve permissions.")
    
    flow = InstalledAppFlow.from_client_secrets_file(
        CLIENT_SECRET_FILE, 
        scopes=SCOPES
    )
    # This runs a local server on port 8080. 
    # Make sure you added http://localhost:8080/ to 'Authorized redirect URIs' in GCP!
    creds = flow.run_local_server(port=8080, prompt='consent')
    
    with open(TOKEN_FILE, "w") as token_file:
        token_file.write(creds.to_json())
        
    print(f"🎉 Success! '{TOKEN_FILE}' has been generated in your workspace.")
    print("You can now copy the contents of this file to your GitHub secret TOKEN_JSON.")

if __name__ == "__main__":
    main()
