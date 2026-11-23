"""Construction de l'index inversé (étape 3).

L'index est un dictionnaire : pour chaque mot, dans quelles fables il se
trouve et à quelles positions.

    index = {"renard": {3: [9, 30], 52: [0]}, ...}
"""
from nettoyage import nettoyer

# Type de l'index : mot -> {numéro de fable -> liste des positions du mot}
Index = dict[str, dict[int, list[int]]]


def mots_positionnes(fable: dict, mots_vides: set[str]) -> list[tuple[int, str]]:
    """Liste des (position, mot) d'une fable : d'abord le titre, puis le texte."""
    titre = nettoyer(fable["titre"], mots_vides)
    texte = nettoyer(fable["texte"], mots_vides)
    # On laisse un « trou » d'une position entre le titre et le texte :
    # ainsi une expression exacte ne peut pas chevaucher les deux.
    decalage = len(titre) + 1
    return list(enumerate(titre)) + [(decalage + i, mot) for i, mot in enumerate(texte)]


def construire_index(
    fables: list[dict], mots_vides: set[str]
) -> tuple[Index, dict[int, int]]:
    """Construit l'index et la longueur (en mots) de chaque fable."""
    index: Index = {}
    longueurs: dict[int, int] = {}
    for fable in fables:
        paires = mots_positionnes(fable, mots_vides)
        longueurs[fable["id"]] = len(paires)  # sert au calcul du « tf » plus tard
        for position, mot in paires:
            # setdefault crée l'entrée du mot, puis celle de la fable, si besoin.
            index.setdefault(mot, {}).setdefault(fable["id"], []).append(position)
    return index, longueurs


def frequences(index: Index) -> dict[str, int]:
    """Nombre total d'apparitions de chaque mot dans tout le livre."""
    return {mot: sum(len(p) for p in fiches.values()) for mot, fiches in index.items()}


def statistiques(index: Index, nb_fables: int) -> dict:
    """Chiffres de la commande stats : fables, mots différents, 10 mots les plus fréquents."""
    # Tri par fréquence décroissante, puis par ordre alphabétique (résultat stable).
    classement = sorted(frequences(index).items(), key=lambda paire: (-paire[1], paire[0]))
    return {"fables": nb_fables, "mots_differents": len(index), "top": classement[:10]}
