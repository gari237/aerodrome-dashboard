from fastapi import FastAPI, HTTPException, Header  # FastAPI pour créer l'API, HTTPException pour les erreurs, Header pour lire les en-têtes HTTP
from pydantic import BaseModel  # BaseModel pour valider les données reçues dans le body
from typing import Any, Dict, Optional  # Types Python pour les annotations
import crud as db  # Module CRUD pour les opérations sur la base de données
import auth  # Module d'authentification et de gestion des rôles
import metier  # Module métier contenant la logique fonctionnelle

app = FastAPI(title="API Aérodrome", version="2.0")  # Création de l'application FastAPI avec titre et version


# ============================================================
# SCHEMA GENERIQUE
# ============================================================
class Corps(BaseModel):  # Schéma générique pour les body JSON de type {"data": {...}}
    data: Dict[str, Any]  # Dictionnaire clé-valeur acceptant n'importe quel type de valeur


# Définition des rôles autorisés par table — contrôle d'accès centralisé
ACCES_TABLE = {
    "Pilote":              ["pilote", "agent", "gestionnaire"],   # CORRIGÉ : pilote peut lire sa propre fiche
    "Compte":              ["gestionnaire"],                       # Uniquement le gestionnaire voit les comptes
    "Facture":             ["pilote", "agent", "gestionnaire"],   # CORRIGÉ : pilote peut voir les factures
    "Visualise":           ["pilote", "agent", "gestionnaire"],   # CORRIGÉ : pilote peut voir la table de liaison
    "Infrastructures":     ["gestionnaire"],                       # Uniquement le gestionnaire gère les infras
    "Infrastructure":      ["gestionnaire"],                       # Alias au cas où le nom varie dans la base
    "Creneaux":            ["pilote", "agent", "gestionnaire"],   # CORRIGÉ : pilote peut voir les créneaux
    "Avion":               ["pilote", "agent", "gestionnaire"],   # Tous les rôles peuvent voir les avions
    "Messagerie":          ["pilote", "agent", "gestionnaire"],   # CORRIGÉ : pilote peut voir ses messages
    "Service_carburant":   ["agent", "gestionnaire"],             # Agent et gestionnaire gèrent le carburant
    "Service_maintenance": ["agent", "gestionnaire"],             # Agent et gestionnaire gèrent la maintenance
    "Service_parking":     ["agent", "gestionnaire"],             # Agent et gestionnaire gèrent le parking
}


# ============================================================
# AUTHENTIFICATION
# POST /login
# ============================================================
@app.post("/login", tags=["Auth"])  # Endpoint de connexion accessible sans authentification
def login(identifiant: str, mot_de_passe: str):  # Reçoit identifiant et mot de passe en paramètres
    return auth.authentifier(identifiant, mot_de_passe)  # Délègue la vérification au module auth


# ============================================================
# ROUTES GENERIQUES (avec restriction de rôle)
# ============================================================

@app.get("/table/{table}", tags=["Generique"])  # Endpoint générique pour lire n'importe quelle table
def get_tout(table: str,  # Nom de la table à lire
             x_identifiant: Optional[str] = Header(None),  # Header optionnel : identifiant utilisateur
             x_mot_de_passe: Optional[str] = Header(None)):  # Header optionnel : mot de passe utilisateur
    if not x_identifiant or not x_mot_de_passe:  # Vérifie que les credentials sont présents
        raise HTTPException(status_code=401, detail="Authentification requise.")  # Retourne 401 si absent
    info = auth.authentifier(x_identifiant, x_mot_de_passe)  # Vérifie les credentials et récupère le rôle
    roles_ok = ACCES_TABLE.get(table, ["gestionnaire"])  # Récupère les rôles autorisés pour cette table
    auth.exiger_role(info, roles_ok)  # Lève 403 si le rôle de l'utilisateur n'est pas dans la liste
    try:
        return db.afficher(table)  # Retourne toutes les lignes de la table
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))  # Retourne 400 si erreur base de données


@app.get("/table/{table}/{colonne}/{valeur}", tags=["Generique"])  # Endpoint pour lire avec filtre
def get_un(table: str, colonne: str, valeur: str,  # Table, colonne et valeur pour le filtre WHERE
           x_identifiant: Optional[str] = Header(None),  # Header optionnel : identifiant
           x_mot_de_passe: Optional[str] = Header(None)):  # Header optionnel : mot de passe
    if not x_identifiant or not x_mot_de_passe:  # Vérifie que les credentials sont présents
        raise HTTPException(status_code=401, detail="Authentification requise.")  # Retourne 401 si absent
    info = auth.authentifier(x_identifiant, x_mot_de_passe)  # Vérifie les credentials
    roles_ok = ACCES_TABLE.get(table, ["gestionnaire"])  # Récupère les rôles autorisés
    auth.exiger_role(info, roles_ok)  # Vérifie le rôle
    resultats = db.lire_ou(table, colonne, valeur)  # Cherche les lignes correspondant au filtre
    if not resultats:  # Si aucun résultat trouvé
        raise HTTPException(status_code=404, detail=f"{table} non trouvé")  # Retourne 404
    return resultats  # Retourne les résultats trouvés


@app.post("/table/{table}", tags=["Generique"])  # Endpoint générique pour insérer dans une table
def post_un(table: str, corps: Corps,  # Nom de la table et données à insérer
            x_identifiant: Optional[str] = Header(None),  # Header optionnel : identifiant
            x_mot_de_passe: Optional[str] = Header(None)):  # Header optionnel : mot de passe
    if not x_identifiant or not x_mot_de_passe:  # Vérifie que les credentials sont présents
        raise HTTPException(status_code=401, detail="Authentification requise.")  # Retourne 401
    info = auth.authentifier(x_identifiant, x_mot_de_passe)  # Vérifie les credentials
    auth.exiger_role(info, ["gestionnaire"])  # Seul le gestionnaire peut insérer via route générique
    try:
        db.ajouter(table, tuple(corps.data.values()))  # Insère les données dans la table
        return {"message": f"Ajouté dans {table} avec succès"}  # Message de confirmation
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))  # Retourne 400 si erreur


@app.put("/table/{table}/{col_where}/{val_where}", tags=["Generique"])  # Endpoint générique pour modifier
def put_un(table: str, col_where: str, val_where: str, corps: Corps,  # Table, filtre WHERE et nouvelles données
           x_identifiant: Optional[str] = Header(None),  # Header optionnel : identifiant
           x_mot_de_passe: Optional[str] = Header(None)):  # Header optionnel : mot de passe
    if not x_identifiant or not x_mot_de_passe:  # Vérifie que les credentials sont présents
        raise HTTPException(status_code=401, detail="Authentification requise.")  # Retourne 401
    info = auth.authentifier(x_identifiant, x_mot_de_passe)  # Vérifie les credentials
    auth.exiger_role(info, ["gestionnaire"])  # Seul le gestionnaire peut modifier via route générique
    try:
        db.modifier(  # Appelle la fonction modifier du module CRUD
            table,
            corps.data["col_set"],  # Colonne à modifier
            corps.data["val_set"],  # Nouvelle valeur
            col_where,  # Colonne du filtre WHERE
            val_where   # Valeur du filtre WHERE
        )
        return {"message": f"{table} modifié avec succès"}  # Message de confirmation
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))  # Retourne 400 si erreur


@app.delete("/table/{table}/{colonne}/{valeur}", tags=["Generique"])  # Endpoint générique pour supprimer
def delete_un(table: str, colonne: str, valeur: str,  # Table et filtre pour la suppression
              x_identifiant: Optional[str] = Header(None),  # Header optionnel : identifiant
              x_mot_de_passe: Optional[str] = Header(None)):  # Header optionnel : mot de passe
    if not x_identifiant or not x_mot_de_passe:  # Vérifie que les credentials sont présents
        raise HTTPException(status_code=401, detail="Authentification requise.")  # Retourne 401
    info = auth.authentifier(x_identifiant, x_mot_de_passe)  # Vérifie les credentials
    auth.exiger_role(info, ["gestionnaire"])  # Seul le gestionnaire peut supprimer via route générique
    try:
        db.supprimer(table, colonne, valeur)  # Supprime les lignes correspondant au filtre
        return {"message": f"Supprimé de {table} avec succès"}  # Message de confirmation
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))  # Retourne 400 si erreur


# ============================================================
# MODULE 1 — CRÉNEAUX ET MOUVEMENTS AÉRIENS
# ============================================================

@app.post("/creneau/demander", tags=["Créneaux"])  # Endpoint pour demander un créneau de vol
def route_demander_creneau(corps: Corps,  # Body contenant les données du créneau
                           x_identifiant: str = Header(...),  # Header obligatoire : identifiant
                           x_mot_de_passe: str = Header(...)):  # Header obligatoire : mot de passe
    info = auth.authentifier(x_identifiant, x_mot_de_passe)  # Vérifie les credentials
    auth.exiger_role(info, ["pilote", "agent"])  # Seuls pilote et agent peuvent demander un créneau
    d = corps.data  # Extrait les données du body
    return metier.demander_creneau(  # Délègue la logique métier au module metier
        d["id_creneaux"], d["date"], d["heure_debut"], d["heure_fin"],
        d["immatriculation"], d.get("num_emplacement"), d.get("numero"), d.get("type_maintenance")
    )


@app.put("/creneau/statut/{id_creneaux}", tags=["Créneaux"])  # Endpoint pour modifier le statut d'un créneau
def route_modifier_statut(id_creneaux: str, corps: Corps,  # ID du créneau et nouveau statut
                          x_identifiant: str = Header(...),  # Header obligatoire : identifiant
                          x_mot_de_passe: str = Header(...)):  # Header obligatoire : mot de passe
    info = auth.authentifier(x_identifiant, x_mot_de_passe)  # Vérifie les credentials
    auth.exiger_role(info, ["agent", "gestionnaire"])  # Agent et gestionnaire peuvent modifier le statut
    return metier.modifier_statut_creneau(id_creneaux, corps.data["statut"])  # Appelle la logique métier


@app.put("/creneau/annuler/{id_creneaux}", tags=["Créneaux"])  # Endpoint pour annuler un créneau
def route_annuler_creneau(id_creneaux: str,  # ID du créneau à annuler
                          x_identifiant: str = Header(...),  # Header obligatoire : identifiant
                          x_mot_de_passe: str = Header(...)):  # Header obligatoire : mot de passe
    info = auth.authentifier(x_identifiant, x_mot_de_passe)  # Vérifie les credentials
    auth.exiger_role(info, ["pilote", "agent"])  # Pilote et agent peuvent annuler un créneau
    return metier.annuler_creneau(id_creneaux)  # Appelle la logique métier d'annulation


@app.get("/creneau/mouvements/{filtre}", tags=["Créneaux"])  # Endpoint pour voir les mouvements filtrés
def route_voir_mouvements(filtre: str,  # Filtre sur les mouvements (date, statut, etc.)
                          x_identifiant: str = Header(...),  # Header obligatoire : identifiant
                          x_mot_de_passe: str = Header(...)):  # Header obligatoire : mot de passe
    info = auth.authentifier(x_identifiant, x_mot_de_passe)  # Vérifie les credentials
    auth.exiger_role(info, ["agent", "gestionnaire"])  # Agent et gestionnaire voient les mouvements
    return metier.voir_mouvements(filtre)  # Appelle la logique métier


# ============================================================
# MODULE 2 — SERVICES AU SOL ET INFRASTRUCTURES
# ============================================================

@app.post("/service/parking", tags=["Services"])  # Endpoint pour demander un service de parking
def route_service_parking(corps: Corps,  # Body contenant num_emplacement et id_creneaux
                          x_identifiant: str = Header(...),  # Header obligatoire : identifiant
                          x_mot_de_passe: str = Header(...)):  # Header obligatoire : mot de passe
    info = auth.authentifier(x_identifiant, x_mot_de_passe)  # Vérifie les credentials
    auth.exiger_role(info, ["pilote", "agent"])  # Pilote et agent peuvent demander le parking
    d = corps.data  # Extrait les données du body
    return metier.demander_service_parking(d["num_emplacement"], d["id_creneaux"])  # Logique métier


@app.post("/service/carburant", tags=["Services"])  # Endpoint pour demander un service de carburant
def route_service_carburant(corps: Corps,  # Body contenant numero et id_creneaux
                            x_identifiant: str = Header(...),  # Header obligatoire : identifiant
                            x_mot_de_passe: str = Header(...)):  # Header obligatoire : mot de passe
    info = auth.authentifier(x_identifiant, x_mot_de_passe)  # Vérifie les credentials
    auth.exiger_role(info, ["pilote", "agent"])  # Pilote et agent peuvent demander le carburant
    d = corps.data  # Extrait les données du body
    return metier.demander_service_carburant(d["numero"], d["id_creneaux"])  # Logique métier


@app.post("/service/maintenance", tags=["Services"])  # Endpoint pour demander une maintenance
def route_service_maintenance(corps: Corps,  # Body contenant type_maintenance et id_creneaux
                              x_identifiant: str = Header(...),  # Header obligatoire : identifiant
                              x_mot_de_passe: str = Header(...)):  # Header obligatoire : mot de passe
    info = auth.authentifier(x_identifiant, x_mot_de_passe)  # Vérifie les credentials
    auth.exiger_role(info, ["pilote", "agent"])  # Pilote et agent peuvent demander la maintenance
    d = corps.data  # Extrait les données du body
    return metier.demander_service_maintenance(d["type_maintenance"], d["id_creneaux"])  # Logique métier


@app.post("/infrastructure", tags=["Infrastructures"])  # Endpoint pour gérer les infrastructures
def route_gerer_infra(corps: Corps,  # Body contenant action, id_infra, type_infra, materiaux, emplacement
                      x_identifiant: str = Header(...),  # Header obligatoire : identifiant
                      x_mot_de_passe: str = Header(...)):  # Header obligatoire : mot de passe
    info = auth.authentifier(x_identifiant, x_mot_de_passe)  # Vérifie les credentials
    auth.exiger_role(info, ["gestionnaire"])  # Seul le gestionnaire gère les infrastructures
    d = corps.data  # Extrait les données du body
    return metier.gerer_infrastructure(  # Délègue la logique métier
        d["action"], d["id_infra"], d["type_infra"], d["materiaux"], d["emplacement"]
    )


# ============================================================
# MODULE 3 — FACTURATION
# ============================================================

@app.post("/facture/generer", tags=["Facturation"])  # Endpoint pour générer une facture
def route_generer_facture(corps: Corps,  # Body contenant les données de la facture
                          x_identifiant: str = Header(...),  # Header obligatoire : identifiant
                          x_mot_de_passe: str = Header(...)):  # Header obligatoire : mot de passe
    info = auth.authentifier(x_identifiant, x_mot_de_passe)  # Vérifie les credentials
    auth.exiger_role(info, ["agent", "gestionnaire", "pilote"])  # Agent, gestionnaire et pilote peuvent générer
    d = corps.data  # Extrait les données du body
    return metier.generer_facture(  # Délègue la logique métier
        d["num_facture"], d["date"], d["heure"],
        d["nom"], d["id_agent"], d["id_gestionnaire"], d["id_creneaux"]
    )


@app.get("/facture/pilote/{id_pilote}", tags=["Facturation"])  # Endpoint pour voir les factures d'un pilote
def route_voir_factures(id_pilote: str,  # ID du pilote dont on veut les factures
                        x_identifiant: str = Header(...),  # Header obligatoire : identifiant
                        x_mot_de_passe: str = Header(...)):  # Header obligatoire : mot de passe
    info = auth.authentifier(x_identifiant, x_mot_de_passe)  # Vérifie les credentials
    auth.exiger_role(info, ["pilote", "agent", "gestionnaire"])  # Tous les rôles peuvent voir
    auth.exiger_proprio(info, id_pilote)  # Un pilote ne peut voir que ses propres factures
    return metier.voir_factures_pilote(id_pilote)  # Retourne les factures du pilote


@app.get("/facture/recettes/{periode}/{valeur}", tags=["Facturation"])  # Endpoint pour voir les recettes
def route_voir_recettes(periode: str, valeur: str,  # Période et valeur pour filtrer les recettes
                        x_identifiant: str = Header(...),  # Header obligatoire : identifiant
                        x_mot_de_passe: str = Header(...)):  # Header obligatoire : mot de passe
    info = auth.authentifier(x_identifiant, x_mot_de_passe)  # Vérifie les credentials
    auth.exiger_role(info, ["gestionnaire"])  # Seul le gestionnaire voit les recettes globales
    return metier.voir_recettes(periode, valeur)  # Retourne les recettes filtrées


# ============================================================
# MODULE 4 — REPORTING
# ============================================================

@app.get("/reporting/mouvements/{periode}/{valeur}", tags=["Reporting"])  # Endpoint rapport mouvements
def route_rapport_mouvements(periode: str, valeur: str,  # Période et valeur pour le rapport
                             x_identifiant: str = Header(...),  # Header obligatoire : identifiant
                             x_mot_de_passe: str = Header(...)):  # Header obligatoire : mot de passe
    info = auth.authentifier(x_identifiant, x_mot_de_passe)  # Vérifie les credentials
    auth.exiger_role(info, ["gestionnaire"])  # Seul le gestionnaire accède au rapport mouvements
    return metier.rapport_mouvements(periode, valeur)  # Retourne le rapport


@app.get("/reporting/aeronef/{immatriculation}", tags=["Reporting"])  # Endpoint rapport historique aéronef
def route_rapport_aeronef(immatriculation: str,  # Immatriculation de l'aéronef
                          x_identifiant: str = Header(...),  # Header obligatoire : identifiant
                          x_mot_de_passe: str = Header(...)):  # Header obligatoire : mot de passe
    info = auth.authentifier(x_identifiant, x_mot_de_passe)  # Vérifie les credentials
    auth.exiger_role(info, ["agent", "gestionnaire"])  # Agent et gestionnaire accèdent au rapport aéronef
    return metier.rapport_historique_aeronef(immatriculation)  # Retourne l'historique de l'aéronef


@app.get("/reporting/occupation", tags=["Reporting"])  # Endpoint rapport occupation des infrastructures
def route_rapport_occupation(x_identifiant: str = Header(...),  # Header obligatoire : identifiant
                             x_mot_de_passe: str = Header(...)):  # Header obligatoire : mot de passe
    info = auth.authentifier(x_identifiant, x_mot_de_passe)  # Vérifie les credentials
    auth.exiger_role(info, ["gestionnaire"])  # Seul le gestionnaire voit le rapport d'occupation
    return metier.rapport_occupation_infra()  # Retourne le rapport d'occupation