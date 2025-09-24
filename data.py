import gspread
import pandas as pd
from oauth2client.service_account import ServiceAccountCredentials


# --- KONFIGURACJA GOOGLE SHEETS ---
scope = ["https://spreadsheets.google.com/feeds",
         "https://www.googleapis.com/auth/drive"]

credentials = ServiceAccountCredentials.from_json_keyfile_name(
    "credentials.json", scope)
client = gspread.authorize(credentials)

spreadsheet = client.open("Magazyn")
worksheet = spreadsheet.sheet1


# --- FUNKCJE DO OBSŁUGI DANYCH ---

def load_data():
    """Wczytuje dane z Google Sheets jako DataFrame"""
    data = worksheet.get_all_records()
    df = pd.DataFrame(data)

    if df.empty:
        df = pd.DataFrame(columns=["ID", "Produkt", "Firma", "Typ", "Nr seryjny", "Lokalizacja", "Stan"])

    # Konwersja typów
    if "Stan" in df.columns:
        df["Stan"] = pd.to_numeric(df["Stan"], errors="coerce").fillna(0).astype(int)
    else:
        df["Stan"] = 0

    # Normalizacja tekstowych kolumn
    for col in ["Produkt", "Firma", "Typ", "Nr seryjny", "Lokalizacja"]:
        if col in df.columns:
            df[col] = df[col].fillna("").astype(str).str.strip()
        else:
            df[col] = ""

    # Ustawienie kolejności kolumn
    desired_cols = ["ID", "Produkt", "Firma", "Typ", "Nr seryjny", "Lokalizacja", "Stan"]
    return df.reindex(columns=desired_cols)


def save_data(df):
    """Zapisuje cały DataFrame do Google Sheets"""
    worksheet.clear()
    worksheet.update([df.columns.values.tolist()] + df.values.tolist())


def append_row(row_dict):
    """Dodaje nowy wiersz do arkusza"""
    worksheet.append_row(list(row_dict.values()))


def delete_row_by_id(item_id):
    """Usuwa wiersz na podstawie ID"""
    df = load_data()
    df = df[df["ID"] != item_id]
    save_data(df)


def update_cell_by_id(item_id, column, value):
    """Aktualizuje jedną komórkę (kolumnę) na podstawie ID"""
    df = load_data()
    df.loc[df["ID"] == item_id, column] = value
    save_data(df)
