"""
urgence.py
-----------
Gère le déclenchement de la priorité d'urgence (spécification F6) :
ambulance, pompiers, bus BRT — via l'interrupteur câblé sur l'Arduino.

MODE SIMULATION : si aucun Arduino n'est détecté, on simule
l'activation avec la touche "u" du clavier pendant main.py — la
liaison série ne fournit alors aucune information (cf. arduino_link.py),
donc ce module se rabat automatiquement sur le clavier.
"""

from arduino_link import LiaisonArduino


class GestionnaireUrgence:
    def __init__(self, liaison: LiaisonArduino = None):
        self.liaison = liaison if liaison else LiaisonArduino()
        self._active = False
        self._voie = "A"  # voie prioritaire par défaut si déclenché

    def rafraichir(self):
        """
        À appeler à chaque tour de boucle dans main.py : vérifie si
        l'Arduino a signalé un changement d'état de l'interrupteur.
        Sans effet en mode simulation (le clavier prend le relais).
        """
        nouvel_etat = self.liaison.lire_urgence()
        if nouvel_etat is not None:
            self._active = nouvel_etat
            etat_txt = "ACTIVÉE" if self._active else "DÉSACTIVÉE"
            print(f"\n  [ARDUINO] Priorité d'urgence {etat_txt} (voie {self._voie})")

    def basculer_simulation(self):
        """Appelé en mode simulation quand l'utilisateur appuie sur 'u' dans main.py."""
        self._active = not self._active
        etat = "ACTIVÉE" if self._active else "DÉSACTIVÉE"
        print(f"\n  [SIMULATION] Priorité d'urgence {etat} (voie {self._voie})")

    def est_activee(self) -> bool:
        return self._active

    def quelle_voie(self) -> str:
        return self._voie

    def definir_voie(self, voie: str):
        assert voie in ("A", "B"), "La voie doit être 'A' ou 'B'"
        self._voie = voie


# ============================================================
# ZONE DE TEST — à exécuter avec : python urgence.py
# ============================================================
if __name__ == "__main__":
    import time

    print("=== Test du module urgence.py (via Arduino) ===\n")
    gestionnaire = GestionnaireUrgence()

    if gestionnaire.liaison.mode_simulation:
        print("Mode simulation : test par basculement logiciel")
        gestionnaire.basculer_simulation()
        print(f"Après basculement -> activée : {gestionnaire.est_activee()}")
        gestionnaire.basculer_simulation()
        print(f"Après second basculement -> activée : {gestionnaire.est_activee()}")
    else:
        print("Arduino détecté : basculez l'interrupteur physique pendant 10 secondes...")
        fin = time.time() + 10
        while time.time() < fin:
            gestionnaire.rafraichir()
            time.sleep(0.1)

    gestionnaire.liaison.fermer()