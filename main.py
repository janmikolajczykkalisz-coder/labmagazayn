import pandas as pd
import streamlit as st
import gspread
from google.oauth2.service_account import Credentials

# 📌 Konfiguracja strony
st.set_page_config(page_title="Lab Magazyn", layout="centered")
# 📌 Dane użytkowników (można przenieść do st.secrets)
AUTHORIZED_USERS = {
    "admin": "admin",
    "jan": "admin"
}
# 📌 Stan logowania
if "logged_in" not in st.session_state:
    st.session_state.logged_in = False
if "username" not in st.session_state:
    st.session_state.username = ""

# 📌 Ekran logowania
if not st.session_state.logged_in:
    st.title(" Logowanie ")

    with st.form("login_form"):
        username = st.text_input("Login")
        password = st.text_input("Hasło", type="password")
        submitted = st.form_submit_button("Zaloguj")

        if submitted:
            if username in AUTHORIZED_USERS and AUTHORIZED_USERS[username] == password:
                st.session_state.logged_in = True
                st.session_state.username = username
                st.rerun()
            else:
                st.error("❌ Niepoprawny login lub hasło.")
    st.stop()

# 📌 Pasek powitalny i wylogowanie
with st.sidebar:
    st.markdown(f"👋 Witaj, **{st.session_state.username}**!")
    if st.button("🚪 Wyloguj"):
        st.session_state.logged_in = False
        st.session_state.username = ""
        st.rerun()

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
@st.cache_data(ttl=60)
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
    load_data.clear()  # czyści cache po zapisie

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
st.markdown('<h2 class="fade-in"> Stan magazynu :</h2>', unsafe_allow_html=True)

# 📌 Paginacja (jeśli produktów jest dużo)
page_size = 20
total_pages = max((len(filtered_df) - 1) // page_size + 1, 1)

if total_pages > 1:
    page = st.sidebar.slider("Strona", 1, total_pages, 1)
else:
    page = 1

start = (page - 1) * page_size
end = start + page_size
filtered_df = filtered_df.iloc[start:end]

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
                with st.spinner(" Zapisuję zmianę..."):
                    df.at[global_index, "Stan"] -= 1
                    save_data(df)
                st.rerun()

        # Inicjalizacja historii
        if "historia_usuniec" not in st.session_state:
            st.session_state["historia_usuniec"] = []

        if col3.button("❌", key=f"usun_{i}"):
            usuniety_produkt = df.loc[global_index].to_dict()
            st.session_state["historia_usuniec"].append(usuniety_produkt)

            with st.spinner("⏳ Usuwam produkt..."):
                df = df.drop(global_index).reset_index(drop=True)
                save_data(df)

            st.success(f"🗑️ Usunięto: {usuniety_produkt['Produkt']}")
            st.rerun()
# 📜 Historia usunięć
st.subheader(" Historia usunięć")

if "historia_usuniec" in st.session_state and st.session_state["historia_usuniec"]:
    for idx, item in enumerate(reversed(st.session_state["historia_usuniec"])):
        col1, col2 = st.columns([4, 1])
        with col1:
            st.write(f"**{item['Produkt']}** — {item.get('Firma', 'brak firmy')} ({item.get('Typ', 'brak typu')})")
        with col2:
            if st.button("↩️ Cofnij", key=f"cofnij_{idx}"):
                df.loc[len(df)] = item  # Dodaj na koniec
                df = df.reset_index(drop=True)
                save_data(df)
                st.success(f"✅ Przywrócono: {item['Produkt']}")
                st.session_state["historia_usuniec"].remove(item)
                st.rerun()
else:
    st.info("Brak usuniętych produktów.")

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
        if produkt:  # tylko nazwa produktu jest wymagana
            # Upewnij się, że kolumny są typu string i bez spacji
            df[["Produkt", "Firma", "Typ", "Nr seryjny", "Lokalizacja"]] = df[
                ["Produkt", "Firma", "Typ", "Nr seryjny", "Lokalizacja"]
            ].astype(str).apply(lambda x: x.str.strip())

            # Porównanie z uwzględnieniem pustych wartości
            istnieje = (
                    (df["Produkt"].fillna("") == produkt) &
                    (df["Firma"].fillna("") == Firma) &
                    (df["Typ"].fillna("") == typ) &
                    (df["Nr seryjny"].fillna("") == nr_ser) &
                    (df["Lokalizacja"].fillna("") == lokalizacja)
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
                with st.spinner(" Dodaję nowy produkt..."):
                    df = pd.concat([df, new_row], ignore_index=True)
                    save_data(df)
                st.success("✅ Dodano nowy produkt.")
                st.rerun()
        else:
            st.warning("⚠️ Podaj przynajmniej nazwę produktu.")

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
