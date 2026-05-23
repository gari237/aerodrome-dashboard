from fastapi import HTTPException
import crud as db

# ============================================================
# AUTHENTIFICATION + DETECTION DU ROLE
# ============================================================

def authentifier(identifiant, mot_de_passe):
    """
    Vérifie le compte en base et retourne le rôle détecté via le préfixe.
    Retourne : {"identifiant": ..., "role": ...}
    """
    # Vérification du compte en base
    resultats = db.lire_ou("Compte", "Identifiant", identifiant)
    if not resultats:
        raise HTTPException(status_code=401, detail="Compte introuvable.")

    compte = resultats[0]
    if compte["Mot_de_passe"] != mot_de_passe:
        raise HTTPException(status_code=401, detail="Mot de passe incorrect.")

    # Détection du rôle par préfixe
    role = None
    if identifiant[:5] == "pilot":
        role = "pilote"
    elif identifiant[:5] == "agent":
        role = "agent"
    elif identifiant[:7] == "gestion":
        role = "gestionnaire"
    else:
        raise HTTPException(status_code=401, detail="Préfixe de compte invalide.")

    return {"identifiant": identifiant, "role": role}


# ============================================================
# RESTRICTION PAR ROLE
# ============================================================

def exiger_role(info, roles_autorises):
    """
    roles_autorises : liste de rôles autorisés, ex: ["agent", "gestionnaire"]
    Bloque avec 403 si le rôle de l'utilisateur n'est pas dans la liste.
    """
    autorise = False
    for role in roles_autorises:
        if info["role"] == role:
            autorise = True
    if not autorise:
        raise HTTPException(
            status_code=403,
            detail="Accès refusé — rôle non autorisé pour cette action."
        )


# ============================================================
# RESTRICTION PROPRIÉTAIRE (pilote = ses données uniquement)
# ============================================================

def exiger_proprio(info, id_pilote):
    """
    Bloque un pilote qui tente d'accéder aux données d'un autre pilote.
    Agents et gestionnaires passent toujours.
    """
    if info["role"] == "pilote":
        resultats = db.lire_ou("Pilote", "Id_compte", info["identifiant"])
        if not resultats:
            raise HTTPException(status_code=403, detail="Pilote introuvable.")
        if resultats[0]["Id_pilote"] != id_pilote:
            raise HTTPException(status_code=403, detail="Accès refusé — données d'un autre pilote.")
