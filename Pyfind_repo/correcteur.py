"""Correction orthographique par distance de Levenshtein."""
from nettoyage import normaliser


def distance_levenshtein(mot_a: str, mot_b: str) -> int:
    """Calcule insertions, suppressions et substitutions minimales."""
    ligne = list(range(len(mot_b) + 1))
    for i, lettre_a in enumerate(mot_a, 1):
        suivante = [i]
        for j, lettre_b in enumerate(mot_b, 1):
            cout = 0 if lettre_a == lettre_b else 1
            suivante.append(min(suivante[-1] + 1, ligne[j] + 1, ligne[j - 1] + cout))
        ligne = suivante
    return ligne[-1]


def suggestions(mot: str, vocabulaire: set[str], limite: int = 5) -> list[str]:
    """Propose les mots les plus proches à une distance de deux maximum."""
    cible = normaliser(mot).replace(" ", "")
    proches = [(distance_levenshtein(cible, terme), terme) for terme in vocabulaire]
    proches = sorted((distance, terme) for distance, terme in proches if distance <= 2)
    return [terme for _, terme in proches[:limite]]
