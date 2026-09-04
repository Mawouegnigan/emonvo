"""
main.py
--------
Point d'entrée du système Emonvo (architecture PC + ESP32).
Assemble tous les modules :

    détection (PC) -> calcul de saturation (PC) -> pilotage des feux (ESP32)
                                                          |
                                              affichage (PC) + urgence (ESP32)

Usage :
    python main.py                     # utilise la webcam par défaut
    python main.py chemin_video.mp4    # utilise un fichier vidéo

Pendant l'exécution, dans la fenêtre vidéo :
    - touche 'u' : bascule l'urgence en mode simulation (si pas d'ESP32 connecté)
    - touche 'q' : quitte proprement le programme

Si un ESP32 est branché et programmé avec emonvo_feux.ino, l'interrupteur
physique prend automatiquement le relais de la touche 'u'.
"""

import sys
import time
import cv2

from detection import compter_vehicules
from saturation import calculer_temps_vert
from arduino_link import LiaisonArduino
from feux import GestionnaireFeux
from urgence import GestionnaireUrgence
import affichage

INTERVALLE_RECALCUL = 5   # secondes entre deux recalculs de saturation (F2)
INTERVALLE_HEARTBEAT = 3  # secondes entre deux "signaux de vie" envoyés à l'ESP32
                           # (empêche l'ESP32 de croire à tort que le PC est en
                           # panne quand une voie reste verte longtemps sans
                           # qu'aucune commande de changement ne soit nécessaire)


def main():
    source = sys.argv[1] if len(sys.argv) > 1 else 0

    capture = cv2.VideoCapture(source)
    if not capture.isOpened():
        print("Erreur : impossible d'ouvrir la source vidéo/caméra.")
        sys.exit(1)

    # Une seule liaison ESP32, partagée entre feux.py et urgence.py
    # (les deux passent par le même câble USB)
    liaison = LiaisonArduino()
    feux = GestionnaireFeux(liaison=liaison)
    gestionnaire_urgence = GestionnaireUrgence(liaison=liaison)

    print("\n=== EMONVO — Preuve de Concept (PC + ESP32) ===")
    print("Touches : [u] simuler urgence (si pas d'ESP32)   |   [q] quitter\n")

    dernier_calcul = 0.0
    dernier_heartbeat = 0.0
    temps_A, temps_B = 30, 30
    nb_A, nb_B = 0, 0

    while True:
        ok, frame = capture.read()
        if not ok:
            print("\nFin de la vidéo ou perte du flux caméra.")
            break

        # Correction de l'effet miroir : la webcam utilisée est en mode
        # "selfie", ce qui inverse gauche/droite par rapport à la scène
        # réelle et fait apparaître les voies A/B croisées à l'écran.
        frame = cv2.flip(frame, 1)

        # Étape 1 : détection (F1) — nb_A/nb_B sont désormais des scores
        # pondérés (voiture=1, moto=0.3), pas un simple comptage
        nb_A, nb_B, frame_annotee = compter_vehicules(frame)

        # Étape 1 bis : vérifier si l'ESP32 signale un changement sur l'interrupteur
        gestionnaire_urgence.rafraichir()

        maintenant = time.time()
        urgence_active = gestionnaire_urgence.est_activee()

        if urgence_active:
            voie_prioritaire = gestionnaire_urgence.quelle_voie()
            if feux.voie_active != voie_prioritaire or feux.temps_restant <= 0:
                feux.forcer_vert(voie_prioritaire, duree_max=30)
        else:
            if maintenant - dernier_calcul >= INTERVALLE_RECALCUL:
                temps_A, temps_B = calculer_temps_vert(nb_A, nb_B)
                if dernier_calcul == 0:
                    feux.demarrer_cycle(temps_A, temps_B)
                else:
                    feux.mettre_a_jour_durees(temps_A, temps_B)
                dernier_calcul = maintenant
            feux.tick()

        # Signal de vie régulier : confirme à l'ESP32 que le PC fonctionne
        # toujours, même quand aucune couleur ne change. Essentiel pour que
        # le mode dégradé de l'ESP32 ne se déclenche pas par erreur alors
        # qu'une voie reste simplement au vert plusieurs dizaines de secondes.
        if maintenant - dernier_heartbeat >= INTERVALLE_HEARTBEAT:
            feux.renvoyer_etat_actuel()
            dernier_heartbeat = maintenant

        affichage.mettre_a_jour(
            nb_A, nb_B, temps_A, temps_B,
            voie_active=feux.voie_active,
            mode_urgence=urgence_active,
        )

        cv2.imshow("Emonvo - PoC  (u = urgence simulee, q = quitter)", frame_annotee)
        touche = cv2.waitKey(1) & 0xFF
        if touche == ord("q"):
            break
        elif touche == ord("u") and liaison.mode_simulation:
            gestionnaire_urgence.basculer_simulation()

    capture.release()
    cv2.destroyAllWindows()
    liaison.fermer()
    print("\nSystème arrêté proprement.")


if __name__ == "__main__":
    main()