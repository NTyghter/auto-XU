
import streamlit as st
import oandapyV20
import oandapyV20.endpoints.orders as orders
import json
import requests
import gspread
from oauth2client.service_account import ServiceAccountCredentials
from datetime import datetime

st.set_page_config(page_title="XAU/USD Auto Trader – Live Feed", layout="centered")
st.title("📈 XAU/USD Auto Trader – Real-Time Monitoring")

# Sidebar: API credentials
st.sidebar.header("🔐 OANDA API Credentials")
access_token = st.sidebar.text_input("Access Token", type="password")
account_id = st.sidebar.text_input("Account ID")

def log_trade_to_sheet(units, entry_price, sl_price, tp_price, result="Executed"):
    try:
        scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
        creds = ServiceAccountCredentials.from_json_keyfile_name("gspread_credentials.json", scope)
        client = gspread.authorize(creds)
        sheet = client.open("XAUUSD Trade Log").sheet1
        now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        sheet.append_row([now, "XAU_USD", units, entry_price, sl_price, tp_price, result])
    except Exception as e:
        st.warning(f"Sheets log error: {e}")

def send_discord_notification(units, entry_price, sl_price, tp_price):
    webhook_url = "https://discord.com/api/webhooks/your_webhook_url"
    message = {
        "content": f"🚨 XAU/USD Trade Alert\nUnits: {units}\nEntry: {entry_price}\nSL: {sl_price}\nTP: {tp_price}"
    }
    try:
        response = requests.post(webhook_url, json=message)
        if response.status_code != 204:
            st.warning(f"Discord failed: {response.status_code}")
    except Exception as e:
        st.warning(f"Discord error: {e}")

def update_trade_status(current_price):
    try:
        scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
        creds = ServiceAccountCredentials.from_json_keyfile_name("gspread_credentials.json", scope)
        client = gspread.authorize(creds)
        sheet = client.open("XAUUSD Trade Log").sheet1

        records = sheet.get_all_records()
        for idx, row in enumerate(records):
            if row["Status"] == "Executed":
                ep = float(row["Entry Price"])
                sl_p = float(row["Stop Loss"])
                tp_p = float(row["Take Profit"])
                if (ep < tp_p and current_price >= tp_p) or (ep > tp_p and current_price <= tp_p):
                    sheet.update_cell(idx + 2, 7, "Hit TP")
                elif (ep < sl_p and current_price <= sl_p) or (ep > sl_p and current_price >= sl_p):
                    sheet.update_cell(idx + 2, 7, "Stopped Out")
                else:
                    sheet.update_cell(idx + 2, 7, "Still Open")
    except Exception as e:
        st.warning(f"Status update error: {e}")

def get_live_price():
    try:
        headers = {"Authorization": f"Bearer {access_token}"}
        response = requests.get(
            f"https://api-fxpractice.oanda.com/v3/accounts/{account_id}/pricing?instruments=XAU_USD",
            headers=headers)
        data = response.json()
        ask = float(data["prices"][0]["asks"][0]["price"])
        bid = float(data["prices"][0]["bids"][0]["price"])
        mid_price = round((ask + bid) / 2, 2)
        return mid_price
    except:
        return None

# Trade Interface
st.header("📊 Manual Trade")
instrument = "XAU_USD"
units = st.number_input("Units (positive = buy, negative = sell)", value=1)
sl_pips = st.number_input("Stop Loss (pips)", value=50)
tp_pips = st.number_input("Take Profit (pips)", value=100)
manual_trade = st.button("🚀 Execute Trade")

def execute_trade(units, sl_pips=None, tp_pips=None):
    try:
        client = oandapyV20.API(access_token=access_token)
        price = get_live_price()
        if price is None:
            st.warning("⚠️ Could not fetch live price.")
            return False

        sl_price = price - sl_pips * 0.1 if units > 0 else price + sl_pips * 0.1
        tp_price = price + tp_pips * 0.1 if units > 0 else price - tp_pips * 0.1

        order_data = {
            "order": {
                "instrument": instrument,
                "units": str(units),
                "type": "MARKET",
                "positionFill": "DEFAULT",
                "stopLossOnFill": {"price": str(round(sl_price, 2))},
                "takeProfitOnFill": {"price": str(round(tp_price, 2))}
            }
        }

        order_request = orders.OrderCreate(accountID=account_id, data=order_data)
        client.request(order_request)
        st.success(f"✅ Trade Executed @ {price:.2f}, SL: {sl_price:.2f}, TP: {tp_price:.2f}")
        log_trade_to_sheet(units, price, sl_price, tp_price)
        send_discord_notification(units, price, sl_price, tp_price)
        update_trade_status(price)
        return True
    except Exception as e:
        st.error(f"❌ Trade Error: {e}")
        return False

if manual_trade:
    if access_token and account_id:
        execute_trade(units, sl_pips, tp_pips)
    else:
        st.warning("⚠️ Please enter your OANDA credentials.")

# Webhook trigger
st.header("📥 Webhook Trigger (TradingView)")
webhook_data = st.text_area("Paste JSON from TradingView", height=150)
trigger = st.button("📡 Simulate Alert")

if trigger and webhook_data:
    try:
        data = json.loads(webhook_data)
        action = data.get("action")
        volume = int(data.get("volume", 1))
        if action.upper() == "BUY":
            execute_trade(volume, sl_pips, tp_pips)
        elif action.upper() == "SELL":
            execute_trade(-volume, sl_pips, tp_pips)
        else:
            st.error("Invalid action.")
    except Exception as e:
        st.error(f"Webhook error: {e}")

# Auto Check Trades
st.header("🔁 Live Status Update")
live_price = get_live_price()
if live_price:
    st.info(f"📡 Current Live XAU/USD Price: {live_price}")
    if st.button("🔄 Check All Trades Now"):
        update_trade_status(live_price)
else:
    st.warning("⚠️ Unable to fetch live price from OANDA.")
