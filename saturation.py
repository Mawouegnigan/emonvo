"""
saturation.py
--------------
Calcule le temps de vert de chaque voie à partir d'un score de trafic
pondéré (et non plus un simple comptage de véhicules) : une voiture,
un bus ou un camion pèsent 1 point, une moto pèse 0,3 point
(cf. detection.py, POIDS_VEHICULE).
"""

DUREE_CYCLE = 60
TEMPS_MIN = 15
TEMPS_MAX = 45


def calculer_temps_vert(score_A: float, score_B: float) -> tuple[int, int]:
    """
    Calcule le temps de vert (en secondes) pour la Voie A et la Voie B,
    à partir du score de trafic pondéré de chacune.

    Exemple :
        calculer_temps_vert(6.0, 1.2)
        -> Voie A représente 6/(6+1.2) = 83% du trafic pondéré -> ~50s
        -> plafonné à 45s -> Voie A = 45s, Voie B = 15s

    Args:
        score_A: score de trafic pondéré de la voie A (voitures=1, motos=0.3)
        score_B: score de trafic pondéré de la voie B

    Returns:
        (temps_A, temps_B) : le temps de vert en secondes pour chaque voie
    """
    total = score_A + score_B

    if total == 0:
        return DUREE_CYCLE // 2, DUREE_CYCLE // 2

    poids_A = score_A / total
    poids_B = score_B / total

    temps_A = poids_A * DUREE_CYCLE
    temps_B = poids_B * DUREE_CYCLE

    temps_A = max(TEMPS_MIN, min(TEMPS_MAX, temps_A))
    temps_B = DUREE_CYCLE - temps_A

    return round(temps_A), round(temps_B)


if __name__ == "__main__":
    print("=== Test du module saturation.py ===\n")

    # Scénarios réalistes : scores pondérés (ex: 12 motos = 12*0.3 = 3.6 points)
    scenarios = [
        (18, 4),      # cas simple, équivalent à l'ancien comptage brut
        (0, 0),
        (10, 10),
        (3.6, 8),     # Voie A = 12 motos (3.6 pts), Voie B = 8 voitures
        (6, 1.2),     # Voie A chargée en voitures, Voie B = 4 motos seulement
    ]

    for score_A, score_B in scenarios:
        temps_A, temps_B = calculer_temps_vert(score_A, score_B)
        print(f"Score -> A: {score_A:4.1f}  B: {score_B:4.1f}  "
              f"=>  Temps de vert -> A: {temps_A:2d}s  B: {temps_B:2d}s  "
              f"(total = {temps_A + temps_B}s)")