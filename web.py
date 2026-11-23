"""Interface web de PyFind.

Serveur WSGI de la bibliothèque standard : une simple fonction suffit,
pas besoin de classe ni de bibliothèque à installer.

Lancer :  python web.py [port]      puis ouvrir http://127.0.0.1:8000
"""
import json
import os
import sys
import webbrowser
from collections.abc import Callable
from typing import Any
from urllib.parse import parse_qs
from wsgiref.simple_server import make_server

from index import statistiques
from moteur import BASE, initialiser
from recherche import rechercher

CHEMIN_PAGE = os.path.join(BASE, "web", "index.html")
PORT_DEFAUT = 8000


def lire_page() -> bytes:
    """Lit la page d'accueil (web/index.html)."""
    try:
        with open(CHEMIN_PAGE, "rb") as fichier:
            return fichier.read()
    except OSError:
        return b"<h1>PyFind</h1><p>Fichier web/index.html introuvable.</p>"


def repondre(demarrer: Callable, statut: str, type_mime: str, corps: bytes) -> list[bytes]:
    """Envoie une réponse HTTP (en-têtes + corps)."""
    demarrer(statut, [
        ("Content-Type", type_mime),
        ("Content-Length", str(len(corps))),
        ("Cache-Control", "no-store"),
    ])
    return [corps]


def repondre_json(demarrer: Callable, donnees: Any, statut: str = "200 OK") -> list[bytes]:
    """Envoie des données au format JSON."""
    corps = json.dumps(donnees, ensure_ascii=False).encode("utf-8")
    return repondre(demarrer, statut, "application/json; charset=utf-8", corps)


def entier_borne(texte: str, defaut: int, minimum: int, maximum: int) -> int:
    """Convertit un texte en entier compris entre minimum et maximum."""
    try:
        valeur = int(texte)
    except ValueError:
        return defaut
    return max(minimum, min(maximum, valeur))


def api_recherche(etat: dict, params: dict) -> dict:
    """/api/recherche?q=...&limite=5"""
    requete = params.get("q", [""])[0]
    limite = entier_borne(params.get("limite", ["5"])[0], 5, 1, 50)
    return rechercher(etat, requete, limite)


def api_stats(etat: dict) -> dict:
    """/api/stats : chiffres du livre et temps de préparation."""
    stats = statistiques(etat["index"], len(etat["fables"]))
    return {
        "fables": stats["fables"],
        "mots_differents": stats["mots_differents"],
        "top": [{"mot": mot, "occurrences": nombre} for mot, nombre in stats["top"]],
        "temps": etat["temps"],
        "origine_index": etat["origine_index"],
        "demo": etat["demo"],
    }


def api_fable(etat: dict, params: dict) -> tuple[dict, str]:
    """/api/fable?id=12 : une fable en entier."""
    numero = entier_borne(params.get("id", ["0"])[0], 0, 0, 10**9)
    fable = etat["fables"].get(numero)
    if fable is None:
        return {"erreur": "Cette fable n'existe pas."}, "404 Not Found"
    return {"id": fable["id"], "titre": fable["titre"], "texte": fable["texte"]}, "200 OK"


def router(etat: dict, chemin: str, params: dict) -> tuple[dict, str]:
    """Choisit la bonne fonction selon l'adresse demandée."""
    if chemin == "/api/recherche":
        return api_recherche(etat, params), "200 OK"
    if chemin == "/api/stats":
        return api_stats(etat), "200 OK"
    if chemin == "/api/fable":
        return api_fable(etat, params)
    return {"erreur": "Page introuvable."}, "404 Not Found"


def creer_application(etat: dict) -> Callable:
    """Construit l'application WSGI qui répond aux requêtes du navigateur."""
    page = lire_page()

    def application(environ: dict, demarrer: Callable) -> list[bytes]:
        """Reçoit une requête HTTP et renvoie la réponse (ne plante jamais)."""
        try:
            if environ["REQUEST_METHOD"] != "GET":
                return repondre_json(demarrer, {"erreur": "Méthode non autorisée."},
                                     "405 Method Not Allowed")
            chemin = environ.get("PATH_INFO", "/")
            if chemin in ("/", "/index.html"):
                return repondre(demarrer, "200 OK", "text/html; charset=utf-8", page)
            params = parse_qs(environ.get("QUERY_STRING", ""))
            donnees, statut = router(etat, chemin, params)
            return repondre_json(demarrer, donnees, statut)
        except Exception:  # noqa: BLE001  # pylint: disable=broad-exception-caught
            return repondre_json(demarrer, {"erreur": "Erreur interne du serveur."},
                                 "500 Internal Server Error")

    return application


def lancer_serveur(etat: dict, port: int) -> None:
    """Démarre le serveur et ouvre le navigateur."""
    try:
        serveur = make_server("127.0.0.1", port, creer_application(etat))
    except OSError:
        print(f"Impossible d'utiliser le port {port} (déjà pris ?). Essayez : python web.py 8080")
        sys.exit(1)
    adresse = f"http://127.0.0.1:{port}"
    print(f"\nPyFind est prêt : {adresse}   (Ctrl+C pour arrêter)")
    webbrowser.open(adresse)
    try:
        serveur.serve_forever()
    except KeyboardInterrupt:
        print("\nServeur arrêté.")
    finally:
        serveur.server_close()


def main() -> None:
    """Prépare le moteur puis lance le serveur web."""
    port = int(sys.argv[1]) if len(sys.argv) > 1 and sys.argv[1].isdigit() else PORT_DEFAUT
    try:
        etat = initialiser()
    except (OSError, ValueError) as erreur:
        print(f"Impossible de démarrer : {erreur}")
        sys.exit(1)
    lancer_serveur(etat, port)


if __name__ == "__main__":
    main()
