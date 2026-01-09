import streamlit as st
import pandas as pd
import pydeck as pdk

# 1. Configuration de la page
st.set_page_config(page_title="Mes spots", layout="wide")
st.title("Mes spots")

# 2. Style CSS
st.markdown(f"""
    <style>
    /* 1. Fond de l'application (Rouge très clair) */
    .stApp {{
        background-color: #fde8ea;
    }}

    /* Titre en Rouge */
    h1 {{
        color: #d92644 !important;
    }}

    /* Texte en Gris foncé */
    html, body, [class*="st-"], p, div {{
        color: #31333f !important;
    }}

    /* Barre de recherche en Gris clair */
    div[data-baseweb="input"] {{
        background-color: #f0f2f6 !important;
        border-radius: 8px !important;
    }}

    /* Switchs (Toggles) : Gris quand éteint, Rouge quand allumé */
    div[data-baseweb="toggle"] > div:nth-child(1) {{
        background-color: #f0f2f6 !important;
    }}
    div[data-baseweb="toggle"][aria-checked="true"] > div:nth-child(2) {{
        background-color: #d92644 !important;
    }}

    /* Étiquettes (Tags) */
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

    /* Bouton "Y aller" */
    .stButton>button {{
        background-color: #d92644 !important;
        color: white !important;
        border-radius: 8px !important;
        border: none !important;
    }}

    /* Cartes (Expanders) blanches */
    .st-expander {{
        background-color: white !important;
        border: 1px solid #fde8ea !important;
        border-radius: 8px !important;
    }}
    </style>
    """, unsafe_allow_html=True)

# 3. Chargement des données (DOIT ÊTRE AVANT LES FILTRES)
try:
    df = pd.read_csv("Spottable v2.csv", sep=None, engine='python')
    df.columns = df.columns.str.strip().str.lower()
    
    # Harmonisation des coordonnées
    df = df.rename(columns={'latitude': 'lat', 'longitude': 'lon'})
    df['lat'] = pd.to_numeric(df['lat'], errors='coerce')
    df['lon'] = pd.to_numeric(df['lon'], errors='coerce')

    # Identification des colonnes clés
    c_name = next((c for c in df.columns if c.lower() in ['name', 'nom']), df.columns[0])
    c_addr = next((c for c in df.columns if c.lower() in ['address', 'adresse']), df.columns[1])
    col_tags = next((c for c in df.columns if c.lower() == 'tags'), None)

    # --- RECHERCHE ---
    col_search, _ = st.columns([1, 2]) 
    with col_search:
        search_query = st.text_input(placeholder="Rechercher un spot")

    if search_query:
        df_filtered = df[df[c_name].str.contains(search_query, case=False, na=False)].copy()
    else:
        df_filtered = df.copy()

    # --- FILTRES (SWITCHS) ---
    st.write("### Filtrer")
    if col_tags:
        all_tags = sorted(list(set([t.strip() for val in df[col_tags].dropna() for t in str(val).split(',')])))
        cols = st.columns(len(all_tags) if len(all_tags) < 6 else 6)
        selected_tags = []
        
        for i, tag in enumerate(all_tags):
            with cols[i % len(cols)]:
                if st.toggle(tag, key=f"toggle_{tag}"):
                    selected_tags.append(tag)
        
        if selected_tags:
            def match_tags(cell_value):
                if pd.isna(cell_value): return False
                cell_tags = [t.strip() for t in str(cell_value).split(',')]
                return any(tag in cell_tags for tag in selected_tags)
            df_filtered = df_filtered[df_filtered[col_tags].apply(match_tags)]

    # --- AFFICHAGE ---
    col1, col2 = st.columns([2, 1])

    with col1:
        df_map = df_filtered.dropna(subset=['lat', 'lon']).copy()
        
        if not df_map.empty:
            ICON_URL = "https://img.icons8.com/ios-filled/100/d92644/marker.png"
            icon_data = {"url": ICON_URL, "width": 100, "height": 100, "anchorY": 100}
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
                tooltip={"text": "{"+c_name+"}\n{"+c_addr+"}"}
            ))
        else:
            st.warning("Aucun spot à afficher sur la carte.")

    with col2:
        if df_filtered.empty:
            st.info("Aucun résultat pour ces filtres.")
        else:
            for _, row in df_filtered.iterrows():
                nom_affiche = str(row[c_name])
                with st.expander(f"**{nom_affiche}**"):
                    st.write(f"📍 {row[c_addr]}")
                    
                    c_desc = next((c for c in df.columns if 'desc' in c.lower()), None)
                    if c_desc and pd.notna(row[c_desc]):
                        st.write(f"*{row[c_desc]}*")
                    
                    if col_tags and pd.notna(row[col_tags]):
                        tags_list = [t.strip() for t in str(row[col_tags]).split(',')]
                        tag_html = "".join([f'<span class="tag-label">{t}</span>' for t in tags_list])
                        st.markdown(tag_html, unsafe_allow_html=True)
                    
                    st.write("")
                    c_link = next((c for c in df.columns if any(word in c.lower() for word in ['map', 'lien', 'geo'])), None)
                    if c_link and pd.notna(row[c_link]):
                        st.link_button("**Y aller**", row[c_link], use_container_width=True)

except Exception as e:
    st.error(f"Erreur lors du chargement ou de l'exécution : {e}")
