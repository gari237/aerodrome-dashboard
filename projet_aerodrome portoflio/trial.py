from fastapi import FastAPI, HTTPException, Header
from pydantic import BaseModel
from typing import Any, Dict
import crud as db
import auth
import metier

app = FastAPI(title="API Aérodrome", version="2.0")


# ============================================================
# SCHEMA GENERIQUE
# ============================================================
class Corps(BaseModel):
    data: Dict[str, Any]


# ============================================================
# AUTHENTIFICATION
# POST /login
# ============================================================
@app.post("/login", tags=["Auth"])
def login(identifiant: str, mot_de_passe: str):
    return auth.authentifier(identifiant, mot_de_passe)


# ============================================================
# ROUTES GENERIQUES (sans restriction de rôle)
# ============================================================

@app.get("/table/{table}", tags=["Generique"])
def get_tout(table: str):
    try:
        return db.afficher(table)
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@app.get("/table/{table}/{colonne}/{valeur}", tags=["Generique"])
def get_un(table: str, colonne: str, valeur: str):
    resultats = db.lire_ou(table, colonne, valeur)
    if not resultats:
        raise HTTPException(status_code=404, detail=f"{table} non trouvé")
    return resultats


@app.post("/table/{table}", tags=["Generique"])
def post_un(table: str, corps: Corps):
    try:
        db.ajouter(table, tuple(corps.data.values()))
        return {"message": f"Ajouté dans {table} avec succès"}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@app.put("/table/{table}/{col_where}/{val_where}", tags=["Generique"])
def put_un(table: str, col_where: str, val_where: str, corps: Corps):
    try:
        db.modifier(
            table,
            corps.data["col_set"],
            corps.data["val_set"],
            col_where,
            val_where
        )
        return {"message": f"{table} modifié avec succès"}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@app.delete("/table/{table}/{colonne}/{valeur}", tags=["Generique"])
def delete_un(table: str, colonne: str, valeur: str):
    try:
        db.supprimer(table, colonne, valeur)
        return {"message": f"Supprimé de {table} avec succès"}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


# ============================================================
# MODULE 1 — CRÉNEAUX ET MOUVEMENTS AÉRIENS
# ============================================================

@app.post("/creneau/demander", tags=["Créneaux"])
def route_demander_creneau(corps: Corps,
                           x_identifiant: str = Header(...),
                           x_mot_de_passe: str = Header(...)):
    # Pilote et agent peuvent demander un créneau
    info = auth.authentifier(x_identifiant, x_mot_de_passe)
    auth.exiger_role(info, ["pilote", "agent"])
    d = corps.data
    return metier.demander_creneau(
        d["id_creneaux"], d["date"], d["heure_debut"], d["heure_fin"],
        d["immatriculation"], d.get("num_emplacement"), d.get("numero"), d.get("type_maintenance")
    )


@app.put("/creneau/statut/{id_creneaux}", tags=["Créneaux"])
def route_modifier_statut(id_creneaux: str, corps: Corps,
                          x_identifiant: str = Header(...),
                          x_mot_de_passe: str = Header(...)):
    # Agent uniquement peut changer le statut
    info = auth.authentifier(x_identifiant, x_mot_de_passe)
    auth.exiger_role(info, ["agent"])
    return metier.modifier_statut_creneau(id_creneaux, corps.data["statut"])


@app.put("/creneau/annuler/{id_creneaux}", tags=["Créneaux"])
def route_annuler_creneau(id_creneaux: str,
                          x_identifiant: str = Header(...),
                          x_mot_de_passe: str = Header(...)):
    # Pilote et agent peuvent annuler
    info = auth.authentifier(x_identifiant, x_mot_de_passe)
    auth.exiger_role(info, ["pilote", "agent"])
    return metier.annuler_creneau(id_creneaux)


@app.get("/creneau/mouvements/{filtre}", tags=["Créneaux"])
def route_voir_mouvements(filtre: str,
                          x_identifiant: str = Header(...),
                          x_mot_de_passe: str = Header(...)):
    # Agent et gestionnaire peuvent voir les mouvements
    info = auth.authentifier(x_identifiant, x_mot_de_passe)
    auth.exiger_role(info, ["agent", "gestionnaire"])
    return metier.voir_mouvements(filtre)


# ============================================================
# MODULE 2 — SERVICES AU SOL ET INFRASTRUCTURES
# ============================================================

@app.post("/service/parking", tags=["Services"])
def route_service_parking(corps: Corps,
                          x_identifiant: str = Header(...),
                          x_mot_de_passe: str = Header(...)):
    # Pilote et agent peuvent demander un parking
    info = auth.authentifier(x_identifiant, x_mot_de_passe)
    auth.exiger_role(info, ["pilote", "agent"])
    d = corps.data
    return metier.demander_service_parking(d["num_emplacement"], d["id_creneaux"])


@app.post("/service/carburant", tags=["Services"])
def route_service_carburant(corps: Corps,
                            x_identifiant: str = Header(...),
                            x_mot_de_passe: str = Header(...)):
    # Pilote et agent peuvent demander du carburant
    info = auth.authentifier(x_identifiant, x_mot_de_passe)
    auth.exiger_role(info, ["pilote", "agent"])
    d = corps.data
    return metier.demander_service_carburant(d["numero"], d["id_creneaux"])


@app.post("/service/maintenance", tags=["Services"])
def route_service_maintenance(corps: Corps,
                              x_identifiant: str = Header(...),
                              x_mot_de_passe: str = Header(...)):
    # Pilote et agent peuvent demander une maintenance
    info = auth.authentifier(x_identifiant, x_mot_de_passe)
    auth.exiger_role(info, ["pilote", "agent"])
    d = corps.data
    return metier.demander_service_maintenance(d["type_maintenance"], d["id_creneaux"])


@app.post("/infrastructure", tags=["Infrastructures"])
def route_gerer_infra(corps: Corps,
                      x_identifiant: str = Header(...),
                      x_mot_de_passe: str = Header(...)):
    # Gestionnaire uniquement
    info = auth.authentifier(x_identifiant, x_mot_de_passe)
    auth.exiger_role(info, ["gestionnaire"])
    d = corps.data
    return metier.gerer_infrastructure(
        d["action"], d["id_infra"], d["type_infra"], d["materiaux"], d["emplacement"]
    )


# ============================================================
# MODULE 3 — FACTURATION
# ============================================================

@app.post("/facture/generer", tags=["Facturation"])
def route_generer_facture(corps: Corps,
                          x_identifiant: str = Header(...),
                          x_mot_de_passe: str = Header(...)):
    # Agent uniquement peut générer une facture
    info = auth.authentifier(x_identifiant, x_mot_de_passe)
    auth.exiger_role(info, ["agent"])
    d = corps.data
    return metier.generer_facture(
        d["num_facture"], d["date"], d["heure"],
        d["nom"], d["id_agent"], d["id_gestionnaire"], d["id_creneaux"]
    )


@app.get("/facture/pilote/{id_pilote}", tags=["Facturation"])
def route_voir_factures(id_pilote: str,
                        x_identifiant: str = Header(...),
                        x_mot_de_passe: str = Header(...)):
    # Pilote voit SES factures, agent et gestionnaire voient tout
    info = auth.authentifier(x_identifiant, x_mot_de_passe)
    auth.exiger_role(info, ["pilote", "agent", "gestionnaire"])
    auth.exiger_proprio(info, id_pilote)
    return metier.voir_factures_pilote(id_pilote)


@app.get("/facture/recettes/{periode}/{valeur}", tags=["Facturation"])
def route_voir_recettes(periode: str, valeur: str,
                        x_identifiant: str = Header(...),
                        x_mot_de_passe: str = Header(...)):
    # Gestionnaire uniquement
    info = auth.authentifier(x_identifiant, x_mot_de_passe)
    auth.exiger_role(info, ["gestionnaire"])
    return metier.voir_recettes(periode, valeur)


# ============================================================
# MODULE 4 — REPORTING
# ============================================================

@app.get("/reporting/mouvements/{periode}/{valeur}", tags=["Reporting"])
def route_rapport_mouvements(periode: str, valeur: str,
                             x_identifiant: str = Header(...),
                             x_mot_de_passe: str = Header(...)):
    # Gestionnaire uniquement
    info = auth.authentifier(x_identifiant, x_mot_de_passe)
    auth.exiger_role(info, ["gestionnaire"])
    return metier.rapport_mouvements(periode, valeur)


@app.get("/reporting/aeronef/{immatriculation}", tags=["Reporting"])
def route_rapport_aeronef(immatriculation: str,
                          x_identifiant: str = Header(...),
                          x_mot_de_passe: str = Header(...)):
    # Agent et gestionnaire
    info = auth.authentifier(x_identifiant, x_mot_de_passe)
    auth.exiger_role(info, ["agent", "gestionnaire"])
    return metier.rapport_historique_aeronef(immatriculation)


@app.get("/reporting/occupation", tags=["Reporting"])
def route_rapport_occupation(x_identifiant: str = Header(...),
                             x_mot_de_passe: str = Header(...)):
    # Gestionnaire uniquement
    info = auth.authentifier(x_identifiant, x_mot_de_passe)
    auth.exiger_role(info, ["gestionnaire"])
    return metier.rapport_occupation_infra()
