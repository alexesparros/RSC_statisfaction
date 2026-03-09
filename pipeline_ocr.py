"""
pipeline_ocr.py – SR Collectivités, Fiche de satisfaction
==========================================================
Produit un DataFrame : fichier | jour | plat | score_qte | score_qual

Scores : 4=Très satisfait | 3=Satisfait | 2=Peu satisfait | 1=Insatisfait

Dépendances :
    pip install opencv-python pytesseract pandas numpy pdf2image
    apt install tesseract-ocr tesseract-ocr-fra poppler-utils
"""

import cv2
import pytesseract
import pandas as pd
import numpy as np
from pdf2image import convert_from_path
from pathlib import Path


# ─── Config Windows (Poppler + Tesseract) ───────────────────────────────────
pytesseract.pytesseract.tesseract_cmd = r"C:\Program Files\Tesseract-OCR\tesseract.exe"
POPPLER_PATH: str | None = r"C:\Users\Utilisateur\Downloads\Release-25.12.0-0 (1)\poppler-25.12.0\Library\bin"


# ═══════════════════════════════════════════════════════════════════════
# CALIBRATION  (300 DPI – image 3509 × 2481 px)
# ═══════════════════════════════════════════════════════════════════════

# Centres Y (px) de chaque rangée de plat
# LUNDI / JEUDI partagent les mêmes Y (colonnes côte-à-côte dans le PDF)
# MARDI / VENDREDI idem
ROW_CENTERS_Y = {
    "LUNDI":    [685,  753,  816,  1016, 1377],
    "JEUDI":    [685,  753,  816,  1016, 1377],
    "MARDI":    [1592, 1684, 1790, 1881, 1976],
    "VENDREDI": [1592, 1684, 1790, 1881, 1976],
    "MERCREDI": [2171, 2265, 2365, 2463, 2555],
}

# Centres X des 4 smileys par colonne de score
# Ordre gauche→droite = très satisfait (4) → insatisfait (1)
SMILEY_X = {
    "left_qte":   [660,  755,  840,  920],
    "left_qual":  [1020, 1100, 1180, 1260],
    "right_qte":  [1700, 1790, 1880, 1960],
    "right_qual": [2060, 2145, 2225, 2320],
}

# Zone texte (x_start, x_end) pour l'OCR du nom du plat
TEXT_X = {
    "left":  (5,   540),
    "right": (1245, 1730),
}

# Rayons de l'anneau ring-ink
RING_R_INNER = 22   # intérieur du smiley imprimé (~20 px)
RING_R_OUTER = 42   # limite du cercle dessiné à la main (~38-42 px)

# Noms de plats (fallback si l'OCR échoue sur un scan dégradé)
KNOWN_DISHES = {
    "LUNDI":    ["Macédoine de légumes",
                 "Rôti de porc au jus",
                 "Purée de pomme de terre",
                 "Camembert à la coupe",
                 "Clémentine Bio"],
    "MARDI":    ["Salade de perles",
                 "Poisson pané",
                 "Haricot beurre",
                 "Saint Môret Bio",
                 "Compote de pêche"],
    "MERCREDI": ["Salade verte aux croûtons",
                 "Saucisse de toulouse",
                 "Petits pois Bio",
                 "Crème dessert à la vanille",
                 "Salade de fruit"],
    "JEUDI":    ["Soupe de légumes BIO",
                 "Hachis parmentier égrené nature Bio",
                 "***",
                 "Gouda à la coupe",
                 "Pomme du Tarn"],
    "VENDREDI": ["Carottes Bio râpées",
                 "Boulette d'agneau sauce provençale",
                 "Riz Bio",
                 "Liégeois au chocolat",
                 "Madeleine Bio"],
}

JOURS = [
    ("LUNDI",    "left"),
    ("MARDI",    "left"),
    ("MERCREDI", "left"),
    ("JEUDI",    "right"),
    ("VENDREDI", "right"),
]


# ───────────────────────────────────────────────────────────────────────
# 1. Chargement image
# ───────────────────────────────────────────────────────────────────────

def _load_image(pdf_path: str) -> tuple[np.ndarray, np.ndarray]:
    """
    Retourne (img_bgr, bw_inversée).
    pdf2image → RGB ; OpenCV attend BGR → conversion obligatoire.
    """
    kwargs = {"dpi": 300}
    if POPPLER_PATH:
        kwargs["poppler_path"] = POPPLER_PATH
    pages   = convert_from_path(pdf_path, **kwargs)
    img_bgr = cv2.cvtColor(np.array(pages[0]), cv2.COLOR_RGB2BGR)
    gray    = cv2.cvtColor(img_bgr, cv2.COLOR_BGR2GRAY)
    _, bw   = cv2.threshold(gray, 0, 255,
                            cv2.THRESH_BINARY_INV + cv2.THRESH_OTSU)
    return img_bgr, bw


# ───────────────────────────────────────────────────────────────────────
# 2. Score par cellule – ring-ink
# ───────────────────────────────────────────────────────────────────────

def _ring_ink_score(bw: np.ndarray,
                    cy: int,
                    smiley_xs: list[int],
                    r_inner: int = RING_R_INNER,
                    r_outer: int = RING_R_OUTER) -> tuple[int, float]:
    """
    Compte les pixels noirs dans l'anneau [r_inner, r_outer] autour de
    chaque smiley. Le smiley avec le plus d'encre est celui entouré à la main.

    Retourne (score 1-4, confidence = ratio max/2nd_max).
    """
    inks = []
    for cx in smiley_xs:
        y1 = max(0, cy - r_outer); y2 = min(bw.shape[0], cy + r_outer)
        x1 = max(0, cx - r_outer); x2 = min(bw.shape[1], cx + r_outer)
        roi  = bw[y1:y2, x1:x2]
        h, w = roi.shape
        mask = np.zeros((h, w), np.uint8)
        cv2.circle(mask, (cx - x1, cy - y1), r_outer, 255, -1)
        cv2.circle(mask, (cx - x1, cy - y1), r_inner, 0,   -1)
        inks.append(cv2.countNonZero(cv2.bitwise_and(roi, mask)))

    sorted_inks = sorted(inks, reverse=True)
    confidence  = sorted_inks[0] / max(sorted_inks[1], 1)
    score       = 4 - int(np.argmax(inks))   # position 0 → score 4
    return score, round(confidence, 2)


# ───────────────────────────────────────────────────────────────────────
# 3. OCR nom du plat
# ───────────────────────────────────────────────────────────────────────

def _ocr_dish(img_bgr: np.ndarray,
              cy: int, x_start: int, x_end: int,
              half_h: int = 55) -> str:
    """
    Recadre la zone cy ± half_h (hauteur réelle d'une ligne)
    et applique Tesseract.
    """
    y1 = max(0, cy - half_h); y2 = min(img_bgr.shape[0], cy + half_h)
    crop = img_bgr[y1:y2, x_start:x_end]
    if crop.size == 0:
        return ""

    gray = cv2.cvtColor(crop, cv2.COLOR_BGR2GRAY)
    gray = cv2.equalizeHist(gray)
    _, bw = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)

    cfg = "--psm 6 --oem 3"
    try:
        text = pytesseract.image_to_string(bw, lang="fra", config=cfg)
    except pytesseract.pytesseract.TesseractError:
        text = pytesseract.image_to_string(bw, lang="eng", config=cfg)

    return " ".join(text.split())


# ───────────────────────────────────────────────────────────────────────
# 4. Traitement d'un seul PDF
# ───────────────────────────────────────────────────────────────────────

def process_pdf(pdf_path: str,
                use_known_dishes: bool = True,
                verbose: bool = True) -> pd.DataFrame:
    """
    Traite un PDF scanné et retourne le DataFrame :

        fichier | jour | plat | score_qte | score_qual

    Paramètres
    ----------
    use_known_dishes : True  → utilise KNOWN_DISHES si l'OCR retourne < 5 car.
    verbose          : True  → affiche les résultats ligne par ligne en console
    """
    img, bw = _load_image(pdf_path)
    fname   = Path(pdf_path).name
    records = []

    if verbose:
        print(f"\n{'─'*70}")
        print(f"  {fname}  ({img.shape[0]}×{img.shape[1]} px)")
        print(f"  {'Jour':<10} {'Plat':<40} {'Qté':>4} {'Qual':>5} {'Conf':>5}")
        print(f"  {'─'*65}")

    for jour, side in JOURS:
        qte_xs  = SMILEY_X[f"{side}_qte"]
        qual_xs = SMILEY_X[f"{side}_qual"]
        x0, x1  = TEXT_X[side]

        for idx, cy in enumerate(ROW_CENTERS_Y[jour]):

            # ── Scores ─────────────────────────────────────────────────
            score_qte,  conf_q  = _ring_ink_score(bw, cy, qte_xs)
            score_qual, conf_qu = _ring_ink_score(bw, cy, qual_xs)
            conf_min            = round(min(conf_q, conf_qu), 2)

            # ── Nom du plat ────────────────────────────────────────────
            plat = _ocr_dish(img, cy, x0, x1)
            if use_known_dishes:
                known = KNOWN_DISHES.get(jour, [])
                if idx < len(known) and len(plat) < 5:
                    plat = known[idx]

            if verbose:
                flag = " ⚠" if conf_min < 1.3 else ""
                print(f"  {jour:<10} {plat[:38]:<40} {score_qte:>4}"
                      f" {score_qual:>5} {conf_min:>5}{flag}")

            records.append({
                "fichier":    fname,
                "jour":       jour,
                "plat":       plat,
                "score_qte":  score_qte,
                "score_qual": score_qual,
                "conf_min":   conf_min,
            })

    return pd.DataFrame(records)


# ───────────────────────────────────────────────────────────────────────
# 5. Traitement multi-fichiers
# ───────────────────────────────────────────────────────────────────────

def process_all(path: str,
                use_known_dishes: bool = True) -> pd.DataFrame:
    """
    Accepte un fichier PDF ou un dossier.
    Retourne un DataFrame combiné (tous les PDF).
    """
    p     = Path(path)
    files = list(p.glob("*.pdf")) if p.is_dir() else [p]

    if not files:
        raise FileNotFoundError(f"Aucun PDF trouvé dans : {path}")

    return pd.concat(
        [process_pdf(str(f), use_known_dishes, verbose=False) for f in files],
        ignore_index=True,
    )


# ───────────────────────────────────────────────────────────────────────
# RUN (test direct)
# ───────────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    import sys
    path = sys.argv[1] if len(sys.argv) > 1 else "RSC_statisfaction.pdf"

    df = process_all(path, use_known_dishes=True)
    df_out = df.drop(columns=["conf_min"])

    pd.set_option("display.max_rows", 50)
    pd.set_option("display.width", 100)
    pd.set_option("display.max_colwidth", 40)
    print(df_out.to_string(index=False))

    print("\nMoyennes par jour :")
    print(df_out.groupby(["fichier","jour"])[["score_qte","score_qual"]]
               .mean().round(2).to_string())

    out = "resultats_satisfaction.csv"
    df_out.to_csv(out, index=False, encoding="utf-8-sig")
    print(f"\n✅ {out}")

    low = df[df["conf_min"] < 1.3]
    if not low.empty:
        print(f"\n⚠️ {len(low)} ligne(s) à vérifier (confiance faible) :")
        print(low[["jour","plat","score_qte","score_qual","conf_min"]]
              .to_string(index=False))
