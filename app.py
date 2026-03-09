"""
app.py – Interface Streamlit · Pipeline OCR SR Collectivités
Multi-site | Multi-semaine | Gestion des menus JSON
"""

import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import json
from pathlib import Path

from pipeline_ocr import (
    process_pdf,
    process_all,
    stats_par_jour,
    stats_par_plat,
    stats_par_site,
    load_menu,
    parse_filename,
)

# ─────────────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="OCR Satisfaction – SR Collectivités",
    page_icon="🍽️",
    layout="wide",
)

SCORE_LABELS = {
    4: "😊 Très satisfait",
    3: "🙂 Satisfait",
    2: "😐 Peu satisfait",
    1: "😟 Insatisfait",
}
JOUR_ORDER = ["LUNDI", "MARDI", "MERCREDI", "JEUDI", "VENDREDI"]
ORANGE = "#E8703A"
SLATE = "#455A64"


def score_color(val):
    if pd.isna(val):
        return ""
    if val >= 3.5:
        return "background-color:#c8e6c9"
    if val >= 2.5:
        return "background-color:#fff9c4"
    return "background-color:#ffcdd2"


def _ask_folder() -> str | None:
    """Ouvre le sélecteur de dossiers Windows et retourne le chemin choisi."""
    try:
        import tkinter as tk
        from tkinter import filedialog
        root = tk.Tk()
        root.wm_attributes("-topmost", 1)
        root.withdraw()
        path = filedialog.askdirectory(title="Choisir un dossier (PDF ou contenant des PDF)")
        root.destroy()
        return path if path else None
    except Exception:
        return None


# ─────────────────────────────────────────────────────────────────────
# SIDEBAR – Gestion des menus JSON
# ─────────────────────────────────────────────────────────────────────

with st.sidebar:
    st.header("📋 Menus hebdomadaires")
    st.caption("Un fichier JSON par semaine de menu")

    menus_dir = st.text_input(
        "Dossier menus/",
        value="menus",
        help="Dossier contenant les fichiers semaine_YYYY_WW.json",
    )

    menus_path = Path(menus_dir)
    menus_path.mkdir(parents=True, exist_ok=True)

    existing = sorted(menus_path.glob("semaine_*.json"))
    if existing:
        st.success(f"{len(existing)} menu(s) configuré(s)")
        with st.expander("Menus disponibles"):
            for m in existing:
                st.code(m.name)
    else:
        st.warning("Aucun menu configuré")

    st.markdown("---")
    st.subheader("➕ Ajouter / modifier un menu")

    with st.form("form_menu"):
        semaine_in = st.text_input("Semaine (YYYY_WW)", placeholder="2026_03")
        periode_in = st.text_input("Période", placeholder="12 au 18 janvier 2026")

        st.caption(
            "5 plats par jour (un par ligne). Saisir `***` si plat non servi."
        )
        cols = st.columns(2)
        jours_left = ["LUNDI", "MARDI", "MERCREDI"]
        jours_right = ["JEUDI", "VENDREDI"]

        plats_input = {}
        for jour in jours_left:
            plats_input[jour] = cols[0].text_area(
                jour, height=120, placeholder="Plat 1\nPlat 2\nPlat 3\nPlat 4\nPlat 5"
            )
        for jour in jours_right:
            plats_input[jour] = cols[1].text_area(
                jour, height=120, placeholder="Plat 1\nPlat 2\nPlat 3\nPlat 4\nPlat 5"
            )

        if st.form_submit_button("💾 Enregistrer le menu"):
            if not semaine_in.strip():
                st.error("Saisissez la semaine (ex. 2026_03)")
            else:
                menu_data = {"semaine": semaine_in, "periode": periode_in}
                for jour, txt in plats_input.items():
                    menu_data[jour] = [
                        l.strip() for l in txt.splitlines() if l.strip()
                    ]
                out_path = menus_path / f"semaine_{semaine_in}.json"
                with open(out_path, "w", encoding="utf-8") as f:
                    json.dump(menu_data, f, ensure_ascii=False, indent=2)
                st.success(f"✅ Sauvegardé : {out_path.name}")
                st.rerun()


# ─────────────────────────────────────────────────────────────────────
# MAIN
# ─────────────────────────────────────────────────────────────────────

st.title("🍽️ Pipeline OCR – Fiches de satisfaction SR Collectivités")
st.caption("Multi-site · Multi-semaine · Lecture automatique des smileys")

st.markdown(
    "**Convention de nommage des PDF :** `SITE_YYYY_WW.pdf`  "
    "*(ex. `VERNALIE_2026_03.pdf`, `SAIX_2026_03.pdf`)*"
)

# Appliquer le dossier choisi via "Parcourir" avant de créer le widget (sinon Streamlit interdit de modifier path_input)
if "chosen_folder_path" in st.session_state:
    st.session_state["path_input"] = st.session_state.pop("chosen_folder_path")

col_path, col_parc, col_btn = st.columns([3, 1, 1])
with col_path:
    path_str = st.text_input(
        "Dossier ou fichier PDF :",
        placeholder="Ex : C:\\RCS\\pdf  ou  C:\\RCS\\pdf\\VERNALIE_2026_03.pdf",
        key="path_input",
    )
with col_parc:
    st.markdown("<br>", unsafe_allow_html=True)
    parcourir = st.button("📁 Parcourir…", use_container_width=True)
with col_btn:
    st.markdown("<br>", unsafe_allow_html=True)
    run = st.button("▶ Lancer", use_container_width=True, type="primary")

if parcourir:
    chosen = _ask_folder()
    if chosen:
        st.session_state["chosen_folder_path"] = chosen
        st.rerun()
    else:
        st.info("Aucun dossier sélectionné.")

if run:
    path_str = (path_str or "").strip()
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
        with st.spinner("Analyse en cours…"):
            df = process_pdf(str(p), menus_dir=menus_dir, verbose=False)
        st.success(f"✅ **{len(df)} plats** analysés")
    else:
        pdf_list = sorted(p.glob("*.pdf"))
        if not pdf_list:
            st.warning("Aucun PDF dans ce dossier.")
            st.stop()
        with st.spinner(f"Analyse de {len(pdf_list)} fichier(s)…"):
            df = process_all(str(p), menus_dir=menus_dir, verbose=False)
        st.success(
            f"✅ **{len(pdf_list)} fichier(s)** · **{len(df)} plats** analysés"
        )

    # ── Résumé rapide ────────────────────────────────────────────────
    df_ok = df[~df["non_servi"]]
    n_ns = df["non_servi"].sum()
    sites = df["site"].unique().tolist()
    semaines = df["semaine"].unique().tolist()

    m1, m2, m3, m4 = st.columns(4)
    m1.metric("Sites", len(sites))
    m2.metric("Semaines", len(semaines))
    m3.metric("Moy. Quantités", f"{df_ok['score_qte'].mean():.2f} / 4")
    m4.metric("Moy. Qualité", f"{df_ok['score_qual'].mean():.2f} / 4")

    if n_ns:
        st.info(
            f"ℹ️ {n_ns} plat(s) **non servis** (`***`) exclus des statistiques."
        )

    # ── Onglets ──────────────────────────────────────────────────────
    tabs = st.tabs(
        [
            "📋 Par plat",
            "📊 Par jour",
            "🏫 Par site",
            "📈 Graphique",
            "💬 Commentaires",
            "⚠️ À vérifier",
            "⬇️ Export",
        ]
    )

    # ── Tab 1 : résultats par plat ───────────────────────────────────
    with tabs[0]:
        st.subheader("Résultats détaillés")

        f_site = st.multiselect(
            "Site :", sorted(sites), default=sorted(sites)
        )
        f_jour = st.multiselect("Jour :", JOUR_ORDER, default=JOUR_ORDER)
        f_sem = st.multiselect(
            "Semaine :", sorted(semaines), default=sorted(semaines)
        )

        mask = (
            df["site"].isin(f_site)
            & df["jour"].isin(f_jour)
            & df["semaine"].isin(f_sem)
        )
        df_f = df[mask].copy()
        df_f["Qté label"] = df_f["score_qte"].map(SCORE_LABELS).fillna(
            "Non servi"
        )
        df_f["Qual label"] = df_f["score_qual"].map(SCORE_LABELS).fillna(
            "Non servi"
        )

        display_cols = [
            "fichier",
            "site",
            "semaine",
            "periode",
            "jour",
            "plat",
            "score_qte",
            "score_qual",
            "Qté label",
            "Qual label",
            "non_servi",
        ]

        styled = (
            df_f[display_cols]
            .rename(columns={"score_qte": "Qté", "score_qual": "Qual"})
            .style.map(score_color, subset=["Qté", "Qual"])
        )
        st.dataframe(styled, use_container_width=True, height=500)

    # ── Tab 2 : moyennes par jour ────────────────────────────────────
    with tabs[1]:
        st.subheader("Moyennes par site / semaine / jour")
        s = stats_par_jour(df).reset_index()
        s.columns = [
            " ".join(c).strip() if isinstance(c, tuple) else c
            for c in s.columns
        ]
        mean_cols = [c for c in s.columns if "mean" in str(c)]
        styled2 = s.style.map(score_color, subset=mean_cols)
        st.dataframe(styled2, use_container_width=True)

    # ── Tab 3 : comparaison sites ────────────────────────────────────
    with tabs[2]:
        st.subheader("Comparaison entre sites")
        ss = stats_par_site(df).reset_index()
        st.dataframe(
            ss.style.map(
                score_color, subset=["score_qte", "score_qual"]
            ),
            use_container_width=True,
        )

        st.markdown("---")
        st.subheader(
            "Classement des plats (par score qualité croissant)"
        )
        sp = stats_par_plat(df).reset_index()
        st.dataframe(
            sp.style.map(
                score_color, subset=["score_qte", "score_qual"]
            ),
            use_container_width=True,
        )

    # ── Tab 4 : graphique ────────────────────────────────────────────
    with tabs[3]:
        st.subheader("Scores par plat")

        g_site = st.selectbox("Site :", sorted(sites))
        g_sem = st.selectbox("Semaine :", sorted(semaines))
        df_g = df_ok[
            (df_ok["site"] == g_site) & (df_ok["semaine"] == g_sem)
        ]

        if df_g.empty:
            st.warning("Aucune donnée pour cette sélection.")
        else:
            df_g = df_g.copy()
            df_g["Jour"] = pd.Categorical(
                df_g["jour"], categories=JOUR_ORDER, ordered=True
            )
            df_g = df_g.sort_values(["Jour", "plat"]).reset_index(drop=True)
            labels = (df_g["jour"] + " – " + df_g["plat"]).tolist()
            n = len(labels)

            fig, ax = plt.subplots(figsize=(9, max(5, n * 0.48)))
            y, h = range(n), 0.35
            ax.barh(
                [i + h / 2 for i in y],
                df_g["score_qte"],
                h,
                color=ORANGE,
                label="Quantités livrées",
            )
            ax.barh(
                [i - h / 2 for i in y],
                df_g["score_qual"],
                h,
                color=SLATE,
                label="Qualité des plats",
            )
            ax.set_yticks(list(y))
            ax.set_yticklabels(labels, fontsize=8)
            ax.set_xlim(0, 4.5)
            ax.set_xlabel("Score (1–4)")
            ax.axvline(3.5, color="green", ls="--", alpha=0.4, lw=0.8)
            ax.legend(loc="lower right")
            ax.invert_yaxis()
            plt.tight_layout()
            st.pyplot(fig)
            plt.close(fig)

    # ── Tab 5 : commentaires ─────────────────────────────────────────
    with tabs[4]:
        st.subheader("Commentaires libres (OCR manuscrit)")
        st.caption(
            "⚠️ Qualité variable — écriture à la main sur scan."
        )
        comm_df = (
            df[
                [
                    "fichier",
                    "site",
                    "semaine",
                    "periode",
                    "commentaire_brut",
                ]
            ]
            .drop_duplicates()
            .rename(
                columns={"commentaire_brut": "Commentaire (brut OCR)"}
            )
        )
        for _, row in comm_df.iterrows():
            with st.expander(
                f"📄 {row['fichier']}  —  {row['site']} / {row['semaine']}"
            ):
                st.write(
                    row["Commentaire (brut OCR)"]
                    or "*(aucun commentaire détecté)*"
                )

    # ── Tab 6 : confiance faible ─────────────────────────────────────
    with tabs[5]:
        st.subheader("Lignes à vérifier (confiance faible < 1.3)")
        low = df[(df["conf_min"].notna()) & (df["conf_min"] < 1.3)]
        if low.empty:
            st.success("Aucune ligne à faible confiance ✅")
        else:
            st.warning(
                f"{len(low)} ligne(s) — comparez avec le PDF original."
            )
            st.dataframe(
                low[
                    [
                        "fichier",
                        "site",
                        "semaine",
                        "jour",
                        "plat",
                        "score_qte",
                        "score_qual",
                        "conf_min",
                    ]
                ],
                use_container_width=True,
            )

    # ── Tab 7 : export ────────────────────────────────────────────────
    with tabs[6]:
        df_exp = df.drop(columns=["conf_min"], errors="ignore")
        csv = df_exp.to_csv(
            index=False, encoding="utf-8-sig"
        ).encode("utf-8-sig")
        st.download_button(
            "⬇️ Télécharger le CSV complet",
            data=csv,
            file_name="resultats_satisfaction.csv",
            mime="text/csv",
        )
        st.dataframe(df_exp.head(10), use_container_width=True)
