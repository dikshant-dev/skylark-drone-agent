import os
import gspread
from oauth2client.service_account import ServiceAccountCredentials
import pandas as pd

SCOPE = [
    "https://spreadsheets.google.com/feeds",
    "https://www.googleapis.com/auth/drive"
]

CREDENTIALS_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "credentials.json")

def get_client():
    creds = ServiceAccountCredentials.from_json_keyfile_name(CREDENTIALS_FILE, SCOPE)
    return gspread.authorize(creds)

def read_sheet(spreadsheet_name, worksheet_name):
    try:
        client = get_client()
        sh = client.open(spreadsheet_name)
        ws = sh.worksheet(worksheet_name)
        data = ws.get_all_records()
        return pd.DataFrame(data)
    except Exception as e:
        print(f"[sheets] read error: {e}")
        return pd.DataFrame()

def update_pilot_status(spreadsheet_name, pilot_id, new_status):
    try:
        client = get_client()
        sh = client.open(spreadsheet_name)
        ws = sh.worksheet("Pilot Roster")
        data = ws.get_all_values()
        headers = [h.strip().lower() for h in data[0]]
        id_col = None
        stat_col = None
        for i, h in enumerate(headers):
            if 'pilot_id' in h:
                id_col = i
            if h == 'status':
                stat_col = i
        if id_col is None or stat_col is None:
            print("[sheets] Columns not found!")
            return False
        for row_idx, row in enumerate(data[1:], start=2):
            if row[id_col].strip() == pilot_id.strip():
                ws.update_cell(row_idx, stat_col + 1, new_status)
                print(f"[sheets] SUCCESS: Updated {pilot_id} to {new_status}")
                return True
        return False
    except Exception as e:
        print(f"[sheets] write error: {e}")
        return False

def update_drone_status(spreadsheet_name, drone_id, new_status):
    try:
        client = get_client()
        sh = client.open(spreadsheet_name)
        ws = sh.worksheet("Drone Fleet")
        data = ws.get_all_values()
        headers = [h.strip().lower() for h in data[0]]
        id_col = None
        stat_col = None
        for i, h in enumerate(headers):
            if 'drone_id' in h:
                id_col = i
            if h == 'status':
                stat_col = i
        if id_col is None or stat_col is None:
            return False
        for row_idx, row in enumerate(data[1:], start=2):
            if row[id_col].strip() == drone_id.strip():
                ws.update_cell(row_idx, stat_col + 1, new_status)
                print(f"[sheets] SUCCESS: Updated {drone_id} to {new_status}")
                return True
        return False
    except Exception as e:
        print(f"[sheets] write error: {e}")
        return False