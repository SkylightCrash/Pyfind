"""Correction des fautes de frappe (étape 8) : distance de Levenshtein."""
from index import Index


def distance_levenshtein(a: str, b: str) -> int:
    """Nombre minimal de lettres à ajouter, enlever ou changer pour passer de a à b.

    Exemple : renar -> renard (1 lettre ajoutée) : distance 1.
    """
    # precedente[j] = distance entre le début de a déjà lu et les j premières lettres de b.
    precedente = list(range(len(b) + 1))
    for i, lettre_a in enumerate(a, start=1):
        courante = [i]  # passer des i premières lettres de a à "" : i suppressions
        for j, lettre_b in enumerate(b, start=1):
            cout = 0 if lettre_a == lettre_b else 1
            courante.append(min(
                precedente[j] + 1,         # on supprime une lettre de a
                courante[j - 1] + 1,       # on ajoute une lettre
                precedente[j - 1] + cout,  # on change (ou on garde) la lettre
            ))
        precedente = courante
    return precedente[-1]


def distance_maximale(mot: str) -> int:
    """Distance maximale acceptée : 1 pour un mot court, 2 sinon."""
    # Avec 2 fautes sur un mot de 4 lettres, on propose n'importe quoi.
    return 1 if len(mot) <= 4 else 2


def proposer(mot: str, index: Index) -> str | None:
    """Propose le mot de l'index le plus proche de `mot` (distance 1 ou 2)."""
    maximum = distance_maximale(mot)
    meilleur: tuple[int, int, str] | None = None
    for candidat, fiches in index.items():
        if abs(len(candidat) - len(mot)) > maximum:
            continue  # écart de longueur trop grand : inutile de calculer
        distance = distance_levenshtein(mot, candidat)
        if 0 < distance <= maximum:
            # À distance égale, on préfère le mot présent dans le plus de fables.
            cle = (distance, -len(fiches), candidat)
            if meilleur is None or cle < meilleur:
                meilleur = cle
    return meilleur[2] if meilleur else None
