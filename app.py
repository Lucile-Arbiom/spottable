import streamlit as st
import pandas as pd
import pydeck as pdk

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
    
    /* Expanders */
    div[data-testid="stExpander"] {{
        background-color: #efede1 !important;
        border: 0.5px solid #b6beb1 !important;
        border-radius: 8px !important;
        margin-bottom: 10px !important;
    }}
    div[data-testid="stExpander"] summary:hover {{ background-color: #b6beb1 !important; }}
    div[data-testid="stExpander"] details[open] summary {{
        background-color: #b6beb1 !important;
        border-bottom: 1px solid #b6beb1 !important;
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
        color: #202b24 !important; 
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

st.title("Mes spots")

try:
    # 3. Chargement et Nettoyage STRICT
    df = pd.read_csv("Spottable v2.csv", sep=None, engine='python')
    df.columns = df.columns.str.strip().str.lower()
    
    # Identification dynamique des colonnes GPS
    lat_col = next((c for c in df.columns if c in ['latitude', 'lat']), None)
    lon_col = next((c for c in df.columns if c in ['longitude', 'lon']), None)
    
    if lat_col and lon_col:
        # Conversion forcée en nombres flottants (en remplaçant les virgules par des points si besoin)
        df['lat'] = pd.to_numeric(df[lat_col].astype(str).str.replace(',', '.'), errors='coerce')
        df['lon'] = pd.to_numeric(df[lon_col].astype(str).str.replace(',', '.'), errors='coerce')
    
    # Suppression des lignes où les coordonnées sont invalides
    df = df.dropna(subset=['lat', 'lon'])

    c_name = next((c for c in df.columns if c in ['name', 'nom']), df.columns[0])
    c_addr = next((c for c in df.columns if c in ['address', 'adresse']), df.columns[1])
    c_link = next((c for c in df.columns if any(w in c for w in ['map', 'lien', 'geo'])), None)
    col_tags = next((c for c in df.columns if c == 'tags'), None)

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
            df_filtered = df_filtered[df_filtered[col_tags].apply(lambda x: any(t.strip() in selected_tags for t in str(x).split(',')) if pd.notna(x) else False)]

    # 4. AFFICHAGE CARTE
    col1, col2 = st.columns([2, 1])

    with col1:
        if not df_filtered.empty:
            # Zoom plus important (15) pour vérifier la précision
            view_state = pdk.ViewState(latitude=df_filtered["lat"].mean(), longitude=df_filtered["lon"].mean(), zoom=14)
            
            icon_data = {"url": "https://img.icons8.com/ios-filled/100/d92644/marker.png", "width": 100, "height": 100, "anchorY": 100}
            df_filtered["icon_data"] = [icon_data for _ in range(len(df_filtered))]
            
            # Utilisation du Layer IconLayer avec les colonnes nettoyées
            layers = [pdk.Layer(
                "IconLayer", 
                data=df_filtered, 
                get_icon="icon_data", 
                get_size=4, 
                size_scale=10, 
                get_position=["lon", "lat"], 
                pickable=True
            )]
            
            st.pydeck_chart(pdk.Deck(
                map_style="https://basemaps.cartocdn.com/gl/positron-gl-style/style.json",
                initial_view_state=view_state,
                layers=layers,
                tooltip={"text": "{"+c_name+"}"}
            ))

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
    st.error(f"Erreur : {e}")
