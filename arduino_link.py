"""
arduino_link.py
-----------------
Gère la connexion USB (liaison série) entre le PC et l'Arduino.

Ce module centralise TOUTE la communication avec l'Arduino, pour que
feux.py et urgence.py n'aient qu'à l'utiliser sans se soucier des
détails techniques (port USB, vitesse, etc.).

MODE SIMULATION : si aucun Arduino n'est détecté (câble débranché,
pas encore reçu, etc.), ce module bascule automatiquement en mode
simulation — comme pour les autres modules du projet.
"""

import time

try:
    import serial
    import serial.tools.list_ports
    PYSERIAL_DISPONIBLE = True
except ImportError:
    PYSERIAL_DISPONIBLE = False


def trouver_port_arduino():
    """
    Cherche automatiquement le port USB sur lequel l'Arduino est branché,
    pour éviter d'avoir à le configurer à la main (ex: "COM3" sur Windows).

    Returns:
        Le nom du port (ex: "COM3") si un Arduino est trouvé, sinon None.
    """
    if not PYSERIAL_DISPONIBLE:
        return None

    ports = serial.tools.list_ports.comports()
    for port in ports:
        # La plupart des Arduino Uno s'identifient avec "Arduino" ou "CH340"
        # (nom de la puce USB utilisée par de nombreux clones) dans leur description
        description = (port.description or "").lower()
        if "arduino" in description or "ch340" in description or "usb serial" in description or "cp210" in description or "silicon labs" in description:
            return port.device
    return None


class LiaisonArduino:
    """Représente la connexion active (ou simulée) avec l'Arduino."""

    def __init__(self):
        self.connexion = None
        self.mode_simulation = True

        port = trouver_port_arduino()
        if port and PYSERIAL_DISPONIBLE:
            try:
                self.connexion = serial.Serial(port, 9600, timeout=0.1)
                time.sleep(2)  # l'Arduino redémarre automatiquement à la connexion ; on lui laisse le temps
                self.mode_simulation = False
                print(f"  [ARDUINO] Connecté sur le port {port}")
            except Exception as e:
                print(f"  [ARDUINO] Port trouvé mais connexion échouée ({e}) — passage en simulation")
        else:
            print("  [ARDUINO] Aucun Arduino détecté — mode simulation activé")

    def envoyer_commande(self, voie: str, couleur: str):
        """
        Envoie une commande à l'Arduino pour allumer une couleur sur une voie.

        Args:
            voie: "A" ou "B"
            couleur: "R" (rouge), "J" (jaune) ou "V" (vert)
        """
        if self.mode_simulation:
            print(f"  [SIMULATION ARDUINO] Voie {voie} -> {couleur}")
        else:
            self.connexion.write(f"{voie}:{couleur}\n".encode())

    def lire_urgence(self) -> bool | None:
        """
        Vérifie si l'Arduino a envoyé une nouvelle information sur l'état
        de l'interrupteur d'urgence.

        Returns:
            True si l'urgence vient d'être activée, False si désactivée,
            None si aucune nouvelle information n'est disponible (pas de changement).
        """
        if self.mode_simulation:
            return None  # en simulation, urgence.py gère ça au clavier directement

        if self.connexion.in_waiting > 0:
            ligne = self.connexion.readline().decode(errors="ignore").strip()
            if ligne.startswith("URGENCE:"):
                return ligne.endswith("1")
        return None

    def fermer(self):
        if self.connexion:
            self.connexion.close()


# ============================================================
# ZONE DE TEST — à exécuter avec : python arduino_link.py
# ============================================================
if __name__ == "__main__":
    print("=== Test du module arduino_link.py ===\n")
    liaison = LiaisonArduino()

    print("\nEnvoi de commandes de test (observez les LED si l'Arduino est branché) :")
    sequence = [("A", "V"), ("B", "R"), ("A", "R"), ("B", "V")]
    for voie, couleur in sequence:
        liaison.envoyer_commande(voie, couleur)
        time.sleep(1)

    if not liaison.mode_simulation:
        print("\nÉcoute de l'interrupteur pendant 10 secondes (basculez-le pour tester)...")
        fin = time.time() + 10
        while time.time() < fin:
            etat = liaison.lire_urgence()
            if etat is not None:
                print(f"  Changement détecté -> urgence activée : {etat}")
            time.sleep(0.1)

    liaison.fermer()
    print("\nTest terminé.")