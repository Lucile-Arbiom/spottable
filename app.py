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
    /* Style du bouton Y aller */
    .stButton>button {{
        background-color: #d92644 !important;
        color: white !important;
        border-radius: 8px !important;
        border: none !important;
    }}
    /* Style des Switchs (Toggles) */
    div[data-baseweb="toggle"] > div:nth-child(2) {{
        background-color: #d92644 !important;
    }}
    /* Style des étiquettes (Tags) */
    .tag-label {{
        display: inline-block;
        background-color: #ffffff;
        color: #d92644;
        padding: 2px 10px;
        border-radius: 15px;
        margin-right: 5px;
        margin-bottom: 5px;
        font-size: 0.75rem;
        font-weight: bold;
        border: 1px solid #d92644;
    }}
    </style>
    """, unsafe_allow_html=True)

# Barre de recherche centrée ou à gauche (1/3 de la largeur sur Web)
col_search, col_empty = st.columns([1, 2]) 

with col_search:
    search_query = st.text_input("🔍 Rechercher un spot", placeholder="Nom du restaurant...")

# On filtre déjà par le nom si une recherche est saisie
if search_query:
    df_filtered = df[df[c_name].str.contains(search_query, case=False, na=False)]
else:
    df_filtered = df.copy()
    

# --- CHARGEMENT DES DONNÉES ---
try:
    df = pd.read_csv("Spottable v2.csv", sep=None, engine='python')
    df.columns = df.columns.str.strip().str.lower()
    
    # Harmonisation des coordonnées
    df = df.rename(columns={'latitude': 'lat', 'longitude': 'lon'})
    df['lat'] = pd.to_numeric(df['lat'], errors='coerce')
    df['lon'] = pd.to_numeric(df['lon'], errors='coerce')

    # Identification des colonnes clés (pour éviter d'autres NameError)
    c_name = next((c for c in df.columns if c.lower() in ['name', 'nom']), df.columns[0])
    c_addr = next((c for c in df.columns if c.lower() in ['address', 'adresse']), df.columns[1])
    col_tags = next((c for c in df.columns if c.lower() == 'tags'), None)

    # --- 2. RECHERCHE ET FILTRES (Seulement si df existe) ---
    col_search, _ = st.columns([1, 2])
    with col_search:
        search_query = st.text_input("🔍 Rechercher un spot", placeholder="Nom du restaurant...")

    if search_query:
        df_filtered = df[df[c_name].str.contains(search_query, case=False, na=False)].copy()
    else:
        df_filtered = df.copy()

    # --- 3. SWITCHS POUR LES TAGS ---
    st.write("### Filtrer")
    if col_tags:
        # Extraction et affichage des switchs... (ton code précédent)
        # ...
        pass # Remplacer par ton code de toggle


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

        st.write("### Filtrer")
        # On récupère tous les tags uniques
        all_tags = sorted(list(set([t.strip() for val in df[col_tags].dropna() for t in str(val).split(',')])))
        
        # Création des switchs sur plusieurs colonnes pour gagner de la place
        cols = st.columns(len(all_tags) if len(all_tags) < 5 else 4) # S'adapte au nombre de tags
        selected_tags = []
        
        for i, tag in enumerate(all_tags):
            # On répartit les switchs dans les colonnes
            with cols[i % len(cols)]:
                if st.toggle(tag, key=tag):
                    selected_tags.append(tag)
        
        # Application du filtre par tags sur le dataframe déjà filtré par le nom
        if selected_tags:
            def match_tags(cell_value):
                if pd.isna(cell_value): return False
                cell_tags = [t.strip() for t in str(cell_value).split(',')]
                return any(tag in cell_tags for tag in selected_tags)
            
            df_filtered = df_filtered[df_filtered[col_tags].apply(match_tags)]
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
        # On s'assure d'utiliser les bonnes colonnes renommées
        df_map = df_filtered.dropna(subset=['lat', 'lon']).copy()
        
        if not df_map.empty:
            # Icône personnalisée avec ta couleur #d92644
            ICON_URL = "https://img.icons8.com/ios-filled/100/d92644/marker.png"
            icon_data = {
                "url": ICON_URL,
                "width": 100,
                "height": 100,
                "anchorY": 100,
            }
            df_map["icon_data"] = [icon_data for _ in range(len(df_map))]
    
            icon_layer = pdk.Layer(
                "IconLayer",
                data=df_map,
                get_icon="icon_data",
                get_size=4,
                size_scale=10,
                get_position=["lon", "lat"],
                pickable=True,
            )
    
            view_state = pdk.ViewState(
                latitude=df_map["lat"].mean(),
                longitude=df_map["lon"].mean(),
                zoom=12,
                pitch=0,
            )
    
            st.pydeck_chart(pdk.Deck(
                map_style="https://basemaps.cartocdn.com/gl/positron-gl-style/style.json",
                initial_view_state=view_state,
                layers=[icon_layer],
                tooltip={"text": "{name}\n{address}"}
            ))
        else:
            st.warning("Vérifiez les coordonnées dans votre fichier.")

    
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
    st.error(f"Erreur lors du chargement des données : {e}")
