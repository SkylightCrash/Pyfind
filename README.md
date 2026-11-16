# PyFind — Les Fables, retrouvées

PyFind est un mini moteur de recherche en Python sur les Fables de Jean de La Fontaine, avec une interface web locale.

## Lancer le projet

Prérequis : Python 3.10 ou plus récent. Aucune bibliothèque externe n'est nécessaire.

```bash
python main.py
```

Au premier lancement, PyFind télécharge le texte Gutenberg, prépare le corpus et construit l'index. Le navigateur s'ouvre ensuite sur http://127.0.0.1:8000.

## Recherches possibles

- `loup ET agneau` : fables contenant les deux mots.
- `renard OU corbeau` : fables contenant au moins un des mots.
- `loup SAUF chien` : fables contenant loup sans chien.
- `"maitre corbeau"` : expression exacte.
- Une faute comme `renar` peut déclencher des suggestions.

Les résultats sont classés avec TF-IDF. La page d'accueil présente également les statistiques du corpus.

## Architecture

- `corpus.py` : récupération et découpage des fables.
- `nettoyage.py` : normalisation et mots vides.
- `indexation.py` : index inversé, sauvegarde et statistiques.
- `recherche.py` : opérateurs booléens, expressions et TF-IDF.
- `correcteur.py` : distance de Levenshtein.
- `webapp.py` : serveur WSGI et API JSON.
- `main.py` : initialisation et lancement.
- `static/` : interface HTML, CSS et JavaScript.
- `data/` : fichiers générés au premier lancement.

## API locale

- `GET /api/search?q=loup%20ET%20agneau`
- `GET /api/stats`
- `GET /api/fable/1`

## Source des textes

Project Gutenberg, ebook 56327 : https://www.gutenberg.org/ebooks/56327

## À noter

Le premier lancement nécessite une connexion Internet pour récupérer le corpus. Les lancements suivants utilisent les fichiers locaux `data/fables.json` et `data/index.json`.
