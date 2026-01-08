import streamlit as st
import pandas as pd
from geopy.geocoders import Nominatim
from geopy.extra.rate_limiter import RateLimiter
import time

# Configuration de la page
st.set_page_config(page_title="Mes spots", layout="wide")

st.title("Mes spots")

# Configuration des couleurs des boutons
st.markdown(f"""
    <style>
    .stButton>button {{
        background-color: #d92644;
        color: white;
        border-radius: 8px;
        border: None;
    }}
    .tag-label {{
        display: inline-block;
        background-color: #f0f2f6;
        color: #d92644;
        padding: 2px 8px;
        border-radius: 12px;
        margin-right: 5px;
        font-size: 0.8rem;
        font-weight: bold;
        border: 1px solid #d92644;
    }}
    </style>
    """, unsafe_allow_html=True)


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

    import pydeck as pdk
    import pandas as pd
    
    # ... (votre code de chargement et filtrage)
    
    with col1:
        st.subheader("📍 Carte")
        df_map = df_filtered.dropna(subset=['lat', 'lon']).copy()
        
        if not df_map.empty:
            # 1. URL de l'icône (Pin type Google)
            ICON_URL = "https://img.icons8.com/color/d92644/marker.png"
            
            # 2. Configuration de l'icône pour chaque point
            icon_data = {
                "url": ICON_URL,
                "width": 100,
                "height": 100,
                "anchorY": 100, # La pointe de l'épingle est sur la coordonnée
            }
            df_map["icon_data"] = [icon_data for _ in range(len(df_map))]
    
            # 3. Création de la couche d'icônes
            icon_layer = pdk.Layer(
                type="IconLayer",
                data=df_map,
                get_icon="icon_data",
                get_size=4,
                size_scale=10,
                get_position=["lon", "lat"],
                pickable=True, # Indispensable pour l'interaction
            )
    
            # 4. Vue centrée dynamiquement
            view_state = pdk.ViewState(
                latitude=df_map["lat"].mean(),
                longitude=df_map["lon"].mean(),
                zoom=13,
                pitch=0,
            )
    
            # 5. Rendu de la carte avec Tooltip (Bulle d'info)
            st.pydeck_chart(pdk.Deck(
                map_style="mapbox://styles/mapbox/streets-v11",
                initial_view_state=view_state,
                layers=[icon_layer],
                tooltip={
                    "html": "<b>{name}</b><br/>{address}<br/><i>Cliquer pour l'itinéraire</i>",
                    "style": {"color": "white"}
                }
            ))
        else:
            st.warning("Aucune coordonnée disponible.")

    
    with col2:
        st.subheader("⬇️ Liste")
        if df_filtered.empty:
            st.info("Aucun résultat pour ces filtres.")
        else:
            for _, row in df_filtered.iterrows():
                # Respect de la casse originale
                nom_affiche = str(row[c_name])
                
                with st.expander(f"**{nom_affiche}**"):
                    # 1. Adresse
                    st.write(f"📍 {row[c_addr]}")
                    
                    # 2. Description en italique (si elle existe)
                    c_desc = next((c for c in df.columns if 'desc' in c.lower()), None)
                    if c_desc and pd.notna(row[c_desc]):
                        st.write(f"*{row[c_desc]}*")
                    
                    # 3. Tags sous forme d'étiquettes colorées
                    if col_tags and pd.notna(row[col_tags]):
                        tags_list = [t.strip() for t in str(row[col_tags]).split(',')]
                        tag_html = ""
                        for t in tags_list:
                            tag_html += f'<span class="tag-label">{t}</span>'
                        st.markdown(tag_html, unsafe_allow_html=True)
                    
                    st.write("") # Petit espace
    
                    # 4. Bouton "Y aller" stylisé
                    c_link = next((c for c in df.columns if any(word in c.lower() for word in ['map', 'lien', 'geo'])), None)
                    if c_link and pd.notna(row[c_link]):
                        # On utilise un st.link_button avec le style injecté plus haut
                        st.link_button("**Y aller**", row[c_link], use_container_width=True)

except FileNotFoundError:
    st.error("Erreur : Le fichier 'Spottable v1.csv' est introuvable sur GitHub.")
except Exception as e:
    st.error(f"Une erreur est survenue : {e}")
