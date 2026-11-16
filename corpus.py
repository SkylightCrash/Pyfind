"""Chargement et découpage du corpus des Fables de La Fontaine."""
import html
import json
import os
import re
import urllib.request

CORPUS_FILE = "data/fables.json"
SOURCE_URL = "https://www.gutenberg.org/cache/epub/56327/pg56327-images.html"


def nettoyer_html(fragment: str) -> str:
    """Retire les balises HTML et décode les entités."""
    texte = re.sub(r"(?is)<[^>]+>", " ", fragment)
    return re.sub(r"\s+", " ", html.unescape(texte)).strip()


def extraire_fables(contenu: str) -> list[dict]:
    """Découpe le HTML Gutenberg en fables à partir des titres h3."""
    blocs = re.split(r"(?is)<h3[^>]*>(.*?)</h3>", contenu)
    fables = []
    for position in range(1, len(blocs), 2):
        titre = nettoyer_html(blocs[position]).strip(" .")
        zone = blocs[position + 1] if position + 1 < len(blocs) else ""
        paragraphes = re.findall(r"(?is)<p[^>]*>(.*?)</p>", zone)
        texte = " ".join(nettoyer_html(p) for p in paragraphes)
        if titre and len(texte.split()) >= 8:
            fables.append({"id": len(fables) + 1, "titre": titre, "texte": texte})
    return fables


def charger_corpus(force: bool = False) -> list[dict]:
    """Charge le corpus local ou le télécharge avec plusieurs tentatives."""

    if os.path.exists(CORPUS_FILE) and not force:
        with open(CORPUS_FILE, encoding="utf-8") as fichier:
            return json.load(fichier)

    requete = urllib.request.Request(
        SOURCE_URL,
        headers={
            "User-Agent": "Mozilla/5.0 (compatible; PyFind/1.0)"
        }
    )

    derniere_erreur = None

    for tentative in range(1, 4):
        try:
            print(f"Téléchargement du corpus (tentative {tentative}/3)...")

            with urllib.request.urlopen(requete, timeout=60) as reponse:
                contenu = reponse.read().decode(
                    "utf-8",
                    errors="replace"
                )

            fables = extraire_fables(contenu)

            if not fables:
                raise RuntimeError(
                    "Aucune fable détectée dans le document Gutenberg."
                )

            os.makedirs("data", exist_ok=True)

            with open(CORPUS_FILE, "w", encoding="utf-8") as fichier:
                json.dump(
                    fables,
                    fichier,
                    ensure_ascii=False,
                    indent=2
                )

            print(f"{len(fables)} fables téléchargées et enregistrées.")
            return fables

        except Exception as erreur:
            derniere_erreur = erreur
            print(f"Échec : {erreur}")

            if tentative < 3:
                import time
                time.sleep(3 * tentative)

    raise RuntimeError(
        "Impossible de télécharger le corpus après 3 tentatives. "
        "Vérifie ta connexion ou réessaie plus tard."
    ) from derniere_erreur
