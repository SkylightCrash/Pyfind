"""Serveur WSGI minimal, sans framework ni dépendance externe."""
import json
import mimetypes
import os
from urllib.parse import parse_qs
from recherche import rechercher
from indexation import statistiques

FABLES = []
INDEX = {}
LONGUEURS = {}
RACINE = os.path.dirname(os.path.abspath(__file__))


def reponse(start_response, donnees: dict, statut: str = "200 OK") -> list[bytes]:
    """Sérialise une réponse JSON."""
    corps = json.dumps(donnees, ensure_ascii=False).encode("utf-8")
    start_response(statut, [("Content-Type", "application/json; charset=utf-8"),
                           ("Content-Length", str(len(corps)))])
    return [corps]


def servir_fichier(chemin: str, start_response) -> list[bytes]:
    """Sert un fichier de l'interface après vérification du chemin."""
    base = os.path.join(RACINE, "static")
    cible = os.path.abspath(os.path.join(base, chemin.lstrip("/")))
    if not cible.startswith(base + os.sep):
        return reponse(start_response, {"erreur": "Accès refusé"}, "403 Forbidden")
    try:
        with open(cible, "rb") as fichier:
            contenu = fichier.read()
        type_mime = mimetypes.guess_type(cible)[0] or "application/octet-stream"
        start_response("200 OK", [("Content-Type", type_mime),
                                  ("Content-Length", str(len(contenu)))])
        return [contenu]
    except OSError:
        return reponse(start_response, {"erreur": "Fichier introuvable"}, "404 Not Found")


def application(environ: dict, start_response) -> list[bytes]:
    """Route les requêtes API et sert les fichiers statiques."""
    chemin = environ.get("PATH_INFO", "/")
    if chemin == "/api/search":
        requete = parse_qs(environ.get("QUERY_STRING", "")).get("q", [""])[0]
        return reponse(start_response, rechercher(requete, FABLES, INDEX, LONGUEURS))
    if chemin == "/api/fables":
        return reponse(start_response, [{"id": f["id"], "titre": f["titre"]} for f in FABLES])
    if chemin == "/api/stats":
        return reponse(start_response, statistiques(FABLES, INDEX))
    if chemin.startswith("/api/fable/"):
        try:
            fid = int(chemin.rsplit("/", 1)[1])
            fable = next(f for f in FABLES if f["id"] == fid)
            return reponse(start_response, fable)
        except (ValueError, StopIteration):
            return reponse(start_response, {"erreur": "Fable introuvable"}, "404 Not Found")
    return servir_fichier("index.html" if chemin == "/" else chemin, start_response)
