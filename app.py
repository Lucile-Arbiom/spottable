import streamlit as st
import pandas as pd
import pydeck as pdk
import re

# 1. Configuration de la page
st.set_page_config(page_title="Mes spots", layout="wide")

# 2. Style CSS
st.markdown(f"""
    <style>
    .stApp {{ background-color: #efede1 !important; }}
    header[data-testid="stHeader"] {{ display: none !important; }}
    div[data-testid="stDecoration"] {{ display: none !important; }}
    .main .block-container {{ padding-top: 2rem !important; }}
    h1 {{ color: #d92644 !important; margin-top: -30px !important; }}
    html, body, [class*="st-"], p, div, span, label, h3 {{ color: #202b24 !important; }}
    div[data-testid="stExpander"] {{ background-color: #efede1 !important; border: 0.5px solid #b6beb1 !important; border-radius: 8px !important; margin-bottom: 10px !important; }}
    div[data-testid="stExpander"] summary:hover {{ background-color: #b6beb1 !important; }}
    div[data-testid="stExpander"] details[open] summary {{ background-color: #b6beb1 !important; border-bottom: 1px solid #b6beb1 !important; }}
    div[data-testid="stExpander"] details[open] > div[role="region"] {{ background-color: #efede1 !important; padding: 15px !important; }}
    div[role="switch"] {{ background-color: #b6beb1 !important; }}
    div[aria-checked="true"][role="switch"] {{ background-color: #d92644 !important; }}
    div[role="switch"] > div:last-child {{ background-color: #efede1 !important; box-shadow: none !important; }}
    div[data-testid="stTextInput"] div[data-baseweb="input"] {{ background-color: #b6beb1 !important; border: none !important; }}
    div[data-testid="stTextInput"] input {{ color: #202b24 !important; -webkit-text-fill-color: #202b24 !important; }}
    .stLinkButton a {{ background-color: #7397a3 !important; color: #202b24 !important; border: none !important; border-radius: 8px !important; font-weight: bold !important; text-decoration: none !important; display: flex !important; justify-content: center !important; }}
    .tag-label {{ display: inline-block; background-color: #b6beb1; color: #202b24; padding: 2px 10px; border-radius: 15px; margin-right: 5px; font-size: 0.75rem; font-weight: bold; }}
    </style>
    """, unsafe_allow_html=True)

# Fonction d'extraction robuste
def extract_coords_strict(url):
    if pd.isna(url): return None, None
    url_str = str(url)
    # Cherche @lat,lon
    match = re.search(r'@(-?\d+\.\d+),(-?\d+\.\d+)', url_str)
    if match:
        return float(match.group(1)), float(match.group(2))
    # Cherche q=lat,lon (autre format courant)
    match_q = re.search(r'q=(-?\d+\.\d+),(-?\d+\.\d+)', url_str)
    if match_q:
        return float(match_q.group(1)), float(match_q.group(2))
    return None, None

st.title("Mes spots")

try:
    df = pd.read_csv("Spottable v2.csv", sep=None, engine='python')
    df.columns = df.columns.str.strip().str.lower()
    
    # Identification des colonnes
    c_link = next((c for c in df.columns if any(w in c.lower() for w in ['map', 'lien', 'geo', 'geolocation'])), None)
    c_lat_orig = next((c for c in df.columns if c.lower() in ['lat', 'latitude']), None)
    c_lon_orig = next((c for c in df.columns if c.lower() in ['lon', 'longitude']), None)

    # 1. On commence par convertir les colonnes existantes proprement
    if c_lat_orig and c_lon_orig:
        df['final_lat'] = pd.to_numeric(df[c_lat_orig], errors='coerce')
        df['final_lon'] = pd.to_numeric(df[c_lon_orig], errors='coerce')
    else:
        df['final_lat'] = None
        df['final_lon'] = None

    # 2. Si on a des liens, on essaie d'extraire des coordonnées plus précises
    if c_link:
        df['coords_tuple'] = df[c_link].apply(extract_coords_strict)
        df['ext_lat'] = df['coords_tuple'].apply(lambda x: x[0])
        df['ext_lon'] = df['coords_tuple'].apply(lambda x: x[1])
        
        # On n'écrase que si l'extraction a fonctionné
        df['final_lat'] = df['ext_lat'].fillna(df['final_lat'])
        df['final_lon'] = df['ext_lon'].fillna(df['final_lon'])

    # Nettoyage final : on vire les lignes sans coordonnées
    df_clean = df.dropna(subset=['final_lat', 'final_lon']).copy()

    c_name = next((c for c in df_clean.columns if c.lower() in ['name', 'nom']), df_clean.columns[0])
    c_addr = next((c for c in df_clean.columns if c.lower() in ['address', 'adresse']), df_clean.columns[1])
    col_tags = next((c for c in df_clean.columns if c.lower() == 'tags'), None)

    # RECHERCHE
    col_search, _ = st.columns([1, 2])
    with col_search:
        search_query = st.text_input("Rechercher", placeholder="Rechercher un spot", label_visibility="collapsed")

    df_filtered = df_clean[df_clean[c_name].str.contains(search_query, case=False, na=False)].copy() if search_query else df_clean.copy()

    # FILTRES
    st.write("### Filtrer")
    if col_tags:
        all_tags = sorted(list(set([t.strip() for val in df_clean[col_tags].dropna() for t in str(val).split(',')])))
        t_cols = st.columns(len(all_tags) if len(all_tags) < 6 else 6)
        selected_tags = []
        for i, tag in enumerate(all_tags):
            with t_cols[i % len(t_cols)]:
                if st.toggle(tag, key=f"toggle_{tag}"):
                    selected_tags.append(tag)
        if selected_tags:
            df_filtered = df_filtered[df_filtered[col_tags].apply(lambda x: any(t.strip() in selected_tags for t in str(x).split(',')) if pd.notna(x) else False)]

    # AFFICHAGE
    col1, col2 = st.columns([2, 1])

    with col1:
        if not df_filtered.empty:
            view_state = pdk.ViewState(latitude=df_filtered["final_lat"].mean(), longitude=df_filtered["final_lon"].mean(), zoom=13)
            icon_data = {"url": "https://img.icons8.com/ios-filled/100/d92644/marker.png", "width": 100, "height": 100, "anchorY": 100}
            df_filtered["icon_data"] = [icon_data for _ in range(len(df_filtered))]
            
            # ATTENTION : On utilise bien final_lat et final_lon ici
            layers = [pdk.Layer("IconLayer", data=df_filtered, get_icon="icon_data", get_size=4, size_scale=10, get_position=["final_lon", "final_lat"], pickable=True)]
            st.pydeck_chart(pdk.Deck(map_style="https://basemaps.cartocdn.com/gl/positron-gl-style/style.json", initial_view_state=view_state, layers=layers))
        else:
            st.warning("Aucun spot trouvé.")

    with col2:
        for _, row in df_filtered.iterrows():
            with st.expander(f"**{row[c_name]}**"):
                st.write(f"📍 {row[c_addr]}")
                c_desc = next((c for c in df_clean.columns if 'desc' in c.lower()), None)
                if c_desc and pd.notna(row[c_desc]): st.write(f"*{row[c_desc]}*")
                if col_tags and pd.notna(row[col_tags]):
                    tags = "".join([f'<span class="tag-label">{t.strip()}</span>' for t in str(row[col_tags]).split(',')])
                    st.markdown(tags, unsafe_allow_html=True)
                st.write("")
                if c_link and pd.notna(row[c_link]):
                    st.link_button("**Y aller**", row[c_link], use_container_width=True)

except Exception as e:
    st.error(f"Une erreur est survenue : {e}")
