import streamlit as st  # Interface web interactive pour créer le dashboard
import requests  # Pour faire des appels HTTP vers l'API FastAPI
import pandas as pd  # Manipulation et analyse des données en tableaux
import plotly.express as px  # Création de graphiques interactifs

# URL de base de l'API FastAPI qui tourne en local sur le port 8000
API = "http://127.0.0.1:8000"

# Configuration générale de la page : titre onglet, icône et layout large
st.set_page_config(page_title="Aérodrome", page_icon="✈️", layout="wide")

# ============================================================
# FONCTIONS UTILITAIRES
# ============================================================

def api_get(endpoint, identifiant, mot_de_passe):
    # Envoie une requête GET à l'API avec les credentials dans les headers HTTP
    response = requests.get(
        f"{API}{endpoint}",  # Construction de l'URL complète
        headers={"x-identifiant": identifiant, "x-mot-de-passe": mot_de_passe}  # Credentials pour l'authentification
    )
    if response.status_code == 200:  # Si la requête réussit (code HTTP 200)
        return response.json()  # Retourne les données au format JSON
    return None  # Retourne None en cas d'erreur

def get_table(table):
    # Envoie une requête GET pour récupérer toute une table sans authentification
    response = requests.get(f"{API}/table/{table}")  # Appel à l'endpoint générique de l'API
    if response.status_code == 200:  # Si la requête réussit
        return pd.DataFrame(response.json())  # Convertit la réponse JSON en DataFrame Pandas
    return pd.DataFrame()  # Retourne un DataFrame vide en cas d'erreur

# ============================================================
# PAGE DE LOGIN
# ============================================================

def page_login():
    # Divise la page en 3 colonnes pour centrer le formulaire
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:  # Utilise uniquement la colonne centrale
        st.title("✈️ Aérodrome — Connexion")  # Titre principal du formulaire
        st.divider()  # Ligne de séparation visuelle
        identifiant = st.text_input("Identifiant", placeholder="ex: pilote01")  # Champ de saisie de l'identifiant
        mot_de_passe = st.text_input("Mot de passe", type="password")  # Champ mot de passe masqué
        if st.button("Se connecter", use_container_width=True):  # Bouton de connexion pleine largeur
            # Envoie les credentials à l'endpoint /login de l'API
            response = requests.post(
                f"{API}/login",  # URL de l'endpoint de login
                params={"identifiant": identifiant, "mot_de_passe": mot_de_passe}  # Paramètres de la requête
            )
            if response.status_code == 200:  # Si le login réussit
                data = response.json()  # Récupère les données retournées par l'API
                st.session_state["connecte"] = True  # Marque l'utilisateur comme connecté dans la session
                st.session_state["identifiant"] = identifiant  # Sauvegarde l'identifiant en session
                st.session_state["mot_de_passe"] = mot_de_passe  # Sauvegarde le mot de passe en session
                st.session_state["role"] = data["role"]  # Sauvegarde le rôle retourné par l'API
                if data["role"] == "pilote":  # Si c'est un pilote on cherche son ID réel
                    pilotes = requests.get(f"{API}/table/Pilote").json()  # Récupère tous les pilotes
                    for p in pilotes:  # Parcourt chaque pilote
                        if p.get("Id_compte") == identifiant:  # Trouve le pilote lié à ce compte
                            st.session_state["user_id"] = p["Id_pilote"]  # Sauvegarde l'ID du pilote
                            break  # Arrête la boucle dès que trouvé
                else:
                    st.session_state["user_id"] = identifiant  # Pour agent/gestionnaire l'ID est l'identifiant
                st.rerun()  # Recharge la page pour afficher le dashboard correspondant au rôle
            else:
                st.error("❌ Identifiant ou mot de passe incorrect")  # Affiche un message d'erreur
        st.divider()  # Ligne de séparation visuelle
        st.markdown("**Comptes disponibles dans ta base :**")  # Titre de la section comptes
        comptes = get_table("Compte")  # Récupère tous les comptes depuis la base via l'API
        if not comptes.empty:  # Vérifie que le DataFrame n'est pas vide
            st.dataframe(comptes[["Identifiant"]], use_container_width=True)  # Affiche uniquement les identifiants

# ============================================================
# DASHBOARD PILOTE
# ============================================================

def dashboard_pilote(identifiant, mot_de_passe, user_id):
    st.title("👨‍✈️ Dashboard Pilote")  # Titre du dashboard pilote
    st.caption(f"Connecté : **{identifiant}** | ID : **{user_id}**")  # Affiche l'identifiant et l'ID
    st.divider()  # Ligne de séparation visuelle

    creneaux = get_table("Creneaux")  # Charge tous les créneaux depuis l'API
    avions = get_table("Avion")  # Charge tous les avions depuis l'API

    # Menu de navigation dans la sidebar avec 3 options
    page = st.sidebar.radio("Menu", ["🛫 Mes Créneaux", "💶 Mes Factures", "📋 Mes Avions"])

    if page == "🛫 Mes Créneaux":
        st.subheader("🛫 Mes Créneaux")  # Titre de la section
        if not creneaux.empty:  # Vérifie que des créneaux existent
            if not avions.empty and "Id_pilote" in avions.columns:  # Vérifie que la colonne Id_pilote existe
                mes_immat = avions[avions["Id_pilote"] == user_id]["Immatriculation"].tolist()  # Récupère les immatriculations du pilote
                mes_creneaux = creneaux[creneaux["Immatriculation"].isin(mes_immat)]  # Filtre les créneaux par immatriculation
            else:
                mes_creneaux = pd.DataFrame()  # DataFrame vide si pas d'avions trouvés

            col1, col2, col3 = st.columns(3)  # 3 colonnes pour les KPIs
            col1.metric("Total", len(mes_creneaux))  # Nombre total de créneaux du pilote
            if not mes_creneaux.empty:  # Si le pilote a des créneaux
                col2.metric("Achevés", len(mes_creneaux[mes_creneaux["Statut"] == "Acheve"]))  # Créneaux terminés
                col3.metric("Annulés", len(mes_creneaux[mes_creneaux["Statut"] == "Annule"]))  # Créneaux annulés
                fig = px.pie(mes_creneaux["Statut"].value_counts().reset_index(),  # Compte les statuts
                             names="Statut", values="count", title="Mes créneaux", hole=0.4)  # Graphique donut
                st.plotly_chart(fig, use_container_width=True)  # Affiche le graphique
                st.dataframe(mes_creneaux, use_container_width=True)  # Affiche le tableau des créneaux
            else:
                st.info("Aucun créneau trouvé.")  # Message si aucun créneau

    elif page == "💶 Mes Factures":
        st.subheader("💶 Mes Factures")  # Titre de la section factures
        data = api_get(f"/facture/pilote/{user_id}", identifiant, mot_de_passe)  # Appel API avec authentification
        if data:  # Si des factures sont retournées
            df = pd.DataFrame(data)  # Convertit en DataFrame
            st.metric("Total facturé", f"{df['Montant'].sum():,.0f} €")  # Affiche le total des factures
            st.dataframe(df, use_container_width=True)  # Affiche le tableau des factures
        else:
            st.info("Aucune facture trouvée.")  # Message si aucune facture

    elif page == "📋 Mes Avions":
        st.subheader("📋 Mes Avions")  # Titre de la section avions
        if not avions.empty and "Id_pilote" in avions.columns:  # Vérifie que les avions existent
            mes_avions = avions[avions["Id_pilote"] == user_id]  # Filtre les avions du pilote
            if not mes_avions.empty:  # Si le pilote a des avions
                st.dataframe(mes_avions, use_container_width=True)  # Affiche le tableau des avions
            else:
                st.info("Aucun avion trouvé.")  # Message si aucun avion

# ============================================================
# DASHBOARD AGENT
# ============================================================

def dashboard_agent(identifiant, mot_de_passe):
    st.title("🛠️ Dashboard Agent d'Exploitation")  # Titre du dashboard agent
    st.caption(f"Connecté : **{identifiant}**")  # Affiche l'identifiant connecté
    st.divider()  # Ligne de séparation visuelle

    # Menu de navigation dans la sidebar avec 3 options
    page = st.sidebar.radio("Menu", ["🛫 Tous les Créneaux", "👥 Pilotes & Avions", "📬 Messagerie"])

    if page == "🛫 Tous les Créneaux":
        st.subheader("🛫 Tous les Créneaux")  # Titre de la section
        creneaux = get_table("Creneaux")  # Charge tous les créneaux depuis l'API
        if not creneaux.empty:  # Vérifie que des créneaux existent
            col1, col2, col3 = st.columns(3)  # 3 colonnes pour les KPIs
            col1.metric("Total", len(creneaux))  # Nombre total de créneaux
            col2.metric("Achevés", len(creneaux[creneaux["Statut"] == "Acheve"]))  # Créneaux achevés
            col3.metric("Annulés", len(creneaux[creneaux["Statut"] == "Annule"]))  # Créneaux annulés
            st.divider()  # Séparation visuelle
            if "Date" in creneaux.columns:  # Vérifie que la colonne Date existe
                fig = px.bar(creneaux.groupby("Date").size().reset_index(name="Mouvements"),  # Groupe par date
                             x="Date", y="Mouvements", title="Mouvements par date",
                             color="Mouvements", color_continuous_scale="blues")  # Dégradé bleu
                st.plotly_chart(fig, use_container_width=True)  # Affiche le graphique
            st.dataframe(creneaux, use_container_width=True)  # Affiche le tableau complet des créneaux

    elif page == "👥 Pilotes & Avions":
        st.subheader("👥 Pilotes")  # Titre section pilotes
        st.dataframe(get_table("Pilote"), use_container_width=True)  # Affiche tous les pilotes
        st.subheader("✈️ Avions")  # Titre section avions
        st.dataframe(get_table("Avion"), use_container_width=True)  # Affiche tous les avions

    elif page == "📬 Messagerie":
        st.subheader("📬 Messages")  # Titre section messagerie
        st.dataframe(get_table("Messagerie"), use_container_width=True)  # Affiche tous les messages

# ============================================================
# DASHBOARD GESTIONNAIRE
# ============================================================

def dashboard_gestionnaire(identifiant, mot_de_passe):
    st.title("📊 Dashboard Gestionnaire")  # Titre du dashboard gestionnaire
    st.caption(f"Connecté : **{identifiant}**")  # Affiche l'identifiant connecté
    st.divider()  # Ligne de séparation visuelle

    # Menu de navigation dans la sidebar avec 4 options — accès complet
    page = st.sidebar.radio("Menu", ["📈 Reporting", "💰 Revenus", "🏗️ Infrastructures", "👁️ Vue Complète"])

    if page == "📈 Reporting":
        st.subheader("📈 Reporting")  # Titre de la section reporting
        creneaux = get_table("Creneaux")  # Charge tous les créneaux
        if not creneaux.empty:  # Vérifie que des données existent
            col1, col2, col3, col4 = st.columns(4)  # 4 colonnes pour les KPIs
            col1.metric("Total", len(creneaux))  # Total des mouvements
            col2.metric("Achevés", len(creneaux[creneaux["Statut"] == "Acheve"]))  # Mouvements achevés
            col3.metric("Confirmés", len(creneaux[creneaux["Statut"] == "Confirme"]))  # Mouvements confirmés
            col4.metric("Annulés", len(creneaux[creneaux["Statut"] == "Annule"]))  # Mouvements annulés
            st.divider()  # Séparation visuelle
            col1, col2 = st.columns(2)  # Deux colonnes pour les graphiques
            with col1:
                fig = px.bar(creneaux.groupby("Date").size().reset_index(name="Mouvements"),  # Groupe par date
                             x="Date", y="Mouvements", title="Mouvements par date",
                             color="Mouvements", color_continuous_scale="blues")  # Dégradé bleu
                st.plotly_chart(fig, use_container_width=True)  # Affiche le graphique
            with col2:
                fig2 = px.pie(creneaux["Statut"].value_counts().reset_index(),  # Compte les statuts
                              names="Statut", values="count",
                              title="Répartition des statuts", hole=0.4)  # Graphique donut
                st.plotly_chart(fig2, use_container_width=True)  # Affiche le graphique

    elif page == "💰 Revenus":
        st.subheader("💰 Revenus")  # Titre de la section revenus
        factures = get_table("Facture")  # Charge toutes les factures
        if not factures.empty:  # Vérifie que des factures existent
            col1, col2, col3 = st.columns(3)  # 3 colonnes pour les KPIs financiers
            col1.metric("Revenus totaux", f"{factures['Montant'].sum():,.0f} €")  # Somme totale des factures
            col2.metric("Factures", len(factures))  # Nombre total de factures
            col3.metric("Montant moyen", f"{factures['Montant'].mean():,.0f} €")  # Montant moyen par facture
            st.divider()  # Séparation visuelle
            fig = px.line(factures.groupby("Date")["Montant"].sum().reset_index(),  # Groupe les revenus par date
                          x="Date", y="Montant", title="Évolution des revenus", markers=True)  # Courbe avec points
            st.plotly_chart(fig, use_container_width=True)  # Affiche le graphique
            st.dataframe(factures, use_container_width=True)  # Affiche le tableau des factures

    elif page == "🏗️ Infrastructures":
        st.subheader("🏗️ Infrastructures")  # Titre de la section infrastructures
        infras = get_table("Infrastructures")  # Charge toutes les infrastructures
        if not infras.empty:  # Vérifie que des infrastructures existent
            col1, col2 = st.columns(2)  # Deux colonnes pour les graphiques
            with col1:
                fig = px.bar(infras["Types_infra"].value_counts().reset_index(),  # Compte par type
                             x="Types_infra", y="count", title="Par type",
                             color="count", color_continuous_scale="teal")  # Dégradé teal
                st.plotly_chart(fig, use_container_width=True)  # Affiche le graphique
            with col2:
                fig2 = px.pie(infras["Emplacement"].value_counts().reset_index(),  # Compte par emplacement
                              names="Emplacement", values="count",
                              title="Par zone", hole=0.4)  # Graphique donut
                st.plotly_chart(fig2, use_container_width=True)  # Affiche le graphique
            st.dataframe(infras, use_container_width=True)  # Affiche le tableau des infrastructures
        else:
            st.info("Aucune infrastructure trouvée.")  # Message si aucune infrastructure

    elif page == "👁️ Vue Complète":
        st.subheader("👁️ Vue Complète")  # Titre de la section vue complète
        # Liste de toutes les tables disponibles dans la base de données
        tables = ["Pilote", "Avion", "Creneaux", "Facture", "Infrastructures", "Messagerie",
                  "Service_carburant", "Service_maintenance", "Service_parking"]
        table_choisie = st.selectbox("Choisir une table", tables)  # Menu déroulant pour choisir une table
        st.dataframe(get_table(table_choisie), use_container_width=True)  # Affiche la table sélectionnée

# ============================================================
# LOGIQUE PRINCIPALE
# ============================================================

if "connecte" not in st.session_state:  # Vérifie si la variable de session existe
    st.session_state["connecte"] = False  # Initialise à False si elle n'existe pas

if st.session_state["connecte"]:  # Si l'utilisateur est connecté
    st.sidebar.divider()  # Ligne de séparation dans la sidebar
    if st.sidebar.button("🚪 Se déconnecter"):  # Bouton de déconnexion dans la sidebar
        st.session_state.clear()  # Efface toutes les variables de session
        st.rerun()  # Recharge la page pour revenir au login

if not st.session_state["connecte"]:  # Si l'utilisateur n'est pas connecté
    page_login()  # Affiche la page de login
else:
    role = st.session_state["role"]  # Récupère le rôle depuis la session
    identifiant = st.session_state["identifiant"]  # Récupère l'identifiant depuis la session
    mot_de_passe = st.session_state["mot_de_passe"]  # Récupère le mot de passe depuis la session
    user_id = st.session_state.get("user_id")  # Récupère l'ID utilisateur depuis la session

    if role == "pilote":  # Si le rôle est pilote
        dashboard_pilote(identifiant, mot_de_passe, user_id)  # Affiche le dashboard pilote
    elif role == "agent":  # Si le rôle est agent
        dashboard_agent(identifiant, mot_de_passe)  # Affiche le dashboard agent
    elif role == "gestionnaire":  # Si le rôle est gestionnaire
        dashboard_gestionnaire(identifiant, mot_de_passe)  # Affiche le dashboard gestionnaire
    else:
        st.error("Rôle non reconnu")  # Affiche une erreur si le rôle est inconnu