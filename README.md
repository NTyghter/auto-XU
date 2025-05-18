
# XAU/USD Streamlit Trading App (Live Monitor)

This is a free-to-deploy Streamlit app that:
- Connects to your OANDA demo/live account
- Trades XAU/USD with SL/TP
- Triggers trades via TradingView webhook
- Logs trades to Google Sheets
- Sends real-time Discord alerts
- Updates open trade statuses using live prices

## 📦 How to Deploy on Streamlit Cloud

1. Fork or upload this repo to your GitHub account
2. Visit https://streamlit.io/cloud
3. Connect your GitHub & click "New App"
4. Choose your repo and deploy

Make sure to upload:
- `gspread_credentials.json` to the root of your project
- Add your OANDA API token and Account ID in the sidebar
- Update your Discord webhook inside `app.py`

Enjoy testing your gold trading strategy!
