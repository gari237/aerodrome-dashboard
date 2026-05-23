import crud as db
from fastapi import HTTPException
from datetime import datetime

# ============================================================
# MODULE 1 — CRÉNEAUX ET MOUVEMENTS AÉRIENS
# ============================================================

def verifier_intervalle_90min(date, heure_debut, heure_fin):
    """
    Vérifie que le créneau respecte un intervalle minimum de 90 minutes.
    Bloque si la durée est inférieure à 90 min.
    """
    debut = datetime.strptime(date + " " + heure_debut, "%Y-%m-%d %H:%M")
    fin   = datetime.strptime(date + " " + heure_fin,   "%Y-%m-%d %H:%M")
    duree = (fin - debut).seconds // 60  # durée en minutes
    if duree < 90:
        raise HTTPException(
            status_code=400,
            detail="Le créneau doit durer au minimum 90 minutes."
        )


def verifier_creneau_disponible(date, heure_debut, heure_fin):
    """
    Vérifie qu'aucun autre créneau non annulé ne chevauche le créneau demandé.
    """
    tous = db.afficher("Creneaux")
    debut_new = datetime.strptime(date + " " + heure_debut, "%Y-%m-%d %H:%M")
    fin_new   = datetime.strptime(date + " " + heure_fin,   "%Y-%m-%d %H:%M")

    for c in tous:
        if c["Status"] == "Annulé":
            continue
        if c["Date"] != date:
            continue
        debut_ex = datetime.strptime(c["Date"] + " " + c["Heure_debut"], "%Y-%m-%d %H:%M")
        fin_ex   = datetime.strptime(c["Date"] + " " + c["Heure_fin"],   "%Y-%m-%d %H:%M")
        # Chevauchement si les créneaux se recoupent
        if debut_new < fin_ex and fin_new > debut_ex:
            raise HTTPException(
                status_code=400,
                detail="Ce créneau chevauche un créneau existant — indisponible."
            )


def demander_creneau(id_creneaux, date, heure_debut, heure_fin, immatriculation,
                     num_emplacement, numero, type_maintenance):
    """
    Pilote ou agent : crée un créneau avec statut 'Demandé'.
    Vérifie l'intervalle 90 min et la disponibilité avant insertion.
    """
    verifier_intervalle_90min(date, heure_debut, heure_fin)
    verifier_creneau_disponible(date, heure_debut, heure_fin)
    db.ajouter("Creneaux", (
        id_creneaux, date, heure_debut, heure_fin,
        "Demandé", num_emplacement, numero, type_maintenance, immatriculation
    ))
    return {"message": "Créneau demandé avec succès.", "status": "Demandé"}


def modifier_statut_creneau(id_creneaux, nouveau_statut):
    """
    Agent uniquement : change le statut d'un créneau.
    Statuts valides : Confirmé, Autorisé, Achevé, Annulé
    """
    statuts_valides = ["Confirmé", "Autorisé", "Achevé", "Annulé"]
    valide = False
    for s in statuts_valides:
        if nouveau_statut == s:
            valide = True
    if not valide:
        raise HTTPException(
            status_code=400,
            detail="Statut invalide. Choisir parmi : Confirmé, Autorisé, Achevé, Annulé."
        )
    db.modifier("Creneaux", "Status", nouveau_statut, "Id_creneaux", id_creneaux)
    return {"message": f"Créneau {id_creneaux} passé à '{nouveau_statut}'."}


def annuler_creneau(id_creneaux):
    """
    Pilote : annule son créneau (passe à 'Annulé').
    """
    db.modifier("Creneaux", "Status", "Annulé", "Id_creneaux", id_creneaux)
    return {"message": f"Créneau {id_creneaux} annulé."}


def voir_mouvements(filtre):
    """
    Agent : visualise les mouvements selon leur statut.
    filtre : 'en_cours', 'futurs', 'acheves', ou 'tous'
    """
    tous = db.afficher("Creneaux")
    maintenant = datetime.now()
    resultats = []

    for c in tous:
        debut = datetime.strptime(c["Date"] + " " + c["Heure_debut"], "%Y-%m-%d %H:%M")
        fin   = datetime.strptime(c["Date"] + " " + c["Heure_fin"],   "%Y-%m-%d %H:%M")

        if filtre == "en_cours" and debut <= maintenant and fin >= maintenant:
            resultats.append(c)
        elif filtre == "futurs" and debut > maintenant:
            resultats.append(c)
        elif filtre == "acheves" and c["Status"] == "Achevé":
            resultats.append(c)
        elif filtre == "tous":
            resultats.append(c)

    return resultats


# ============================================================
# MODULE 2 — SERVICES AU SOL ET INFRASTRUCTURES
# ============================================================

def demander_service_parking(num_emplacement, id_creneaux):
    """
    Pilote : vérifie que l'emplacement parking existe puis l'associe au créneau.
    """
    parking = db.lire_ou("Service_parking", "Num_Emplacement", num_emplacement)
    if not parking:
        raise HTTPException(status_code=404, detail="Emplacement parking introuvable.")
    db.modifier("Creneaux", "Num_Emplacement", num_emplacement, "Id_creneaux", id_creneaux)
    return {"message": f"Parking {num_emplacement} affecté au créneau {id_creneaux}."}


def demander_service_carburant(numero, id_creneaux):
    """
    Pilote : vérifie que la pompe carburant existe puis l'associe au créneau.
    """
    carburant = db.lire_ou("Service_carburant", "Numero", numero)
    if not carburant:
        raise HTTPException(status_code=404, detail="Pompe carburant introuvable.")
    db.modifier("Creneaux", "Numero", numero, "Id_creneaux", id_creneaux)
    return {"message": f"Carburant {numero} affecté au créneau {id_creneaux}."}


def demander_service_maintenance(type_maintenance, id_creneaux):
    """
    Pilote : vérifie que le service maintenance existe puis l'associe au créneau.
    """
    maintenance = db.lire_ou("Service_maintenance", "Type_maintenance", type_maintenance)
    if not maintenance:
        raise HTTPException(status_code=404, detail="Service de maintenance introuvable.")
    db.modifier("Creneaux", "Type_maintenance", type_maintenance, "Id_creneaux", id_creneaux)
    return {"message": f"Maintenance '{type_maintenance}' affectée au créneau {id_creneaux}."}


def gerer_infrastructure(action, id_infra, type_infra, materiaux, emplacement):
    """
    Gestionnaire uniquement : ajouter ou supprimer une infrastructure.
    action : 'ajouter' ou 'supprimer'
    """
    if action == "ajouter":
        db.ajouter("Infrastructure", (id_infra, type_infra, materiaux, emplacement))
        return {"message": f"Infrastructure {id_infra} ajoutée."}
    elif action == "supprimer":
        db.supprimer("Infrastructure", "Id_infra", id_infra)
        return {"message": f"Infrastructure {id_infra} supprimée."}
    else:
        raise HTTPException(status_code=400, detail="Action invalide. Choisir 'ajouter' ou 'supprimer'.")


# ============================================================
# MODULE 3 — FACTURATION
# ============================================================

def calculer_montant(id_creneaux):
    """
    Calcule le montant total d'un créneau en additionnant les prix des services associés.
    """
    creneaux = db.lire_ou("Creneaux", "Id_creneaux", id_creneaux)
    if not creneaux:
        raise HTTPException(status_code=404, detail="Créneau introuvable.")
    c = creneaux[0]
    montant = 0.0

    # Prix parking
    if c["Num_Emplacement"]:
        parking = db.lire_ou("Service_parking", "Num_Emplacement", c["Num_Emplacement"])
        if parking:
            montant = montant + parking[0]["Prix"]

    # Prix carburant
    if c["Numero"]:
        carburant = db.lire_ou("Service_carburant", "Numero", c["Numero"])
        if carburant:
            montant = montant + carburant[0]["Prix"]

    # Prix maintenance
    if c["Type_maintenance"]:
        maintenance = db.lire_ou("Service_maintenance", "Type_maintenance", c["Type_maintenance"])
        if maintenance:
            montant = montant + maintenance[0]["Prix"]

    return montant


def generer_facture(num_facture, date, heure, nom, id_agent, id_gestionnaire, id_creneaux):
    """
    Agent : génère une facture en calculant automatiquement le montant total.
    """
    montant = calculer_montant(id_creneaux)
    db.ajouter("Facture", (num_facture, date, heure, montant, nom, id_gestionnaire, id_agent))
    return {
        "message": f"Facture {num_facture} générée.",
        "montant_total": montant
    }


def voir_factures_pilote(id_pilote):
    """
    Pilote : visualise ses propres factures via la table Visualise.
    """
    liens = db.lire_ou("Visualise", "Id_pilote", id_pilote)
    if not liens:
        return {"message": "Aucune facture trouvée.", "factures": []}
    factures = []
    for lien in liens:
        facture = db.lire_ou("Facture", "Num_Facture", lien["Num_Facture"])
        if facture:
            factures.append(facture[0])
    return {"factures": factures}


def voir_recettes(periode, valeur):
    """
    Gestionnaire : visualise les recettes selon une période.
    periode : 'jour', 'mois', 'annee'
    valeur  : ex '2025-01-15' pour jour, '2025-01' pour mois, '2025' pour annee
    """
    toutes = db.afficher("Facture")
    resultats = []
    for f in toutes:
        if periode == "jour" and f["Date"] == valeur:
            resultats.append(f)
        elif periode == "mois" and f["Date"][:7] == valeur:
            resultats.append(f)
        elif periode == "annee" and f["Date"][:4] == valeur:
            resultats.append(f)

    total = 0.0
    for f in resultats:
        total = total + f["Montant"]

    return {"periode": periode, "valeur": valeur, "total_recettes": total, "factures": resultats}


# ============================================================
# MODULE 4 — REPORTING (gestionnaire uniquement)
# ============================================================

def rapport_mouvements(periode, valeur):
    """
    Gestionnaire : flux des mouvements aériens par jour, semaine ou mois.
    periode : 'jour', 'mois'
    valeur  : '2025-01-15' ou '2025-01'
    """
    tous = db.afficher("Creneaux")
    resultats = []
    for c in tous:
        if periode == "jour" and c["Date"] == valeur:
            resultats.append(c)
        elif periode == "mois" and c["Date"][:7] == valeur:
            resultats.append(c)
    return {"nb_mouvements": len(resultats), "mouvements": resultats}


def rapport_historique_aeronef(immatriculation):
    """
    Gestionnaire : historique de tous les mouvements d'un aéronef.
    """
    creneaux = db.lire_ou("Creneaux", "Immatriculation", immatriculation)
    return {"immatriculation": immatriculation, "nb_mouvements": len(creneaux), "historique": creneaux}


def rapport_occupation_infra():
    """
    Gestionnaire : taux d'occupation des parkings et hangars.
    Compte le nombre de créneaux avec un emplacement parking affecté.
    """
    tous = db.afficher("Creneaux")
    total_parkings = db.afficher("Service_parking")
    nb_occupes = 0
    for c in tous:
        if c["Num_Emplacement"] and c["Status"] != "Annulé":
            nb_occupes = nb_occupes + 1
    nb_total = len(total_parkings)
    if nb_total == 0:
        taux = 0
    else:
        taux = (nb_occupes * 100) // nb_total
    return {
        "emplacements_total": nb_total,
        "emplacements_occupes": nb_occupes,
        "taux_occupation_pct": taux
    }
