import streamlit as st
import pandas as pd
import pydeck as pdk

# 1. Configuration de la page
st.set_page_config(page_title="Mes spots", layout="wide")

# 2. Style CSS complet
st.markdown(f"""
    <style>
    /* Fond de l'application */
    .stApp {{
        background-color: #fde8ea;
    }}

    /* Titre en Rouge */
    h1 {{
        color: #d92644 !important;
    }}

    /* Texte global en Gris foncé */
    html, body, [class*="st-"], p, div, span, label {{
        color: #31333f !important;
    }}

    /* 1. BARRE DE RECHERCHE : Gris clair, SANS CONTOUR, Texte gris foncé */
    div[data-testid="stTextInput"] div[data-baseweb="input"] {{
        background-color: #f0f2f6 !important;
        border: none !important; /* Supprime le contour */
        box-shadow: none !important; /* Supprime l'ombre/halo au clic */
    }}
    
    div[data-testid="stTextInput"] input {{
        color: #31333f !important;
        -webkit-text-fill-color: #31333f !important;
        background-color: #f0f2f6 !important;
        border: none !important;
    }}

    /* Texte du placeholder (Rechercher un spot) en gris foncé */
    div[data-testid="stTextInput"] input::placeholder {{
        color: #31333f !important;
        opacity: 0.7 !important;
    }}

    /* 2. TOGGLES (Switchs) : Gris clair quand éteint */
    div[data-testid="stWidgetLabel"] + div div[role="switch"] {{
        background-color: #f0f2f6 !important;
        background-image: none !important;
    }}

    /* Switch quand il est ACTIVÉ (Rouge) */
    div[data-testid="stWidgetLabel"] + div div[aria-checked="true"] {{
        background-color: #d92644 !important;
    }}

    /* 3. LISTE ET BOUTONS */
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

    .stButton>button {{
        background-color: #d92644 !important;
        color: white !important;
        border-radius: 8px !important;
        border: none !important;
    }}

    .st-expander {{
        background-color: white !important;
        border: 1px solid #fde8ea !important;
        border-radius: 8px !important;
    }}
    </style>
    """, unsafe_allow_html=True)

st.title("Mes spots")

# 3. Chargement des données
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
        # label_visibility="collapsed" enlève le texte au-dessus
        search_query = st.text_input(
            "Rechercher", 
            placeholder="Rechercher un spot", 
            label_visibility="collapsed"
        )

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
                # Key unique obligatoire pour les toggles
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
    st.error(f"Une erreur est survenue : {e}")
