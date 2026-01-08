import streamlit as st
import pandas as pd

st.set_page_config(page_title="Mon Guide Perso", layout="wide")

st.title("🍴 Mon Répertoire de Restaurants & Bars")

# Chargement des données
df = pd.read_csv("spottable v1.xlsx")

# Extraction des tags uniques pour le filtre
all_tags = set()
df['tags'].str.split(',').apply(lambda x: [all_tags.add(t.strip()) for t in x])

# Interface de filtrage
selection = st.multiselect("Filtrer par ambiance :", sorted(list(all_tags)))

# Logique de filtre
if selection:
    df_final = df[df['tags'].apply(lambda x: any(t.strip() in selection for t in x.split(',')))]
else:
    df_final = df

# Affichage Carte et Liste
col1, col2 = st.columns([2, 1])

with col1:
    st.subheader("La Carte")
    st.map(df_final)

with col2:
    st.subheader("Les Adresses")
    for _, row in df_final.iterrows():
        st.write(f"**{row['name']}**")
        st.caption(row['address'])
        st.write(f"_{row['tags']}_")
        st.divider()
