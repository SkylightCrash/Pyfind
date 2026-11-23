"""PyFind : un mini Google pour les Fables de La Fontaine (version terminal).

Lancer :  python main.py
"""
import sys

from index import statistiques
from moteur import initialiser
from recherche import rechercher

AIDE = """Comment chercher :
  loup ET agneau       les fables qui contiennent les DEUX mots
  renard OU corbeau    les fables qui contiennent AU MOINS UN des deux mots
  loup SAUF chien      les fables avec « loup » mais SANS « chien »
  "maitre corbeau"     l'expression exacte (mots côte à côte, dans cet ordre)
Commandes :
  stats      nombre de fables, de mots différents, 10 mots les plus fréquents
  :lire N    affiche la fable numéro N en entier
  :aide      affiche ce message
  :quitter   quitte le programme"""


def afficher_stats(etat: dict) -> None:
    """Affiche le nombre de fables, de mots différents et les 10 mots les plus fréquents."""
    stats = statistiques(etat["index"], len(etat["fables"]))
    print(f"  Fables : {stats['fables']}")
    print(f"  Mots différents : {stats['mots_differents']}")
    print("  Les 10 mots les plus fréquents :")
    for rang, (mot, nombre) in enumerate(stats["top"], start=1):
        print(f"    {rang:>2}. {mot:<15} {nombre}")


def afficher_suggestion(reponse: dict) -> None:
    """Affiche « Vouliez-vous dire : ... ? » quand un mot est inconnu."""
    if reponse["suggestions"]:
        propositions = ", ".join(s["propose"] for s in reponse["suggestions"])
        print(f"  Vouliez-vous dire : {propositions} ?")


def afficher_resultats(reponse: dict) -> None:
    """Affiche les résultats d'une recherche (ou le message d'erreur)."""
    if not reponse["ok"]:
        print(f"  ! {reponse['erreur']}")
        return
    if reponse["ignores"]:
        print(f"  (mots ignorés car trop courants : {', '.join(reponse['ignores'])})")
    if not reponse["resultats"]:
        print("  Aucun résultat.")
    for rang, resultat in enumerate(reponse["resultats"], start=1):
        print(f"  {rang}. {resultat['titre']:<42} score {resultat['score']:.3f}")
        print(f"       {resultat['extrait']}")
    afficher_suggestion(reponse)
    if reponse["resultats"]:
        millisecondes = reponse["duree"] * 1000
        print(f"  {reponse['total']} fable(s) trouvée(s) en {millisecondes:.1f} ms.")


def afficher_fable(etat: dict, numero: str) -> None:
    """Affiche une fable en entier (commande :lire N)."""
    if not numero.isdigit() or int(numero) not in etat["fables"]:
        print(f"  ! Tapez :lire suivi d'un numéro entre 1 et {len(etat['fables'])}.")
        return
    fable = etat["fables"][int(numero)]
    print(f"\n  {fable['titre']}\n")
    for ligne in fable["texte"].splitlines():
        print(f"    {ligne}")


def executer(etat: dict, saisie: str) -> bool:
    """Exécute une saisie de l'utilisateur. Renvoie False pour quitter."""
    commande = saisie.strip()
    if commande.lower() == ":quitter":
        return False
    if commande.lower() in ("stats", ":stats"):
        afficher_stats(etat)
    elif commande.lower() == ":aide":
        print(AIDE)
    elif commande.lower().startswith(":lire"):
        afficher_fable(etat, commande[5:].strip())
    elif commande:
        afficher_resultats(rechercher(etat, commande))
    return True


def boucle(etat: dict) -> None:
    """Menu : tourne en boucle jusqu'à :quitter (ou Ctrl+C / Ctrl+D)."""
    print("\nPyFind - tapez une recherche, :aide pour l'aide, :quitter pour sortir.")
    while True:
        try:
            saisie = input("\n> ")
            if not executer(etat, saisie):
                break
        except (EOFError, KeyboardInterrupt):
            print()
            break
        except Exception:  # noqa: BLE001  # pylint: disable=broad-exception-caught
            print("  ! Une erreur inattendue est survenue, essayez autre chose.")
    print("Au revoir !")


def main() -> None:
    """Prépare le moteur puis lance le menu."""
    try:
        etat = initialiser()
    except (OSError, ValueError) as erreur:
        print(f"Impossible de démarrer : {erreur}")
        sys.exit(1)
    boucle(etat)


if __name__ == "__main__":
    main()
