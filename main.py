import streamlit as st
import pandas as pd
import os

CSV_FILE = "magazyn.csv"

# -------------------------------
# Wczytaj lub utwórz plik CSV
# -------------------------------
def load_data():
    if os.path.exists(CSV_FILE):
        return pd.read_csv(CSV_FILE)
    else:
        df = pd.DataFrame(columns=["Produkt", "Firma", "Typ", "NrSeryjny", "Lokalizacja", "Stan"])
        df.to_csv(CSV_FILE, index=False)
        return df

def save_data(df):
    df.to_csv(CSV_FILE, index=False)

# -------------------------------
# Interfejs główny
# -------------------------------
st.title("Lab Magazyn")

df = load_data()

# Filtry
st.sidebar.header("🔍 Filtry")

# Funkcja czyszcząca filtry
def clear_filters():
    st.session_state.clear()
    st.rerun()

# Użyj session_state, aby przechowywać wartości filtrów
produkt_filter = st.sidebar.text_input("Nazwa produktu", key="produkt_filter", value=st.session_state.get("produkt_filter", ""))
firma_filter = st.sidebar.selectbox("Firma", options=[""] + sorted(df["Firma"].dropna().unique().tolist()), index=0, key="firma_filter")
typ_filter = st.sidebar.selectbox("Typ", options=[""] + sorted(df["Typ"].dropna().unique().tolist()), index=0, key="typ_filter")
nr_ser_filter = st.sidebar.text_input("Numer seryjny", key="nr_ser_filter", value=st.session_state.get("nr_ser_filter", ""))
lokalizacja_filter = st.sidebar.selectbox("Lokalizacja", options=[""] + sorted(df["Lokalizacja"].dropna().unique().tolist()), index=0, key="lokalizacja_filter")

# Przycisk czyszczący filtry
if st.sidebar.button("Wyczyść filtry"):
    clear_filters()

# Zastosowanie filtrów
filtered_df = df.copy()

# Konwersja kolumn na string i zastąpienie NaN pustymi ciągami
filtered_df["Produkt"] = filtered_df["Produkt"].astype(str).fillna("")
filtered_df["Firma"] = filtered_df["Firma"].astype(str).fillna("")
filtered_df["Typ"] = filtered_df["Typ"].astype(str).fillna("")
filtered_df["NrSeryjny"] = filtered_df["NrSeryjny"].astype(str).fillna("")
filtered_df["Lokalizacja"] = filtered_df["Lokalizacja"].astype(str).fillna("")

if produkt_filter:
    filtered_df = filtered_df[filtered_df["Produkt"].str.contains(produkt_filter, case=False, na=False)]

if firma_filter:
    filtered_df = filtered_df[filtered_df["Firma"] == firma_filter]

if typ_filter:
    filtered_df = filtered_df[filtered_df["Typ"] == typ_filter]

if nr_ser_filter:
    filtered_df = filtered_df[filtered_df["NrSeryjny"].str.contains(nr_ser_filter, case=False, na=False)]

if lokalizacja_filter:
    filtered_df = filtered_df[filtered_df["Lokalizacja"] == lokalizacja_filter]

# Wyświetlanie tabeli

# Dodanie nagłówków
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
    cols[3].write(row["NrSeryjny"])
    cols[4].write(row["Lokalizacja"])
    cols[5].write(int(row["Stan"]))

    if cols[6].button("➕", key=f"plus_{i}"):
        df.at[i, "Stan"] += 1
        save_data(df)
        st.rerun()

    if cols[7].button("➖", key=f"minus_{i}"):
        if df.at[i, "Stan"] > 0:
            df.at[i, "Stan"] -= 1
            save_data(df)
            st.rerun()

    if cols[8].button("❌", key=f"usun_{i}"):
        st.session_state["potwierdz_usuniecie"] = i

    if st.session_state.get("potwierdz_usuniecie") == i:
        if st.checkbox(f"✅ Potwierdź usunięcie: {row['Produkt']}", key=f"confirm_{i}"):
            df = df.drop(i).reset_index(drop=True)
            save_data(df)
            st.success(f"🗑️ Usunięto: {row['Produkt']}")
            del st.session_state["potwierdz_usuniecie"]
            st.rerun()

# -------------------------------
# Formularz dodawania nowego produktu
# -------------------------------
st.subheader("➕ Dodaj nowy produkt")

with st.form("add_form"):
    produkt = st.text_input("Nazwa produktu").strip()
    firma = st.text_input("Firma").strip()
    typ = st.text_input("Typ").strip()
    nr_ser = st.text_input("Numer seryjny").strip()
    lokalizacja = st.text_input("Lokalizacja").strip()
    stan = st.number_input("Stan", min_value=0, step=1)

    submitted = st.form_submit_button("Dodaj produkt")
    if submitted:
        if produkt and firma and typ and nr_ser and lokalizacja:
            # Konwersja kolumn na string przed użyciem str.strip()
            df["Produkt"] = df["Produkt"].astype(str).str.strip()
            df["Firma"] = df["Firma"].astype(str).str.strip()
            df["Typ"] = df["Typ"].astype(str).str.strip()
            df["NrSeryjny"] = df["NrSeryjny"].astype(str).str.strip()
            df["Lokalizacja"] = df["Lokalizacja"].astype(str).str.strip()

            # Szukamy istniejącego wiersza po wszystkich polach (pełna zgodność)
            istnieje = (
                (df["Produkt"] == produkt) &
                (df["Firma"] == firma) &
                (df["Typ"] == typ) &
                (df["NrSeryjny"] == nr_ser) &
                (df["Lokalizacja"] == lokalizacja)
            )
            st.write(f"Debug - istnieje: {istnieje}")  # Debugowanie

            if istnieje.any():
                index = df[istnieje].index[0]
                df.at[index, "Stan"] += int(stan)
                st.success(f"✅ Zwiększono stan produktu '{produkt}' o {int(stan)} szt.")
            else:
                new_row = pd.DataFrame([{
                    "Produkt": produkt,
                    "Firma": firma,
                    "Typ": typ,
                    "NrSeryjny": nr_ser,
                    "Lokalizacja": lokalizacja,
                    "Stan": int(stan)
                }])
                df = pd.concat([df, new_row], ignore_index=True)
                st.success("✅ Dodano nowy produkt.")
            save_data(df)
            st.rerun()