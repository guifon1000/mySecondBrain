---
type: source
author: user
domaines: [assemblages, données, mécanique, normes, paramétrique]
source: SB-0052
pdf: "[Yves_Benoit,_Bernard_Legrand,_Vincent_Tastet]_Cal(BookZZ.org).pdf"
lie: ["[[Rincewind]]", "[[Sapientpearwood]]"]
---
# Eurocode 5 — Calcul des structures en bois (guide d'application)

Guide de référence FR pour l'application de l'Eurocode 5 (structures bois) :
passage des Règles CB 71 aux états limites, avec applications résolues
chapitre par chapitre.

## Idées principales

- **Deux vérifications systématiques** : ELU (sécurité/rupture) et ELS
  (déformations/confort). Toute justification suit ce double critère —
  structure mentale transposable à tout code de calcul.
- **Classes de résistance** C18→C40 (bois massif) et GL24h→GL36h (lamellé) ;
  résistance corrigée par kmod (durée de charge, humidité/classe de service)
  et γM (coeff partiel).
- **Sollicitations traitées de la simple à la composée** : traction/compression
  axiale + flambement, flexion simple (ELU + flèches instantanée/différée),
  cisaillement, flexion déviée avec compression.
- **Assemblages = chapitre le plus riche** : embrèvements, tenons-mortaises,
  puis tiges (pointes, bouchons, boulons, broches, tire-fond) — avec deux
  nouveautés majeures vs CB 71 : **rupture de bloc** et **rupture par
  fendage**, phénomènes de groupe à modéliser.
- **Rigideité des assemblages** : Kser (raideur par tige/plan de cisaillement)
  fonction du diamètre et de la classe — entrée pour tout modèle
  semi-rigide.
- Chapitre 5 : tableaux de synthèse complets (résistances caractéristiques
  par diamètre, angle, nombre de boulons...) — directement exploitable en
  données.

## Rattachements

- **Rincewind** : le **solver de comble** (priorité 1 du TODO) devra
  s'appuyer sur ces formulations ELU/ELS et les vérifications
  d'assemblages. Les tableaux du ch. 5 sont des jeux de données candidats
  pour des tests unitaires du solver.
- **Sapientpearwood** : les règles de prédimensionnement conditionnent les
  choix de sections → impact direct sur le chiffrage du devis.
- **Casquette Charpentier** : langue commune avec l'ingénieur,
  vocabulaire ELU/ELS, compréhension des justifications demandées par le
  bureau d'études.
