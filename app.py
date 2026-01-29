import streamlit as st
import pandas as pd
import pydeck as pdk
import re  # Indispensable pour la précision via les liens

# 1. Configuration de la page
st.set_page_config(page_title="Mes spots", layout="wide")

st.write("Fichiers détectés :", st.runtime.get_instance().get_script_run_context().file_path)
# Affiche le contenu brut des premières lignes pour vérifier
test_df = pd.read_csv("Spottable v3.csv")
st.write("Aperçu V3 :", test_df.head(2))

# FORCE LE RECHARGEMENT : On vide le cache pour lire ton fichier CSV à chaque fois
st.cache_data.clear() 

# 2. Style CSS (Couleurs demandées et suppression barre blanche)
st.markdown(f"""
    <style>
    .stApp {{ background-color: #efede1 !important; }}
    header[data-testid="stHeader"] {{ display: none !important; }}
    div[data-testid="stDecoration"] {{ display: none !important; }}
    .main .block-container {{ padding-top: 2rem !important; }}

    h1 {{ color: #d92644 !important; margin-top: -30px !important; }}
    html, body, [class*="st-"], p, div, span, label, h3 {{ color: #202b24 !important; }}

    /* Expanders */
    div[data-testid="stExpander"] {{
        background-color: #efede1 !important;
        border: 0.25px solid #b6beb1 !important;
        border-radius: 8px !important;
        margin-bottom: 10px !important;
    }}
    div[data-testid="stExpander"] summary:hover {{ background-color: #b6beb1 !important; }}
    div[data-testid="stExpander"] details[open] summary {{
        background-color: #b6beb1 !important;
        border-bottom: 1px solid #b6beb1 !important;
    }}
    div[data-testid="stExpander"] details[open] > div[role="region"] {{
        background-color: #efede1 !important;
    }}

    /* Switch */
    div[role="switch"] {{ background-color: #b6beb1 !important; }}
    div[aria-checked="true"][role="switch"] {{ background-color: #d92644 !important; }}
    div[role="switch"] > div:last-child {{ background-color: #efede1 !important; box-shadow: none !important; }}

    /* Recherche */
    div[data-testid="stTextInput"] div[data-baseweb="input"] {{ background-color: #b6beb1 !important; border: none !important; }}
    div[data-testid="stTextInput"] input {{ color: #202b24 !important; -webkit-text-fill-color: #202b24 !important; }}

    .stLinkButton a {{ 
        background-color: #7397a3 !important; 
        color: #efede1 !important; 
        border: none !important; 
        border-radius: 8px !important; 
        font-weight: bold !important; 
        text-decoration: none !important;
        display: flex !important;
        justify-content: center !important;
    }}
    .tag-label {{ display: inline-block; background-color: #b6beb1; color: #202b24; padding: 2px 10px; border-radius: 15px; margin-right: 5px; font-size: 0.75rem; font-weight: bold; }}
    </style>
    """, unsafe_allow_html=True)

# Fonction pour extraire les coordonnées GPS précises d'un lien Google Maps
def get_precise_coords(url):
    if pd.isna(url): return None, None
    # Cherche le format @lat,long (ex: @48.8584,2.2945)
    match = re.search(r'@(-?\d+\.\d+),(-?\d+\.\d+)', str(url))
    if match:
        return float(match.group(1)), float(match.group(2))
    return None, None

st.title("Mes spots")

# 3. Chargement des Données (Utilisation explicite du fichier Spottable v2.csv)
try:
    # Lecture directe
    df = pd.read_csv("Spottable v3.csv", sep=None, engine='python')
    df.columns = df.columns.str.strip().str.lower()
    
    # Identification des colonnes GPS et Lien
    lat_col = next((c for c in df.columns if c in ['latitude', 'lat']), None)
    lon_col = next((c for c in df.columns if c in ['longitude', 'lon']), None)
    c_link = next((c for c in df.columns if any(w in c for w in ['map', 'lien', 'geo'])), None)
    
    # 1. Conversion de base (remplace virgule par point)
    if lat_col and lon_col:
        df['lat'] = pd.to_numeric(df[lat_col].astype(str).str.replace(',', '.'), errors='coerce')
        df['lon'] = pd.to_numeric(df[lon_col].astype(str).str.replace(',', '.'), errors='coerce')
    
    # 2. AFFINAGE : On écrase avec les coordonnées du lien si elles sont trouvées (plus précis)
    if c_link:
        df['precise_tuple'] = df[c_link].apply(get_precise_coords)
        df['lat'] = df.apply(lambda r: r['precise_tuple'][0] if r['precise_tuple'][0] else r['lat'], axis=1)
        df['lon'] = df.apply(lambda r: r['precise_tuple'][1] if r['precise_tuple'][1] else r['lon'], axis=1)

    # Nettoyage des lignes sans coordonnées
    df = df.dropna(subset=['lat', 'lon'])

    c_name = next((c for c in df.columns if c in ['name', 'nom']), df.columns[0])
    c_addr = next((c for c in df.columns if c in ['address', 'adresse']), df.columns[1])
    col_tags = next((c for c in df.columns if c == 'tags'), None)

    # --- RECHERCHE ---
    col_search, _ = st.columns([1, 2])
    with col_search:
        search_query = st.text_input("Rechercher", placeholder="Rechercher un spot", label_visibility="collapsed")

    df_filtered = df[df[c_name].str.contains(search_query, case=False, na=False)].copy() if search_query else df.copy()

    # --- FILTRES ---
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
            df_filtered = df_filtered[df_filtered[col_tags].apply(lambda x: any(t.strip() in selected_tags for t in str(x).split(',')) if pd.notna(x) else False)]

    # --- AFFICHAGE ---
    col1, col2 = st.columns([2, 1])

    with col1:
        if not df_filtered.empty:
            view_state = pdk.ViewState(latitude=df_filtered["lat"].mean(), longitude=df_filtered["lon"].mean(), zoom=13)
            icon_data = {"url": "https://img.icons8.com/ios-filled/100/d92644/marker.png", "width": 100, "height": 100, "anchorY": 100}
            df_filtered["icon_data"] = [icon_data for _ in range(len(df_filtered))]
            layers = [pdk.Layer("IconLayer", data=df_filtered, get_icon="icon_data", get_size=4, size_scale=10, get_position=["lon", "lat"], pickable=True)]
            st.pydeck_chart(pdk.Deck(map_style="https://basemaps.cartocdn.com/gl/positron-gl-style/style.json", initial_view_state=view_state, layers=layers))

    with col2:
        for _, row in df_filtered.iterrows():
            with st.expander(f"**{row[c_name]}**"):
                st.write(f"📍 {row[c_addr]}")
                if col_tags and pd.notna(row[col_tags]):
                    tags = "".join([f'<span class="tag-label">{t.strip()}</span>' for t in str(row[col_tags]).split(',')])
                    st.markdown(tags, unsafe_allow_html=True)
                if c_link and pd.notna(row[c_link]):
                    st.link_button("**Y aller**", row[c_link], use_container_width=True)

except Exception as e:
    st.error(f"Erreur avec le fichier 'Spottable v3.csv' : {e}")
