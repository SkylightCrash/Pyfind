"""Serveur WSGI minimal, sans framework ni dépendance externe."""
import json
import mimetypes
import os
import socket
import time
from urllib.parse import parse_qs
from recherche import rechercher
from indexation import statistiques

JOURNAL_FILE = "data/journal.log"
_CACHE_DNS: dict[str, str] = {}


def nom_hote(ip: str) -> str:
    """Tente une résolution DNS inversée (souvent vide sur un réseau domestique)."""
    if ip not in _CACHE_DNS:
        try:
            _CACHE_DNS[ip] = socket.gethostbyaddr(ip)[0]
        except (socket.herror, socket.gaierror, OSError):
            _CACHE_DNS[ip] = "?"
    return _CACHE_DNS[ip]


def journaliser(environ: dict, statut: str) -> None:
    """Ajoute une ligne au journal : date, IP, hôte (si résolu), requête, statut."""
    ip = environ.get("REMOTE_ADDR", "?")
    methode = environ.get("REQUEST_METHOD", "?")
    chemin = environ.get("PATH_INFO", "?")
    requete = environ.get("QUERY_STRING", "")
    agent = environ.get("HTTP_USER_AGENT", "?")
    ligne = (
        f"{time.strftime('%Y-%m-%d %H:%M:%S')}\t{ip}\t{nom_hote(ip)}\t"
        f"{methode} {chemin}{'?' + requete if requete else ''}\t{statut}\t{agent}\n"
    )
    try:
        os.makedirs(os.path.dirname(JOURNAL_FILE), exist_ok=True)
        with open(JOURNAL_FILE, "a", encoding="utf-8") as fichier:
            fichier.write(ligne)
    except OSError:
        pass
    print(ligne, end="")

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
    repondre_original = start_response

    def start_response_journalise(statut, en_tetes, exc_info=None):
        journaliser(environ, statut)
        return repondre_original(statut, en_tetes, exc_info)

    chemin = environ.get("PATH_INFO", "/")
    if chemin == "/api/search":
        requete = parse_qs(environ.get("QUERY_STRING", "")).get("q", [""])[0]
        return reponse(start_response_journalise, rechercher(requete, FABLES, INDEX, LONGUEURS))
    if chemin == "/api/fables":
        return reponse(start_response_journalise, [{"id": f["id"], "titre": f["titre"]} for f in FABLES])
    if chemin == "/api/stats":
        return reponse(start_response_journalise, statistiques(FABLES, INDEX))
    if chemin.startswith("/api/fable/"):
        try:
            fid = int(chemin.rsplit("/", 1)[1])
            fable = next(f for f in FABLES if f["id"] == fid)
            return reponse(start_response_journalise, fable)
        except (ValueError, StopIteration):
            return reponse(start_response_journalise, {"erreur": "Fable introuvable"}, "404 Not Found")
    return servir_fichier("index.html" if chemin == "/" else chemin, start_response_journalise)
