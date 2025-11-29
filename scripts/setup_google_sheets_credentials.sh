#!/usr/bin/env bash
# Setup Google Sheets OAuth2 Credentials for IPO Monitor
# This script helps create the credentials.json file needed for Google Sheets API access

set -e

echo "╔══════════════════════════════════════════════════════════════╗"
echo "║     Google Sheets Credentials Setup for IPO Monitor         ║"
echo "╚══════════════════════════════════════════════════════════════╝"
echo ""

CREDENTIALS_FILE="data/google_sheets_credentials.json"
CREDENTIALS_DIR=$(dirname "$CREDENTIALS_FILE")

# Create data directory if it doesn't exist
mkdir -p "$CREDENTIALS_DIR"

echo "📝 Creating credentials.json file..."
echo ""
echo "You'll need to provide:"
echo "  1. Client ID (from Google Cloud Console)"
echo "  2. Client Secret (from Google Cloud Console)"
echo ""

read -p "Enter Client ID: " CLIENT_ID
read -p "Enter Client Secret: " CLIENT_SECRET

# Create credentials.json
cat > "$CREDENTIALS_FILE" << EOF
{
  "installed": {
    "client_id": "${CLIENT_ID}",
    "project_id": "trading-system",
    "auth_uri": "https://accounts.google.com/o/oauth2/auth",
    "token_uri": "https://oauth2.googleapis.com/token",
    "auth_provider_x509_cert_url": "https://www.googleapis.com/oauth2/v1/certs",
    "client_secret": "${CLIENT_SECRET}",
    "redirect_uris": ["http://localhost:8080/"]
  }
}
EOF

echo ""
echo "✅ Credentials file created: $CREDENTIALS_FILE"
echo ""
echo "📋 Next steps:"
echo "   1. Set GitHub Secret: GOOGLE_SHEETS_CREDENTIALS_PATH"
echo "      Value: $CREDENTIALS_FILE"
echo ""
echo "   2. Or for GitHub Actions, you can base64 encode this file:"
echo "      base64 $CREDENTIALS_FILE | pbcopy"
echo "      Then paste as GOOGLE_SHEETS_CREDENTIALS_PATH secret"
echo ""
echo "   3. Create Google Sheet with 'Target IPOs' tab"
echo "   4. Set GitHub Secret: GOOGLE_SHEETS_IPO_SPREADSHEET_ID"
echo "      (Get ID from Google Sheets URL)"
echo ""
