"""
detection.py
-------------
Ce module utilise YOLOv8 (intelligence artificielle de détection d'objets)
pour repérer les véhicules dans une image, puis calcule un score pondéré
de trafic pour la zone "Voie A" et la zone "Voie B".

Pondération : une voiture, un bus ou un camion compte pour 1 point ;
une moto compte pour 0,3 point (elle occupe moins d'espace et dégage
plus vite qu'une voiture, ce qui reflète mieux la réalité du trafic
ouest-africain, où les motos sont majoritaires).
"""

from ultralytics import YOLO
import cv2

# ============================================================
# CHARGEMENT DU MODÈLE IA
# ============================================================
modele = YOLO("yolov8n.pt")

# Classes YOLO (jeu de données COCO) qui nous intéressent :
#   2 = voiture, 3 = moto, 5 = bus, 7 = camion
CLASSES_VEHICULES = {2, 3, 5, 7}

# Poids de chaque type de véhicule dans le calcul de saturation.
# Une moto compte pour 0,3 point ; les autres véhicules comptent pour 1 point.
POIDS_VEHICULE = {
    2: 1.0,   # voiture
    3: 0.3,   # moto
    5: 1.0,   # bus
    7: 1.0,   # camion
}

# Seuil de confiance minimum pour qu'une détection soit prise en compte.
# Valeur par défaut de YOLOv8 : 0.25. On l'abaisse légèrement ici pour
# réduire les détections manquées, quitte à accepter un peu plus de
# faux positifs — à réajuster selon les résultats observés sur le terrain.
SEUIL_CONFIANCE = 0.2


def definir_zones(largeur_image: int, hauteur_image: int) -> dict:
    """
    Définit les deux zones rectangulaires de l'image correspondant
    à la Voie A (gauche) et la Voie B (droite).
    """
    milieu = largeur_image // 2
    return {
        "A": (0, 0, milieu, hauteur_image),
        "B": (milieu, 0, largeur_image, hauteur_image),
    }


def centre_dans_zone(cx: float, cy: float, zone: tuple) -> bool:
    """Vérifie si le centre d'un véhicule détecté (cx, cy) tombe dans une zone donnée."""
    x1, y1, x2, y2 = zone
    return x1 <= cx <= x2 and y1 <= cy <= y2


def compter_vehicules(frame) -> tuple[float, float, "any"]:
    """
    Analyse une image (frame) et calcule un score de trafic pondéré
    pour chaque voie (une moto pèse moins qu'une voiture).

    Returns:
        (score_A, score_B, frame_annotee) :
            - score_A, score_B : score de trafic pondéré (nombre décimal) par voie
            - frame_annotee : la même image, avec les rectangles de détection
    """
    hauteur, largeur = frame.shape[:2]
    zones = definir_zones(largeur, hauteur)

    resultats = modele(frame, conf=SEUIL_CONFIANCE, verbose=False)[0]

    score_A, score_B = 0.0, 0.0
    frame_annotee = frame.copy()

    for boite in resultats.boxes:
        classe_id = int(boite.cls[0])
        if classe_id not in CLASSES_VEHICULES:
            continue

        x1, y1, x2, y2 = boite.xyxy[0]
        cx, cy = (x1 + x2) / 2, (y1 + y2) / 2
        poids = POIDS_VEHICULE[classe_id]

        if centre_dans_zone(cx, cy, zones["A"]):
            score_A += poids
            couleur = (0, 200, 0)
        elif centre_dans_zone(cx, cy, zones["B"]):
            score_B += poids
            couleur = (0, 140, 255)
        else:
            couleur = (150, 150, 150)

        # Étiquette : type de véhicule + poids, utile pour vérifier visuellement
        label = "moto" if classe_id == 3 else "vehicule"
        cv2.rectangle(frame_annotee, (int(x1), int(y1)), (int(x2), int(y2)), couleur, 2)
        cv2.putText(frame_annotee, f"{label} ({poids:.1f})", (int(x1), int(y1) - 8),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.5, couleur, 1)

    milieu = largeur // 2
    cv2.line(frame_annotee, (milieu, 0), (milieu, hauteur), (255, 255, 255), 1)
    cv2.putText(frame_annotee, f"Voie A: {score_A:.1f}", (20, 30),
                cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 200, 0), 2)
    cv2.putText(frame_annotee, f"Voie B: {score_B:.1f}", (milieu + 20, 30),
                cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 140, 255), 2)

    return score_A, score_B, frame_annotee


# ============================================================
# ZONE DE TEST — à exécuter avec : python detection.py chemin_video.mp4
# ============================================================
if __name__ == "__main__":
    import sys

    source = sys.argv[1] if len(sys.argv) > 1 else 0
    print(f"=== Test du module detection.py === (source: {source})")
    print("Appuyez sur 'q' dans la fenêtre vidéo pour arrêter.\n")

    capture = cv2.VideoCapture(source)

    if not capture.isOpened():
        print("Erreur : impossible d'ouvrir la source vidéo/caméra.")
        sys.exit(1)

    while True:
        ok, frame = capture.read()
        if not ok:
            print("Fin de la vidéo ou perte du flux caméra.")
            break

        score_A, score_B, frame_annotee = compter_vehicules(frame)
        print(f"Score de trafic -> Voie A: {score_A:.1f}  Voie B: {score_B:.1f}", end="\r")

        cv2.imshow("Emonvo - Detection (appuyez sur q pour quitter)", frame_annotee)
        if cv2.waitKey(1) & 0xFF == ord("q"):
            break

    capture.release()
    cv2.destroyAllWindows()