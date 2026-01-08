import streamlit as st
import pandas as pd
from geopy.geocoders import Nominatim
from geopy.extra.rate_limiter import RateLimiter
import time

# Configuration de la page
st.set_page_config(page_title="Mes spots", layout="wide")

st.title("Mes spots")


# --- CHARGEMENT DES DONNÉES ---
try:
    # Lecture du CSV avec détection automatique du séparateur (virgule ou point-virgule)
    df = pd.read_csv("Spottable v2.csv", sep=None, engine='python')
    df.columns = df.columns.str.strip().str.lower() # Nettoyage des noms de colonnes


    # --- FILTRES ---
    # On identifie dynamiquement la colonne des tags (peu importe la casse)
    col_tags = next((c for c in df.columns if c.lower() == 'tags'), None)

    if col_tags:
        # On récupère tous les tags uniques en nettoyant les espaces et les vides
        all_tags = set()
        for val in df[col_tags].dropna():
            for t in str(val).split(','):
                tag_clean = t.strip()
                if tag_clean:
                    all_tags.add(tag_clean)
        
        selected_tags = st.multiselect("Filtrer par tags :", sorted(list(all_tags)))

        # Logique de filtrage
        if selected_tags:
            # On vérifie si au moins un des tags sélectionnés est présent dans la cellule
            def match_tags(cell_value):
                if pd.isna(cell_value): return False
                cell_tags = [t.strip() for t in str(cell_value).split(',')]
                return any(tag in cell_tags for tag in selected_tags)
            
            df_filtered = df[df[col_tags].apply(match_tags)]
        else:
            df_filtered = df
    else:
        st.error("Colonne 'Tags' non trouvée dans le fichier CSV.")
        df_filtered = df

    # --- AFFICHAGE ---
    col1, col2 = st.columns([2, 1])

    # On détecte les colonnes utiles automatiquement
    c_name = next((c for c in df.columns if c.lower() in ['name', 'nom']), df.columns[0])
    c_addr = next((c for c in df.columns if c.lower() in ['address', 'adresse']), df.columns[1])

    with col1:
        st.subheader("📍 Carte")
        df_map = df_filtered.dropna(subset=['lat', 'lon'])
        if not df_map.empty:
            st.map(df_map)
        else:
            st.warning("Aucune coordonnée disponible pour la carte. Vérifiez les adresses dans votre fichier.")

    with col2:
        st.subheader("📋 Liste des établissements")
        if df_filtered.empty:
            st.info("Aucun résultat pour ces filtres.")
        else:
            for _, row in df_filtered.iterrows():
                # On utilise les noms de colonnes détectés plus haut
                titre = str(row[c_name]).upper()
                with st.expander(f"**{titre}**"):
                    st.write(f"📍 {row[c_addr]}")
                    if col_tags:
                        st.caption(f"Tags : {row[col_tags]}")
                    
                    # Gestion du lien Google Maps
                    c_link = next((c for c in df.columns if 'map' in c.lower() or 'lien' in c.lower()), None)
                    if c_link and pd.notna(row[c_link]):
                        st.link_button("Voir sur Google Maps", row[c_link])

except FileNotFoundError:
    st.error("Erreur : Le fichier 'Spottable v1.csv' est introuvable sur GitHub.")
except Exception as e:
    st.error(f"Une erreur est survenue : {e}")
