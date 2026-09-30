---
author: agent
domaines: [géométrie, numérique]
source: "[[_sources/SB-0060 — Offset de polylignes]]"
---
L'offset se construit en trois temps : offsets naïfs de chaque segment →
trim/joint des coins selon leur type → clipping des boucles parasites.
Chaque temps a des règles explicites et une preuve.