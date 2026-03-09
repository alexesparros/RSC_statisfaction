"""
pipeline_ocr.py – SR Collectivités · Pipeline OCR multi-site / multi-semaine
=============================================================================

DataFrame produit :
    fichier | site | semaine | periode | jour | plat | score_qte | score_qual
    | commentaire_brut | non_servi | conf_min

Convention de nommage des PDF :
    SITE_YYYY_WW.pdf   →  ex. VERNALIE_2026_03.pdf

Fichiers de menu (dossier menus/) :
    semaine_YYYY_WW.json
    {
        "semaine":  "2026_03",
        "periode":  "12 au 18 janvier 2026",
        "LUNDI":    ["Plat 1", "Plat 2", ...],
        ...
    }
    → "***" dans la liste = plat non servi (exclu des stats)

Dépendances :
    pip install opencv-python pytesseract pandas numpy pdf2image
    apt install tesseract-ocr tesseract-ocr-fra poppler-utils
"""

from __future__ import annotations
import re
import json
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
# CALIBRATION  (300 DPI – formulaire SR Collectivités)
# ═══════════════════════════════════════════════════════════════════════

ROW_CENTERS_Y = {
    "LUNDI":    [685,  753,  816,  1016, 1377],
    "JEUDI":    [685,  753,  816,  1016, 1377],
    "MARDI":    [1592, 1684, 1790, 1881, 1976],
    "VENDREDI": [1592, 1684, 1790, 1881, 1976],
    "MERCREDI": [2171, 2265, 2365, 2463, 2555],
}

# Centres X des 4 smileys [très satisfait → insatisfait] = [score 4 → 1]
SMILEY_X = {
    "left_qte":   [660,  755,  840,  920],
    "left_qual":  [1020, 1100, 1180, 1260],
    "right_qte":  [1700, 1790, 1880, 1960],
    "right_qual": [2060, 2145, 2225, 2320],
}

TEXT_X        = {"left": (5, 540), "right": (1245, 1730)}
# Zone commentaire manuscrit (y1, y2, x1, x2) en px
COMMENT_ZONE  = (2500, 3400, 1200, 2481)
RING_R_INNER  = 22
RING_R_OUTER  = 42
PLAT_NON_SERVI = "***"

JOURS = [
    ("LUNDI",    "left"),
    ("MARDI",    "left"),
    ("MERCREDI", "left"),
    ("JEUDI",    "right"),
    ("VENDREDI", "right"),
]


# ═══════════════════════════════════════════════════════════════════════
# MENUS
# ═══════════════════════════════════════════════════════════════════════

def load_menu(semaine: str, menus_dir: str | Path = "menus") -> dict | None:
    path = Path(menus_dir) / f"semaine_{semaine}.json"
    if not path.exists():
        return None
    with open(path, encoding="utf-8") as f:
        return json.load(f)


def parse_filename(pdf_path: str) -> dict:
    """
    Extrait site et semaine du nom de fichier.
    Formats acceptés :
      SITE_YYYY_WW.pdf          → site='SITE', semaine='YYYY_WW'
      SITE_YYYYMMDD_YYYYMMDD.pdf → site='SITE', semaine ISO calculée
    """
    stem  = Path(pdf_path).stem
    parts = stem.split("_")

    if len(parts) >= 3 and parts[-2].isdigit() and parts[-1].isdigit():
        site    = "_".join(parts[:-2])
        semaine = f"{parts[-2]}_{parts[-1].zfill(2)}"
        return {"site": site, "semaine": semaine}

    if len(parts) >= 3 and len(parts[-2]) == 8 and parts[-2].isdigit():
        import datetime
        try:
            d   = datetime.date(int(parts[-2][:4]),
                                int(parts[-2][4:6]),
                                int(parts[-2][6:]))
            iso = d.isocalendar()
            return {"site": "_".join(parts[:-2]),
                    "semaine": f"{iso[0]}_{str(iso[1]).zfill(2)}"}
        except ValueError:
            pass

    return {"site": stem, "semaine": "inconnue"}


# ═══════════════════════════════════════════════════════════════════════
# IMAGE
# ═══════════════════════════════════════════════════════════════════════

def _load_image(pdf_path: str) -> tuple[np.ndarray, np.ndarray]:
    kwargs = {"dpi": 300}
    if POPPLER_PATH:
        kwargs["poppler_path"] = POPPLER_PATH
    pages   = convert_from_path(pdf_path, **kwargs)
    img_bgr = cv2.cvtColor(np.array(pages[0]), cv2.COLOR_RGB2BGR)
    gray    = cv2.cvtColor(img_bgr, cv2.COLOR_BGR2GRAY)
    _, bw   = cv2.threshold(gray, 0, 255,
                            cv2.THRESH_BINARY_INV + cv2.THRESH_OTSU)
    return img_bgr, bw


# ═══════════════════════════════════════════════════════════════════════
# SCORES
# ═══════════════════════════════════════════════════════════════════════

def _ring_ink_score(bw: np.ndarray, cy: int, xs: list[int],
                    ri: int = RING_R_INNER,
                    ro: int = RING_R_OUTER) -> tuple[int, float]:
    inks = []
    for cx in xs:
        y1 = max(0, cy-ro); y2 = min(bw.shape[0], cy+ro)
        x1 = max(0, cx-ro); x2 = min(bw.shape[1], cx+ro)
        roi  = bw[y1:y2, x1:x2]; h, w = roi.shape
        mask = np.zeros((h, w), np.uint8)
        cv2.circle(mask, (cx-x1, cy-y1), ro, 255, -1)
        cv2.circle(mask, (cx-x1, cy-y1), ri, 0,   -1)
        inks.append(cv2.countNonZero(cv2.bitwise_and(roi, mask)))
    si   = sorted(inks, reverse=True)
    return 4 - int(np.argmax(inks)), round(si[0] / max(si[1], 1), 2)


# ═══════════════════════════════════════════════════════════════════════
# OCR
# ═══════════════════════════════════════════════════════════════════════

def _tesseract(bw: np.ndarray, psm: int = 6) -> str:
    cfg = f"--psm {psm} --oem 3"
    try:
        return pytesseract.image_to_string(bw, lang="fra", config=cfg)
    except pytesseract.pytesseract.TesseractError:
        return pytesseract.image_to_string(bw, lang="eng", config=cfg)


def _ocr_confidence(text: str) -> float:
    if not text or len(text) < 2: return 0.0
    s = text.lstrip()
    if s and not s[0].isalpha() and not s[0].isdigit(): return 0.1
    alpha = sum(c.isalpha() for c in text)
    r     = alpha / len(text)
    words = re.findall(r"[a-zA-ZÀ-ÿ]+", text)
    lw    = [w for w in words if len(w) >= 3]
    caps  = len(words) >= 2 and all(w.isupper() and len(w) <= 4 for w in words)
    sc = r
    if caps:  sc *= 0.25
    if not lw: sc *= 0.4
    if r < 0.5: sc *= 0.3
    return round(min(sc, 1.0), 3)


_OCR_THRESH = 0.55


def _ocr_dish(img: np.ndarray, cy: int, x0: int, x1: int,
              half_h: int = 55) -> str:
    y1 = max(0, cy-half_h); y2 = min(img.shape[0], cy+half_h)
    crop = img[y1:y2, x0:x1]
    if crop.size == 0: return ""
    gray = cv2.cvtColor(crop, cv2.COLOR_BGR2GRAY)
    gray = cv2.equalizeHist(gray)
    _, bw = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
    return " ".join(_tesseract(bw, 6).split())


def _ocr_comment(img: np.ndarray) -> str:
    """OCR brut de la zone commentaire manuscrit."""
    y1, y2, x1, x2 = COMMENT_ZONE
    crop = img[y1:y2, x1:x2]
    if crop.size == 0: return ""
    gray   = cv2.cvtColor(crop, cv2.COLOR_BGR2GRAY)
    big    = cv2.resize(gray, (gray.shape[1]*2, gray.shape[0]*2),
                        interpolation=cv2.INTER_CUBIC)
    dnoise = cv2.fastNlMeansDenoising(big, h=10)
    _, bw  = cv2.threshold(dnoise, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
    raw    = _tesseract(bw, psm=4)
    text   = re.sub(r"commentaires?\s*:", "", raw, flags=re.IGNORECASE)
    lines  = [l.strip() for l in text.splitlines() if len(l.strip()) > 4]
    return " | ".join(lines)


# ═══════════════════════════════════════════════════════════════════════
# PIPELINE
# ═══════════════════════════════════════════════════════════════════════

def process_pdf(pdf_path: str,
                menus_dir: str | Path = "menus",
                verbose: bool = True) -> pd.DataFrame:
    """
    Traite un PDF de fiche de satisfaction.

    Paramètres
    ----------
    pdf_path  : chemin vers le PDF  (ex. 'pdf/VERNALIE_2026_03.pdf')
    menus_dir : dossier contenant les JSON de menus hebdomadaires
    verbose   : affiche le détail en console
    """
    meta    = parse_filename(pdf_path)
    site    = meta["site"]
    semaine = meta["semaine"]
    menu    = load_menu(semaine, menus_dir)
    periode = menu.get("periode", "") if menu else ""

    if verbose:
        print(f"\n{'─'*72}")
        print(f"  Fichier : {Path(pdf_path).name}")
        print(f"  Site={site}  |  Semaine={semaine}  |  Période={periode}")
        if menu is None:
            print(f"  ⚠️  menus/semaine_{semaine}.json introuvable → OCR seul")

    img, bw = _load_image(pdf_path)
    commentaire = _ocr_comment(img)

    if verbose:
        print(f"  💬 Commentaire brut : {commentaire[:100] or '(vide)'}")
        print(f"\n  {'Jour':<10} {'Plat':<38} {'Qté':>4} {'Qual':>5} {'Conf':>5} {'NS':>3}")
        print(f"  {'─'*70}")

    records = []

    for jour, side in JOURS:
        qte_xs = SMILEY_X[f"{side}_qte"]
        qual_xs = SMILEY_X[f"{side}_qual"]
        x0, x1 = TEXT_X[side]
        known  = (menu or {}).get(jour, [])

        for idx, cy in enumerate(ROW_CENTERS_Y[jour]):

            # ── Nom du plat ──────────────────────────────────────────
            if idx < len(known):
                plat = known[idx]
            else:
                raw  = _ocr_dish(img, cy, x0, x1)
                plat = raw if _ocr_confidence(raw) >= _OCR_THRESH else "—"

            # ── Non servi ? ──────────────────────────────────────────
            non_servi = plat.strip() == PLAT_NON_SERVI

            # ── Scores (sautés si non servi) ─────────────────────────
            if non_servi:
                score_qte = score_qual = conf_min = None
            else:
                sq,  cq  = _ring_ink_score(bw, cy, qte_xs)
                squ, cqu = _ring_ink_score(bw, cy, qual_xs)
                score_qte, score_qual = sq, squ
                conf_min = round(min(cq, cqu), 2)

            if verbose:
                ns  = "NS" if non_servi else ""
                cf  = f"{conf_min:.2f}" if conf_min is not None else " — "
                sq_ = str(score_qte)  if score_qte  is not None else "—"
                su_ = str(score_qual) if score_qual is not None else "—"
                print(f"  {jour:<10} {plat[:36]:<38} {sq_:>4} {su_:>5} {cf:>5} {ns:>3}")

            records.append({
                "fichier":          Path(pdf_path).name,
                "site":             site,
                "semaine":          semaine,
                "periode":          periode,
                "jour":             jour,
                "plat":             plat,
                "score_qte":        score_qte,
                "score_qual":       score_qual,
                "commentaire_brut": commentaire,
                "non_servi":        non_servi,
                "conf_min":         conf_min,
            })

    return pd.DataFrame(records)


def process_all(path: str,
                menus_dir: str | Path = "menus",
                verbose: bool = False) -> pd.DataFrame:
    """Traite un PDF ou tous les PDF d'un dossier."""
    p     = Path(path)
    files = list(p.glob("*.pdf")) if p.is_dir() else [p]
    if not files:
        raise FileNotFoundError(f"Aucun PDF trouvé : {path}")
    return pd.concat(
        [process_pdf(str(f), menus_dir, verbose) for f in sorted(files)],
        ignore_index=True,
    )


# ═══════════════════════════════════════════════════════════════════════
# FONCTIONS STATS
# ═══════════════════════════════════════════════════════════════════════

def stats_par_jour(df: pd.DataFrame) -> pd.DataFrame:
    """Moyennes par site/semaine/jour – plats non servis exclus."""
    return (df[~df["non_servi"]]
            .groupby(["site", "semaine", "jour"])[["score_qte", "score_qual"]]
            .agg(["mean", "min", "max", "count"])
            .round(2))


def stats_par_plat(df: pd.DataFrame) -> pd.DataFrame:
    """Classement des plats par score moyen – hors non servis."""
    return (df[~df["non_servi"]]
            .groupby("plat")[["score_qte", "score_qual"]]
            .mean().round(2)
            .sort_values("score_qual"))


def stats_par_site(df: pd.DataFrame) -> pd.DataFrame:
    """Comparaison des sites."""
    return (df[~df["non_servi"]]
            .groupby("site")[["score_qte", "score_qual"]]
            .mean().round(2))


# ═══════════════════════════════════════════════════════════════════════
# RUN
# ═══════════════════════════════════════════════════════════════════════

if __name__ == "__main__":
    import sys
    pdf_path  = sys.argv[1] if len(sys.argv) > 1 else "RSC_statisfaction.pdf"
    menus_dir = sys.argv[2] if len(sys.argv) > 2 else "menus"

    df = process_all(pdf_path, menus_dir, verbose=True)

    df_ok = df[~df["non_servi"]]
    print("\n\n══ RÉSULTATS ═══════════════════════════════════════════════")
    print(df_ok[["site","semaine","jour","plat","score_qte","score_qual"]]
          .to_string(index=False))

    print("\n\n══ MOYENNES PAR JOUR ════════════════════════════════════")
    print(stats_par_jour(df).to_string())

    ns = df[df["non_servi"]]
    if not ns.empty:
        print(f"\nℹ️  {len(ns)} plat(s) non servis (exclus des stats) :")
        print(ns[["site","jour","plat"]].to_string(index=False))

    out = "resultats_satisfaction.csv"
    df.drop(columns=["conf_min"], errors="ignore").to_csv(
        out, index=False, encoding="utf-8-sig")
    print(f"\n✅ {out}")
