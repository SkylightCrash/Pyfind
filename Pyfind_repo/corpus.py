"""Chargement et découpage du corpus des Fables de La Fontaine.

Le texte provient d'un fichier local (export texte Project Gutenberg,
ebook 56327) : plus aucune requête réseau n'est effectuée.
"""
import json
import os
import re

CORPUS_FILE = "data/fables.json"
SOURCE_FILE = "data/fables_gutenberg.txt"

DEBUT_FABLES = re.compile(r"\[Illustration:\s*LIVRE\s+1\.\]")
FIN_FABLES = re.compile(r"^\s*TABLE DES FABLES\s*$", re.M)
BRUIT = re.compile(
    r"^\s*(\[Illustration[^\]]*\]|\[Illustration:?|FIN DU LIVRE .*)\s*$"
)
TITRE_NUMERO = re.compile(r"^\s*[IVXLC]+\s*$")
TITRE_SPECIAL = re.compile(r"^\s*(ÉPILOGUE|ÉPITAPHE DE LA FONTAINE)\s*$")
NOTE_DEBUT = re.compile(r"^\s*\[\d+\]\s")
RENVOI = re.compile(r"\[\d+\]")


def extraire_fables(contenu: str) -> list[dict]:
    """Découpe le texte brut Gutenberg en fables.

    Chaque fable commence par un numéro romain seul sur sa ligne, suivi du
    titre (jusqu'à la première ligne vide), puis des vers.
    """
    contenu = contenu.replace("\r\n", "\n").replace("\r", "\n")

    debut = DEBUT_FABLES.search(contenu)
    if not debut:
        raise RuntimeError("Début des fables introuvable dans le fichier texte.")
    fin = FIN_FABLES.search(contenu, debut.end())
    zone = contenu[debut.end(): fin.start() if fin else len(contenu)]

    lignes = []
    en_note = False
    for l in zone.split("\n"):
        if BRUIT.match(l):
            continue
        if NOTE_DEBUT.match(l):  # note de bas de page de l'éditeur
            en_note = True
            continue
        if en_note and l.strip():
            continue
        en_note = False
        lignes.append(RENVOI.sub("", l))

    fables, titre, corps = [], None, []

    def clore() -> None:
        texte = re.sub(r"\s+", " ", " ".join(corps).replace("_", "")).strip()
        if titre and len(texte.split()) >= 8:
            fables.append({"id": len(fables) + 1, "titre": titre, "texte": texte})

    i = 0
    while i < len(lignes):
        ligne = lignes[i]
        if TITRE_NUMERO.match(ligne) or TITRE_SPECIAL.match(ligne):
            clore()
            corps = []
            i += 1
            if TITRE_SPECIAL.match(ligne):
                titre = ("Épilogue" if "ÉPILOGUE" in ligne
                         else "Épitaphe de La Fontaine")
                if titre != "Épilogue":  # sous-titre « composée par lui-même »
                    while i < len(lignes) and (not lignes[i].strip()
                                               or lignes[i].strip().isupper()):
                        i += 1
                continue
            morceaux = []
            while i < len(lignes) and not lignes[i].strip():
                i += 1
            while i < len(lignes) and lignes[i].strip():
                morceaux.append(lignes[i].strip())
                i += 1
            titre = " ".join(morceaux).strip(" .")
            continue
        if titre is not None:
            corps.append(ligne.strip())
        i += 1
    clore()
    return fables


def charger_corpus(force: bool = False) -> list[dict]:
    """Charge le cache JSON, ou le reconstruit à partir du fichier texte local."""
    cache_a_jour = (
        os.path.exists(CORPUS_FILE)
        and os.path.exists(SOURCE_FILE)
        and os.path.getmtime(CORPUS_FILE) >= os.path.getmtime(SOURCE_FILE)
    )
    if cache_a_jour and not force:
        with open(CORPUS_FILE, encoding="utf-8") as fichier:
            return json.load(fichier)

    if not os.path.exists(SOURCE_FILE):
        raise FileNotFoundError(
            f"Fichier source introuvable : {SOURCE_FILE}. "
            "Place-y le texte Gutenberg des Fables de La Fontaine."
        )

    print(f"Lecture du corpus depuis {SOURCE_FILE}...")
    with open(SOURCE_FILE, encoding="utf-8-sig") as fichier:
        fables = extraire_fables(fichier.read())
    if not fables:
        raise RuntimeError("Aucune fable détectée dans le fichier texte.")

    os.makedirs(os.path.dirname(CORPUS_FILE), exist_ok=True)
    with open(CORPUS_FILE, "w", encoding="utf-8") as fichier:
        json.dump(fables, fichier, ensure_ascii=False, indent=2)

    # Le corpus a changé : l'ancien index n'est plus valable.
    from indexation import INDEX_FILE
    if os.path.exists(INDEX_FILE):
        os.remove(INDEX_FILE)

    print(f"{len(fables)} fables extraites et enregistrées.")
    return fables
