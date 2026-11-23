"""Tests automatiques de PyFind. Lancer :  python -m unittest discover -s tests -v"""
import os
import sys
import tempfile
import unittest

# Permet d'importer les modules du projet depuis le dossier tests/.
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))

from corpus import charger_fables
from correcteur import distance_levenshtein, proposer
from index import construire_index, statistiques
from moteur import CHEMIN_DEMO, CHEMIN_MOTS_VIDES
from nettoyage import charger_mots_vides, nettoyer
from recherche import rechercher
from stockage import charger_index, sauvegarder_index

MOTS_VIDES = charger_mots_vides(CHEMIN_MOTS_VIDES)
FABLES = charger_fables(CHEMIN_DEMO)
INDEX, LONGUEURS = construire_index(FABLES, MOTS_VIDES)
ETAT = {
    "fables": {f["id"]: f for f in FABLES},
    "index": INDEX,
    "longueurs": LONGUEURS,
    "mots_vides": MOTS_VIDES,
}


def titres(requete: str) -> list[str]:
    """Titres des fables trouvées pour une requête."""
    return [r["titre"] for r in rechercher(ETAT, requete, 50)["resultats"]]


class TestCorpus(unittest.TestCase):
    """Étape 1 : découpage du livre."""

    def test_nombre_de_fables(self) -> None:
        self.assertEqual(len(FABLES), 6)

    def test_licence_et_preface_ignorees(self) -> None:
        texte = " ".join(f["texte"] for f in FABLES)
        self.assertNotIn("Gutenberg", texte)
        self.assertNotIn("PHRYGIEN", texte)

    def test_titre_sur_deux_lignes(self) -> None:
        self.assertIn("Le Loup Plaidant contre le Renard par-devant le Singe", titres("plaidant"))

    def test_apostrophe_dans_le_titre(self) -> None:
        self.assertIn("Le Loup et l'Agneau", [f["titre"] for f in FABLES])


class TestNettoyage(unittest.TestCase):
    """Étape 2 : nettoyage du texte."""

    def test_exemple_du_sujet(self) -> None:
        mots = nettoyer("Maître Corbeau, sur un arbre perché", MOTS_VIDES)
        self.assertEqual(mots, ["maitre", "corbeau", "arbre", "perche"])

    def test_ligature_et_apostrophe(self) -> None:
        self.assertEqual(nettoyer("L’ŒUF du bœuf", MOTS_VIDES), ["oeuf", "boeuf"])


class TestIndex(unittest.TestCase):
    """Étape 3 : index et statistiques."""

    def test_positions(self) -> None:
        fable = next(f for f in FABLES if f["titre"] == "Le Corbeau et le Renard")
        self.assertIn(fable["id"], INDEX["corbeau"])
        # Titre : corbeau(0) renard(1) ; trou en 2 ; texte : maitre(3) corbeau(4) ... maitre(10)
        self.assertEqual(INDEX["maitre"][fable["id"]], [3, 10])

    def test_stats(self) -> None:
        stats = statistiques(INDEX, len(FABLES))
        self.assertEqual(stats["fables"], 6)
        self.assertEqual(len(stats["top"]), 10)

    def test_sauvegarde_et_rechargement(self) -> None:
        with tempfile.TemporaryDirectory() as dossier:
            chemin = os.path.join(dossier, "index.json")
            sauvegarder_index(chemin, INDEX, LONGUEURS, "abc")
            self.assertEqual(charger_index(chemin, "abc"), (INDEX, LONGUEURS))
            self.assertIsNone(charger_index(chemin, "autre-empreinte"))
            self.assertIsNone(charger_index(os.path.join(dossier, "absent.json"), "abc"))


class TestRecherche(unittest.TestCase):
    """Étapes 5, 6 et 7 : opérateurs, classement, expressions exactes."""

    def test_et(self) -> None:
        self.assertEqual(titres("loup ET agneau"), ["Le Loup et l'Agneau"])

    def test_ou(self) -> None:
        self.assertEqual(len(titres("corbeau OU cigogne")), 2)

    def test_sauf(self) -> None:
        self.assertNotIn("Le Loup et l'Agneau", titres("loup SAUF chiens"))
        self.assertEqual(len(titres("renard SAUF corbeau")), 2)

    def test_classement_decroissant(self) -> None:
        scores = [r["score"] for r in rechercher(ETAT, "loup OU renard")["resultats"]]
        self.assertEqual(scores, sorted(scores, reverse=True))

    def test_extrait_en_majuscules(self) -> None:
        extrait = rechercher(ETAT, "agneau")["resultats"][0]["extrait"]
        self.assertIn("AGNEAU", extrait)

    def test_expression_exacte(self) -> None:
        self.assertEqual(titres('"maitre corbeau"'), ["Le Corbeau et le Renard"])
        self.assertEqual(titres('"corbeau maitre"'), [])  # mauvais ordre

    def test_tout_en_minuscules_ou_avec_accents(self) -> None:
        self.assertEqual(titres("THÉMIS"), titres("themis"))


class TestCorrecteur(unittest.TestCase):
    """Étape 8 : distance de Levenshtein et suggestions."""

    def test_distance(self) -> None:
        self.assertEqual(distance_levenshtein("renar", "renard"), 1)
        self.assertEqual(distance_levenshtein("chat", "chat"), 0)
        self.assertEqual(distance_levenshtein("", "abc"), 3)
        self.assertEqual(distance_levenshtein("kitten", "sitting"), 3)

    def test_suggestion(self) -> None:
        self.assertEqual(proposer("renar", INDEX), "renard")
        self.assertIsNone(proposer("zzzzzzzz", INDEX))

    def test_vouliez_vous_dire(self) -> None:
        reponse = rechercher(ETAT, "renar")
        self.assertEqual(reponse["total"], 0)
        self.assertEqual(reponse["requete_corrigee"], "renard")


class TestRobustesse(unittest.TestCase):
    """Le programme ne doit jamais planter, quoi que l'utilisateur tape."""

    def test_saisies_bizarres(self) -> None:
        bizarres = ["", "   ", "ET", "loup ET", "OU loup", "loup ET OU renard", '"loup',
                    "le la les", "!!!???", "x" * 500, "\x00\x01", "SELECT * FROM fables;",
                    "<script>alert(1)</script>", "日本語", "🐺", '""', "((()))", None, 42]
        for saisie in bizarres:
            reponse = rechercher(ETAT, saisie)  # type: ignore[arg-type]
            self.assertIn("ok", reponse)
            if not reponse["ok"]:
                self.assertTrue(reponse["erreur"])

    def test_message_clair(self) -> None:
        self.assertIn("suivi d'un mot", rechercher(ETAT, "loup ET")["erreur"])
        self.assertIn("Guillemet", rechercher(ETAT, '"loup')["erreur"])


if __name__ == "__main__":
    unittest.main()
