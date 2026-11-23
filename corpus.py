"""Lecture du livre et découpage en fables (étape 1).

Le fichier du Projet Gutenberg contient toutes les fables à la suite.
Chaque fable commence par un numéro en chiffres romains seul sur sa ligne
(I, II, III...) suivi de son titre écrit en MAJUSCULES.
"""
import http.client
import os
import re
import urllib.request

URL_GUTENBERG = "https://www.gutenberg.org/cache/epub/56327/pg56327.txt"

# Un numéro de fable : chiffres romains seuls sur la ligne (« XVIII »).
RE_NUMERO = re.compile(r"^[IVXLC]+\.?$")

# Appels de note [12] et images [image: ] à supprimer du texte.
RE_APPEL = re.compile(r"\[(?:\d+|image:[^\]]*|Illustration[^\]]*)\]", re.IGNORECASE)

# Petits mots qui restent en minuscules dans un titre embelli.
PETITS_MOTS = {
    "et", "de", "du", "des", "la", "le", "les", "un", "une", "au", "aux", "à",
    "a", "en", "sur", "sous", "dans", "par", "pour", "avec", "qui", "que", "se",
    "son", "sa", "ses", "ou", "entre", "chez", "contre", "par-devant",
}


def lire_fichier(chemin: str) -> str:
    """Lit un fichier texte en UTF-8 (sinon les accents seraient abîmés)."""
    # « utf-8-sig » supprime au passage l'éventuel BOM en début de fichier.
    with open(chemin, encoding="utf-8-sig") as fichier:
        return fichier.read()


def telecharger_livre(chemin: str, url: str = URL_GUTENBERG) -> bool:
    """Télécharge le livre depuis le Projet Gutenberg. Renvoie True si réussi."""
    try:
        with urllib.request.urlopen(url, timeout=20) as reponse:
            contenu = reponse.read()
        if b"START OF" not in contenu:  # ce n'est pas le bon fichier
            return False
        os.makedirs(os.path.dirname(chemin), exist_ok=True)
        with open(chemin, "wb") as fichier:
            fichier.write(contenu)
        return True
    except (OSError, ValueError, http.client.HTTPException):
        return False


def extraire_corps(texte: str) -> list[str]:
    """Garde uniquement les lignes du livre, sans la licence anglaise."""
    lignes = texte.splitlines()
    # Le livre est entre les lignes « *** START OF ... » et « *** END OF ... ».
    debut = next((i + 1 for i, l in enumerate(lignes) if l.startswith("*** START OF")), 0)
    fin = next((i for i, l in enumerate(lignes) if l.startswith("*** END OF")), len(lignes))
    if fin <= debut:
        fin = len(lignes)
    return lignes[debut:fin]


def trouver_debut(lignes: list[str]) -> int:
    """Trouve la ligne où commencent les fables (après préface et dédicace)."""
    for i, ligne in enumerate(lignes):
        if ligne.strip() == "LES FABLES":
            # Ce « LES FABLES » doit être suivi d'un numéro de fable.
            suite = [l.strip() for l in lignes[i + 1:i + 12] if l.strip()]
            if suite and RE_NUMERO.match(suite[0]):
                return i + 1
    return 0  # repère introuvable : on cherche dans tout le livre


def est_titre(ligne: str) -> bool:
    """Vrai si la ligne est entièrement en majuscules (un titre de fable)."""
    texte = RE_APPEL.sub("", ligne).strip()
    lettres = [c for c in texte if c.isalpha()]
    return len(lettres) >= 3 and texte == texte.upper()


def lire_titre(lignes: list[str], debut: int) -> tuple[str, int]:
    """Lit le titre qui suit un numéro. Renvoie (titre, indice de la ligne suivante)."""
    i = debut
    while i < len(lignes) and not lignes[i].strip():
        i += 1  # on saute les lignes vides
    morceaux: list[str] = []
    # Un titre peut tenir sur plusieurs lignes consécutives.
    while i < len(lignes) and lignes[i].strip() and est_titre(lignes[i]):
        morceaux.append(RE_APPEL.sub("", lignes[i]).strip())
        i += 1
    if not morceaux:
        return "", debut
    return " ".join(morceaux), i


def embellir_titre(titre: str) -> str:
    """Transforme « LE LOUP ET L'AGNEAU. » en « Le Loup et l'Agneau »."""
    mots = titre.lower().replace("’", "'").rstrip(". ").split()
    resultat: list[str] = []
    for rang, mot in enumerate(mots):
        prefixe, apostrophe, reste = mot.rpartition("'")  # « l'agneau » -> l ' agneau
        if rang > 0 and reste in PETITS_MOTS:
            reste_final = reste
        else:
            reste_final = reste[:1].upper() + reste[1:]
        if rang == 0:
            prefixe = prefixe.capitalize()
        resultat.append(prefixe + apostrophe + reste_final)
    return " ".join(resultat)


def assembler_texte(lignes: list[str]) -> str:
    """Rassemble les lignes d'une fable en un texte propre."""
    propres = [RE_APPEL.sub("", ligne).strip() for ligne in lignes]
    texte = "\n".join(propres)
    # Plus d'une ligne vide d'affilée ne sert à rien.
    return re.sub(r"\n{3,}", "\n\n", texte).strip()


def decouper_fables(lignes: list[str]) -> list[dict]:
    """Coupe le livre en fables : une liste de dictionnaires titre / texte."""
    fables: list[dict] = []
    courante: dict | None = None
    i = 0
    while i < len(lignes):
        ligne = lignes[i].strip()
        if RE_NUMERO.match(ligne):
            titre, suivant = lire_titre(lignes, i + 1)
            if titre:  # numéro + titre : c'est le début d'une nouvelle fable
                courante = {"titre": embellir_titre(titre), "lignes": []}
                fables.append(courante)
                i = suivant
                continue
        if ligne.startswith("FIN DU LIVRE") or (ligne.startswith("LIVRE ") and ligne.isupper()):
            courante = None  # fin de livre : ce qui suit n'est pas une fable
        elif courante is not None:
            courante["lignes"].append(lignes[i])
        i += 1
    return [{"titre": f["titre"], "texte": assembler_texte(f["lignes"])} for f in fables]


def charger_fables(chemin: str) -> list[dict]:
    """Lit le fichier du livre et renvoie la liste des fables.

    Chaque fable est un dictionnaire : {"id": 12, "titre": "...", "texte": "..."}
    """
    lignes = extraire_corps(lire_fichier(chemin))
    debut = trouver_debut(lignes)
    fables = [f for f in decouper_fables(lignes[debut:]) if f["texte"]]
    if not fables:
        raise ValueError(f"Aucune fable reconnue dans {chemin}.")
    for numero, fable in enumerate(fables, start=1):
        fable["id"] = numero  # numérotation continue : 1, 2, 3...
    return fables


if __name__ == "__main__":
    # Petit outil de diagnostic : python corpus.py data/fables.txt
    import sys

    fichier = sys.argv[1] if len(sys.argv) > 1 else "data/fables.txt"
    resultat = charger_fables(fichier)
    print(f"{len(resultat)} fables lues dans {fichier}")
    for exemple in (resultat[0], resultat[-1]):
        print(f"  n°{exemple['id']} : {exemple['titre']} ({len(exemple['texte'])} caractères)")
