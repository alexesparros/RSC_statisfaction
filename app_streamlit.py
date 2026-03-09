import streamlit as st
import pandas as pd
from pathlib import Path

from pipeline_ocr import process_folder, process_pdf


def _show_results(df: pd.DataFrame) -> None:
    if df.empty:
        return
    st.subheader("Résultats détaillés")
    st.dataframe(df, use_container_width=True)
    st.subheader("Moyennes par fichier et par jour")
    stats = (
        df.groupby(["fichier", "jour"])[["score_qte", "score_qual"]]
        .mean()
        .round(2)
        .reset_index()
    )
    st.dataframe(stats, use_container_width=True)
    st.subheader("Télécharger les résultats")
    csv_bytes = df.to_csv(index=False, encoding="utf-8-sig").encode("utf-8-sig")
    st.download_button(
        label="Télécharger le CSV",
        data=csv_bytes,
        file_name="resultats_satisfaction_tous_pdf.csv",
        mime="text/csv",
    )


st.set_page_config(
    page_title="OCR Satisfaction SR Collectivités",
    layout="wide",
)

st.title("Pipeline OCR – Fiches de satisfaction SR Collectivités")
st.markdown(
    "Indiquez un **dossier** (tous les PDF du dossier seront traités) "
    "ou le chemin d’**un seul fichier PDF**."
)


default_folder = str(Path(".").resolve())
folder_path = st.text_input(
    "Dossier ou fichier PDF :",
    value=default_folder,
    help="Ex. C:\\MonDossier ou C:\\MonDossier\\fiche.pdf",
)


if st.button("Lancer le traitement"):
    p = Path(folder_path.strip())
    if not p.exists():
        st.error("Ce chemin n'existe pas.")
    elif p.is_file():
        if p.suffix.lower() != ".pdf":
            st.error("Le fichier indiqué n'est pas un PDF.")
        else:
            with st.spinner("Traitement du PDF en cours..."):
                df = process_pdf(str(p))
                df.insert(0, "fichier", p.name)
            st.success("Traitement terminé ✅")
            _show_results(df)
    elif p.is_dir():
        pdf_list = sorted(p.glob("*.pdf"))
        if not pdf_list:
            st.warning("Aucun fichier PDF trouvé dans ce dossier.")
        else:
            with st.spinner(f"Traitement de {len(pdf_list)} fichier(s) PDF..."):
                df = process_folder(str(p))
            st.success("Traitement terminé ✅")
            _show_results(df)
    else:
        st.error("Le chemin fourni n'est ni un dossier ni un fichier valide.")

