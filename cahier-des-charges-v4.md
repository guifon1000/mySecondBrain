# Cahier des charges v4 — la rentrée (brouillon)

*v4 garde intacte la doctrine v3 (le vault source unique, l'agent ne pense
pas, l'humain signe) et lui ajoute la couche qui manquait : le code
généré redevient visitable. État : brouillon issu de la discussion
d'octobre.*

## Le problème : le coût de rentrée

Presque tout le code est généré par IA, y compris le nôtre. On n'ouvre
même plus les fichiers ; quand il faut s'y remettre, c'est difficile.
Le code généré est une ville qu'on habite sans connaître : on y revient
après des semaines et il faut se rappeler où sont les rues.

La v3 pointait déjà vers la sortie (`incarnation:`, liens `pdf:` et
`code:` cliquables) mais restait au niveau du document : elle ouvre la
porte de l'immeuble, pas la bonne page du bon chapitre.

## La réponse : chantier → session → ordonnance

Trois échelles, un seul flux de travail.

### Le chantier — le contexte qui vit dans le vault

Fiche `type: chantier`, `author: user`, dans `myVault/Chantiers/`.

- **Remplace la casquette** : c'est le même rôle (un contexte de travail
  qui éclaire la carte) rendu concret. Une question de fond, des fiches
  reliées, un projet associé (`projet: [[hex]]`).
- **Un seul ouvert à la fois.** Il peut rester ouvert des semaines.
- **Éclairage exact, plus statistique** : le chantier éclaire les fiches
  qu'il touche (liens `lie:`), pas celles qui ressemblent à son domaine.
  Chantier fermé = carte éteinte ; pas de chantier = carte entière.
- La fermeture d'un chantier est une récolte : les fiches élevées pendant
  les sessions restent, le chantier se ferme en laissant le vault plus
  riche, pas des décombres.

### La session — la passe de travail

Le moment où l'on discute avec l'agent (pi/Telegram) devant les
matériaux. La discussion **reste où elle est** — pas de chat dans la
page en v4.0 ; la session est l'objet partagé qu'on a sous les yeux.

Pendant la session, l'agent **cueille** : il sélectionne les passages
pertinents (pages PDF, plages de code), les justifie en une ligne, et
dresse l'établi. Cueillir n'est pas penser : c'est le geste du
réceptionniste qui prépare le chantier.

### L'ordonnance — ce que la session produit

Un **markdown** avec des blocs fence typés, lisible par un humain,
parsable par un agent de codage :

    ```pdf
    doc=Ali et al. 2017 page=14
    « la décomposition en blocs hexaèdres repose sur la MIT »
    ```

    ```code
    depot=rincewind chemin=src/modelers/maison.rs lignes=220-260
    → creer_maison() : c'est ici que l'entraxe est figé
    ```

Cycle de vie (le « liens à deux mains » transposé) :

1. **préparée** — par l'agent, pendant la session ; vivante hors du vault
   (`data/sessions/`), artefact dérivé, `author: agent`.
2. **visitée & signée** — par l'humain. La signature est l'acte décisif :
   l'agent de codage ne reçoit que ce qui a été vu et validé.
   L'ordonnance est éditable avant signature (retirer un passage
   hors-sujet, ajuster une consigne).
3. **confiée** — le fichier part vivre dans le dépôt du projet
   (`<repo>/sessions/AAAA-MM-JJ — titre.md`), committé : traçabilité
   durable, l'agent de codage le lit à son emplacement naturel.

## Les widgets — extensible par construction

Chaque type de bloc = une entrée de registre : une fonction `render`
côté page, un résolveur côté serveur (valide le chemin, sert le
contenu). Ajouter un widget = une entrée, rien d'autre.

- **`pdf`** — la carte montre la citation ; le clic ouvre le PDF à la
  page. (Highlight textuel dans la page : v4.2, si l'usage le réclame.)
- **`code`** — le fichier **entier** servi en lecture seule, coloré
  syntaxiquement ; les lignes hors plages en opacité ~20 %, les plages
  pertinentes marquées, auto-position sur la première. Pour un fichier
  de 2000 lignes : la structure en gris, le passage en vie. **Pas de
  VS Code.**
- **`fiche`** — la carte d'une fiche du vault (titre, corps, liens).
- **`capture`** — une image fichée.
- Prévus en v4.2 : extraits de wiki, cartes Galaxie, tout ce que
  l'usage réclamera.

## Le notebook — la spec exécutable (v4.1)

Le prototype d'une session peut prendre la forme d'un `ipynb` :

- l'agent écrit les cellules (validation numérique, cas limites,
  contre-exemple) et les exécute à la préparation ;
- les sorties figées deviennent le **critère de recette** pour l'agent
  de codage ;
- si le projet n'est pas en Python, **c'est l'agent de codage qui
  convertit** le prototype dans le langage du projet — on ne construit
  jamais de convertisseur nous-mêmes. On livre l'ipynb + une ligne de
  consigne dans l'ordonnance.

## La règle d'or : l'agent paie en traçabilité

Toute intervention de l'agent dans un dépôt laisse derrière elle une
ordonnance « ce qu'il faut re-visiter » : ce qu'il a changé, où, pourquoi,
avec les passages. La rentrée devient un geste bon marché. C'est
l'antidote direct au problème de départ.

## La stack : rien de neuf

Pas de RAG, pas d'IA embarquée dans l'app. Tout existe :

- FTS5 sur les pages PDF (68 000 pages), fiches, `incarnation:`,
  liens `pdf:`/`code:` de la v3 ;
- la sélection = l'agent avec ces index (pi/Telegram) ;
- l'app reste bête : elle affiche, elle ne pense pas.

## Ce qui disparaît

- **Les casquettes** : le mot et le mécanisme. Les 8 fiches se retirent ;
  la casquette active (Menuisier) devient le premier chantier. Le champ
  `domaines:` reste (utile au climat de la carte), l'éclairage
  domaines-partagés disparaît avec les casquettes.
- Le calcul d'éclairage statistique dans `graphe.py` → remplacé par les
  fiches touchées par le chantier ouvert.

## Ordre du chantier v4

1. **v4.0** — fiche `chantier` + éclairage exact ; ordonnance markdown +
   widgets `pdf`/`code` (grisage) + les trois états (préparée, signée,
   confiée) + dépôt dans le repo ; vue session dans l'Archipel.
2. **v4.1** — cellules notebook exécutables (jupyter local).
3. **v4.2** — extensions du registre selon l'usage.

Restent du plan v3, inchangés : réécriture de l'app (capture → fiches),
OCR des scans, étoffage des fiches sources (rôle de l'humain).

## Critères de réussite

- Rentrer dans un code quitté depuis des semaines et retrouver le fil
  en une session, sans ouvrir un fichier au hasard.
- Une ordonnance signée suffit à l'agent de codage : pas de question
  en retour sur « où était le passage ».
- Ouvrir l'Archipel, ouvrir le chantier, tout ce qui compte est éclairé
  en un coup d'œil — et rien d'autre ne crie.
