---
author: agent
domaines: [géométrie, CFD, usinage]
parent: "[[Hex]]"
---
L'offset de polyligne est un opérateur unique qui change de destination :
en charpente, l'offset du contour **est** la trajectoire CNC (renardiere) ;
en fraisage de gabarits, l'offset douille-fraise **est** la couture du
gabarit à dessiner ; en CFD structuré, l'offset en couches successives
**est** la couche-limite maillée (Hex). Même les trois temps du problème
(auto-intersection, connexité, distance au bord) sont les mêmes. Une
seule implémentation bien faite peut servir trois métiers.