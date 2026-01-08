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

    # Force le renommage pour Streamlit et conversion en nombres
    df = df.rename(columns={'latitude': 'lat', 'longitude': 'lon'})
    df['lat'] = pd.to_numeric(df['lat'], errors='coerce')
    df['lon'] = pd.to_numeric(df['lon'], errors='coerce')


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

    import pydeck as pdk  # Ajoute cet import tout en haut de ton fichier app.py

# ... (reste du code inchangé)

with col1:
    st.subheader("📍 Carte")
    df_map = df_filtered.dropna(subset=['lat', 'lon'])
    
    if not df_map.empty:
        # Configuration de l'icône
        ICON_URL = "https://img.icons8.com/plasticine/100/marker.png"
        icon_data = {
            "url": ICON_URL,
            "width": 128,
            "height": 128,
            "anchorY": 128,
        }
        
        # Ajout de la colonne icône au dataframe
        df_map["icon_data"] = [icon_data for _ in range(len(df_map))]

        # Création de la couche d'icônes (Pins)
        icon_layer = pdk.Layer(
            type="IconLayer",
            data=df_map,
            get_icon="icon_data",
            get_size=4,
            size_scale=10,
            get_position=["lon", "lat"],
            pickable=True,
        )

        # Configuration de la vue initiale (centrée sur tes points)
        view_state = pdk.ViewState(
            latitude=df_map["lat"].mean(),
            longitude=df_map["lon"].mean(),
            zoom=13,
            pitch=0,
        )

        # Affichage de la carte avec échelle et contrôles
        st.pydeck_chart(pdk.Deck(
            map_style="mapbox://styles/mapbox/light-v9",
            initial_view_state=view_state,
            layers=[icon_layer],
            tooltip={"text": "{name}\n{address}"} # Bulle d'info au survol
        ))
    else:
        st.warning("Aucune coordonnée disponible.")

    with col2:
        st.subheader("⬇️ Liste")
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
