"""
app.py – Interface Streamlit pour le pipeline OCR SR Collectivités
"""

import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
from pathlib import Path

from pipeline_ocr import process_pdf, process_all

# ─────────────────────────────────────────────────────────────────────
# Config page
# ─────────────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="OCR Satisfaction – SR Collectivités",
    page_icon="🍽️",
    layout="wide",
)

SCORE_LABELS = {4: "😊 Très satisfait", 3: "🙂 Satisfait",
                2: "😐 Peu satisfait",  1: "😟 Insatisfait"}

JOUR_ORDER = ["LUNDI", "MARDI", "MERCREDI", "JEUDI", "VENDREDI"]

# ─────────────────────────────────────────────────────────────────────
# Helpers
# ─────────────────────────────────────────────────────────────────────

def score_color(val):
    """Coloration conditionnelle du texte (pas du fond)."""
    if pd.isna(val):
        return ""
    if val >= 3.5:
        return "color: #2e7d32"   # vert
    if val >= 2.5:
        return "color: #f9a825"   # jaune/orange
    return "color: #c62828"       # rouge


def build_pivot(df: pd.DataFrame) -> pd.DataFrame:
    """
    Construit un tableau croisé :
    colonnes = [jour, plat] × lignes = [fichier]
    avec scores Qté et Qual.
    """
    rows = []
    for _, r in df.iterrows():
        rows.append({
            "Fichier":  r["fichier"],
            "Jour":     r["jour"],
            "Plat":     r["plat"],
            "Qté (score)":  r["score_qte"],
            "Qual (score)": r["score_qual"],
            "Qté (label)":  SCORE_LABELS.get(r["score_qte"], "—"),
            "Qual (label)": SCORE_LABELS.get(r["score_qual"], "—"),
        })
    return pd.DataFrame(rows)


def show_results(df: pd.DataFrame) -> None:
    if df.empty:
        st.warning("Aucun résultat.")
        return

    df_display = build_pivot(df)
    conf_col   = "conf_min" in df.columns

    # ── Onglets ──────────────────────────────────────────────────────
    tabs = st.tabs(["📋 Résultats par plat", "📊 Moyennes", "📈 Graphique",
                    "⚠️ À vérifier", "⬇️ Export"])

    # ── Onglet 1 : résultats détaillés ────────────────────────────────
    with tabs[0]:
        st.subheader("Résultats détaillés – tous les plats")

        # Filtre jour
        jours_dispo = [j for j in JOUR_ORDER if j in df["jour"].unique()]
        sel_jours   = st.multiselect("Filtrer par jour :", jours_dispo,
                                     default=jours_dispo, key="filter_jour")
        df_f = df_display[df_display["Jour"].isin(sel_jours)]

        # Affichage coloré (Styler.map remplace applymap en pandas 2.2+)
        styled = (
            df_f[["Fichier", "Jour", "Plat",
                  "Qté (score)", "Qual (score)",
                  "Qté (label)", "Qual (label)"]]
            .style
            .map(score_color, subset=["Qté (score)", "Qual (score)"])
            .format({"Qté (score)": "{:.0f}", "Qual (score)": "{:.0f}"})
        )
        st.dataframe(styled, use_container_width=True, height=600)

    # ── Onglet 2 : moyennes ───────────────────────────────────────────
    with tabs[1]:
        st.subheader("Moyennes par fichier et par jour")

        stats = (
            df.groupby(["fichier", "jour"])[["score_qte", "score_qual"]]
            .mean()
            .round(2)
            .reset_index()
            .rename(columns={"fichier": "Fichier", "jour": "Jour",
                              "score_qte": "Moy. Qté", "score_qual": "Moy. Qual"})
        )
        # Trier par ordre calendaire
        stats["Jour"] = pd.Categorical(stats["Jour"], categories=JOUR_ORDER,
                                        ordered=True)
        stats = stats.sort_values(["Fichier", "Jour"])

        styled2 = (
            stats.style
            .map(score_color, subset=["Moy. Qté", "Moy. Qual"])
            .format({"Moy. Qté": "{:.2f}", "Moy. Qual": "{:.2f}"})
        )
        st.dataframe(styled2, use_container_width=True)

        # Moyenne globale
        st.markdown("---")
        c1, c2 = st.columns(2)
        c1.metric("Moyenne globale – Quantités livrées",
                  f"{df['score_qte'].mean():.2f} / 4")
        c2.metric("Moyenne globale – Qualité des plats",
                  f"{df['score_qual'].mean():.2f} / 4")

    # ── Onglet 3 : graphique ──────────────────────────────────────────
    with tabs[2]:
        st.subheader("Scores par plat")

        df_chart = df.copy()
        df_chart["Jour"] = pd.Categorical(df_chart["jour"],
                                           categories=JOUR_ORDER, ordered=True)
        df_chart = df_chart.sort_values(["Jour", "plat"]).reset_index(drop=True)
        labels = (df_chart["jour"] + " – " + df_chart["plat"]).tolist()
        n = len(labels)

        fig, ax = plt.subplots(figsize=(9, max(5, n * 0.45)))
        y      = range(n)
        height = 0.35
        ax.barh([i + height/2 for i in y], df_chart["score_qte"],
                height, color="#E8703A", label="Quantités livrées")
        ax.barh([i - height/2 for i in y], df_chart["score_qual"],
                height, color="#455A64", label="Qualité des plats")
        ax.set_yticks(list(y))
        ax.set_yticklabels(labels, fontsize=8)
        ax.set_xlim(0, 4.5)
        ax.set_xlabel("Score (1–4)")
        ax.axvline(x=3.5, color="green", linestyle="--", alpha=0.4, linewidth=0.8)
        ax.legend(loc="lower right")
        ax.invert_yaxis()
        plt.tight_layout()
        st.pyplot(fig)
        plt.close(fig)

    # ── Onglet 4 : confiance faible ───────────────────────────────────
    with tabs[3]:
        if conf_col:
            low = df[df["conf_min"] < 1.3].copy()
            if low.empty:
                st.success("Aucune ligne à faible confiance ✅")
            else:
                st.warning(
                    f"**{len(low)} ligne(s)** avec une confiance de détection "
                    f"< 1.3 (smiley entouré difficile à distinguer du bruit). "
                    f"Comparez avec le PDF original."
                )
                st.dataframe(
                    low[["fichier", "jour", "plat",
                          "score_qte", "score_qual", "conf_min"]],
                    use_container_width=True,
                )
        else:
            st.info("Données de confiance non disponibles.")

    # ── Onglet 5 : export ─────────────────────────────────────────────
    with tabs[4]:
        df_export = df.drop(columns=["conf_min"], errors="ignore")
        csv = df_export.to_csv(index=False, encoding="utf-8-sig").encode("utf-8-sig")
        st.download_button(
            label="⬇️ Télécharger le CSV complet",
            data=csv,
            file_name="resultats_satisfaction.csv",
            mime="text/csv",
        )

        # Aperçu
        st.dataframe(df_export.head(10), use_container_width=True)


# ─────────────────────────────────────────────────────────────────────
# Interface principale
# ─────────────────────────────────────────────────────────────────────

st.title("🍽️ Pipeline OCR – Fiches de satisfaction SR Collectivités")
st.caption("Lecture automatique des smileys entourés à la main • Semaine du menu")

st.markdown(
    "Indiquez le chemin d'un **fichier PDF** ou d'un **dossier** "
    "(tous les PDF seront traités ensemble)."
)

col_path, col_btn = st.columns([4, 1])
with col_path:
    path_str = st.text_input(
        "Dossier ou fichier PDF :",
        value="",
        placeholder="Ex : C:\\Travail\\RCS\\RSC_pdf  ou  C:\\...\\fiche.pdf",
        label_visibility="visible",
    )
with col_btn:
    st.markdown("<br>", unsafe_allow_html=True)   # alignement vertical
    run = st.button("▶ Lancer", use_container_width=True, type="primary")

if run:
    path_str = path_str.strip()
    if not path_str:
        st.error("Veuillez saisir un chemin.")
        st.stop()

    p = Path(path_str)
    if not p.exists():
        st.error(f"Chemin introuvable : `{path_str}`")
        st.stop()

    if p.is_file():
        if p.suffix.lower() != ".pdf":
            st.error("Le fichier doit être un PDF.")
            st.stop()
        with st.spinner("Analyse du PDF en cours…"):
            df = process_pdf(str(p), use_known_dishes=True, verbose=False)
        st.success(f"✅ Traitement terminé – **{len(df)} plats** analysés")

    else:  # dossier
        pdf_list = sorted(p.glob("*.pdf"))
        if not pdf_list:
            st.warning("Aucun fichier PDF trouvé dans ce dossier.")
            st.stop()
        with st.spinner(f"Analyse de {len(pdf_list)} PDF…"):
            df = process_all(str(p), use_known_dishes=True)
        st.success(
            f"✅ Traitement terminé – "
            f"**{len(pdf_list)} fichier(s)**, **{len(df)} plats** analysés"
        )

    show_results(df)
