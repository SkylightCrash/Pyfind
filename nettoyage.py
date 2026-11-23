"""Nettoyage du texte (étape 2).

Transforme un texte en liste de mots « propres » : tout en minuscules,
sans accents, sans ponctuation et sans mots vides.
"""
import re
import unicodedata

# Ligatures que la décomposition Unicode ne sait pas séparer en lettres simples.
LIGATURES: dict[str, str] = {"œ": "oe", "æ": "ae"}

# Un mot = une suite de lettres a-z (le texte est déjà en minuscules, sans accents).
MOT = re.compile(r"[a-z]+")


def retirer_accents(texte: str) -> str:
    """Remplace chaque lettre accentuée par la même lettre sans accent."""
    for ligature, remplacement in LIGATURES.items():
        texte = texte.replace(ligature, remplacement)
    # La forme « NFD » sépare « é » en « e » + un accent isolé...
    decompose = unicodedata.normalize("NFD", texte)
    # ... et on supprime ensuite tous les accents isolés.
    return "".join(c for c in decompose if not unicodedata.combining(c))


def normaliser(texte: str) -> str:
    """Met le texte en minuscules puis retire les accents."""
    # On met en minuscules d'abord : « Œ » devient « œ » avant le remplacement.
    return retirer_accents(texte.lower())


def charger_mots_vides(chemin: str) -> set[str]:
    """Lit le fichier des mots vides (un mot par ligne) et renvoie un set."""
    mots: set[str] = set()
    try:
        with open(chemin, encoding="utf-8") as fichier:
            for ligne in fichier:
                ligne = ligne.strip()
                # On ignore les lignes vides et les commentaires (# ...).
                if ligne and not ligne.startswith("#"):
                    mots.add(normaliser(ligne))
    except OSError:
        print(f"Attention : impossible de lire {chemin} (aucun mot vide utilisé).")
    return mots


def nettoyer(texte: str, mots_vides: set[str]) -> list[str]:
    """Renvoie la liste des mots propres d'un texte.

    Exemple : "Maître Corbeau, sur un arbre perché"
    donne ["maitre", "corbeau", "arbre", "perche"].
    """
    mots = MOT.findall(normaliser(texte))
    # On garde les mots d'au moins 2 lettres qui ne sont pas des mots vides.
    return [mot for mot in mots if len(mot) > 1 and mot not in mots_vides]
