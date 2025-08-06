import os
import pandas as pd
import streamlit as st
import gspread
from google.oauth2.service_account import Credentials

# 📌 1. Autoryzacja Google Sheets
SCOPES = [
    "https://www.googleapis.com/auth/spreadsheets",
    "https://www.googleapis.com/auth/drive"
]

creds = Credentials.from_service_account_file(
    "magazyn-lab2-7e442540fb8b.json",
    scopes=SCOPES
)

client = gspread.authorize(creds)

# 📌 2. Otwórz arkusz Google
sheet = client.open("Magazyn").worksheet("Sheet1")


# 📌 3. Wczytywanie danych
def load_data():
    values = sheet.get_all_values()
    if not values:
        return pd.DataFrame(columns=["Produkt", "Firma", "Typ", "Nr seryjny", "Lokalizacja", "Stan"])

    header = [h.strip() for h in values[0]]
    rows = values[1:]
    df = pd.DataFrame(rows, columns=header)

    # Konwersja kolumn
    df.columns = df.columns.str.strip()
    df["Stan"] = pd.to_numeric(df["Stan"], errors="coerce").fillna(0).astype(int)
    return df


# 📌 4. Zapisywanie danych
def save_data(df):
    sheet.clear()
    sheet.update([df.columns.tolist()] + df.values.tolist())


# 📌 5. Interfejs
st.title("Lab Magazyn")

df = load_data()


# 📌 6. Filtry
st.sidebar.header("🔍 Filtry")


def clear_filters():
    st.session_state.clear()
    st.rerun()


produkt_filter = st.sidebar.text_input("Nazwa produktu", key="produkt_filter",
                                       value=st.session_state.get("produkt_filter", ""))
Firma_filter = st.sidebar.selectbox("Firma", options=[""] + sorted(df["Firma"].dropna().unique()), index=0,
                                    key="Firma_filter")
typ_filter = st.sidebar.selectbox("Typ", options=[""] + sorted(df["Typ"].dropna().unique()), index=0, key="typ_filter")
nr_ser_filter = st.sidebar.text_input("Numer seryjny", key="nr_ser_filter",
                                      value=st.session_state.get("nr_ser_filter", ""))
lokalizacja_filter = st.sidebar.selectbox("Lokalizacja", options=[""] + sorted(df["Lokalizacja"].dropna().unique()),
                                          index=0, key="lokalizacja_filter")

if st.sidebar.button("Wyczyść filtry"):
    clear_filters()

# 📌 6b. Filtrowanie
filtered_df = df.copy()
for col in ["Produkt", "Firma", "Typ", "Nr seryjny", "Lokalizacja"]:
    filtered_df[col] = filtered_df[col].astype(str).fillna("")

if produkt_filter:
    filtered_df = filtered_df[filtered_df["Produkt"].str.contains(produkt_filter, case=False)]
if Firma_filter:
    filtered_df = filtered_df[filtered_df["Firma"] == Firma_filter]
if typ_filter:
    filtered_df = filtered_df[filtered_df["Typ"] == typ_filter]
if nr_ser_filter:
    filtered_df = filtered_df[filtered_df["Nr seryjny"].str.contains(nr_ser_filter, case=False)]
if lokalizacja_filter:
    filtered_df = filtered_df[filtered_df["Lokalizacja"] == lokalizacja_filter]

# 📌 7. Tabela
st.subheader("📋 Stan magazynu (przefiltrowane):")

header_cols = st.columns([2, 2, 2, 2, 2, 1, 1, 1, 1])
header_cols[0].write("**Produkt**")
header_cols[1].write("**Firma**")
header_cols[2].write("**Typ**")
header_cols[3].write("**Nr Seryjny**")
header_cols[4].write("**Lokalizacja**")
header_cols[5].write("**Stan**")

for i, row in filtered_df.iterrows():
    cols = st.columns([2, 2, 2, 2, 2, 1, 1, 1, 1])

    cols[0].write(row["Produkt"])
    cols[1].write(row["Firma"])
    cols[2].write(row["Typ"])
    cols[3].write(row["Nr seryjny"])
    cols[4].write(row["Lokalizacja"])
    cols[5].write(int(row["Stan"]))

    global_index = df[
        (df["Produkt"] == row["Produkt"]) &
        (df["Firma"] == row["Firma"]) &
        (df["Typ"] == row["Typ"]) &
        (df["Nr seryjny"] == row["Nr seryjny"]) &
        (df["Lokalizacja"] == row["Lokalizacja"])
        ].index[0]

    if cols[6].button("➕", key=f"plus_{i}"):
        df.at[global_index, "Stan"] += 1
        save_data(df)
        st.rerun()

    if cols[7].button("➖", key=f"minus_{i}"):
        if df.at[global_index, "Stan"] > 0:
            df.at[global_index, "Stan"] -= 1
            save_data(df)
            st.rerun()

    if cols[8].button("❌", key=f"usun_{i}"):
        st.session_state["potwierdz_usuniecie"] = i

    if st.session_state.get("potwierdz_usuniecie") == i:
        if st.checkbox(f"✅ Potwierdź usunięcie: {row['Produkt']}", key=f"confirm_{i}"):
            df = df.drop(global_index).reset_index(drop=True)
            save_data(df)
            st.success(f"🗑️ Usunięto: {row['Produkt']}")
            del st.session_state["potwierdz_usuniecie"]
            st.rerun()

# 📌 8. Dodawanie nowego produktu
st.subheader("➕ Dodaj nowy produkt")

with st.form("add_form"):
    produkt = st.text_input("Nazwa produktu").strip()
    Firma = st.text_input("Firma").strip()
    typ = st.text_input("Typ").strip()
    nr_ser = st.text_input("Numer seryjny").strip()
    lokalizacja = st.text_input("Lokalizacja").strip()
    stan = st.number_input("Stan", min_value=0, step=1)

    submitted = st.form_submit_button("Dodaj produkt")
    if submitted:
        if produkt and Firma and typ and nr_ser and lokalizacja:
            df[["Produkt", "Firma", "Typ", "Nr seryjny", "Lokalizacja"]] = df[
                ["Produkt", "Firma", "Typ", "Nr seryjny", "Lokalizacja"]].astype(str).apply(lambda x: x.str.strip())

            istnieje = (
                    (df["Produkt"] == produkt) &
                    (df["Firma"] == Firma) &
                    (df["Typ"] == typ) &
                    (df["Nr seryjny"] == nr_ser) &
                    (df["Lokalizacja"] == lokalizacja)
            )

            if istnieje.any():
                index = df[istnieje].index[0]
                df.at[index, "Stan"] += int(stan)
                st.success(f"✅ Zwiększono stan produktu '{produkt}' o {int(stan)} szt.")
            else:
                new_row = pd.DataFrame([{
                    "Produkt": produkt,
                    "Firma": Firma,
                    "Typ": typ,
                    "Nr seryjny": nr_ser,
                    "Lokalizacja": lokalizacja,
                    "Stan": int(stan)
                }])
                df = pd.concat([df, new_row], ignore_index=True)
                st.success("✅ Dodano nowy produkt.")
            save_data(df)
            st.rerun()
