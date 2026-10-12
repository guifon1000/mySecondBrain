---
type: source
author: user
domaines: [géométrie, mécanique]
source: SB-0055
ouvrage: "Konyukhov A. & Izi R., « Introduction to Computational Contact Mechanics: A Geometrical Approach », Wiley 2015 (305 p.)"
lie: ["[[Rincewind]]"]
---
# Computational Contact Mechanics — approche géométrique

Manuel KIT sur la mécanique du contact numérique : théorie + implémentation
pas-à-pas d'éléments de contact dans FEAP (Fortran), avec vérification sur
solutions analytiques.

## Idées principales

- **L'approche « géométrique »** : le contact est formulé via la géométrie
  différentielle des surfaces (coordonnées de Gauss, courbure, formules de
  Weingarten/Gauss-Codazzi) — le contact devient un problème de géométrie
  de projection avant d'être un problème de mécanique.
- **Closest Point Projection (CPP)** : brique centrale — projeter un point
  sur la surface maître définit la cinématique du contact. Existence/
  unicité du CPP traitée explicitement (cas irréguliers).
- **Trois formulations classiques** : Lagrange multiplier (exact, point
  selle), Penalty (régularisé, raideur artificielle), Nitsche (stabilisé
  sans multiplicateur) — implémentées toutes trois, comparées.
- **Famille d'éléments de contact** : Node-To-Node, Node-To-Segment,
  Segment-To-Analytical-Surface (surface rigide analytique → solutions
  fermées), Segment-To-Segment (Mortar) — le choix du modèle de contact
  est un choix de discrétisation.
- **Friction** : loi de Coulomb, algorithme de return-mapping par analogie
  élasto-plastique, principe de maximum de dissipation.
- **Pédagogie par le code** : chaque leçon = un élément Fortran implémenté
  + exemples de vérification (Hertz, punch, Euler-Eytelwein, impact
  pendule) — la vérification contre l'analytique est systématique.

## Rattachements

- **Casquette Ingénieur CFD** : socle méthodologique contact/FEM
  (complément des méthodes fluides).
- **Rincewind** : la mécanique du contact est ce qui se passe *dans* les
  assemblages bois (embrèvements, contacts tendons-mortaises). L'approche
  géométrique (CPP sur surfaces) est très proche de l'esprit du noyau
  (surfaces, projections, frames).
- **Méthode de travail à retenir** : implémenter petit + vérifier contre
  l'analytique à chaque pas — pattern directement applicable au solver de
  comble de rincewind.
