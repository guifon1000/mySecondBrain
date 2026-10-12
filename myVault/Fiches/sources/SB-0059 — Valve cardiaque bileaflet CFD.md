---
type: source
author: user
domaines: [CFD, mécanique]
source: SB-0059
ouvrage: "Ghaeb N.H., Khalaf T.Y., Al-Timemy A., « Velocity analysis of bileaflet artificial heart valve: from opening to near close position », J. Applied Sciences Research 5(10), 2009 (9 p.)"

---
# CFD d'une valve cardiaque bileaflet (ANSYS)

Petit article appliqué : simulation du flux sanguin dans 7 géométries de
valves mécaniques bileaflet (angles 55° à 85°) pendant la fermeture, en
ANSYS (éléments finis), écoulement laminaire permanent.

## Idées principales

- **Configuration d'étude simple et reproductible** : valve dans une conduit
  divergent (22→28 mm), fluide Newtonien incompressible (ρ=1,05, μ=0,004),
  vitesse d'entrée 10 cm/s, 44 cas (7 angles × étapes de fermeture).
- **Critère de qualité = stabilité du profil de vitesse** : la valve dont la
  vitesse moyenne décroît le plus lissément à la fermeture minimise
  turbulence et tourbillons — métrique simple pour comparer des designs.
- **La valve bileaflet (St. Jude Medical, 1978)** : feuilletts dans le flux,
  grande orifice effectif, profil de flux quasi normal, régurgitation
  normale 5-10 ml/battement — le design gagne quand il gêne le moins.
- **Enjeu clinique = hémodynamique** : thrombogenèse/hémolyse corrélées aux
  cisaillements élevés et à la turbulence — la CFD est un « banc d'essai
  virtuel » avant l'implant.
- **Histoire technique en une page** : cage-bille (Starr-Edwards) → disque
  inclinable (Lillehei-Kaster) → bileaflet : chaque génération résout le
  défaut de la précédente (obstruction, thrombo, fatigue des struts).
- **FSI** : le vrai sujet est l'interaction fluide-structure feuilletts/flux
  (Peskin 1972, méthode immersed boundary originée pour... les valves
  cardiaques) — lien direct avec SB-0061.

## Rattachements

- **Casquette Ingénieur CFD** : cas d'école FSI biomécanique, bon exemple de
  paramétrique géométrique (l'angle ouvre/ferme = paramètre d'étude) +
  CFD statique série.
- **Lien Peskin** : la méthode immersed boundary est née de ce problème —
  à lire avec SB-0061 (IB-LBM moderne du même laboratoire que la thèse
  SB-0058).
