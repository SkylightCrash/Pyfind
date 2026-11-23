"""Prépare le moteur de recherche : charge le livre, puis l'index (construit ou rechargé)."""
import os

from corpus import charger_fables, telecharger_livre
from index import Index, construire_index
from nettoyage import charger_mots_vides
from stockage import charger_index, empreinte_fichiers, mesurer, sauvegarder_index

# Tous les chemins partent du dossier du projet : on peut lancer le programme de n'importe où.
BASE = os.path.dirname(os.path.abspath(__file__))
CHEMIN_FABLES = os.path.join(BASE, "data", "fables.txt")
CHEMIN_DEMO = os.path.join(BASE, "data", "fables_demo.txt")
CHEMIN_MOTS_VIDES = os.path.join(BASE, "mots_vides.txt")
CHEMIN_INDEX = os.path.join(BASE, "data", "index.json")


def choisir_source() -> str:
    """Renvoie le fichier du livre à utiliser : le vrai livre, sinon la démo."""
    if not os.path.exists(CHEMIN_FABLES):
        print("data/fables.txt est absent : téléchargement depuis le Projet Gutenberg...")
        telecharger_livre(CHEMIN_FABLES)
    if os.path.exists(CHEMIN_FABLES):
        return CHEMIN_FABLES
    print("ATTENTION : téléchargement impossible. Utilisation du mini-corpus de démonstration.")
    print("  -> Téléchargez le livre (Plain Text UTF-8) et enregistrez-le sous data/fables.txt")
    return CHEMIN_DEMO


def obtenir_index(
    fables: list[dict], mots_vides: set[str], source: str, temps: dict[str, float]
) -> tuple[Index, dict[int, int], str]:
    """Recharge l'index sauvegardé s'il est valable, sinon le reconstruit et le sauvegarde."""
    empreinte = empreinte_fichiers([source, CHEMIN_MOTS_VIDES])
    charge, duree = mesurer("Lecture du fichier d'index", charger_index, CHEMIN_INDEX, empreinte)
    if charge is not None:
        temps["Chargement de l'index"] = duree
        return charge[0], charge[1], "fichier"
    (index, longueurs), duree = mesurer("Construction de l'index", construire_index, fables, mots_vides)
    temps["Construction de l'index"] = duree
    _, duree = mesurer(
        "Sauvegarde de l'index", sauvegarder_index, CHEMIN_INDEX, index, longueurs, empreinte
    )
    temps["Sauvegarde de l'index"] = duree
    return index, longueurs, "calcul"


def initialiser() -> dict:
    """Prépare tout ce qu'il faut pour chercher et renvoie « l'état » du moteur."""
    temps: dict[str, float] = {}
    source = choisir_source()
    fables, duree = mesurer("Lecture et découpage des fables", charger_fables, source)
    temps["Lecture et découpage des fables"] = duree
    mots_vides = charger_mots_vides(CHEMIN_MOTS_VIDES)
    index, longueurs, origine = obtenir_index(fables, mots_vides, source, temps)
    return {
        "fables": {fable["id"]: fable for fable in fables},  # accès direct par numéro
        "index": index,
        "longueurs": longueurs,
        "mots_vides": mots_vides,
        "temps": temps,
        "origine_index": origine,
        "demo": source == CHEMIN_DEMO,
    }
