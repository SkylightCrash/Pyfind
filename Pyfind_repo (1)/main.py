"""Point d'entrée PyFind : prépare les données et démarre le site local."""
import socket
from socketserver import ThreadingMixIn
from wsgiref.simple_server import WSGIRequestHandler, WSGIServer, make_server
from corpus import charger_corpus
from indexation import construire_index, charger_index, sauvegarder_index
from webapp import application
import webbrowser


def initialiser() -> None:
    """Charge les fables et prépare l'index de recherche."""
    fables = charger_corpus()
    donnees = charger_index()
    if donnees:
        index, longueurs = donnees
    else:
        index, longueurs = construire_index(fables)
        sauvegarder_index(index, longueurs)
    from webapp import FABLES, INDEX, LONGUEURS
    FABLES.extend(fables)
    INDEX.update(index)
    LONGUEURS.update(longueurs)


HOTE = "0.0.0.0"  # écoute sur toutes les interfaces : accessible depuis le réseau local
PORT = 8000


class ServeurMultiClient(ThreadingMixIn, WSGIServer):
    """Serveur WSGI qui traite chaque connexion dans son propre thread."""
    daemon_threads = True


class Requete(WSGIRequestHandler):
    def log_message(self, format, *args):
        pass  # évite de noyer le terminal sous les logs de chaque requête


def adresse_reseau() -> str | None:
    """Trouve l'adresse IP locale de ce PC sur le réseau (sans envoyer de données)."""
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as sock:
            sock.connect(("10.255.255.255", 1))
            return sock.getsockname()[0]
    except OSError:
        return None


def lancer_serveur() -> None:
    """Démarre le serveur, accessible en local et depuis le réseau."""
    initialiser()
    try:
        serveur = make_server(HOTE, PORT, application,
                              server_class=ServeurMultiClient,
                              handler_class=Requete)
    except OSError as erreur:
        raise SystemExit(f"Impossible de démarrer sur le port {PORT} : {erreur}")
    local = f"http://127.0.0.1:{PORT}"
    reseau = adresse_reseau()
    print("PyFind est lancé — Ctrl+C pour arrêter.")
    print(f"  Sur ce PC          : {local}")
    if reseau:
        print(f"  Sur le réseau local : http://{reseau}:{PORT}")
    else:
        print("  Réseau local : adresse IP introuvable (êtes-vous connecté ?)")
    try:
        webbrowser.open(local)
    except Exception:
        pass
    with serveur:
        try:
            serveur.serve_forever()
        except KeyboardInterrupt:
            print("\nServeur arrêté.")


if __name__ == "__main__":
    lancer_serveur()
