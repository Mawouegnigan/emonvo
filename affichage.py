"""
affichage.py
-------------
Affiche en direct, dans le terminal, l'état du système pendant la démo
(spécification F4) : nombre de véhicules détectés, temps de vert calculé,
voie active, et statut du mode urgence.

C'est ce module qui sert de "preuve visuelle" pendant la présentation au
jury : on voit les chiffres ET les LED réagir en même temps.
"""


def mettre_a_jour(nb_A, nb_B, temps_A, temps_B, voie_active, mode_urgence=False):
    """
    Affiche une ligne de statut, réécrite en continu sur la même ligne
    du terminal (grâce à '\\r'), pour un affichage propre et lisible
    qui ne fait pas défiler l'écran en continu.
    """
    if mode_urgence:
        ligne = f"🚨 MODE URGENCE ACTIF — Voie prioritaire : {voie_active}"
    else:
        ligne = (
            f"Véhicules -> A: {nb_A:4.1f}  B: {nb_B:4.1f}   |   "
            f"Temps de vert -> A: {temps_A:2d}s  B: {temps_B:2d}s   |   "
            f"Voie au vert : {voie_active}"
        )

    # .ljust(100) garantit que les anciennes lignes plus longues sont
    # bien effacées, même quand la nouvelle ligne est plus courte
    print(ligne.ljust(100), end="\r")


# ============================================================
# ZONE DE TEST — à exécuter avec : python affichage.py
# ============================================================
if __name__ == "__main__":
    import time

    print("=== Test du module affichage.py ===\n")
    print("(la ligne ci-dessous doit se mettre à jour en place, sans défiler)\n")

    for i in range(10):
        mettre_a_jour(nb_A=i, nb_B=10 - i, temps_A=30 + i, temps_B=30 - i, voie_active="A" if i % 2 == 0 else "B")
        time.sleep(0.3)

    print("\n\nTest du mode urgence :")
    mettre_a_jour(0, 0, 0, 0, voie_active="A", mode_urgence=True)
    print()