"""Vérifie les règles du sujet : pas de classe, bibliothèques standard seulement,
docstring + annotations de type + moins de 30 lignes pour chaque fonction.

Lancer :  python verifier_regles.py
"""
import ast
import glob
import os
import sys

LIGNES_MAX = 30
DOSSIER = os.path.dirname(os.path.abspath(__file__))


def lire_arbre(chemin: str) -> ast.Module:
    """Lit un fichier Python et renvoie son arbre syntaxique."""
    with open(chemin, encoding="utf-8") as fichier:
        return ast.parse(fichier.read(), filename=chemin)


def verifier_fonction(fonction: ast.FunctionDef) -> list[str]:
    """Liste les problèmes d'une fonction (docstring, annotations, longueur)."""
    problemes = []
    if ast.get_docstring(fonction) is None:
        problemes.append("pas de docstring")
    arguments = fonction.args.args + fonction.args.kwonlyargs
    if any(arg.annotation is None for arg in arguments):
        problemes.append("argument sans annotation de type")
    if fonction.returns is None:
        problemes.append("pas d'annotation de retour")
    longueur = (fonction.end_lineno or fonction.lineno) - fonction.lineno + 1
    if longueur >= LIGNES_MAX:
        problemes.append(f"{longueur} lignes (maximum {LIGNES_MAX - 1})")
    return problemes


def verifier_imports(noeud: ast.AST, modules_locaux: set[str]) -> list[str]:
    """Liste les imports qui ne sont ni standard ni locaux."""
    problemes = []
    if isinstance(noeud, ast.Import):
        noms = [alias.name.split(".")[0] for alias in noeud.names]
    elif isinstance(noeud, ast.ImportFrom) and noeud.module:
        noms = [noeud.module.split(".")[0]]
    else:
        return []
    for nom in noms:
        if nom not in sys.stdlib_module_names and nom not in modules_locaux:
            problemes.append(f"import externe : {nom}")
    return problemes


def verifier_fichier(chemin: str, modules_locaux: set[str]) -> list[str]:
    """Vérifie toutes les règles sur un fichier. Renvoie la liste des problèmes."""
    problemes = []
    for noeud in ast.walk(lire_arbre(chemin)):
        if isinstance(noeud, ast.ClassDef):
            problemes.append(f"ligne {noeud.lineno} : classe interdite ({noeud.name})")
        if isinstance(noeud, (ast.FunctionDef, ast.AsyncFunctionDef)):
            for probleme in verifier_fonction(noeud):
                problemes.append(f"ligne {noeud.lineno} : {noeud.name}() {probleme}")
        problemes.extend(verifier_imports(noeud, modules_locaux))
    return problemes


def main() -> None:
    """Vérifie tous les modules du projet et affiche un bilan."""
    fichiers = sorted(glob.glob(os.path.join(DOSSIER, "*.py")))
    modules = {os.path.basename(f)[:-3] for f in fichiers}
    total = 0
    for chemin in fichiers:
        nom = os.path.basename(chemin)
        problemes = verifier_fichier(chemin, modules)
        total += len(problemes)
        print(f"{'OK ' if not problemes else 'KO '} {nom}")
        for probleme in problemes:
            print(f"      - {probleme}")
    print(f"\n{len(fichiers)} fichiers vérifiés, {total} problème(s).")
    sys.exit(1 if total else 0)


if __name__ == "__main__":
    main()
