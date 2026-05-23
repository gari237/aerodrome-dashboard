import crud as db  # Module CRUD pour les opérations sur la base de données
from fastapi import HTTPException  # Pour lever des erreurs HTTP avec codes et messages
from datetime import datetime  # Pour manipuler et comparer les dates et heures


# ============================================================
# FONCTION UTILITAIRE — Parse une date+heure depuis la base
# ============================================================

def parser_datetime(date_str, heure_str):
    # Heure_debut peut contenir "HH:MM", "HH:MM:SS", ou "YYYY-MM-DD HH:MM:SS"
    heure_propre = heure_str.strip()  # Supprime les espaces inutiles
    if " " in heure_propre:  # Format complet "YYYY-MM-DD HH:MM:SS" — contient un espace
        heure_propre = heure_propre.split(" ")[1]  # Prend la partie heure après l'espace
    if len(heure_propre) > 5:  # Format "HH:MM:SS" — contient les secondes
        heure_propre = heure_propre[:5]  # Garde uniquement "HH:MM"
    return datetime.strptime(date_str + " " + heure_propre, "%Y-%m-%d %H:%M")  # Construit le datetime

# ============================================================
# MODULE 1 — CRÉNEAUX ET MOUVEMENTS AÉRIENS
# ============================================================

def verifier_intervalle_90min(date, heure_debut, heure_fin):
    # Vérifie que le créneau dure au minimum 90 minutes
    debut = parser_datetime(date, heure_debut)  # Parse la date+heure de début
    fin   = parser_datetime(date, heure_fin)    # Parse la date+heure de fin
    duree = (fin - debut).seconds // 60  # Calcule la durée en minutes
    if duree < 90:  # Si la durée est inférieure à 90 minutes
        raise HTTPException(
            status_code=400,
            detail="Le créneau doit durer au minimum 90 minutes."
        )


def verifier_creneau_disponible(date, heure_debut, heure_fin):
    # Vérifie qu'aucun créneau existant ne chevauche le nouveau créneau demandé
    tous = db.afficher("Creneaux")  # Récupère tous les créneaux en base
    debut_new = parser_datetime(date, heure_debut)  # Parse le début du nouveau créneau
    fin_new   = parser_datetime(date, heure_fin)    # Parse la fin du nouveau créneau

    for c in tous:  # Parcourt tous les créneaux existants
        if c["Status"] == "Annule" or c["Status"] == "Annulé":  # Ignore les créneaux annulés
            continue
        if c["Date"] != date:  # Ignore les créneaux sur une autre date
            continue
        debut_ex = parser_datetime(c["Date"], c["Heure_debut"])  # Parse le début du créneau existant
        fin_ex   = parser_datetime(c["Date"], c["Heure_fin"])    # Parse la fin du créneau existant
        if debut_new < fin_ex and fin_new > debut_ex:  # Vérifie le chevauchement
            raise HTTPException(
                status_code=400,
                detail="Ce créneau chevauche un créneau existant — indisponible."
            )


def demander_creneau(id_creneaux, date, heure_debut, heure_fin, immatriculation,
                     num_emplacement, numero, type_maintenance):
    # Pilote ou agent : crée un créneau avec statut 'Demande'
    verifier_intervalle_90min(date, heure_debut, heure_fin)  # Vérifie la durée minimale
    verifier_creneau_disponible(date, heure_debut, heure_fin)  # Vérifie la disponibilité
    db.ajouter("Creneaux", (  # Insère le créneau dans la base
        id_creneaux, date, heure_debut, heure_fin,
        "Demande", num_emplacement, numero, type_maintenance, immatriculation
    ))
    return {"message": "Créneau demandé avec succès.", "status": "Demande"}


def modifier_statut_creneau(id_creneaux, nouveau_statut):
    # Agent ou gestionnaire : change le statut d'un créneau existant
    statuts_valides = ["Confirme", "Autorise", "Acheve", "Annule"]  # Statuts acceptés en base
    valide = False  # Flag de validation
    for s in statuts_valides:  # Parcourt les statuts valides
        if nouveau_statut == s:  # Si le statut correspond
            valide = True  # Marque comme valide
    if not valide:  # Si aucun statut ne correspond
        raise HTTPException(
            status_code=400,
            detail="Statut invalide. Choisir parmi : Confirme, Autorise, Acheve, Annule."
        )
    db.modifier("Creneaux", "Status", nouveau_statut, "Id_creneaux", id_creneaux)  # Met à jour en base
    return {"message": f"Créneau {id_creneaux} passé à '{nouveau_statut}'."}


def annuler_creneau(id_creneaux):
    # Pilote : annule son créneau en passant son statut à 'Annule'
    db.modifier("Creneaux", "Status", "Annule", "Id_creneaux", id_creneaux)  # Met à jour en base
    return {"message": f"Créneau {id_creneaux} annulé."}


def voir_mouvements(filtre):
    # Agent : visualise les mouvements selon leur statut ou leur timing
    tous = db.afficher("Creneaux")  # Récupère tous les créneaux en base
    maintenant = datetime.now()  # Heure actuelle pour comparer
    resultats = []  # Liste des créneaux filtrés

    for c in tous:  # Parcourt tous les créneaux
        debut = parser_datetime(c["Date"], c["Heure_debut"])  # Parse le début du créneau
        fin   = parser_datetime(c["Date"], c["Heure_fin"])    # Parse la fin du créneau

        if filtre == "en_cours" and debut <= maintenant and fin >= maintenant:  # Créneau en cours
            resultats.append(dict(c))  # Convertit en dict et ajoute
        elif filtre == "futurs" and debut > maintenant:  # Créneau futur
            resultats.append(dict(c))
        elif filtre == "Acheve" and c["Status"] == "Acheve":  # Créneaux achevés
            resultats.append(dict(c))
        elif filtre == "Confirme" and c["Status"] == "Confirme":  # Créneaux confirmés
            resultats.append(dict(c))
        elif filtre == "Annule" and c["Status"] == "Annule":  # Créneaux annulés
            resultats.append(dict(c))
        elif filtre == "tous":  # Tous les créneaux sans filtre
            resultats.append(dict(c))

    return {"nb_resultats": len(resultats), "mouvements": resultats}  # Retourne les résultats avec compteur


# ============================================================
# MODULE 2 — SERVICES AU SOL ET INFRASTRUCTURES
# ============================================================

def demander_service_parking(num_emplacement, id_creneaux):
    # Pilote : vérifie que l'emplacement parking existe puis l'associe au créneau
    parking = db.lire_ou("Service_parking", "Num_Emplacement", num_emplacement)  # Cherche l'emplacement
    if not parking:  # Si l'emplacement n'existe pas
        raise HTTPException(status_code=404, detail="Emplacement parking introuvable.")
    db.modifier("Creneaux", "Num_Emplacement", num_emplacement, "Id_creneaux", id_creneaux)  # Associe
    return {"message": f"Parking {num_emplacement} affecté au créneau {id_creneaux}."}


def demander_service_carburant(numero, id_creneaux):
    # Pilote : vérifie que la pompe carburant existe puis l'associe au créneau
    carburant = db.lire_ou("Service_carburant", "Numero", numero)  # Cherche la pompe
    if not carburant:  # Si la pompe n'existe pas
        raise HTTPException(status_code=404, detail="Pompe carburant introuvable.")
    db.modifier("Creneaux", "Numero", numero, "Id_creneaux", id_creneaux)  # Associe
    return {"message": f"Carburant {numero} affecté au créneau {id_creneaux}."}


def demander_service_maintenance(type_maintenance, id_creneaux):
    # Pilote : vérifie que le service maintenance existe puis l'associe au créneau
    maintenance = db.lire_ou("Service_maintenance", "Type_maintenance", type_maintenance)  # Cherche
    if not maintenance:  # Si le service n'existe pas
        raise HTTPException(status_code=404, detail="Service de maintenance introuvable.")
    db.modifier("Creneaux", "Type_maintenance", type_maintenance, "Id_creneaux", id_creneaux)  # Associe
    return {"message": f"Maintenance '{type_maintenance}' affectée au créneau {id_creneaux}."}


def gerer_infrastructure(action, id_infra, type_infra, materiaux, emplacement):
    # Gestionnaire uniquement : ajouter ou supprimer une infrastructure
    if action == "ajouter":  # Si l'action est d'ajouter
        db.ajouter("Infrastructure", (id_infra, type_infra, materiaux, emplacement))  # Insère
        return {"message": f"Infrastructure {id_infra} ajoutée."}
    elif action == "supprimer":  # Si l'action est de supprimer
        db.supprimer("Infrastructure", "Id_infra", id_infra)  # Supprime
        return {"message": f"Infrastructure {id_infra} supprimée."}
    else:  # Si l'action est invalide
        raise HTTPException(status_code=400, detail="Action invalide. Choisir 'ajouter' ou 'supprimer'.")


# ============================================================
# MODULE 3 — FACTURATION
# ============================================================

def calculer_montant(id_creneaux):
    # Calcule le montant total d'un créneau en additionnant les prix des services associés
    creneaux = db.lire_ou("Creneaux", "Id_creneaux", id_creneaux)  # Cherche le créneau
    if not creneaux:  # Si le créneau n'existe pas
        raise HTTPException(status_code=404, detail="Créneau introuvable.")
    c = creneaux[0]  # Prend le premier résultat
    montant = 0.0  # Initialise le montant à zéro

    if c["Num_Emplacement"]:  # Si un emplacement parking est associé
        parking = db.lire_ou("Service_parking", "Num_Emplacement", c["Num_Emplacement"])
        if parking:  # Si le parking existe
            montant = montant + parking[0]["Prix"]  # Ajoute le prix parking

    if c["Numero"]:  # Si une pompe carburant est associée
        carburant = db.lire_ou("Service_carburant", "Numero", c["Numero"])
        if carburant:  # Si le carburant existe
            montant = montant + carburant[0]["Prix"]  # Ajoute le prix carburant

    if c["Type_maintenance"]:  # Si un service maintenance est associé
        maintenance = db.lire_ou("Service_maintenance", "Type_maintenance", c["Type_maintenance"])
        if maintenance:  # Si la maintenance existe
            montant = montant + maintenance[0]["Prix"]  # Ajoute le prix maintenance

    return montant  # Retourne le montant total calculé


def generer_facture(num_facture, date, heure, nom, id_agent, id_gestionnaire, id_creneaux):
    # Agent : génère une facture en calculant automatiquement le montant total
    montant = calculer_montant(id_creneaux)  # Calcule le montant via les services du créneau
    db.ajouter("Facture", (num_facture, date, heure, montant, nom, id_gestionnaire, id_agent))  # Insère
    return {
        "message": f"Facture {num_facture} générée.",
        "montant_total": montant
    }


def voir_factures_pilote(id_pilote):
    # Pilote : visualise ses propres factures via la table Visualise
    liens = db.lire_ou("Visualise", "Id_pilote", id_pilote)  # Cherche les liens facture-pilote
    if not liens:  # Si aucune facture trouvée
        return {"message": "Aucune facture trouvée.", "factures": []}
    factures = []  # Liste des factures du pilote
    for lien in liens:  # Parcourt les liens
        facture = db.lire_ou("Facture", "Num_Facture", lien["Num_Facture"])  # Cherche la facture
        if facture:  # Si la facture existe
            factures.append(dict(facture[0]))  # Ajoute la facture convertie en dict
    return {"factures": factures}  # Retourne toutes les factures du pilote


def voir_recettes(periode, valeur):
    # Gestionnaire : visualise les recettes selon une période donnée
    toutes = db.afficher("Facture")  # Récupère toutes les factures
    resultats = []  # Liste des factures correspondant à la période
    for f in toutes:  # Parcourt toutes les factures
        if periode == "jour" and f["Date"] == valeur:  # Filtre par jour exact
            resultats.append(dict(f))
        elif periode == "mois" and f["Date"][:7] == valeur:  # Filtre par mois (YYYY-MM)
            resultats.append(dict(f))
        elif periode == "annee" and f["Date"][:4] == valeur:  # Filtre par année (YYYY)
            resultats.append(dict(f))

    total = 0.0  # Initialise le total à zéro
    for f in resultats:  # Parcourt les factures filtrées
        total = total + f["Montant"]  # Additionne les montants

    return {"periode": periode, "valeur": valeur, "total_recettes": total, "factures": resultats}


# ============================================================
# MODULE 4 — REPORTING
# ============================================================

def rapport_mouvements(periode, valeur):
    # Gestionnaire : flux des mouvements aériens par jour ou par mois
    tous = db.afficher("Creneaux")  # Récupère tous les créneaux
    resultats = []  # Liste des créneaux correspondant à la période
    for c in tous:  # Parcourt tous les créneaux
        if periode == "jour" and c["Date"] == valeur:  # Filtre par jour exact
            resultats.append(dict(c))
        elif periode == "mois" and c["Date"][:7] == valeur:  # Filtre par mois
            resultats.append(dict(c))
    return {"nb_mouvements": len(resultats), "mouvements": resultats}  # Retourne avec compteur


def rapport_historique_aeronef(immatriculation):
    # Agent ou gestionnaire : historique de tous les mouvements d'un aéronef
    creneaux = db.lire_ou("Creneaux", "Immatriculation", immatriculation)  # Cherche par immatriculation
    return {
        "immatriculation": immatriculation,
        "nb_mouvements": len(creneaux),
        "historique": [dict(c) for c in creneaux]  # Convertit chaque ligne en dict
    }


def rapport_occupation_infra():
    # Gestionnaire : taux d'occupation des parkings
    tous = db.afficher("Creneaux")  # Récupère tous les créneaux
    total_parkings = db.afficher("Service_parking")  # Récupère tous les emplacements parking
    nb_occupes = 0  # Compteur d'emplacements occupés
    for c in tous:  # Parcourt tous les créneaux
        if c["Num_Emplacement"] and c["Status"] != "Annule":  # Si parking associé et non annulé
            nb_occupes = nb_occupes + 1  # Incrémente le compteur
    nb_total = len(total_parkings)  # Nombre total d'emplacements
    if nb_total == 0:  # Évite la division par zéro
        taux = 0
    else:
        taux = (nb_occupes * 100) // nb_total  # Calcule le taux en pourcentage entier
    return {
        "emplacements_total": nb_total,
        "emplacements_occupes": nb_occupes,
        "taux_occupation_pct": taux
    }