"""
feux.py
--------
Pilote les deux feux tricolores (Voie A et Voie B) via l'ESP32,
connecté en USB et contrôlé par la liaison série (cf. arduino_link.py).

MODE SIMULATION : automatique si aucun ESP32 n'est détecté
(cf. arduino_link.py) — le comportement du reste du système
(main.py, saturation.py...) ne change pas.
"""

import time
from arduino_link import LiaisonArduino


class Feu:
    """Représente un seul feu tricolore (une voie)."""

    def __init__(self, nom_voie: str, liaison: LiaisonArduino):
        self.nom_voie = nom_voie
        self.liaison = liaison
        self.etat = "rouge"

    def _allumer(self, couleur_code: str, nom_affiche: str):
        self.etat = nom_affiche
        self.liaison.envoyer_commande(self.nom_voie, couleur_code)

    def rouge(self):
        self._allumer("R", "rouge")

    def vert(self):
        self._allumer("V", "vert")


class GestionnaireFeux:
    """
    Gère le cycle des deux feux ensemble, en respectant la règle de
    sécurité absolue : les deux voies ne sont JAMAIS au vert en même temps.
    """

    def __init__(self, liaison: LiaisonArduino = None):
        # Une liaison peut être partagée avec urgence.py (même connexion USB) ;
        # si aucune n'est fournie, on en crée une nouvelle.
        self.liaison = liaison if liaison else LiaisonArduino()

        self.feu_A = Feu("A", self.liaison)
        self.feu_B = Feu("B", self.liaison)

        self.durees = {"A": 30, "B": 30}
        self.voie_active = "A"
        self.temps_restant = 0
        self.derniere_maj = time.time()

        self.feu_A.rouge()
        self.feu_B.rouge()

    def demarrer_cycle(self, temps_A: int, temps_B: int):
        self.durees = {"A": temps_A, "B": temps_B}
        self.voie_active = "A"
        self.temps_restant = temps_A
        self.derniere_maj = time.time()
        self._appliquer_etat()

    def mettre_a_jour_durees(self, temps_A: int, temps_B: int):
        """
        Met à jour les durées cibles pour le prochain cycle,
        SANS interrompre la voie actuellement active (contrairement
        à demarrer_cycle, qui force le retour à la voie A).
        """
        self.durees = {"A": temps_A, "B": temps_B}

    def renvoyer_etat_actuel(self):
        """
        Réenvoie la couleur actuelle de chaque voie à l'ESP32, sans rien
        changer côté logique. Sert de signal de vie régulier pour que
        l'ESP32 sache que le PC fonctionne toujours (cf. mode dégradé,
        emonvo_feux.ino), même quand aucune voie ne change de couleur
        pendant plusieurs dizaines de secondes.
        """
        self._appliquer_etat()

    def _appliquer_etat(self):
        if self.voie_active == "A":
            self.feu_A.vert()
            self.feu_B.rouge()
        else:
            self.feu_B.vert()
            self.feu_A.rouge()

    def tick(self):
        maintenant = time.time()
        ecoule = maintenant - self.derniere_maj
        self.derniere_maj = maintenant
        self.temps_restant -= ecoule

        if self.temps_restant <= 0:
            self.voie_active = "B" if self.voie_active == "A" else "A"
            self.temps_restant = self.durees[self.voie_active]
            self._appliquer_etat()

    def forcer_vert(self, voie: str, duree_max: int = 30):
        """Mode urgence (F6) : force immédiatement le vert sur une voie."""
        self.voie_active = voie
        self.temps_restant = duree_max
        self.durees = {
            "A": duree_max if voie == "A" else 0,
            "B": duree_max if voie == "B" else 0,
        }
        self.derniere_maj = time.time()
        self._appliquer_etat()
        print(f"  [URGENCE] Passage forcé au vert — Voie {voie} ({duree_max}s max)")


# ============================================================
# ZONE DE TEST — à exécuter avec : python feux.py
# ============================================================
if __name__ == "__main__":
    print("=== Test du module feux.py (via ESP32) ===\n")

    gestionnaire = GestionnaireFeux()

    print("--- Cycle normal (Voie A: 4s, Voie B: 2s) ---")
    gestionnaire.demarrer_cycle(temps_A=4, temps_B=2)
    debut = time.time()
    while time.time() - debut < 10:
        gestionnaire.tick()
        time.sleep(0.5)

    print("\n--- Déclenchement du mode urgence sur la Voie B ---")
    gestionnaire.forcer_vert("B", duree_max=3)

    gestionnaire.liaison.fermer()