import pandas as pd
import streamlit as st
import gspread
from google.oauth2.service_account import Credentials

# 📌 Konfiguracja strony
st.set_page_config(page_title="Lab Magazyn", layout="centered")

# 📌 Autoryzacja Google Sheets
SCOPES = [
    "https://www.googleapis.com/auth/spreadsheets",
    "https://www.googleapis.com/auth/drive"
]
creds = Credentials.from_service_account_info(
    st.secrets["gcp_service_account"],
    scopes=SCOPES
)
client = gspread.authorize(creds)
sheet = client.open("Magazyn").worksheet("Sheet1")

# 📌 Wczytywanie danych
def load_data():
    values = sheet.get_all_values()
    if not values:
        return pd.DataFrame(columns=["Produkt", "Firma", "Typ", "Nr seryjny", "Lokalizacja", "Stan"])
    header = [h.strip() for h in values[0]]
    rows = values[1:]
    df = pd.DataFrame(rows, columns=header)
    df.columns = df.columns.str.strip()
    df["Stan"] = pd.to_numeric(df["Stan"], errors="coerce").fillna(0).astype(int)
    return df

# 📌 Zapisywanie danych
def save_data(df):
    sheet.clear()
    sheet.update([df.columns.tolist()] + df.values.tolist())

# 📌 Interfejs główny
st.title(" Lab Magazyn")

df = load_data()

# 📌 Filtry
st.sidebar.header(" Filtry")

def clear_filters():
    st.session_state.clear()
    st.rerun()

produkt_filter = st.sidebar.text_input("Nazwa produktu", key="produkt_filter", value=st.session_state.get("produkt_filter", ""))
Firma_filter = st.sidebar.selectbox("Firma", options=[""] + sorted(df["Firma"].dropna().unique()), index=0, key="Firma_filter")
typ_filter = st.sidebar.selectbox("Typ", options=[""] + sorted(df["Typ"].dropna().unique()), index=0, key="typ_filter")
nr_ser_filter = st.sidebar.text_input("Numer seryjny", key="nr_ser_filter", value=st.session_state.get("nr_ser_filter", ""))
lokalizacja_filter = st.sidebar.selectbox("Lokalizacja", options=[""] + sorted(df["Lokalizacja"].dropna().unique()), index=0, key="lokalizacja_filter")

if st.sidebar.button("Wyczyść filtry"):
    clear_filters()

# 📌 Filtrowanie danych
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

# 📌 Wyświetlanie produktów
st.markdown('<h2 class="fade-in"> Stan magazynu (przefiltrowane):</h2>', unsafe_allow_html=True)

for i, row in filtered_df.iterrows():
    with st.expander(f" {row['Produkt']} — {row['Firma']}", expanded=False):
        st.markdown(f"** Typ:** {row['Typ']}")
        st.markdown(f"** Nr seryjny:** {row['Nr seryjny']}")
        st.markdown(f"** Lokalizacja:** {row['Lokalizacja']}")
        st.markdown(f"** Stan:** {int(row['Stan'])}")

        global_index = df[
            (df["Produkt"] == row["Produkt"]) &
            (df["Firma"] == row["Firma"]) &
            (df["Typ"] == row["Typ"]) &
            (df["Nr seryjny"] == row["Nr seryjny"]) &
            (df["Lokalizacja"] == row["Lokalizacja"])
        ].index[0]

        col1, col2, col3 = st.columns(3)
        if col1.button("➕", key=f"plus_{i}"):
            with st.spinner("⏳ Zapisuję zmianę..."):
                df.at[global_index, "Stan"] += 1
                save_data(df)
            st.rerun()

        if col2.button("➖", key=f"minus_{i}"):
            if df.at[global_index, "Stan"] > 0:
                with st.spinner("⏳ Zapisuję zmianę..."):
                    df.at[global_index, "Stan"] -= 1
                    save_data(df)
                st.rerun()

        if f"potwierdz_usuniecie_{i}" not in st.session_state:
            st.session_state[f"potwierdz_usuniecie_{i}"] = False

        if col3.button("❌", key=f"usun_{i}"):
            st.session_state[f"potwierdz_usuniecie_{i}"] = True

        if st.session_state[f"potwierdz_usuniecie_{i}"]:
            if st.checkbox(f"✅ Potwierdź usunięcie: {row['Produkt']}", key=f"confirm_{i}"):
                with st.spinner("⏳ Usuwam produkt..."):
                    df = df.drop(global_index).reset_index(drop=True)
                    save_data(df)
                st.success(f"🗑️ Usunięto: {row['Produkt']}")
                st.session_state[f"potwierdz_usuniecie_{i}"] = False
                st.rerun()

# 📌 Formularz dodawania produktu
st.subheader("➕ Dodaj nowy produkt")

with st.form("add_form"):
    produkt = st.text_input(" Nazwa produktu").strip()
    Firma = st.text_input(" Firma").strip()
    typ = st.text_input(" Typ").strip()
    nr_ser = st.text_input(" Numer seryjny").strip()
    lokalizacja = st.text_input(" Lokalizacja").strip()
    stan = st.number_input(" Stan", min_value=0, step=1)

    submitted = st.form_submit_button("✅ Dodaj produkt")
    if submitted:
        if produkt and Firma and typ and nr_ser and lokalizacja:
            df[["Produkt", "Firma", "Typ", "Nr seryjny", "Lokalizacja"]] = df[
                ["Produkt", "Firma", "Typ", "Nr seryjny", "Lokalizacja"]
            ].astype(str).apply(lambda x: x.str.strip())

            istnieje = (
                (df["Produkt"] == produkt) &
                (df["Firma"] == Firma) &
                (df["Typ"] == typ) &
                (df["Nr seryjny"] == nr_ser) &
                (df["Lokalizacja"] == lokalizacja)
            )

            if istnieje.any():
                index = df[istnieje].index[0]
                with st.spinner("⏳ Aktualizuję produkt..."):
                    df.at[index, "Stan"] += int(stan)
                    save_data(df)
                st.success(f"✅ Zwiększono stan produktu '{produkt}' o {int(stan)} szt.")
                st.rerun()
            else:
                new_row = pd.DataFrame([{
                    "Produkt": produkt,
                    "Firma": Firma,
                    "Typ": typ,
                    "Nr seryjny": nr_ser,
                    "Lokalizacja": lokalizacja,
                    "Stan": int(stan)
                }])
                with st.spinner("⏳ Dodaję nowy produkt..."):
                    df = pd.concat([df, new_row], ignore_index=True)
                    save_data(df)
                st.success("✅ Dodano nowy produkt.")
                st.rerun()

st.markdown("""
<style>
.stButton > button {
    background-color: #f0f0f0;
    color: #333;
    border: 1px solid #ccc;
    padding: 0.4em 1em;
    border-radius: 6px;
    transition: 0.3s ease;
}
.stButton > button:hover {
    background-color: #e0e0e0;
    color: #000;
}
.streamlit-expander {
    border-radius: 8px;
    border: 1px solid #ddd;
    padding: 0.5em;
}

/* 🔄 Fade-in animacja dla sekcji tabeli */
.fade-in {
    animation: fadeIn 0.6s ease-in-out;
}
@keyframes fadeIn {
    from { opacity: 0; transform: translateY(10px); }
    to { opacity: 1; transform: translateY(0); }
}
</style>
""", unsafe_allow_html=True)
