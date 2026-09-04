/*
  emonvo_feux.ino
  ----------------
  Gère les feux Voie A / Voie B, piloté normalement par le PC,
  avec un mode dégradé autonome en cas de panne de communication.

  MODES :
  - NORMAL          : suit les commandes du PC ("A:V", "A:R", "B:V", "B:R")
  - PASSAGE_SECURISE : transition interne avant de changer de mode
  - CLIGNOTANT      : signal visuel de 3s (jaune clignotant) au changement de mode
  - CYCLE_AUTONOME  : cycle fixe (20s/voie) si le PC ne répond plus

  SÉCURITÉ :
  - Transition jaune (1s) systématique avant tout passage au rouge
  - En mode dégradé, l'urgence est gérée directement par l'ESP32
    (le PC étant hors service, il ne peut plus relayer l'interrupteur)
  - Limite de 30s de vert forcé maximum en mode autonome (réarmement
    nécessaire : il faut relâcher puis rappuyer le bouton pour
    redéclencher une urgence après ce délai)
*/

// --- Broches (ESP32 DevKit V1, confirmées par le câblage réel) ---
// NOTE : Voie A et Voie B ont été permutées ici suite à une inversion
// de câblage constatée sur le breadboard (les noms de variables
// restent cohérents avec le reste du code, seuls les numéros de
// broches ont été échangés).
const int rougeA = 19;
const int jauneA = 21;
const int vertA  = 22;
const int rougeB = 4;
const int jauneB = 5;
const int vertB  = 18;
const int urgence = 23;

// --- États des voies en mode normal ---
String etatA = "rouge";
String etatB = "rouge";

// --- Détection de panne PC ---
unsigned long derniereCommandePC = 0;
const unsigned long DELAI_PANNE = 10000;  // 10s sans commande = PC considéré en panne

// --- Modes du système ---
enum ModeSysteme { NORMAL, CLIGNOTANT, CYCLE_AUTONOME };
ModeSysteme mode = NORMAL;

// --- Clignotement (3 secondes, transition de mode) ---
unsigned long clignDebut = 0;
unsigned long dernierToggle = 0;
const unsigned long DUREE_CLIGNOTEMENT = 3000;
const unsigned long INTERVALLE_TOGGLE = 500;
bool clignoteAllume = false;

// --- Cycle autonome (mode dégradé) ---
String voieActiveAutonome = "A";
String phaseAutonome = "vert";      // "vert" ou "jaune"
unsigned long phaseDebutAutonome = 0;
const unsigned long DUREE_VERT_FIXE = 20000;
const unsigned long DUREE_JAUNE_FIXE = 1000;

// --- Interrupteur d'urgence ---
bool urgenceActivePrecedente = false;
unsigned long dernierChangementUrgence = 0;
const unsigned long ANTI_REBOND_MS = 50;
bool urgenceGereeLocalement = false;  // true si l'ESP32 force le vert lui-même (mode dégradé)

// --- Limite de durée de l'urgence en mode autonome ---
unsigned long urgenceDebutAutonome = 0;
const unsigned long DUREE_URGENCE_MAX_AUTONOME = 30000;  // 30s max de vert forcé en mode autonome

void setup() {
  Serial.begin(9600);

  pinMode(rougeA, OUTPUT); pinMode(jauneA, OUTPUT); pinMode(vertA, OUTPUT);
  pinMode(rougeB, OUTPUT); pinMode(jauneB, OUTPUT); pinMode(vertB, OUTPUT);
  pinMode(urgence, INPUT_PULLUP);

  digitalWrite(rougeA, HIGH); digitalWrite(jauneA, LOW); digitalWrite(vertA, LOW);
  digitalWrite(rougeB, HIGH); digitalWrite(jauneB, LOW); digitalWrite(vertB, LOW);

  derniereCommandePC = millis();  // on démarre le chrono de surveillance
}

// ============================================================
// Fonctions de bas niveau (allumage, transitions sécurisées)
// ============================================================

void allumerVert(int pinRouge, int pinJaune, int pinVert, String &etat) {
  digitalWrite(pinRouge, LOW);
  digitalWrite(pinJaune, LOW);
  digitalWrite(pinVert, HIGH);
  etat = "vert";
}

void allumerRouge(int pinRouge, int pinJaune, int pinVert, String &etat) {
  if (etat == "vert") {
    digitalWrite(pinVert, LOW);
    digitalWrite(pinJaune, HIGH);
    etat = "jaune";
    delay(1000);  // transition de sécurité, brève et acceptée (comme validé sur le PoC)
  }
  digitalWrite(pinJaune, LOW);
  digitalWrite(pinRouge, HIGH);
  etat = "rouge";
}

void toutRougeImmediat() {
  digitalWrite(vertA, LOW); digitalWrite(jauneA, LOW); digitalWrite(rougeA, HIGH);
  digitalWrite(vertB, LOW); digitalWrite(jauneB, LOW); digitalWrite(rougeB, HIGH);
  etatA = "rouge"; etatB = "rouge";
}

// ============================================================
// Traitement des commandes venant du PC (mode normal uniquement)
// ============================================================

void traiterCommande(String commande) {
  commande.trim();
  if (commande.length() < 3) return;

  char voie = commande.charAt(0);
  char couleur = commande.charAt(2);

  if (voie == 'A') {
    if (couleur == 'V') allumerVert(rougeA, jauneA, vertA, etatA);
    else if (couleur == 'R') allumerRouge(rougeA, jauneA, vertA, etatA);
  } else if (voie == 'B') {
    if (couleur == 'V') allumerVert(rougeB, jauneB, vertB, etatB);
    else if (couleur == 'R') allumerRouge(rougeB, jauneB, vertB, etatB);
  }
}

// ============================================================
// Gestion de l'urgence (interrupteur) — commune à tous les modes
// ============================================================

void verifierUrgence() {
  bool boutonAppuye = (digitalRead(urgence) == LOW);

  if (boutonAppuye != urgenceActivePrecedente) {
    unsigned long maintenant = millis();
    if (maintenant - dernierChangementUrgence > ANTI_REBOND_MS) {
      urgenceActivePrecedente = boutonAppuye;
      dernierChangementUrgence = maintenant;

      // On informe toujours le PC, même s'il ne répond plus (au cas où il écoute encore)
      Serial.println(boutonAppuye ? "URGENCE:1" : "URGENCE:0");

      // En mode dégradé, le PC ne peut pas relayer l'urgence : l'ESP32 la gère seul.
      if (mode == CYCLE_AUTONOME) {
        if (boutonAppuye) {
          // Priorité Voie A (règle fixée pour le PoC), transition sécurisée depuis l'état courant
          allumerRouge(rougeB, jauneB, vertB, etatB);
          allumerVert(rougeA, jauneA, vertA, etatA);
          urgenceGereeLocalement = true;
          urgenceDebutAutonome = millis();   // démarrage du chrono des 30s max
        } else if (urgenceGereeLocalement) {
          // Fin de l'urgence locale (relâchement du bouton) : on relance proprement le cycle autonome
          allumerRouge(rougeA, jauneA, vertA, etatA);
          voieActiveAutonome = "A";
          phaseAutonome = "vert";
          phaseDebutAutonome = millis();
          allumerVert(rougeA, jauneA, vertA, etatA);
          urgenceGereeLocalement = false;
        }
      }
    }
  }
}

// ============================================================
// Boucle principale
// ============================================================

void loop() {
  verifierUrgence();

  // --- Réception d'une commande PC ---
  if (Serial.available() > 0) {
    String commande = Serial.readStringUntil('\n');
    commande.trim();

    if (commande.length() >= 3) {
      derniereCommandePC = millis();  // preuve de vie du PC

      if (mode != NORMAL) {
        // Le PC revient : on quitte proprement le mode dégradé avant d'exécuter sa commande
        if (etatA == "vert") allumerRouge(rougeA, jauneA, vertA, etatA);
        if (etatB == "vert") allumerRouge(rougeB, jauneB, vertB, etatB);
        mode = NORMAL;
      }

      traiterCommande(commande);
    }
  }

  // --- Détection de panne PC (uniquement si on est encore en mode normal) ---
  if (mode == NORMAL && (millis() - derniereCommandePC > DELAI_PANNE)) {
    if (etatA == "vert") allumerRouge(rougeA, jauneA, vertA, etatA);
    if (etatB == "vert") allumerRouge(rougeB, jauneB, vertB, etatB);
    mode = CLIGNOTANT;
    clignDebut = millis();
    dernierToggle = millis();
    clignoteAllume = false;
  }

  // --- Mode CLIGNOTANT : jaune simultané pendant 3 secondes ---
  if (mode == CLIGNOTANT) {
    if (millis() - dernierToggle >= INTERVALLE_TOGGLE) {
      clignoteAllume = !clignoteAllume;
      digitalWrite(jauneA, clignoteAllume ? HIGH : LOW);
      digitalWrite(jauneB, clignoteAllume ? HIGH : LOW);
      dernierToggle = millis();
    }
    if (millis() - clignDebut >= DUREE_CLIGNOTEMENT) {
      digitalWrite(jauneA, LOW);
      digitalWrite(jauneB, LOW);
      mode = CYCLE_AUTONOME;
      voieActiveAutonome = "A";
      phaseAutonome = "vert";
      phaseDebutAutonome = millis();
      allumerVert(rougeA, jauneA, vertA, etatA);
    }
  }

  // --- Limite de 30s pour l'urgence en mode autonome ---
  if (mode == CYCLE_AUTONOME && urgenceGereeLocalement) {
    if (millis() - urgenceDebutAutonome >= DUREE_URGENCE_MAX_AUTONOME) {
      // Le temps est écoulé : on reprend le cycle autonome normal,
      // même si le bouton est toujours appuyé (il faudra le relâcher
      // puis le rappuyer pour redéclencher une nouvelle urgence).
      allumerRouge(rougeA, jauneA, vertA, etatA);
      voieActiveAutonome = "A";
      phaseAutonome = "vert";
      phaseDebutAutonome = millis();
      allumerVert(rougeA, jauneA, vertA, etatA);
      urgenceGereeLocalement = false;
    }
  }

  // --- Mode CYCLE_AUTONOME : cycle fixe 20s vert / 1s jaune, sans le PC ---
  if (mode == CYCLE_AUTONOME && !urgenceGereeLocalement) {
    unsigned long ecoule = millis() - phaseDebutAutonome;

    if (phaseAutonome == "vert" && ecoule >= DUREE_VERT_FIXE) {
      if (voieActiveAutonome == "A") allumerRouge(rougeA, jauneA, vertA, etatA);
      else allumerRouge(rougeB, jauneB, vertB, etatB);

      voieActiveAutonome = (voieActiveAutonome == "A") ? "B" : "A";
      phaseAutonome = "vert";
      phaseDebutAutonome = millis();

      if (voieActiveAutonome == "A") allumerVert(rougeA, jauneA, vertA, etatA);
      else allumerVert(rougeB, jauneB, vertB, etatB);
    }
  }
}