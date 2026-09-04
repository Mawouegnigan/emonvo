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


Caméra → Poste de calcul (détection + calcul) → Liaison série USB → ESP32 → Feux LED
↑
Interrupteur d'urgence


Le système repose sur deux niveaux volontairement séparés : un poste de calcul (PC) exécute la détection vidéo et le calcul de saturation en Python, tandis qu'un microcontrôleur ESP32 pilote directement les feux et surveille l'urgence en autonomie. Cette séparation garantit que les fonctions de sécurité restent fiables même en cas de ralentissement du traitement logiciel.

## Stack technique

- **Traitement** : Python (Anaconda), OpenCV, Ultralytics YOLOv8 (modèle nano)
- **Microcontrôleur** : ESP32-WROOM-32 (DevKit V1), programmé en C++ (Arduino)
- **Communication** : liaison série USB, 9600 bauds

## Structure du dépôt

emonvo/
├── main.py # Point d'entrée, assemble tous les modules
├── detection.py # Détection vidéo et score de trafic pondéré (YOLOv8)
├── saturation.py # Calcul du temps de vert par voie
├── arduino_link.py # Liaison série avec l'ESP32 (+ mode simulation)
├── feux.py # Pilotage du cycle des deux feux
├── urgence.py # Gestion de la priorité d'urgence
├── affichage.py # Supervision visuelle
└── emonvo_feux/
└── emonvo_feux.ino # Firmware ESP32 (pilotage feux, urgence, mode dégradé)




## Installation

### Côté PC (traitement)

```bash
# Environnement Anaconda recommandé
pip install ultralytics opencv-python pyserial --break-system-packages
```

Le modèle `yolov8n.pt` est téléchargé automatiquement au premier lancement.

### Côté ESP32 (firmware)

1. Installer l'IDE Arduino et le support de carte ESP32 (package Espressif).
2. Installer le pilote USB **CP210x** (Silicon Labs) pour la carte DevKit V1.
3. Ouvrir `emonvo_feux/emonvo_feux.ino`, sélectionner la carte **ESP32 Dev Module**, Upload Speed **115200**.
4. Téléverser sur la carte.

## Utilisation

```bash
python main.py                     # utilise la webcam par défaut
python main.py chemin_video.mp4    # utilise un fichier vidéo
```

Touches disponibles dans la fenêtre vidéo :
- `u` : simule l'urgence (si aucun ESP32 n'est connecté)
- `q` : quitte proprement

Si aucun ESP32 n'est détecté, le système bascule automatiquement en mode simulation (aucun matériel requis pour tester la logique).

## Câblage (ESP32 DevKit V1)

| Élément | Broche |
|---|---|
| Voie A — Rouge / Jaune / Vert | GPIO 4 / 5 / 18 |
| Voie B — Rouge / Jaune / Vert | GPIO 19 / 21 / 22 |
| Interrupteur d'urgence | GPIO 23 (INPUT_PULLUP) |

## Modes de fonctionnement

- **Normal** : le PC pilote les feux selon le trafic détecté, recalcul toutes les 5 s.
- **Urgence** : priorité immédiate à une voie, avec transition de sécurité et limite de 30 s.
- **Dégradé** : si l'ESP32 ne reçoit plus de commande pendant 10 s, il signale la panne par un clignotement jaune (3 s) puis bascule sur un cycle fixe autonome (20 s/voie), jusqu'au retour de la communication.

## Feuille de route

- Remplacement de l'interrupteur d'urgence manuel par un capteur de détection automatique (déploiement réel)
- Second point d'urgence par voie (gestion de véhicules prioritaires simultanés)
- Boîtier étanche et alimentation solaire continue
- Entraînement d'un modèle de détection personnalisé si nécessaire
- Supervision à distance et historisation des données de trafic

## Équipe

Projet porté par deux co-fondateurs béninois — développement logiciel & IA, et génie électrique.

## Licence

Voir le fichier [LICENSE](LICENSE) — tous droits réservés.

