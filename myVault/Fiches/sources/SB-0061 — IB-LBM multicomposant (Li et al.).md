---
type: source
author: user
domaines: [CFD, matériaux, numérique]
source: SB-0061
ouvrage: "Li Z., Favier J., D'Ortona U., Poncet S., « An immersed boundary-lattice Boltzmann method for single- and multi-component fluid flows », J. Comput. Physics, 2016 (28 p.)"

---
# IB-LBM : frontières immergées + écoulements multicomposants

Article CNRS/M2P2 (Marseille) : couplage méthode des frontières immergées
(IB) et Lattice Boltzmann (LB) pour des écoulements monophasiques et
bicomposants autour de solides mobiles/déformables. Application finale :
transport de mucus par des cils vibratifs en 3D.

## Idées principales

- **Le duo gagnant** : LB sur grille cartésienne fixe (simple, massivement
  parallèle) + IB en points lagrangiens pour les corps mobiles — pas de
  remaillage quand le solide bouge.
- **Force IB obtenue par la définition même de la vitesse macroscopique**
  (u = Σeᵢfᵢ + Δt/2 F) : on impose no-slip aux points lagrangiens et on
  remonte à la force — pas de sous-pas de prédiction.
- **Spreading operator amélioré** (Pinelli et al.) : rendre réciproques les
  opérations interpolation-épandage (système linéaire A·ε = 1, résolu une
  seule fois si le solide est fixe) → no-slip mieux assuré que le schéma
  explicite classique.
- **Multicomposant Shan-Chen « explicit forcing »** : potentiel
  interparticulaire pour mucus/periciliaire, + forces d'adhésion solide
  réglables (G_adh) pour imposer mouillabilité/angle de contact sur
  parois courbes — là où le bounce-back classique échoue.
- **Application signature** : nappe de 9 cils battants (2 phases, grande
  déformation) → écoulement moyen dirigé = transport du mucus des voies
  respiratoires.
- **Validations** : sillage de cylindre Re=30, film hydrophobe brisé,
  précision quasi 2e ordre.

## Rattachements

- **Casquette Ingénieur CFD** : cœur de compétence LBM + FSI ; lecteurs
  cibles des références Peskin/Pinelli citées en biblio.
- **Lecture croisée** avec SB-0058 (thèse Wissocq : stabilité LBM) — le
  même laboratoire M2P2/Aix-Marseille ; et SB-0059 (valve : l'IB est née
  des valves cardiaques).
- **Idée réutilisable générale** : le pattern « force = résidu entre vitesse
  imposée et vitesse calculée » se retrouve dans la correction de
  contraintes partout en méca numérique.
