import sqlite3
import random
from datetime import datetime, timedelta

DB = r"C:\Users\gkamm\Downloads\projet_aerodrome portoflio\NNN.db"

conn = sqlite3.connect(DB)
cur = conn.cursor()
random.seed(42)

def date_aleatoire():
    debut = datetime(2025, 11, 1)
    return debut + timedelta(days=random.randint(0, 180))

# Données existantes
immatriculations = [r[0] for r in cur.execute("SELECT Immatriculation FROM Avion").fetchall()]
pilotes = [r[0] for r in cur.execute("SELECT Id_pilote FROM Pilote").fetchall()]
agents = [r[0] for r in cur.execute("SELECT Id_agent FROM Agent").fetchall()]
gestionnaires = [r[0] for r in cur.execute("SELECT Id_gestionnaire FROM Gestionnaire").fetchall()]
statuts = ["Acheve", "Acheve", "Acheve", "Confirme", "Annule"]

# Ajouter plus d'avions — plusieurs par pilote
print("Ajout d'avions supplémentaires...")
marques = ["Cessna", "Piper", "Beechcraft", "Robin", "Socata"]
types = ["C172", "PA28", "B36TC", "DR400", "TB20"]
immat_existantes = set(immatriculations)
nouvelles_immat = []
compteur = 0
for pilote in pilotes:
    for j in range(3):  # 3 avions par pilote
        immat = f"F-Z{pilote[1:]}{j:02d}"
        if immat not in immat_existantes:
            try:
                cur.execute(
                    "INSERT INTO Avion (Immatriculation, Type, Marque, Id_pilote) VALUES (?, ?, ?, ?)",
                    (immat, random.choice(types), random.choice(marques), pilote)
                )
                immat_existantes.add(immat)
                nouvelles_immat.append(immat)
                compteur += 1
            except:
                pass

print(f"  {compteur} avions ajoutés")

# Recharge toutes les immatriculations
toutes_immat = [r[0] for r in cur.execute("SELECT Immatriculation FROM Avion").fetchall()]

# Supprimer les anciens créneaux générés
cur.execute("DELETE FROM Creneaux WHERE Id_creneaux LIKE 'CR0%' AND Id_creneaux > 'CR015'")
cur.execute("DELETE FROM Creneaux WHERE Id_creneaux LIKE 'CR1%'")

# Ajouter 300 créneaux répartis sur tous les pilotes
print("Ajout des créneaux...")
compteur = 0
for i in range(16, 316):
    date = date_aleatoire()
    heure_debut = random.randint(6, 17)
    heure_fin = heure_debut + random.randint(1, 3)
    statut = random.choice(statuts)
    immat = random.choice(toutes_immat)
    id_creneau = f"CR{i:04d}"
    date_str = date.strftime("%Y-%m-%d")
    heure_debut_str = f"{heure_debut:02d}:00:00"
    heure_fin_str = f"{heure_fin:02d}:00:00"
    try:
        cur.execute("""
            INSERT INTO Creneaux (Id_creneaux, Date, Heure_debut, Heure_fin, Status, Immatriculation)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (id_creneau, date_str, heure_debut_str, heure_fin_str, statut, immat))
        compteur += 1
    except:
        pass

print(f"  {compteur} créneaux ajoutés")

# Supprimer les anciennes factures générées
cur.execute("DELETE FROM Facture WHERE Num_Facture > 'FAC015'")
cur.execute("DELETE FROM Visualise WHERE Num_Facture > 'FAC015'")

# Ajouter 250 factures — plusieurs par pilote
print("Ajout des factures...")
compteur = 0
for i in range(16, 266):
    date = date_aleatoire()
    montant = round(random.uniform(50, 800), 2)
    id_facture = f"FAC{i:03d}"
    id_agent = random.choice(agents)
    id_gestionnaire = random.choice(gestionnaires)
    pilote = random.choice(pilotes)
    try:
        cur.execute("""
            INSERT INTO Facture (Num_Facture, Date, Heure, Montant, Nom, Id_gestionnaire, Id_agent)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (id_facture, date.strftime("%Y-%m-%d"),
              f"{random.randint(8,18):02d}:00:00",
              montant, f"Facture {pilote} {id_facture}",
              id_gestionnaire, id_agent))
        cur.execute("""
            INSERT INTO Visualise (Num_Facture, Id_pilote)
            VALUES (?, ?)
        """, (id_facture, pilote))
        compteur += 1
    except:
        pass

print(f"  {compteur} factures ajoutées")

# Ajouter des messages pour chaque pilote/agent
print("Ajout des messages...")
compteur = 0
sujets = ["Demande créneau", "Question carburant", "Problème parking",
          "Demande maintenance", "Confirmation vol", "Annulation créneau"]
for i in range(50):
    try:
        cur.execute("""
            INSERT INTO Messagerie (Id_agent, Id_pilote, Objet, Date, Heure, Status)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (random.choice(agents), random.choice(pilotes),
              random.choice(sujets),
              date_aleatoire().strftime("%Y-%m-%d"),
              f"{random.randint(8,18):02d}:00:00",
              random.choice(["Lu", "Non lu", "Repondu"])))
        compteur += 1
    except:
        pass

print(f"  {compteur} messages ajoutés")

conn.commit()
conn.close()
print("\n✅ Base enrichie avec succès !")
print("Résumé :")

# Vérification finale
conn2 = sqlite3.connect(DB)
cur2 = conn2.cursor()
for table in ["Avion", "Creneaux", "Facture", "Visualise", "Messagerie"]:
    count = cur2.execute(f"SELECT COUNT(*) FROM {table}").fetchone()[0]
    print(f"  {table} : {count} lignes")
conn2.close()