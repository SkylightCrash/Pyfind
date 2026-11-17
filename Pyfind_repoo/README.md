# PyFind — Les Fables, retrouvées

PyFind est un mini moteur de recherche en Python sur les Fables de Jean de La Fontaine, avec une interface web locale.

## Lancer le projet

Prérequis : Python 3.10 ou plus récent. Aucune bibliothèque externe n'est nécessaire.

```bash
python main.py
```

Au premier lancement, PyFind lit le texte local `data/fables_gutenberg.txt`, découpe les fables et construit l'index. Aucune connexion Internet n'est nécessaire. Le navigateur s'ouvre ensuite sur http://127.0.0.1:8000.

## Partager sur le réseau local

Le serveur écoute sur toutes les interfaces (`0.0.0.0`, port 8000). Au lancement, le terminal affiche l'adresse réseau du PC, par exemple `http://192.168.1.42:8000` : toute personne connectée au même réseau (Wi-Fi ou câble) peut l'ouvrir dans son navigateur.

- Le PC doit rester allumé et `python main.py` doit tourner.
- Au premier lancement, le pare-feu Windows peut demander d'autoriser Python : choisir « Réseaux privés ».
- À n'utiliser que sur un réseau de confiance : il n'y a ni mot de passe ni chiffrement (HTTP). Pour rester en local seulement, remplacer `HOTE = "0.0.0.0"` par `"127.0.0.1"` dans `main.py`.

## Recherches possibles

- `loup ET agneau` : fables contenant les deux mots.
- `renard OU corbeau` : fables contenant au moins un des mots.
- `loup SAUF chien` : fables contenant loup sans chien.
- `"maitre corbeau"` : expression exacte.
- Une faute comme `renar` peut déclencher des suggestions.

Les résultats sont classés avec TF-IDF. La section « Parcourir les fables » liste tout le recueil (avec filtre par titre) et ouvre chaque fable dans un lecteur : flèches ← → pour naviguer, Échap pour fermer. La page d'accueil présente également les statistiques du corpus.

## Architecture

- `corpus.py` : lecture du fichier texte local et découpage des fables.
- `nettoyage.py` : normalisation et mots vides.
- `indexation.py` : index inversé, sauvegarde et statistiques.
- `recherche.py` : opérateurs booléens, expressions et TF-IDF.
- `correcteur.py` : distance de Levenshtein.
- `webapp.py` : serveur WSGI et API JSON.
- `main.py` : initialisation et lancement.
- `static/` : interface HTML, CSS et JavaScript.
- `data/fables_gutenberg.txt` : texte source (Project Gutenberg).
- `data/fables.json` et `data/index.json` : fichiers générés au premier lancement.

## API locale

- `GET /api/search?q=loup%20ET%20agneau`
- `GET /api/fables` : liste de toutes les fables (id et titre).
- `GET /api/stats`
- `GET /api/fable/1`

## Source des textes

Project Gutenberg, ebook 56327 : https://www.gutenberg.org/ebooks/56327

## À noter

Le corpus compte 243 entrées : les 240 fables numérotées, les deux Épilogues et l'Épitaphe de La Fontaine. Les notes de bas de page de l'éditeur sont retirées. Si `data/fables_gutenberg.txt` est modifié, le corpus et l'index sont reconstruits automatiquement au lancement suivant.
