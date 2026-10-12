---
type: source
author: user
domaines: [CFD, numérique]
source: SB-0058
ouvrage: "Wissocq G., « Investigation of lattice Boltzmann methods for turbomachinery secondary air system simulations », thèse Aix-Marseille/CERFACS/Safran 2019 (429 p.)"

---
# Lattice Boltzmann pour les cavités tournantes de turbomachines

Thèse CERFACS/Safran sur la méthode de Boltzmann sur réseau (LBM) appliquée
au circuit de bore cooling d'un turboréacteur : cavités tournantes,
instabilités thermiques, stabilité numérique des schémas LBM.

## Idées principales

- **Le LBM comme alternative aux solveurs NS classiques** : intrinsèquement
  instationnaire, parallélisable, naturel pour les géométries 3D complexes
  — le fluide est décrit par des fonctions de distribution cinétiques, NS
  n'est récupéré qu'à la limite macroscopique (Hermite, Chapman-Enskog).
- **Instabilités physiques** : cavités tournantes à gradient de température
  radial → analyses de stabilité linéaire donnant Rayleigh/Reynolds
  critiques ; le cycle limite non linéaire exige la simulation complète.
- **Stabilité numérique = objet d'étude à part entière** : méthodologie
  von Neumann pour identifier les ondes propagées par le schéma ; le choix
  du lattice et du modèle de collision gouverne la stabilité.
- **Modèles régularisés** : deux propriétés fondamentales influencent la
  stabilité subsonique — régularisation de la fonction de distribution
  (prolongement des travaux Coreixas/Sagaut).
- **Validation industrielle** : PowerFLOW (seul code LBM commercial mûr)
  testé du cas académique à la configuration multi-étages avec couplage
  chaleur conjuguée (CHT) — profils de température bien estimés vs essais.
- **Méthode de thèse à retenir** : physique simplifiée → analyse linéaire →
  simulation numérique → confrontation expérimentale, par paliers de
  complexité croissante.

## Rattachements

- **Casquette Ingénieur CFD** : référence LBM de premier plan ; utile pour
  comprendre les solveurs de type PowerFLOW/Palabos et leurs limites.
- **Écho avec SB-0061 (Li et al., IB-LBM)** : même famille de méthodes — la
  thèse traite la stabilité des schémas, l'article le couplage aux
  frontières immergées ; lecture croisée recommandée.
