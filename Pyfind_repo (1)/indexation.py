"""Construction, statistiques et persistance de l'index inversé."""
import json
import os
import time
from collections import Counter, defaultdict
from nettoyage import nettoyer

INDEX_FILE = "data/index.json"


def construire_index(fables: list[dict]) -> tuple[dict, dict]:
    """Construit l'index mot -> fable -> positions et les longueurs."""
    debut = time.perf_counter()
    index = defaultdict(dict)
    longueurs = {}
    for fable in fables:
        mots = nettoyer(fable["texte"])
        longueurs[fable["id"]] = max(len(mots), 1)
        positions = defaultdict(list)
        for position, mot in enumerate(mots):
            positions[mot].append(position)
        for mot, occurrences in positions.items():
            index[mot][str(fable["id"])] = occurrences
    resultat = {mot: dict(entrees) for mot, entrees in index.items()}
    print(f"Index construit en {time.perf_counter() - debut:.3f} s")
    return resultat, longueurs


def sauvegarder_index(index: dict, longueurs: dict) -> None:
    """Enregistre l'index et les longueurs dans un fichier JSON."""
    debut = time.perf_counter()
    os.makedirs("data", exist_ok=True)
    with open(INDEX_FILE, "w", encoding="utf-8") as fichier:
        json.dump({"index": index, "longueurs": longueurs}, fichier)
    print(f"Index sauvegardé en {time.perf_counter() - debut:.3f} s")


def charger_index() -> tuple[dict, dict] | None:
    """Recharge l'index depuis le disque si disponible."""
    debut = time.perf_counter()
    try:
        with open(INDEX_FILE, encoding="utf-8") as fichier:
            donnees = json.load(fichier)
        print(f"Index chargé en {time.perf_counter() - debut:.3f} s")
        return donnees["index"], donnees["longueurs"]
    except (OSError, ValueError, KeyError):
        return None


def statistiques(fables: list[dict], index: dict) -> dict:
    """Calcule les statistiques générales du moteur."""
    frequences = Counter()
    for fable in fables:
        frequences.update(nettoyer(fable["texte"]))
    top = [{"mot": mot, "frequence": n} for mot, n in frequences.most_common(10)]
    return {"nb_fables": len(fables), "nb_mots": len(index), "top_mots": top}
