"""Moteur de recherche booléen, expressions exactes et classement TF-IDF."""
import math
import re
from nettoyage import nettoyer
from correcteur import suggestions


def analyser_requete(requete: str) -> tuple[list[str], str]:
    """Sépare les termes et l'opérateur booléen de la requête."""
    morceaux = re.split(r'\s+(ET|OU|SAUF)\s+', requete.strip(), flags=re.I)
    termes = [m.strip() for m in morceaux[::2] if m.strip()]
    operateur = morceaux[1].upper() if len(morceaux) > 1 else "ET"
    return termes, operateur


def fables_du_terme(terme: str, index: dict) -> set[int]:
    """Retourne les identifiants contenant un mot ou une expression exacte."""
    phrase = terme.startswith('"') and terme.endswith('"')
    mots = nettoyer(terme.strip('"'))
    if not mots:
        return set()
    if not phrase and len(mots) == 1:
        return {int(fid) for fid in index.get(mots[0], {})}
    ensembles = [{int(fid) for fid in index.get(mot, {})} for mot in mots]
    candidats = set.intersection(*ensembles) if ensembles else set()
    resultat = set()
    for fid in candidats:
        debuts = index[mots[0]][str(fid)]
        if any(all(depart + i in index[mot].get(str(fid), [])
                   for i, mot in enumerate(mots[1:], 1)) for depart in debuts):
            resultat.add(fid)
    return resultat


def combiner(ensembles: list[set[int]], operateur: str) -> set[int]:
    """Combine les résultats avec ET, OU ou SAUF."""
    if not ensembles:
        return set()
    resultat = set(ensembles[0])
    for ensemble in ensembles[1:]:
        resultat = (resultat | ensemble if operateur == "OU" else
                    resultat - ensemble if operateur == "SAUF" else resultat & ensemble)
    return resultat


def score_fable(fid: int, termes: list[str], index: dict, longueurs: dict, total: int) -> float:
    """Calcule le score TF-IDF d'une fable pour les termes demandés."""
    score = 0.0
    for terme in termes:
        for mot in nettoyer(terme.strip('"')):
            documents = index.get(mot, {})
            occurrences = documents.get(str(fid), [])
            if occurrences:
                tf = len(occurrences) / max(int(longueurs.get(str(fid), longueurs.get(fid, 1))), 1)
                idf = math.log10(total / max(len(documents), 1))
                score += tf * idf
    return score


def extrait(texte: str, termes: list[str]) -> str:
    """Produit un extrait autour du premier terme trouvé."""
    mots = [mot for terme in termes for mot in nettoyer(terme.strip('"'))]
    positions = [texte.lower().find(mot) for mot in mots if texte.lower().find(mot) >= 0]
    debut = max(0, min(positions or [0]) - 90)
    fin = min(len(texte), debut + 280)
    return ("…" if debut else "") + texte[debut:fin] + ("…" if fin < len(texte) else "")


def rechercher(requete: str, fables: list[dict], index: dict, longueurs: dict) -> dict:
    """Exécute une recherche et renvoie les résultats classés."""
    termes, operateur = analyser_requete(requete)
    if not termes:
        return {"resultats": [], "suggestions": []}
    ensembles = [fables_du_terme(terme, index) for terme in termes]
    ids = combiner(ensembles, operateur)
    corrections = []
    for terme, ensemble in zip(termes, ensembles):
        mots = nettoyer(terme.strip('"'))
        if not ensemble and len(mots) == 1:
            corrections.extend(suggestions(mots[0], set(index)))
    par_id = {f["id"]: f for f in fables}
    classes = sorted(ids, key=lambda fid: score_fable(fid, termes, index, longueurs, len(fables)), reverse=True)
    resultats = []
    for fid in classes[:20]:
        fable = par_id[fid]
        score = score_fable(fid, termes, index, longueurs, len(fables))
        resultats.append({"id": fid, "titre": fable["titre"], "texte": fable["texte"],
                          "score": round(score, 5), "extrait": extrait(fable["texte"], termes)})
    return {"resultats": resultats, "suggestions": list(dict.fromkeys(corrections))[:5]}
