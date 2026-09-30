---
author: agent
domaines: [géométrie, maths]
source: "[[_sources/SB-0060 — Offset de polylignes]]"
---
Les cas pathologiques (auto-intersection, arc plus petit que l'offset,
superpositions) ont chacun un traitement explicite, et l'algorithme est
prouvé complet : on ne perd rien, on ne coupe pas trop. L'implémentation
devient testable cas par cas.