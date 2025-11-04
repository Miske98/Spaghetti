# -*- coding: utf-8 -*-
"""
Created on Tue Nov  4 19:36:31 2025

@author: Administrator
"""
import pandas as pd
import streamlit as st
import altair as alt

# --- Podesite naslov stranice ---
st.set_page_config(page_title="Spaghetti Plot Analiza", layout="wide")
st.title("Interaktivni Spaghetti Plot")

# --- Učitavanje podataka ---
# NAPOMENA: CSV fajl 'sredjena_baza_elas.csv' mora biti u istom folderu kao i ovaj .py skript
FILE_PATH = "sredjena_baza_elas.csv"

@st.cache_data  # Keširanje podataka za bolje performanse
def load_data(path):
    try:
        data = pd.read_csv(path)
        # Konvertujemo 'code' u string da bi se izbegli problemi sa formatiranjem u Altair-u
        if 'code' in data.columns:
            data['code'] = data['code'].astype(str)
        return data
    except FileNotFoundError:
        st.error(f"GREŠKA: Fajl nije pronađen na putanji: {path}")
        st.error("Molimo vas da postavite 'sredjena_baza_elas.csv' u isti folder kao i Streamlit .py skript, ili da kontaktirate Pavla ukoliko niste on.")
        return None

sredjena_baza = load_data(FILE_PATH)

# Ako podaci nisu učitani, zaustavi izvršavanje
if sredjena_baza is None:
    st.stop()

# --- Definisanje filtera u Sidebar-u ---
st.sidebar.header("Filteri za Prikaz")

# Dobijanje jedinstvenih vrednosti za filtere
Patient = sorted(sredjena_baza['code'].unique())
Muscle = sorted(sredjena_baza['muscle'].unique())
Position = sorted(sredjena_baza['position'].unique())
Health = sorted(sredjena_baza['health_status'].unique())

# Kreiranje multiselect widget-a u sidebar-u
# 'default=...' osigurava da su sve opcije inicijalno štiklirane
selected_patients = st.sidebar.multiselect("Pacijent", Patient, default=Patient)
selected_muscles = st.sidebar.multiselect("Mišić", Muscle, default=Muscle)
selected_positions = st.sidebar.multiselect("Pozicija", Position, default=Position)
selected_health = st.sidebar.multiselect("Zdravstveni status", Health, default=Health)

# --- Filtriranje DataFrame-a na osnovu selekcije ---
filtered_df = sredjena_baza[
    sredjena_baza['code'].isin(selected_patients) &
    sredjena_baza['muscle'].isin(selected_muscles) &
    sredjena_baza['position'].isin(selected_positions) &
    sredjena_baza['health_status'].isin(selected_health)
]

# --- Prikazivanje grafa ---
if filtered_df.empty:
    st.warning("Nema podataka za prikaz sa odabranim filterima. Molimo promenite selekciju. Verovatno ste neki filter ostavili prazan.")
else:
    # --- Logika za bojenje (Crvena/Zelena) ---
    color_encoding = alt.Color('health_status', title='Zdravstveni Status')
    
    if len(Health) == 2:
        domain_ = [Health[0], Health[1]]
        range_ = ['green', 'red']  # Podesite ovo: Prva vrednost = zelena, Druga = crvena
        
        color_encoding = alt.Color(
            'health_status',
            title='Zdravstveni status',
            scale=alt.Scale(domain=domain_, range=range_)
        )
        

    # --- Logika za naslov (prikaz mišića i pozicije) ---
    title_parts = []
    if len(selected_muscles) == 1:
        title_parts.append(f"Mišić: {selected_muscles[0]}")
    if len(selected_positions) == 1:
        title_parts.append(f"Pozicija: {selected_positions[0]}")
    
    plot_title = " | ".join(title_parts)

# --- Kreiranje Altair grafa (Layered Chart) ---

    # 1. Kreiranje Selekcije (ostaje isto, hvata celog pacijenta)
    highlight = alt.selection_point(
        on='mouseover', 
        fields=['code'],
        nearest=True
    )

    # 2. Definicija Osnovnog Enkodiranja (za oba sloja)
    base = alt.Chart(filtered_df).encode(
        x=alt.X(
            'time_days', 
            title='Vreme (meseci)',
            axis=alt.Axis(grid=False)
        ),
        y=alt.Y('value', title='Vrednost'),
        # Kljuc za pravilno crtanje linije (ostaje)
        detail=['code', 'muscle', 'position'],
        # Tooltip ce biti vezan za TACKE, ali ga definisemo u bazi
        tooltip=[
            alt.Tooltip('code', title='Pacijent (code)'),
            alt.Tooltip('muscle', title='Mišić'),
            alt.Tooltip('position', title='Pozicija'),
            alt.Tooltip('health_status', title='Status'),
            alt.Tooltip('time_days', title='Vreme (dani)'),
            alt.Tooltip('value', title='Vrednost')
        ]
    )

    # 3. Sloj za LINIJE (Linije su tanke, a na hover se podebljaju)
    line_layer = base.mark_line().encode(
        color=color_encoding,
        
        # Debljina LINIJE - USLOVNO
        strokeWidth=alt.condition(
            highlight, 
            alt.value(3.5),  # <--- Debljina linije NA HOVER
            alt.value(1)     # <--- Normalna debljina linije
        ),
        
        # Providnost - USLOVNO
        opacity=alt.condition(
            highlight, 
            alt.value(1.0), # <--- Puna vidljivost
            alt.value(0.3)  # <--- Bledo
        ),
    )

    # 4. Sloj za TAČKE (Tačke su fiksne velicine i uvek vidljive)
    point_layer = base.mark_point().encode(
        # Tačke dobijaju boju po statusu
        color=color_encoding,
        
        # Veličina TAČKE - FIKSNA i DOVOLJNO VELIKA da se Vidi (50 je obično dobro)
        size=alt.value(50), 
        
        # Providnost - USLOVNO (da se i tačke vide/izblede zajedno sa linijom)
        opacity=alt.condition(
            highlight, 
            alt.value(1.0), 
            alt.value(0.3)
        ),
    )

    # 5. Spajanje slojeva
    chart = alt.layer(line_layer, point_layer).properties(
        title=plot_title
    ).add_selection(
        highlight # Selekciju dodajemo celom sloju
    ).interactive()

    # Prikazivanje grafa u Streamlit-u
    st.altair_chart(chart, use_container_width=True)
    
    # Opciono: Prikaz filtriranih podataka u tabeli
    with st.expander("Pogledajte filtrirane podatke"):

        st.dataframe(filtered_df)
