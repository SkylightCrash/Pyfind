"""Moteur de recherche : ET / OU / SAUF (étape 5), classement TF-IDF (étape 6),
expressions exactes (étape 7) et suggestions de correction (étape 8).

Les requêtes sont évaluées de gauche à droite :
    loup ET agneau SAUF chien  =  (loup ET agneau) SAUF chien
"""
import math
import re
import time

from correcteur import proposer
from index import Index
from nettoyage import nettoyer, normaliser

OPERATEURS = {"ET", "OU", "SAUF"}
LONGUEUR_MAX = 200

# Un morceau de requête : une expression entre guillemets OU un mot isolé.
RE_PIECE = re.compile(r'"([^"]*)"|([^\s"]+)')

# Les guillemets typographiques sont remplacés par des guillemets droits.
GUILLEMETS = str.maketrans({"“": '"', "”": '"', "«": '"', "»": '"'})


# ---------------------------------------------------------------- analyse de la requête
def decouper_requete(requete: str) -> list[tuple[str, bool]]:
    """Découpe la requête en morceaux (texte, est_une_expression_entre_guillemets)."""
    requete = requete.translate(GUILLEMETS)
    if requete.count('"') % 2 == 1:
        raise ValueError('Guillemet non fermé : écrivez par exemple "maitre corbeau".')
    morceaux = []
    for trouve in RE_PIECE.finditer(requete):
        if trouve.group(1) is not None:
            morceaux.append((trouve.group(1), True))
        else:
            morceaux.append((trouve.group(2), False))
    return morceaux


def choisir_operateur(nouveau: str, precedent: str | None, a_des_termes: bool) -> str:
    """Vérifie qu'un opérateur est bien placé et le renvoie."""
    if not a_des_termes:
        raise ValueError(f"La requête ne peut pas commencer par {nouveau}.")
    if precedent is not None:
        raise ValueError(
            f"Deux opérateurs d'affilée ({precedent} {nouveau}) : mettez un mot entre les deux."
        )
    return nouveau


def verifier_requete(termes: list[dict], operateur: str | None) -> None:
    """Lève une erreur claire si la requête est incomplète."""
    if operateur is not None:
        raise ValueError(f"L'opérateur {operateur} doit être suivi d'un mot.")
    if not termes:
        raise ValueError(
            "Aucun mot utile dans la requête (les mots très courants "
            "comme « le » ou « de » sont ignorés)."
        )


def analyser_requete(requete: str, mots_vides: set[str]) -> tuple[list[dict], list[str]]:
    """Transforme la requête en liste de termes + liste des mots ignorés.

    Un terme est un dictionnaire : {"op": "ET", "mots": ["loup"], "exacte": False}.
    Le premier terme n'a pas d'opérateur (op = None).
    """
    termes: list[dict] = []
    ignores: list[str] = []
    operateur: str | None = None
    for texte, entre_guillemets in decouper_requete(requete):
        if not entre_guillemets and texte.upper() in OPERATEURS:
            operateur = choisir_operateur(texte.upper(), operateur, bool(termes))
            continue
        mots = nettoyer(texte, mots_vides)
        if not mots:
            if texte.strip():
                ignores.append(texte)  # mot vide : on le signale à l'utilisateur
            continue
        # Sans opérateur écrit, deux mots de suite signifient ET.
        op = (operateur or "ET") if termes else None
        termes.append({"op": op, "mots": mots, "exacte": entre_guillemets or len(mots) > 1})
        operateur = None
    verifier_requete(termes, operateur)
    return termes, ignores


# ---------------------------------------------------------------- recherche dans l'index
def expression_presente(index: Index, mots: list[str], fable_id: int) -> bool:
    """Vrai si les mots se suivent, dans cet ordre, dans la fable."""
    suivants = [set(index[mot][fable_id]) for mot in mots[1:]]
    for depart in index[mots[0]][fable_id]:
        # Le mot n°k de l'expression doit être à la position depart + k.
        if all(depart + k + 1 in positions for k, positions in enumerate(suivants)):
            return True
    return False


def fables_avec_expression(index: Index, mots: list[str]) -> set[int]:
    """Fables qui contiennent l'expression exacte (mots côte à côte)."""
    if any(mot not in index for mot in mots):
        return set()
    # D'abord les fables qui contiennent tous les mots, puis on vérifie l'ordre.
    candidates = set.intersection(*(set(index[mot]) for mot in mots))
    return {f for f in candidates if expression_presente(index, mots, f)}


def fables_du_terme(index: Index, terme: dict) -> set[int]:
    """Ensemble des fables qui correspondent à un terme (mot ou expression)."""
    mots = terme["mots"]
    if len(mots) == 1:
        return set(index.get(mots[0], {}))
    return fables_avec_expression(index, mots)


def evaluer(index: Index, termes: list[dict]) -> set[int]:
    """Applique ET (&), OU (|) et SAUF (-) de gauche à droite sur des sets."""
    resultat = fables_du_terme(index, termes[0])
    for terme in termes[1:]:
        ensemble = fables_du_terme(index, terme)
        if terme["op"] == "ET":
            resultat = resultat & ensemble  # intersection
        elif terme["op"] == "OU":
            resultat = resultat | ensemble  # union
        else:
            resultat = resultat - ensemble  # différence (SAUF)
    return resultat


# ---------------------------------------------------------------- classement TF-IDF
def mots_a_scorer(termes: list[dict]) -> list[str]:
    """Mots qui comptent dans le score : ceux qui ne sont pas après un SAUF."""
    mots: list[str] = []
    for terme in termes:
        if terme["op"] == "SAUF":
            continue
        for mot in terme["mots"]:
            if mot not in mots:
                mots.append(mot)
    return mots


def score_tfidf(
    index: Index, longueurs: dict[int, int], nb_fables: int, mots: list[str], fable_id: int
) -> float:
    """Score TF-IDF d'une fable : somme de tf x idf pour chaque mot cherché."""
    total = 0.0
    for mot in mots:
        fiches = index.get(mot, {})
        if fable_id in fiches:
            tf = len(fiches[fable_id]) / longueurs[fable_id]  # fréquence dans la fable
            idf = math.log10(nb_fables / len(fiches))  # rareté dans le livre
            total += tf * idf
    return total


# ---------------------------------------------------------------- extrait et suggestions
def decouper_ligne(ligne: str, mots: set[str]) -> list[tuple[str, bool]]:
    """Découpe une ligne en segments (texte, est_un_mot_cherché)."""
    segments: list[tuple[str, bool]] = []
    fin = 0
    for trouve in re.finditer(r"\w+", ligne):
        if normaliser(trouve.group()) in mots:
            if trouve.start() > fin:
                segments.append((ligne[fin:trouve.start()], False))
            segments.append((trouve.group(), True))
            fin = trouve.end()
    if fin < len(ligne):
        segments.append((ligne[fin:], False))
    return segments


def choisir_extrait(fable: dict, mots: set[str]) -> list[tuple[str, bool]]:
    """Choisit la ligne du texte qui contient le plus de mots cherchés."""
    lignes = [ligne for ligne in fable["texte"].splitlines() if ligne.strip()]
    candidats = [decouper_ligne(ligne, mots) for ligne in lignes]
    meilleur = max(candidats, key=lambda seg: sum(1 for _, trouve in seg if trouve), default=[])
    if any(trouve for _, trouve in meilleur):
        return meilleur
    # Le mot n'est que dans le titre : on affiche alors le titre.
    return decouper_ligne(fable["titre"], mots)


def fabriquer_resultat(fable: dict, score: float, mots: list[str]) -> dict:
    """Prépare le résultat d'une fable : titre, score et extrait en MAJUSCULES."""
    segments = choisir_extrait(fable, set(mots))
    # Les mots trouvés sont écrits en MAJUSCULES dans l'extrait.
    segments = [(texte.upper() if trouve else texte, trouve) for texte, trouve in segments]
    return {
        "id": fable["id"],
        "titre": fable["titre"],
        "score": round(score, 4),
        "extrait": "".join(texte for texte, _ in segments),
        "segments": segments,
    }


def chercher_suggestions(index: Index, termes: list[dict]) -> list[dict]:
    """Pour chaque mot absent de l'index, propose le mot le plus proche."""
    propositions: list[dict] = []
    vus: set[str] = set()
    for terme in termes:
        for mot in terme["mots"]:
            if mot in index or mot in vus:
                continue
            vus.add(mot)
            proposition = proposer(mot, index)
            if proposition:
                propositions.append({"mot": mot, "propose": proposition})
    return propositions


def reconstruire_requete(termes: list[dict], remplacements: dict[str, str]) -> str:
    """Réécrit la requête en remplaçant les mots fautifs par les mots proposés."""
    morceaux: list[str] = []
    for terme in termes:
        mots = [remplacements.get(mot, mot) for mot in terme["mots"]]
        texte = " ".join(mots)
        if terme["exacte"]:
            texte = f'"{texte}"'
        morceaux.append(f"{terme['op']} {texte}" if terme["op"] else texte)
    return " ".join(morceaux)


# ---------------------------------------------------------------- point d'entrée
def verifier_saisie(requete: object) -> None:
    """Refuse les saisies vides, trop longues ou qui ne sont pas du texte."""
    if not isinstance(requete, str):
        raise TypeError("La requête doit être du texte.")
    if not requete.strip():
        raise ValueError("Tapez un ou plusieurs mots à chercher.")
    if len(requete) > LONGUEUR_MAX:
        raise ValueError(f"Requête trop longue (maximum {LONGUEUR_MAX} caractères).")


def remplir_reponse(etat: dict, requete: str, limite: int, reponse: dict) -> None:
    """Fait la recherche complète et remplit le dictionnaire de réponse."""
    termes, ignores = analyser_requete(requete, etat["mots_vides"])
    index = etat["index"]
    trouvees = evaluer(index, termes)
    mots = mots_a_scorer(termes)
    notes = {
        f: score_tfidf(index, etat["longueurs"], len(etat["fables"]), mots, f) for f in trouvees
    }
    # Meilleur score d'abord ; à égalité, la fable au plus petit numéro.
    classement = sorted(trouvees, key=lambda f: (-notes[f], f))
    reponse["total"] = len(classement)
    reponse["resultats"] = [
        fabriquer_resultat(etat["fables"][f], notes[f], mots) for f in classement[:limite]
    ]
    reponse["ignores"] = ignores
    reponse["suggestions"] = chercher_suggestions(index, termes)
    if reponse["suggestions"]:
        corrections = {s["mot"]: s["propose"] for s in reponse["suggestions"]}
        reponse["requete_corrigee"] = reconstruire_requete(termes, corrections)


def rechercher(etat: dict, requete: str, limite: int = 5) -> dict:
    """Lance une recherche. Ne plante jamais : les problèmes sont dans reponse["erreur"]."""
    debut = time.perf_counter()
    reponse: dict = {
        "requete": requete if isinstance(requete, str) else "",
        "ok": False,
        "erreur": None,
        "total": 0,
        "resultats": [],
        "suggestions": [],
        "requete_corrigee": None,
        "ignores": [],
        "duree": 0.0,
    }
    try:
        verifier_saisie(requete)
        remplir_reponse(etat, requete, limite, reponse)
        reponse["ok"] = True
    except (ValueError, TypeError) as erreur:
        reponse["erreur"] = str(erreur)  # message clair destiné à l'utilisateur
    except Exception:  # noqa: BLE001  # pylint: disable=broad-exception-caught
        reponse["erreur"] = "Une erreur inattendue est survenue pendant la recherche."
    reponse["duree"] = time.perf_counter() - debut
    return reponse
