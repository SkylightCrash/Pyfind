"""Point d'entrée PyFind : prépare les données et démarre le site local."""
from wsgiref.simple_server import make_server
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


def lancer_serveur() -> None:
    """Démarre le serveur local sur le port 8000."""
    initialiser()
    adresse = "http://127.0.0.1:8000"
    print(f"PyFind est disponible sur {adresse} — Ctrl+C pour arrêter.")
    try:
        webbrowser.open(adresse)
    except Exception:
        pass
    with make_server("127.0.0.1", 8000, application) as serveur:
        serveur.serve_forever()


if __name__ == "__main__":
    lancer_serveur()
