import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime
import json
import os
import re

# ============================================================================
# CONFIGURATION & THÈME
# ============================================================================

st.set_page_config(
    page_title="MenuPro - Gestion des Menus",
    page_icon="🍽️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# CSS personnalisé pour un look moderne et professionnel
st.markdown("""
<style>
    /* Import Google Fonts */
    @import url('https://fonts.googleapis.com/css2?family=Outfit:wght@300;400;500;600;700&display=swap');
    
    /* Base styles */
    .stApp {
        font-family: 'Outfit', sans-serif !important;
        background: linear-gradient(135deg, #f0f4ff 0%, #fdf4ff 50%, #fff7ed 100%);
    }
    
    /* Ensure all text is visible */
    .stApp, .stApp p, .stApp span, .stApp label, .stApp div {
        color: #1e293b !important;
    }
    
    /* Hide default Streamlit elements */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    .stDeployButton {display: none;}
    
    /* Header styling */
    .main-header {
        background: linear-gradient(135deg, #1e3a5f 0%, #2563eb 50%, #7c3aed 100%);
        padding: 2rem 2.5rem;
        border-radius: 20px;
        margin-bottom: 2rem;
        box-shadow: 0 10px 15px -3px rgba(0, 0, 0, 0.1);
        position: relative;
        overflow: hidden;
    }
    
    .main-header h1 {
        color: white !important;
        font-size: 2.5rem;
        font-weight: 700;
        margin: 0;
    }
    
    .main-header p {
        color: rgba(255,255,255,0.9) !important;
        font-size: 1.1rem;
        margin-top: 0.5rem;
    }
    
    /* Day cards for planning */
    .day-card {
        background: white;
        border-radius: 16px;
        padding: 1.25rem;
        text-align: center;
        transition: all 0.3s ease;
        border: 2px solid transparent;
        min-height: 180px;
        box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1);
    }
    
    .day-card:hover {
        transform: translateY(-4px);
        box-shadow: 0 10px 15px -3px rgba(0, 0, 0, 0.1);
    }
    
    .day-card.empty {
        background: linear-gradient(135deg, #f8fafc 0%, #f1f5f9 100%);
        border-color: #e2e8f0;
    }
    
    .day-card.pending {
        background: linear-gradient(135deg, #fffbeb 0%, #fef3c7 100%);
        border-color: #fbbf24;
    }
    
    .day-card.completed {
        background: linear-gradient(135deg, #ecfdf5 0%, #d1fae5 100%);
        border-color: #10b981;
    }
    
    .day-name {
        font-size: 1.1rem;
        font-weight: 600;
        color: #1e293b !important;
        margin-bottom: 0.75rem;
    }
    
    .day-stats {
        font-size: 0.85rem;
        color: #64748b !important;
    }
    
    /* Tab styling - fix text visibility */
    .stTabs [data-baseweb="tab-list"] {
        gap: 8px;
        background: white;
        padding: 0.5rem;
        border-radius: 12px;
        box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1);
    }
    
    .stTabs [data-baseweb="tab"] {
        border-radius: 8px;
        padding: 0.75rem 1.5rem;
        font-weight: 500;
        color: #1e293b !important;
    }
    
    .stTabs [aria-selected="true"] {
        background: linear-gradient(135deg, #2563eb 0%, #7c3aed 100%) !important;
    }
    
    .stTabs [aria-selected="true"] span {
        color: white !important;
    }
    
    /* Button styling */
    .stButton > button {
        border-radius: 10px;
        padding: 0.6rem 1.5rem;
        font-weight: 500;
        transition: all 0.2s ease;
    }
    
    .stButton > button:hover {
        transform: translateY(-2px);
        box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1);
    }
    
    /* Metric cards */
    .metric-card {
        background: white;
        border-radius: 16px;
        padding: 1.5rem;
        text-align: center;
        box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1);
        border-left: 4px solid;
    }
    
    .metric-card.blue { border-left-color: #2563eb; }
    .metric-card.green { border-left-color: #10b981; }
    .metric-card.orange { border-left-color: #f59e0b; }
    .metric-card.purple { border-left-color: #7c3aed; }
    
    .metric-value {
        font-size: 2.5rem;
        font-weight: 700;
        color: #2563eb !important;
    }
    
    .metric-label {
        font-size: 0.9rem;
        color: #64748b !important;
        margin-top: 0.25rem;
    }
    
    /* Selectbox and inputs */
    .stSelectbox > div > div {
        background: white;
        border-radius: 10px;
    }
    
    .stSelectbox label, .stMultiSelect label, .stCheckbox label, .stRadio label {
        color: #1e293b !important;
        font-weight: 500;
    }
    
    /* Checkbox text */
    .stCheckbox span {
        color: #1e293b !important;
    }
    
    /* Expander styling */
    .streamlit-expanderHeader {
        background: white;
        border-radius: 12px;
        font-weight: 500;
        color: #1e293b !important;
    }
    
    .streamlit-expanderHeader p {
        color: #1e293b !important;
    }
    
    /* Section titles */
    .section-title {
        font-size: 1.5rem;
        font-weight: 600;
        color: #1e293b !important;
        margin-bottom: 1rem;
        display: flex;
        align-items: center;
        gap: 0.75rem;
    }
    
    /* Info boxes */
    .info-box {
        background: linear-gradient(135deg, #eff6ff 0%, #f0f4ff 100%);
        border-left: 4px solid #2563eb;
        border-radius: 0 12px 12px 0;
        padding: 1rem 1.25rem;
        margin: 1rem 0;
        color: #1e293b !important;
    }
    
    .info-box.warning {
        background: linear-gradient(135deg, #fffbeb 0%, #fef3c7 100%);
        border-left-color: #f59e0b;
    }
    
    /* Caption text */
    .stCaption, small {
        color: #64748b !important;
    }
    
    /* DataFrame */
    .stDataFrame {
        background: white;
        border-radius: 12px;
        padding: 1rem;
    }
</style>
""", unsafe_allow_html=True)

# ============================================================================
# CONSTANTES
# ============================================================================

EMOJIS = {0: "😢", 1: "😕", 2: "😊", 3: "😍"}
EMOJI_LABELS = {0: "Insuffisant", 1: "Passable", 2: "Bien", 3: "Excellent"}
JOURS_SEMAINE = ["Lundi", "Mardi", "Mercredi", "Jeudi", "Vendredi"]
JOURS_ICONS = {"Lundi": "🌅", "Mardi": "🌤️", "Mercredi": "☀️", "Jeudi": "🌈", "Vendredi": "🎉"}
MONTHS = ['janvier', 'février', 'mars', 'avril', 'mai', 'juin', 'juillet', 'août', 'septembre', 'octobre', 'novembre', 'décembre']
EXCLUDE_KEYWORDS = ['siret', 'intercommunautaire', 'agrément', 'laboratoire', 'normes', 'email', 'contact', 'tel', 'tél', 'bureau', 'comptabilité', 'chef', 'entreprise', 'fiche', 'satisfaction', 'menus', 'site', 'alpa', 'veuillez', 'entourer', 'smiley', 'correspond', 'ressenti', 'lundi', 'mardi', 'mercredi', 'jeudi', 'vendredi', 'quantité', 'quantités', 'livrés', 'qualité', 'plats']
SITES = ["Site 1", "Site 2", "Site 3"]
CATEGORY_ICONS = {'entree': '🥗', 'plat': '🍖', 'dessert': '🍰'}
CATEGORY_NAMES = {'entree': 'Entrées', 'plat': 'Plats', 'dessert': 'Desserts'}

# ============================================================================
# FONCTIONS UTILITAIRES
# ============================================================================

def classify_plat(plat_name):
    """Classifie un plat en entrée, plat principal ou dessert"""
    plat_lower = plat_name.lower()
    if any(kw in plat_lower for kw in ['salade', 'soupe', 'gaspacho', 'velouté', 'consommé']):
        return 'entree'
    elif any(kw in plat_lower for kw in ['gateau', 'gâteau', 'crème', 'creme', 'dessert', 'yaourt', 'fruit', 'melon', 'anglaise', 'ananas', 'poire']):
        return 'dessert'
    else:
        return 'plat'

@st.cache_data
def load_plats_from_excel():
    """Charge et classe les plats depuis FS.xlsx"""
    try:
        df = pd.read_excel('FS.xlsx')
        plats = []
        for col in df.columns:
            for value in df[col]:
                if pd.notna(value):
                    plat_str = str(value).strip()
                    plat_lower = plat_str.lower()
                    if (len(plat_str) > 4 and plat_lower not in ['nan', 'none', ''] and
                        not any(m in plat_lower for m in MONTHS) and
                        not re.search(r'\d{5}', plat_str) and
                        sum(c.isdigit() for c in plat_str) <= len(plat_str) * 0.5 and
                        not any(excl in plat_lower for excl in EXCLUDE_KEYWORDS) and
                        any(c.isalpha() for c in plat_str) and not plat_str.replace(' ', '').isdigit() and
                        plat_str not in plats):
                        plats.append(plat_str)
        
        plats_classifies = {'entree': [], 'plat': [], 'dessert': []}
        for plat in sorted(plats):
            plats_classifies[classify_plat(plat)].append(plat)
        return plats_classifies
    except Exception as e:
        st.error(f"Erreur lors du chargement: {e}")
        return {'entree': [], 'plat': [], 'dessert': []}

def init_session_state():
    """Initialise les données de session"""
    defaults = {
        'menus': {},
        'current_site': "Site 1",
        'current_semaine': 1,
        'selected_day': None,
        'view_mode': "semaine",
        'show_toast': False,
        'toast_message': ""
    }
    for key, value in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = value

def save_data():
    """Sauvegarde les données"""
    with open('menu_data.json', 'w', encoding='utf-8') as f:
        json.dump({'menus': st.session_state.menus, 'last_update': datetime.now().isoformat()}, f, ensure_ascii=False, indent=2)

def load_data():
    """Charge les données sauvegardées"""
    if os.path.exists('menu_data.json'):
        try:
            with open('menu_data.json', 'r', encoding='utf-8') as f:
                st.session_state.menus = json.load(f).get('menus', {})
        except Exception:
            pass

def get_key(site, semaine):
    return f"{site}_Semaine{semaine}"

def get_jour_data(site, semaine, jour):
    """Récupère les données d'un jour spécifique"""
    key = get_key(site, semaine)
    if key in st.session_state.menus and jour in st.session_state.menus[key]:
        return st.session_state.menus[key][jour]
    return {}

def get_jour_status(site, semaine, jour):
    """Obtient le statut d'évaluation d'un jour"""
    data = get_jour_data(site, semaine, jour)
    if not data:
        return None, None, 0
    
    qte_values = []
    qual_values = []
    for plat, values in data.items():
        if isinstance(values, dict):
            qte = values.get('quantite')
            qual = values.get('qualite')
            if qte is not None:
                qte_values.append(qte)
            if qual is not None:
                qual_values.append(qual)
    
    avg_qte = sum(qte_values) / len(qte_values) if qte_values else None
    avg_qual = sum(qual_values) / len(qual_values) if qual_values else None
    total_plats = len(data)
    
    return avg_qte, avg_qual, total_plats

def calculate_averages():
    """Calcule les moyennes par plat"""
    if not st.session_state.menus:
        return pd.DataFrame()
    
    all_data = []
    for key, menu_data in st.session_state.menus.items():
        for jour, plats in menu_data.items():
            if isinstance(plats, dict):
                for plat, values in plats.items():
                    if isinstance(values, dict):
                        qte, qual = values.get('quantite'), values.get('qualite')
                        cat = values.get('categorie', 'plat')
                        if qte is not None or qual is not None:
                            all_data.append({'Plat': plat, 'Catégorie': cat, 'Quantité': qte, 'Qualité': qual})
    
    if not all_data:
        return pd.DataFrame()
    
    df = pd.DataFrame(all_data)
    return df.groupby(['Plat', 'Catégorie']).agg({'Quantité': 'mean', 'Qualité': 'mean'}).reset_index().round(2)

def prepare_evolution_data():
    """Prépare les données pour l'évolution"""
    evolution_data = []
    for key, menu_data in st.session_state.menus.items():
        parts = key.split('_Semaine')
        if len(parts) == 2:
            site, semaine = parts
            for jour, plats in menu_data.items():
                if isinstance(plats, dict):
                    for plat, values in plats.items():
                        if isinstance(values, dict):
                            qte, qual = values.get('quantite'), values.get('qualite')
                            if qte is not None or qual is not None:
                                evolution_data.append({
                                    'Site': site, 'Semaine': int(semaine), 'Jour': jour,
                                    'Plat': plat, 'Quantité': qte, 'Qualité': qual
                                })
    return pd.DataFrame(evolution_data) if evolution_data else pd.DataFrame()

def get_global_stats():
    """Calcule les statistiques globales"""
    total_plats = 0
    total_evaluations = 0
    sum_qte = 0
    sum_qual = 0
    count_qte = 0
    count_qual = 0
    
    for key, menu_data in st.session_state.menus.items():
        for jour, plats in menu_data.items():
            if isinstance(plats, dict):
                total_plats += len(plats)
                for plat, values in plats.items():
                    if isinstance(values, dict):
                        qte = values.get('quantite')
                        qual = values.get('qualite')
                        if qte is not None:
                            sum_qte += qte
                            count_qte += 1
                            total_evaluations += 1
                        if qual is not None:
                            sum_qual += qual
                            count_qual += 1
    
    avg_qte = round(sum_qte / count_qte, 2) if count_qte > 0 else 0
    avg_qual = round(sum_qual / count_qual, 2) if count_qual > 0 else 0
    
    return {
        'total_plats': total_plats,
        'total_evaluations': total_evaluations,
        'avg_quantite': avg_qte,
        'avg_qualite': avg_qual
    }

# ============================================================================
# COMPOSANTS UI
# ============================================================================

def render_header():
    """Affiche l'en-tête principal"""
    st.markdown("""
    <div class="main-header">
        <h1>🍽️ MenuPro</h1>
        <p>Gestion intelligente des menus et évaluation de la satisfaction</p>
    </div>
    """, unsafe_allow_html=True)

def render_metric_cards(stats):
    """Affiche les cartes de métriques"""
    cols = st.columns(4)
    
    metrics = [
        ("Total Plats", stats['total_plats'], "🍽️", "blue"),
        ("Évaluations", stats['total_evaluations'], "📊", "green"),
        (f"Moy. Quantité", f"{stats['avg_quantite']:.1f}/3", "📦", "orange"),
        (f"Moy. Qualité", f"{stats['avg_qualite']:.1f}/3", "⭐", "purple")
    ]
    
    for col, (label, value, icon, color) in zip(cols, metrics):
        with col:
            st.markdown(f"""
            <div class="metric-card {color}">
                <div style="font-size: 1.5rem; margin-bottom: 0.5rem;">{icon}</div>
                <div class="metric-value">{value}</div>
                <div class="metric-label">{label}</div>
            </div>
            """, unsafe_allow_html=True)

def render_day_card(jour, site, semaine, idx):
    """Affiche une carte de jour cliquable"""
    avg_qte, avg_qual, nb_plats = get_jour_status(site, semaine, jour)
    
    # Déterminer le statut
    if nb_plats == 0:
        status = "empty"
        status_icon = "⚪"
        status_text = "Aucun plat"
    elif avg_qte is not None or avg_qual is not None:
        status = "completed"
        status_icon = "✅"
        status_text = f"{nb_plats} plat(s) évalué(s)"
    else:
        status = "pending"
        status_icon = "⏳"
        status_text = f"{nb_plats} plat(s) en attente"
    
    # Affichage de la carte
    st.markdown(f"""
    <div class="day-card {status}">
        <div style="font-size: 1.5rem; margin-bottom: 0.5rem;">{JOURS_ICONS.get(jour, '📅')}</div>
        <div class="day-name">{jour}</div>
        <div style="font-size: 1.2rem; margin: 0.5rem 0;">{status_icon}</div>
        <div class="day-stats">{status_text}</div>
    </div>
    """, unsafe_allow_html=True)
    
    # Affichage des moyennes si disponibles
    if avg_qte is not None or avg_qual is not None:
        col1, col2 = st.columns(2)
        with col1:
            if avg_qte is not None:
                emoji = EMOJIS[int(round(avg_qte))]
                st.caption(f"📦 {emoji} {avg_qte:.1f}")
        with col2:
            if avg_qual is not None:
                emoji = EMOJIS[int(round(avg_qual))]
                st.caption(f"⭐ {emoji} {avg_qual:.1f}")
    
    # Bouton pour sélectionner le jour
    if st.button(f"📝 Gérer", key=f"btn_{jour}_{semaine}_{idx}", use_container_width=True):
        st.session_state.selected_day = jour
        st.rerun()

def render_emoji_rating(plat, key_base, jour, type_eval, label):
    """Affiche les boutons emoji pour l'évaluation"""
    current_val = st.session_state.menus[key_base][jour][plat].get(type_eval)
    
    st.markdown(f"**{label}**")
    cols = st.columns(4)
    
    for note, col in enumerate(cols):
        with col:
            is_selected = current_val == note
            btn_style = "selected" if is_selected else ""
            
            if st.button(
                f"{'✓ ' if is_selected else ''}{EMOJIS[note]}",
                key=f"rate_{type_eval}_{key_base}_{jour}_{plat}_{note}",
                use_container_width=True,
                type="primary" if is_selected else "secondary"
            ):
                st.session_state.menus[key_base][jour][plat][type_eval] = note
                save_data()
                st.rerun()
    
    if current_val is not None:
        st.caption(f"Note actuelle: {EMOJIS[current_val]} {EMOJI_LABELS[current_val]}")

def render_dish_selection(categorie, plats_list, key_base, jour):
    """Affiche la sélection de plats par catégorie"""
    if not plats_list:
        return
    
    icon = CATEGORY_ICONS.get(categorie, '🍽️')
    name = CATEGORY_NAMES.get(categorie, categorie.title())
    
    with st.expander(f"{icon} {name} ({len(plats_list)} disponibles)", expanded=True):
        # Organiser en grille
        cols = st.columns(2)
        
        for idx, plat in enumerate(plats_list):
            with cols[idx % 2]:
                is_selected = plat in st.session_state.menus[key_base][jour]
                
                if st.checkbox(
                    plat,
                    value=is_selected,
                    key=f"dish_{key_base}_{jour}_{categorie}_{plat}"
                ):
                    if plat not in st.session_state.menus[key_base][jour]:
                        st.session_state.menus[key_base][jour][plat] = {
                            'quantite': None,
                            'qualite': None,
                            'categorie': categorie
                        }
                        save_data()
                else:
                    if plat in st.session_state.menus[key_base][jour]:
                        del st.session_state.menus[key_base][jour][plat]
                        save_data()

# ============================================================================
# PAGES PRINCIPALES
# ============================================================================

def page_dashboard():
    """Page tableau de bord"""
    stats = get_global_stats()
    
    # Métriques
    render_metric_cards(stats)
    
    st.markdown("<br>", unsafe_allow_html=True)
    
    # Planning de la semaine
    st.markdown('<div class="section-title">📅 Planning de la semaine</div>', unsafe_allow_html=True)
    
    col_config1, col_config2 = st.columns(2)
    with col_config1:
        site = st.selectbox(
            "🏢 Site",
            SITES,
            index=SITES.index(st.session_state.current_site) if st.session_state.current_site in SITES else 0,
            key="dashboard_site"
        )
        st.session_state.current_site = site
    
    with col_config2:
        semaine = st.selectbox(
            "📆 Semaine",
            list(range(1, 6)),
            index=st.session_state.current_semaine - 1,
            key="dashboard_semaine"
        )
        st.session_state.current_semaine = semaine
    
    st.markdown("<br>", unsafe_allow_html=True)
    
    # Cartes des jours
    key = get_key(st.session_state.current_site, st.session_state.current_semaine)
    if key not in st.session_state.menus:
        st.session_state.menus[key] = {j: {} for j in JOURS_SEMAINE}
    
    cols = st.columns(5)
    for idx, (col, jour) in enumerate(zip(cols, JOURS_SEMAINE)):
        with col:
            render_day_card(jour, st.session_state.current_site, st.session_state.current_semaine, idx)

def page_planning():
    """Page de planification des menus"""
    st.markdown('<div class="section-title">📋 Planification des Menus</div>', unsafe_allow_html=True)
    
    # Configuration
    col1, col2, col3 = st.columns([2, 2, 1])
    with col1:
        site = st.selectbox("🏢 Site", SITES, 
                           index=SITES.index(st.session_state.current_site) if st.session_state.current_site in SITES else 0,
                           key="planning_site_select")
        st.session_state.current_site = site
    
    with col2:
        semaine = st.selectbox("📆 Semaine", list(range(1, 6)),
                              index=st.session_state.current_semaine - 1,
                              key="planning_semaine_select")
        st.session_state.current_semaine = semaine
    
    with col3:
        st.markdown("<br>", unsafe_allow_html=True)
        if st.button("💾 Sauvegarder", use_container_width=True, type="primary"):
            save_data()
            st.success("✅ Sauvegardé !")
    
    key = get_key(st.session_state.current_site, st.session_state.current_semaine)
    if key not in st.session_state.menus:
        st.session_state.menus[key] = {j: {} for j in JOURS_SEMAINE}
    
    plats_classifies = load_plats_from_excel()
    
    st.markdown("---")
    
    # Si un jour est sélectionné, afficher uniquement ce jour
    if st.session_state.selected_day:
        jour = st.session_state.selected_day
        
        col_back, col_title = st.columns([1, 4])
        with col_back:
            if st.button("← Retour", use_container_width=True):
                st.session_state.selected_day = None
                st.rerun()
        with col_title:
            st.markdown(f"### {JOURS_ICONS.get(jour, '📅')} {jour}")
        
        if jour not in st.session_state.menus[key]:
            st.session_state.menus[key][jour] = {}
        
        # Sélection des plats
        st.markdown("#### 🍽️ Sélection des plats")
        
        tab_entree, tab_plat, tab_dessert = st.tabs(["🥗 Entrées", "🍖 Plats", "🍰 Desserts"])
        
        with tab_entree:
            render_dish_selection('entree', plats_classifies.get('entree', []), key, jour)
        with tab_plat:
            render_dish_selection('plat', plats_classifies.get('plat', []), key, jour)
        with tab_dessert:
            render_dish_selection('dessert', plats_classifies.get('dessert', []), key, jour)
        
        # Évaluation des plats sélectionnés
        if st.session_state.menus[key][jour]:
            st.markdown("---")
            st.markdown("#### 📊 Évaluation des plats")
            
            for plat, values in st.session_state.menus[key][jour].items():
                cat = values.get('categorie', 'plat')
                cat_icon = CATEGORY_ICONS.get(cat, '🍽️')
                
                with st.expander(f"{cat_icon} {plat}", expanded=True):
                    col1, col2 = st.columns(2)
                    
                    with col1:
                        render_emoji_rating(plat, key, jour, 'quantite', '📦 Quantité')
                    
                    with col2:
                        render_emoji_rating(plat, key, jour, 'qualite', '⭐ Qualité')
    else:
        # Afficher tous les jours
        for jour in JOURS_SEMAINE:
            if jour not in st.session_state.menus[key]:
                st.session_state.menus[key][jour] = {}
            
            avg_qte, avg_qual, nb_plats = get_jour_status(st.session_state.current_site, st.session_state.current_semaine, jour)
            
            # Indicateur de statut
            if nb_plats == 0:
                status_badge = "⚪ Vide"
            elif avg_qte is not None or avg_qual is not None:
                status_badge = "✅ Évalué"
            else:
                status_badge = "⏳ En attente"
            
            with st.expander(f"{JOURS_ICONS.get(jour, '📅')} {jour} - {status_badge} ({nb_plats} plats)"):
                col_select, col_eval = st.columns([1, 1])
                
                with col_select:
                    st.markdown("**Sélection des plats**")
                    for cat in ['entree', 'plat', 'dessert']:
                        render_dish_selection(cat, plats_classifies.get(cat, []), key, jour)
                
                with col_eval:
                    if st.session_state.menus[key][jour]:
                        st.markdown("**Évaluations**")
                        for plat in st.session_state.menus[key][jour]:
                            st.markdown(f"**{plat}**")
                            render_emoji_rating(plat, key, jour, 'quantite', '📦 Quantité')
                            render_emoji_rating(plat, key, jour, 'qualite', '⭐ Qualité')
                            st.markdown("---")
                    else:
                        st.info("Sélectionnez des plats pour les évaluer")

def page_statistiques():
    """Page des statistiques et graphiques"""
    st.markdown('<div class="section-title">📊 Statistiques & Analyses</div>', unsafe_allow_html=True)
    
    moyennes_df = calculate_averages()
    
    if moyennes_df.empty:
        st.markdown("""
        <div class="info-box warning">
            <strong>📭 Aucune donnée disponible</strong><br>
            Commencez par planifier des menus et évaluer des plats pour voir les statistiques.
        </div>
        """, unsafe_allow_html=True)
        return
    
    # Graphiques principaux
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("#### 📦 Moyennes des Quantités")
        fig_qte = px.bar(
            moyennes_df.sort_values('Quantité', ascending=True),
            x='Quantité',
            y='Plat',
            orientation='h',
            color='Catégorie',
            color_discrete_map={'entree': '#10b981', 'plat': '#ef4444', 'dessert': '#f59e0b'},
            template='plotly_white'
        )
        fig_qte.update_layout(
            height=400,
            margin=dict(l=0, r=0, t=20, b=0),
            font=dict(family='Outfit'),
            legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1)
        )
        fig_qte.update_traces(marker_line_width=0)
        st.plotly_chart(fig_qte, use_container_width=True)
    
    with col2:
        st.markdown("#### ⭐ Moyennes des Qualités")
        fig_qual = px.bar(
            moyennes_df.sort_values('Qualité', ascending=True),
            x='Qualité',
            y='Plat',
            orientation='h',
            color='Catégorie',
            color_discrete_map={'entree': '#10b981', 'plat': '#ef4444', 'dessert': '#f59e0b'},
            template='plotly_white'
        )
        fig_qual.update_layout(
            height=400,
            margin=dict(l=0, r=0, t=20, b=0),
            font=dict(family='Outfit'),
            legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1)
        )
        fig_qual.update_traces(marker_line_width=0)
        st.plotly_chart(fig_qual, use_container_width=True)
    
    # Tableau récapitulatif
    st.markdown("#### 📋 Tableau récapitulatif")
    
    # Formater le tableau avec des emojis
    display_df = moyennes_df.copy()
    display_df['Emoji Qté'] = display_df['Quantité'].apply(lambda x: EMOJIS[int(round(x))] if pd.notna(x) else '')
    display_df['Emoji Qual'] = display_df['Qualité'].apply(lambda x: EMOJIS[int(round(x))] if pd.notna(x) else '')
    
    st.dataframe(
        display_df[['Plat', 'Catégorie', 'Quantité', 'Emoji Qté', 'Qualité', 'Emoji Qual']],
        use_container_width=True,
        hide_index=True
    )

def page_evolution():
    """Page de l'évolution dans le temps"""
    st.markdown('<div class="section-title">📈 Évolution dans le temps</div>', unsafe_allow_html=True)
    
    df_evolution = prepare_evolution_data()
    
    if df_evolution.empty:
        st.markdown("""
        <div class="info-box warning">
            <strong>📭 Aucune donnée d'évolution disponible</strong><br>
            Évaluez des plats sur plusieurs semaines pour voir leur évolution.
        </div>
        """, unsafe_allow_html=True)
        return
    
    # Filtres dans une sidebar compacte
    with st.expander("🔍 Filtres", expanded=True):
        col1, col2, col3 = st.columns(3)
        
        with col1:
            sites_sel = st.multiselect(
                "Sites",
                sorted(df_evolution['Site'].unique()),
                default=sorted(df_evolution['Site'].unique()),
                key="evo_sites"
            )
        
        with col2:
            semaines_disponibles = sorted(df_evolution['Semaine'].unique())
            semaines_sel = st.multiselect(
                "Semaines",
                semaines_disponibles,
                default=semaines_disponibles,
                key="evo_semaines"
            )
        
        with col3:
            metrique = st.selectbox(
                "Métrique",
                ["Quantité", "Qualité", "Les deux"],
                index=2,
                key="evo_metrique"
            )
    
    # Appliquer les filtres
    df_filtre = df_evolution.copy()
    if sites_sel:
        df_filtre = df_filtre[df_filtre['Site'].isin(sites_sel)]
    if semaines_sel:
        df_filtre = df_filtre[df_filtre['Semaine'].isin(semaines_sel)]
    
    if df_filtre.empty:
        st.warning("⚠️ Aucune donnée avec ces filtres.")
        return
    
    # Graphique d'évolution globale
    moy_global = df_filtre.groupby(['Semaine', 'Site']).agg({
        'Quantité': 'mean',
        'Qualité': 'mean'
    }).reset_index()
    
    col1, col2 = st.columns(2)
    
    with col1:
        if metrique in ["Quantité", "Les deux"]:
            st.markdown("#### 📦 Évolution des Quantités")
            fig = px.line(
                moy_global,
                x='Semaine',
                y='Quantité',
                color='Site',
                markers=True,
                template='plotly_white',
                color_discrete_sequence=['#2563eb', '#10b981', '#f59e0b']
            )
            fig.update_layout(
                height=350,
                margin=dict(l=0, r=0, t=20, b=0),
                font=dict(family='Outfit'),
                legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1)
            )
            fig.update_traces(line=dict(width=3))
            st.plotly_chart(fig, use_container_width=True)
    
    with col2:
        if metrique in ["Qualité", "Les deux"]:
            st.markdown("#### ⭐ Évolution des Qualités")
            fig = px.line(
                moy_global,
                x='Semaine',
                y='Qualité',
                color='Site',
                markers=True,
                template='plotly_white',
                color_discrete_sequence=['#2563eb', '#10b981', '#f59e0b']
            )
            fig.update_layout(
                height=350,
                margin=dict(l=0, r=0, t=20, b=0),
                font=dict(family='Outfit'),
                legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1)
            )
            fig.update_traces(line=dict(width=3))
            st.plotly_chart(fig, use_container_width=True)
    
    # Comparaison des sites
    st.markdown("#### 🏢 Comparaison des Sites")
    
    moy_sites = df_filtre.groupby('Site').agg({
        'Quantité': 'mean',
        'Qualité': 'mean'
    }).reset_index()
    
    fig_radar = go.Figure()
    
    for site in moy_sites['Site'].unique():
        site_data = moy_sites[moy_sites['Site'] == site]
        fig_radar.add_trace(go.Scatterpolar(
            r=[site_data['Quantité'].values[0], site_data['Qualité'].values[0], site_data['Quantité'].values[0]],
            theta=['Quantité', 'Qualité', 'Quantité'],
            fill='toself',
            name=site
        ))
    
    fig_radar.update_layout(
        polar=dict(radialaxis=dict(visible=True, range=[0, 3])),
        showlegend=True,
        template='plotly_white',
        height=400,
        font=dict(family='Outfit')
    )
    
    st.plotly_chart(fig_radar, use_container_width=True)

# ============================================================================
# APPLICATION PRINCIPALE
# ============================================================================

def main():
    # Initialisation
    init_session_state()
    load_data()
    
    # Header
    render_header()
    
    # Navigation par onglets
    tab_dashboard, tab_planning, tab_stats, tab_evolution = st.tabs([
        "🏠 Tableau de bord",
        "📋 Planification",
        "📊 Statistiques",
        "📈 Évolution"
    ])
    
    with tab_dashboard:
        page_dashboard()
    
    with tab_planning:
        page_planning()
    
    with tab_stats:
        page_statistiques()
    
    with tab_evolution:
        page_evolution()
    
    # Footer
    st.markdown("---")
    col1, col2, col3 = st.columns([2, 1, 2])
    with col2:
        st.caption(f"🕐 {datetime.now().strftime('%d/%m/%Y %H:%M')}")

if __name__ == "__main__":
    main()
