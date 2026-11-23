"""Sauvegarde et rechargement de l'index (étape 4) + mesure du temps."""
import hashlib
import json
import time
from collections.abc import Callable
from typing import Any

from index import Index

# Si le format du fichier change, on augmente ce numéro : l'ancien fichier est ignoré.
VERSION = 1


def empreinte_fichiers(chemins: list[str]) -> str:
    """Calcule une « empreinte » du contenu des fichiers sources.

    Si le livre ou la liste des mots vides change, l'empreinte change et
    l'index sauvegardé n'est plus valable : on le reconstruit.
    """
    calcul = hashlib.sha256()
    for chemin in chemins:
        try:
            with open(chemin, "rb") as fichier:
                calcul.update(fichier.read())
        except OSError:
            calcul.update(b"absent")
    return calcul.hexdigest()


def sauvegarder_index(
    chemin: str, index: Index, longueurs: dict[int, int], empreinte: str
) -> bool:
    """Enregistre l'index dans un fichier JSON. Renvoie True si réussi."""
    donnees = {
        "version": VERSION,
        "empreinte": empreinte,
        "longueurs": longueurs,
        "index": index,
    }
    try:
        with open(chemin, "w", encoding="utf-8") as fichier:
            json.dump(donnees, fichier, ensure_ascii=False)
        return True
    except OSError:
        return False


def charger_index(chemin: str, empreinte: str) -> tuple[Index, dict[int, int]] | None:
    """Recharge l'index sauvegardé, ou renvoie None s'il est absent/périmé/abîmé."""
    try:
        with open(chemin, encoding="utf-8") as fichier:
            donnees = json.load(fichier)
        if donnees["version"] != VERSION or donnees["empreinte"] != empreinte:
            return None
        # JSON transforme les numéros de fables (int) en texte : on les remet en int.
        index = {
            mot: {int(num): positions for num, positions in fiches.items()}
            for mot, fiches in donnees["index"].items()
        }
        longueurs = {int(num): taille for num, taille in donnees["longueurs"].items()}
        return index, longueurs
    except (OSError, ValueError, KeyError, TypeError, AttributeError):
        return None  # fichier absent ou corrompu : on reconstruira l'index


def mesurer(libelle: str, fonction: Callable[..., Any], *args: Any) -> tuple[Any, float]:
    """Exécute fonction(*args), affiche sa durée et renvoie (résultat, durée)."""
    debut = time.perf_counter()
    resultat = fonction(*args)
    duree = time.perf_counter() - debut
    print(f"  [{libelle} : {duree:.3f} s]")
    return resultat, duree
