import streamlit as st
import pandas as pd
import pydeck as pdk

# 1. Configuration de la page
st.set_page_config(page_title="Mes spots", layout="wide")

# 2. Style CSS (Contrôle total des Expanders et du Switch)
st.markdown(f"""
    <style>
    /* Fond de l'application */
    .stApp {{ background-color: #efede1 !important; }}
    header[data-testid="stHeader"] {{ display: none !important; }}
    div[data-testid="stDecoration"] {{ display: none !important; }}
    .main .block-container {{ padding-top: 2rem !important; }}

    /* Textes */
    h1 {{ color: #d92644 !important; margin-top: -30px !important; }}
    html, body, [class*="st-"], p, div, span, label, h3 {{ color: #202b24 !important; }}

    /* --- ACCORDÉONS (Expanders) --- */
    /* 1. Base non sélectionnée (Fond #efede1 + Contour #b6beb1) */
    div[data-testid="stExpander"] {{
        background-color: #efede1 !important;
        border: 0.5px solid #b6beb1 !important;
        border-radius: 8px !important;
        margin-bottom: 10px !important;
    }}

    /* 2. Couleur de survol (Background #b6beb1) */
    div[data-testid="stExpander"] summary:hover {{
        background-color: #b6beb1 !important;
    }}

    /* 3. Couleur sélectionnée background TITRE (#b6beb1) */
    div[data-testid="stExpander"] details[open] summary {{
        background-color: #b6beb1 !important;
        border-bottom: 1px solid #b6beb1 !important;
    }}

    /* 4. Couleur sélectionnée background CORPS (#efede1) */
    div[data-testid="stExpander"] details[open] > div[role="region"] {{
        background-color: #efede1 !important;
        padding: 15px !important;
    }}

    /* --- SWITCH (Toggles) --- */
    /* Rail éteint */
    div[role="switch"] {{
        background-color: #b6beb1 !important;
    }}
    
    /* Rail allumé */
    div[aria-checked="true"][role="switch"] {{
        background-color: #d92644 !important;
    }}

    /* BOUTON ROND (Thumb) - Forçage du cercle blanc/beige #efede1 */
    /* On cible l'élément rond spécifique par sa transformation CSS */
    div[role="switch"] > div:last-child {{
        background-color: #efede1 !important;
        box-shadow: none !important;
    }}

    /* --- AUTRES ÉLÉMENTS --- */
    /* Barre de recherche */
    div[data-testid="stTextInput"] div[data-baseweb="input"] {{ 
        background-color: #b6beb1 !important; 
        border: none !important; 
    }}
    div[data-testid="stTextInput"] input {{ 
        color: #202b24 !important; 
        -webkit-text-fill-color: #202b24 !important; 
    }}

    /* Bouton Y aller */
    .stLinkButton a {{ 
        background-color: #7397a3 !important; 
        color: #202b24 !important; 
        border: none !important; 
        border-radius: 8px !important; 
        font-weight: bold !important; 
        text-decoration: none !important; 
        display: flex !important; 
        justify-content: center !important; 
    }}

    /* Étiquettes de tags */
    .tag-label {{
        display: inline-block;
        background-color: #b6beb1;
        color: #202b24;
        padding: 2px 10px;
        border-radius: 15px;
        margin-right: 5px;
        font-size: 0.75rem;
        font-weight: bold;
    }}
    </style>
    """, unsafe_allow_html=True)

st.title("Mes spots")

# 3. Chargement et Traitement des Données
try:
    df = pd.read_csv("Spottable v2.csv", sep=None, engine='python')
    df.columns = df.columns.str.strip().str.lower()
    df = df.rename(columns={'latitude': 'lat', 'longitude': 'lon'})
    df['lat'] = pd.to_numeric(df['lat'], errors='coerce')
    df['lon'] = pd.to_numeric(df['lon'], errors='coerce')

    c_name = next((c for c in df.columns if c.lower() in ['name', 'nom']), df.columns[0])
    c_addr = next((c for c in df.columns if c.lower() in ['address', 'adresse']), df.columns[1])
    col_tags = next((c for c in df.columns if c.lower() == 'tags'), None)

    # RECHERCHE
    col_search, _ = st.columns([1, 2])
    with col_search:
        search_query = st.text_input("Rechercher", placeholder="Rechercher un spot", label_visibility="collapsed")

    df_filtered = df[df[c_name].str.contains(search_query, case=False, na=False)].copy() if search_query else df.copy()

    # FILTRES
    st.write("### Filtrer")
    if col_tags:
        all_tags = sorted(list(set([t.strip() for val in df[col_tags].dropna() for t in str(val).split(',')])))
        t_cols = st.columns(len(all_tags) if len(all_tags) < 6 else 6)
        selected_tags = []
        for i, tag in enumerate(all_tags):
            with t_cols[i % len(t_cols)]:
                if st.toggle(tag, key=f"toggle_{tag}"):
                    selected_tags.append(tag)
        
        if selected_tags:
            def match_tags(val):
                if pd.isna(val): return False
                return any(t.strip() in selected_tags for t in str(val).split(','))
            df_filtered = df_filtered[df_filtered[col_tags].apply(match_tags)]

    # AFFICHAGE
    col1, col2 = st.columns([2, 1])

    with col1:
        df_map = df_filtered.dropna(subset=['lat', 'lon']).copy()
        view_lat = df_map["lat"].mean() if not df_map.empty else 48.8566
        view_lon = df_map["lon"].mean() if not df_map.empty else 2.3522
        view_state = pdk.ViewState(latitude=view_lat, longitude=view_lon, zoom=13)
        icon_data = {"url": "https://img.icons8.com/ios-filled/100/d92644/marker.png", "width": 100, "height": 100, "anchorY": 100}
        df_map["icon_data"] = [icon_data for _ in range(len(df_map))]
        layers = [pdk.Layer("IconLayer", data=df_map, get_icon="icon_data", get_size=4, size_scale=10, get_position=["lon", "lat"], pickable=True)]
        st.pydeck_chart(pdk.Deck(map_style="https://basemaps.cartocdn.com/gl/positron-gl-style/style.json", initial_view_state=view_state, layers=layers))

    with col2:
        if df_filtered.empty:
            st.info("Aucun résultat.")
        else:
            for _, row in df_filtered.iterrows():
                # L'Expander utilise désormais les paramètres de couleur demandés
                with st.expander(f"**{row[c_name]}**"):
                    st.write(f"📍 {row[c_addr]}")
                    c_desc = next((c for c in df.columns if 'desc' in c.lower()), None)
                    if c_desc and pd.notna(row[c_desc]):
                        st.write(f"*{row[c_desc]}*")
                    if col_tags and pd.notna(row[col_tags]):
                        tags = "".join([f'<span class="tag-label">{t.strip()}</span>' for t in str(row[col_tags]).split(',')])
                        st.markdown(tags, unsafe_allow_html=True)
                    st.write("")
                    c_link = next((c for c in df.columns if any(w in c.lower() for w in ['map', 'lien', 'geo'])), None)
                    if c_link and pd.notna(row[c_link]):
                        st.link_button("**Y aller**", row[c_link], use_container_width=True)

except Exception as e:
    st.error(f"Une erreur est survenue : {e}")
