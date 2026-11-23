# PyFind — Moteur de recherche des Fables de La Fontaine

PyFind est un moteur de recherche écrit en Python qui permet de retrouver des fables à partir de mots, de plusieurs critères ou d'une expression. Les résultats sont classés par pertinence grâce à un score TF-IDF.

Le projet propose deux façons d'utiliser le moteur :
- **une interface en ligne de commande** avec `main.py` ;
- **une interface web locale** avec `web.py` et la page `web/index.html`.

## Sommaire

- [Fonctionnalités](#fonctionnalités)
- [Prérequis](#prérequis)
- [Installation et lancement](#installation-et-lancement)
- [Utilisation](#utilisation)
- [Fonctionnement technique](#fonctionnement-technique)
- [Organisation des fichiers](#organisation-des-fichiers)
- [Tests et vérifications](#tests-et-vérifications)
- [Limites connues](#limites-connues)

## Fonctionnalités

- Recherche dans les Fables de La Fontaine.
- Opérateurs `ET`, `OU` et `SAUF`.
- Recherche d'expression entre guillemets.
- Classement des résultats avec TF-IDF.
- Affichage d'un extrait avec les termes recherchés mis en évidence.
- Suggestions de correction en cas de faute de frappe, avec la distance de Levenshtein.
- Statistiques sur le corpus et les mots indexés.
- Sauvegarde de l'index au format JSON pour éviter de le reconstruire à chaque lancement.
- Interface terminal et interface web accessibles localement.

## Prérequis

- Python **3.10 ou une version ultérieure**.
- Aucune dépendance Python externe n'est nécessaire : le programme utilise la bibliothèque standard.
- Une connexion Internet est nécessaire au premier lancement si le corpus complet doit être téléchargé automatiquement.

## Installation et lancement

### 1. Récupérer le projet

Téléchargez ou clonez le dépôt, puis ouvrez un terminal dans le dossier `pyfind/`, là où se trouvent `main.py` et `web.py`.

### 2. Lancer la version terminal

```bash
python main.py
```

Sous Windows, si la commande `python` n'est pas reconnue, essayez :

```powershell
py main.py
```

### 3. Lancer l'interface web

```bash
python web.py
```

Le serveur démarre sur `http://127.0.0.1:8000` et le navigateur est ouvert automatiquement. Pour choisir un autre port :

```bash
python web.py 8080
```

L'interface est hébergée localement sur la machine : le serveur écoute sur `127.0.0.1`.

### Corpus utilisé

Au premier démarrage, PyFind cherche le fichier `data/fables.txt`. S'il n'existe pas, le programme tente de télécharger le texte depuis le Projet Gutenberg :

<https://www.gutenberg.org/ebooks/56327>

Si le téléchargement échoue, PyFind utilise automatiquement `data/fables_demo.txt`, qui contient un petit corpus de démonstration. Pour utiliser le corpus complet, téléchargez la version **Plain Text UTF-8** du livre et placez-la ici :

```text
data/fables.txt
```

Le dossier `data/` est créé automatiquement lors de la sauvegarde de l'index si nécessaire.

## Utilisation

### Recherche

Les opérateurs peuvent être écrits en majuscules ou en minuscules. Les exemples suivants sont à saisir dans le terminal ou dans le champ de recherche de l'interface web.

| Requête | Résultat attendu |
|---|---|
| `loup ET agneau` | Fables contenant les deux termes. |
| `renard OU corbeau` | Fables contenant au moins l'un des deux termes. |
| `loup SAUF chien` | Fables contenant « loup », mais pas « chien ». |
| `"maitre corbeau"` | Recherche de l'expression dans cet ordre, sur les mots indexés. |
| `renar` | Peut proposer « renard » si le mot est suffisamment proche. |

Règles de recherche :

- Deux termes sans opérateur sont interprétés comme une opération `ET` : `loup agneau` équivaut à `loup ET agneau`.
- Les opérateurs sont évalués de gauche à droite. Par exemple, `loup ET agneau SAUF chien` correspond à `(loup ET agneau) SAUF chien`.
- Les majuscules et les accents ne sont pas pris en compte : `THÉMIS` et `themis` sont équivalents.
- Les mots vides définis dans `mots_vides.txt` sont ignorés pendant l'indexation et la recherche.
- Les expressions exactes portent sur les mots après nettoyage : les mots vides étant retirés, ils ne sont pas pris en compte dans la proximité des mots.

### Commandes du terminal

| Commande | Action |
|---|---|
| `stats` ou `:stats` | Affiche le nombre de fables, le nombre de mots différents et les dix mots les plus fréquents. |
| `:lire N` | Affiche intégralement la fable numéro `N`. |
| `:aide` | Affiche l'aide et la syntaxe des recherches. |
| `:quitter` | Ferme le programme. |

### API locale de l'interface web

L'interface web communique avec le serveur Python à l'aide de routes HTTP GET :

| Route | Rôle |
|---|---|
| `/` ou `/index.html` | Renvoie la page de l'interface. |
| `/api/recherche?q=...&limite=5` | Effectue une recherche. La limite est comprise entre 1 et 50. |
| `/api/stats` | Renvoie les statistiques et les informations de préparation du moteur. |
| `/api/fable?id=12` | Renvoie le contenu d'une fable. |

Les réponses de l'API sont au format JSON.

## Fonctionnement technique

Le traitement se déroule en deux grandes phases.

### 1. Préparation au démarrage

1. `corpus.py` lit le texte et le découpe en fables.
2. `nettoyage.py` normalise les mots et retire les mots vides.
3. `index.py` construit un index inversé associant chaque mot aux identifiants des fables et à ses positions.
4. `stockage.py` enregistre l'index dans `data/index.json`.

Lors des démarrages suivants, le programme tente de recharger l'index existant. Une empreinte SHA-256 du corpus et du fichier `mots_vides.txt` permet de détecter si les données utilisées pour construire l'index ont changé. Dans ce cas, l'index est reconstruit.

### 2. Traitement d'une recherche

1. `recherche.py` analyse la requête et applique les opérateurs logiques.
2. Le moteur consulte l'index pour identifier les fables correspondantes.
3. Les résultats sont classés à l'aide du score TF-IDF.
4. Un extrait est préparé et les mots recherchés sont mis en évidence.
5. Si un terme ne donne aucun résultat, `correcteur.py` peut proposer un terme proche.

Le titre est également pris en compte dans l'index. Une position est laissée entre les mots du titre et ceux du texte afin qu'une expression ne puisse pas être reconnue en chevauchant artificiellement ces deux parties.

## Organisation des fichiers

```text
pyfind/
├── main.py                 # Point d'entrée et interface terminal
├── moteur.py               # Préparation et initialisation du moteur
├── corpus.py               # Lecture, téléchargement et découpage du corpus
├── nettoyage.py            # Normalisation et suppression des mots vides
├── index.py                # Construction de l'index inversé et statistiques
├── stockage.py             # Sauvegarde, chargement et empreintes
├── recherche.py            # Analyse des requêtes, recherche et classement
├── correcteur.py           # Suggestions de correction orthographique
├── web.py                  # Serveur web local et API HTTP
├── web/
│   └── index.html           # Interface web
├── data/
│   ├── fables_demo.txt      # Petit corpus fourni pour la démonstration
│   ├── fables.txt           # Corpus complet (téléchargé ou ajouté manuellement)
│   └── index.json           # Index généré automatiquement
├── tests/
│   └── test_pyfind.py       # Tests automatisés
├── mots_vides.txt           # Liste des mots ignorés
├── verifier_regles.py       # Vérification des contraintes du projet
└── README.md                # Documentation
```

`data/fables.txt` et `data/index.json` sont générés ou ajoutés à l'exécution : ils ne sont pas nécessaires dans l'archive initiale pour lancer la démonstration, car le corpus de démonstration est fourni.

## Tests et vérifications

Depuis le dossier `pyfind/`, exécutez les tests automatisés :

```bash
python -m unittest discover -s tests -v
```

Le projet contient actuellement **21 tests** couvrant notamment le découpage du corpus, le nettoyage, l'indexation, les recherches, les corrections et les erreurs de saisie.

Le script de vérification des règles du projet se lance avec :

```bash
python verifier_regles.py
```

Il contrôle notamment l'absence de classes, l'utilisation de la bibliothèque standard, les annotations de types, les docstrings et la longueur des fonctions.

Pour lancer une vérification complémentaire du style avec Ruff (outil facultatif, à installer séparément) :

```bash
python -m pip install ruff
ruff check .
```

## Limites connues

- Les variantes singulier/pluriel ne sont pas automatiquement rapprochées : `loup` et `loups` sont deux termes distincts.
- Les parenthèses ne sont pas prises en charge dans les requêtes.
- Les expressions exactes sont évaluées après suppression des mots vides ; les mots ignorés ne comptent donc pas dans les positions comparées.
- Le corpus de démonstration ne contient qu'une sélection de fables ; les résultats complets nécessitent le corpus intégral.

---

**Projet réalisé dans le cadre du Bachelor 1 à l'ESAIP.**
