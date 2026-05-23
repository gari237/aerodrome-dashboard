import sqlite3  # Importation du module sqlite3 pour interagir avec la base de données SQLite
 
DB = r"C:\Users\gkamm\Downloads\projet_aerodrome portoflio\NNN.db"  # Chemin absolu vers la base de données
 
# ============================================================================
# CONNEXION
# ============================================================================
def get_connection():
    conn = sqlite3.connect(DB)          # Ouvre une connexion à la base de données
    conn.row_factory = sqlite3.Row      # Permet d'accéder aux colonnes par nom (ex: row["Nom"])
    conn.execute("PRAGMA foreign_keys = ON")  # Active le respect des clés étrangères
    return conn                         # Retourne la connexion active
 
 
# ============================================================================
# 1. AFFICHER
# ============================================================================
def afficher(table):
    conn = sqlite3.connect(DB)      # Ouvre une connexion à la base de données
    conn.row_factory = sqlite3.Row  # Permet d'accéder aux colonnes par nom
    cur = conn.cursor()             # Crée un curseur pour exécuter les requêtes SQL
    cur.execute("SELECT * FROM " + table)  # Exécute la requête pour récupérer toutes les lignes
    lignes = cur.fetchall()         # Récupère toutes les lignes retournées
    conn.close()                    # Ferme la connexion à la base de données

    print("\n--- " + table + " ---")    # Affiche le nom de la table comme titre
    for ligne in lignes:               # Parcourt chaque ligne récupérée
        print(ligne)                   # Affiche la ligne dans le terminal

    return [dict(r) for r in lignes]   # Retourne aussi les données pour l'API
 
# ============================================================================
# 2. AJOUTER
# ============================================================================
def ajouter(table, valeurs):
    conn = sqlite3.connect(DB)      # Ouvre une connexion à la base de données
    cur = conn.cursor()             # Crée un curseur pour exécuter les requêtes SQL
 
    nb = len(valeurs)               # Calcule le nombre de valeurs à insérer
    questions = "?"                 # Initialise le premier placeholder SQL
    for i in range(nb - 1):         # Boucle pour ajouter les placeholders manquants
        questions = questions + ",?"  # Ajoute un placeholder "?" pour chaque valeur supplémentaire
 
    sql = "INSERT INTO " + table + " VALUES (" + questions + ")"  # Construit la requête INSERT dynamiquement
    cur.execute(sql, valeurs)       # Exécute la requête avec les valeurs passées en paramètre
    conn.commit()                   # Valide et enregistre les changements dans la base
    conn.close()                    # Ferme la connexion à la base de données
    print("Ajouté !")               # Confirme l'ajout dans le terminal
 
  
# ============================================================================
# 3. MODIFIER
# ============================================================================
def modifier(table, col_set, val_set, col_where, val_where):
    conn = sqlite3.connect(DB)      # Ouvre une connexion à la base de données
    cur = conn.cursor()             # Crée un curseur pour exécuter les requêtes SQL
 
    sql = "UPDATE " + table + " SET " + col_set + "=? WHERE " + col_where + "=?"  # Construit la requête UPDATE dynamiquement
    cur.execute(sql, (val_set, val_where))  # Exécute la requête avec les nouvelles valeurs et la condition
    conn.commit()                   # Valide et enregistre les changements dans la base
    conn.close()                    # Ferme la connexion à la base de données
    print("Modifié !")              # Confirme la modification dans le terminal
 
 
# ============================================================================
# 4. SUPPRIMER
# ============================================================================
def supprimer(table, col_where, val_where):
    conn = sqlite3.connect(DB)      # Ouvre une connexion à la base de données
    cur = conn.cursor()             # Crée un curseur pour exécuter les requêtes SQL
 
    sql = "DELETE FROM " + table + " WHERE " + col_where + "=?"  # Construit la requête DELETE dynamiquement
    cur.execute(sql, (val_where,))  # Exécute la requête avec la valeur de la condition (tuple obligatoire)
    conn.commit()                   # Valide et enregistre les changements dans la base
    conn.close()                    # Ferme la connexion à la base de données
    print("Supprimé !")             # Confirme la suppression dans le terminal
 
 
# ============================================================================
# 5. LIRE UN SEUL ENREGISTREMENT
# ============================================================================
def lire(table, col_where, val_where):
    conn = get_connection()         # Ouvre une connexion avec row_factory activé
    row = conn.execute(             # Exécute la requête SELECT avec une condition
        "SELECT * FROM " + table + " WHERE " + col_where + " = ?",  # Requête SQL dynamique
        [val_where]                 # Valeur de la condition passée en paramètre
    ).fetchall()                    # Récupère uniquement la première ligne correspondante
    conn.close()                    # Ferme la connexion à la base de données
    return dict(row) if row else None  # Retourne un dictionnaire si trouvé, sinon None
 
 
# ============================================================================
# 6. LIRE TOUTE UNE TABLE
# ============================================================================
# ============================================================================
# 8. LIRE PLUSIEURS ENREGISTREMENTS AVEC CONDITION
# ============================================================================
def lire_ou(table, col_where, val_where):
    conn = get_connection()         # Ouvre une connexion avec row_factory activé
    rows = conn.execute(            # Exécute la requête SELECT avec une condition
        "SELECT * FROM " + table + " WHERE " + col_where + " = ?",  # Requête dynamique
        [val_where]                 # Valeur de la condition
    ).fetchall()                    # Récupère TOUTES les lignes correspondantes
    conn.close()                    # Ferme la connexion
    return [dict(r) for r in rows]  # Retourne une liste de dictionnaires
 
# ============================================================================
# 7. REQUETE PERSONNALISEE
# ============================================================================
def requete(sql, params=[]):
    conn = get_connection()         # Ouvre une connexion avec row_factory activé
    rows = conn.execute(sql, params).fetchall()  # Exécute la requête SQL personnalisée avec ses paramètres
    conn.close()                    # Ferme la connexion à la base de données
    return [dict(r) for r in rows]  # Retourne une liste de dictionnaires pour chaque ligne
 
 
# ============================================================================
# EXEMPLES D'UTILISATION
# ============================================================================
if __name__ == "__main__":
 
    # Afficher toute la table Pilote
    modifier("Pilote","Nom","Pedro","Id_pilote","P001")
 
    # Ajouter un compte
    # ajouter("Compte", ("user1", "pass1", "pilote"))
 
    # Modifier le mot de passe d'un compte
    # modifier("Compte", "Mot_de_passe", "newpass", "Identifiant", "user1")
 
    # Supprimer un compte
    # supprimer("Compte", "Identifiant", "user1")
 
    # Lire un pilote spécifique
    # print(lire("Pilote", "Id_pilote", "P001"))
 
    # Lire tous les avions
    # print(lire_tout("Avion"))
 
