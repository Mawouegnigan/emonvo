# Emonvo — « La voie est libre »

Système de feux de circulation intelligents pour la mobilité urbaine ouest-africaine.

Emonvo observe le trafic en temps réel à l'aide d'une caméra et d'un modèle d'intelligence artificielle (YOLOv8), puis ajuste automatiquement la durée du feu vert de chaque voie d'une intersection selon la charge réelle observée. Le système intègre une priorité d'urgence pour les véhicules prioritaires (ambulances, pompiers) et un mode de fonctionnement dégradé garantissant qu'un carrefour équipé ne reste jamais bloqué, même en cas de panne de communication.

Projet candidat aux concours **African Next Entrepreneurs 2026** (African Business Club Paris) et **AfriTech Challenge 2026** (Fédération APNA).

---

## Fonctionnalités

| Réf. | Fonction | Description |
|---|---|---|
| F1 | Détection des véhicules | Comptage en temps réel par voie, via caméra et YOLOv8 |
| F2 | Calcul de saturation | Recalcul du temps de vert toutes les 5 s, entre 15 et 45 s, selon un score pondéré (voiture = 1, moto = 0,3) |
| F3 | Pilotage des feux | Commande des LED rouge/jaune/vert, jamais deux voies vertes simultanément |
| F4 | Transition de sécurité | Phase jaune obligatoire avant tout passage au rouge, gérée par le microcontrôleur |
| F5 | Affichage / supervision | Visualisation en direct de l'état du trafic et des feux |
| F6 | Priorité d'urgence | Interrupteur dédié donnant la priorité immédiate à une voie (destiné à être remplacé par un capteur automatique lors du déploiement réel) |
| — | Mode dégradé autonome | Bascule automatique vers un cycle à durées fixes en cas de perte de communication avec le poste de calcul |

## Architecture