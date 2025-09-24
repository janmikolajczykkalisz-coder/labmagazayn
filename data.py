import gspread
import pandas as pd
import streamlit as st
from oauth2client.service_account import ServiceAccountCredentials
import json

scope = ["https://spreadsheets.google.com/feeds",
         "https://www.googleapis.com/auth/drive"]

# Spróbuj z sekretów Streamlit
if "gcp_service_account" in st.secrets:
    creds_dict = st.secrets["gcp_service_account"]
    credentials = ServiceAccountCredentials.from_json_keyfile_dict(creds_dict, scope)
else:
    # Fallback: lokalnie z pliku credentials.json
    credentials = ServiceAccountCredentials.from_json_keyfile_name("credentials.json", scope)

client = gspread.authorize(credentials)
spreadsheet = client.open("Magazyn")   # nazwa Twojego arkusza
ws = spreadsheet.sheet1
