"""Normalisation des textes pour la recherche."""
import re
import unicodedata

MOTS_VIDES = set("""a au aux avec ce ces dans de des du elle en et eux il ils je la le les leur lui ma mais me même mes moi mon ne nos notre nous on ou par pas pour qu que qui sa se ses son sur ta te tes toi ton tu un une vos votre vous y d l c j m n s t""".split())


def normaliser(texte: str) -> str:
    """Met en minuscules et retire les accents et la ponctuation."""
    texte = unicodedata.normalize("NFD", texte.lower())
    texte = "".join(c for c in texte if unicodedata.category(c) != "Mn")
    return re.sub(r"[^a-z0-9]+", " ", texte).strip()


def nettoyer(texte: str, retirer_vides: bool = True) -> list[str]:
    """Transforme un texte en liste de mots normalisés."""
    mots = normaliser(texte).split()
    return [mot for mot in mots if mot and (not retirer_vides or mot not in MOTS_VIDES)]


def charger_mots_vides() -> set[str]:
    """Charge les mots vides personnalisés si le fichier existe."""
    try:
        with open("mots_vides.txt", encoding="utf-8") as fichier:
            return MOTS_VIDES | {normaliser(ligne) for ligne in fichier if ligne.strip()}
    except OSError:
        return MOTS_VIDES
