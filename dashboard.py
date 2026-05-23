import streamlit as st        # Import Streamlit pour l'interface web
import requests                # Import requests pour appeler l'API FastAPI
import plotly.express as px    # Import Plotly pour les graphiques interactifs
import pandas as pd            # Import Pandas pour manipuler les données

# ============================================================
# CONFIGURATION
# ============================================================
API = "http://127.0.0.1:8000"  # URL de l'API FastAPI — doit tourner en parallèle
st.set_page_config(            # Configuration de la page Streamlit
    page_title="Aérodrome Dashboard",  # Titre de l'onglet navigateur
    page_icon="✈️",                    # Icône de l'onglet
    layout="wide"                      # Layout large pour le dashboard
)


# ============================================================
# FONCTION GENERIQUE — APPEL API
# ============================================================
def get_table(table):
    """Récupère toutes les données d'une table via l'API"""
    try:
        reponse = requests.get(f"{API}/table/{table}")  # Appel GET à l'API
        return reponse.json()                            # Retourne les données JSON
    except:
        st.error("❌ API non accessible — Lance uvicorn d'abord !")  # Message d'erreur
        return []                                        # Retourne liste vide si erreur


# ============================================================
# LOGIN
# ============================================================
def login():
    """Page de connexion — vérifie le rôle gestionnaire"""
    st.title("✈️ Aérodrome — Connexion")              # Titre de la page login

    identifiant  = st.text_input("Identifiant")        # Champ identifiant
    mot_de_passe = st.text_input("Mot de passe", type="password")  # Champ mot de passe masqué
    bouton       = st.button("Se connecter")           # Bouton de connexion

    if bouton:                                          # Si le bouton est cliqué
        comptes = get_table("Compte")                  # Récupère tous les comptes via API
        for compte in comptes:                         # Parcourt chaque compte
            if (compte["Identifiant"] == identifiant   # Vérifie identifiant
            and compte["Mot_de_passe"] == mot_de_passe # Vérifie mot de passe
            and compte["Role"] == "gestionnaire"):     # Vérifie que c'est un gestionnaire
                st.session_state["connecte"] = True    # Marque l'utilisateur comme connecté
                st.session_state["identifiant"] = identifiant  # Sauvegarde l'identifiant
                st.rerun()                             # Recharge la page
        st.error("❌ Identifiants incorrects ou accès non autorisé")  # Erreur si échec


# ============================================================
# DASHBOARD PRINCIPAL
# ============================================================
def dashboard():
    """Dashboard principal réservé au gestionnaire"""

    # --- SIDEBAR ---
    st.sidebar.title("✈️ Aérodrome")                   # Titre de la sidebar
    st.sidebar.success(f"👤 {st.session_state['identifiant']}")  # Affiche l'utilisateur connecté
    page = st.sidebar.radio("Navigation", [            # Menu de navigation
        "🏠 Accueil",
        "📅 Créneaux",
        "💶 Factures",
        "✈️ Avions",
        "🏗️ Infrastructures",
        "👤 Pilotes"
    ])
    if st.sidebar.button("🚪 Déconnexion"):            # Bouton déconnexion
        st.session_state.clear()                       # Efface la session
        st.rerun()                                     # Recharge la page


    # ============================================================
    # PAGE ACCUEIL — KPIs
    # ============================================================
    if page == "🏠 Accueil":
        st.title("🏠 Tableau de bord Gestionnaire")    # Titre de la page

        # Récupération des données via API
        creneaux       = get_table("Creneaux")         # Données créneaux
        factures       = get_table("Facture")          # Données factures
        pilotes        = get_table("Pilote")           # Données pilotes
        avions         = get_table("Avion")            # Données avions
        infrastructures = get_table("Infrastructure")  # Données infrastructures

        # --- KPIs en colonnes ---
        col1, col2, col3, col4, col5 = st.columns(5)  # 5 colonnes pour les KPIs

        col1.metric("✈️ Avions",          len(avions))         # Nombre d'avions
        col2.metric("👤 Pilotes",         len(pilotes))        # Nombre de pilotes
        col3.metric("📅 Créneaux",        len(creneaux))       # Nombre de créneaux
        col4.metric("💶 Revenu Total",    f"{sum(f['Montant'] for f in factures):.0f} €")  # Revenu total
        col5.metric("🏗️ Infrastructures", len(infrastructures))  # Nombre d'infrastructures

        st.divider()                                   # Ligne de séparation

        # --- GRAPHIQUES ---
        col_g1, col_g2 = st.columns(2)                # 2 colonnes pour les graphiques

        with col_g1:
            st.subheader("📅 Créneaux par statut")    # Titre graphique
            if creneaux:                               # Si des données existent
                df_cr = pd.DataFrame(creneaux)         # Convertit en DataFrame
                fig   = px.pie(                        # Graphique camembert
                    df_cr,
                    names="Status",                    # Colonne pour les catégories
                    title="Répartition des créneaux",  # Titre du graphique
                    color_discrete_sequence=px.colors.qualitative.Set3  # Palette de couleurs
                )
                st.plotly_chart(fig, use_container_width=True)  # Affiche le graphique

        with col_g2:
            st.subheader("💶 Revenus par date")       # Titre graphique
            if factures:                               # Si des données existent
                df_fac = pd.DataFrame(factures)        # Convertit en DataFrame
                df_rev = df_fac.groupby("Date")["Montant"].sum().reset_index()  # Groupe par date
                fig    = px.bar(                       # Graphique barres
                    df_rev,
                    x="Date",                          # Axe X
                    y="Montant",                       # Axe Y
                    title="Revenus par date",          # Titre
                    color="Montant",                   # Couleur selon montant
                    color_continuous_scale="Blues"     # Palette bleue
                )
                st.plotly_chart(fig, use_container_width=True)  # Affiche le graphique

        # --- GRAPHIQUE INFRASTRUCTURES ---
        st.subheader("🏗️ Infrastructures par type")  # Titre graphique
        if infrastructures:                            # Si des données existent
            df_inf = pd.DataFrame(infrastructures)     # Convertit en DataFrame
            fig    = px.bar(                           # Graphique barres
                df_inf.groupby("Type_infra").size().reset_index(name="Total"),  # Groupe par type
                x="Type_infra",                        # Axe X
                y="Total",                             # Axe Y
                title="Répartition des infrastructures",  # Titre
                color="Type_infra",                    # Couleur par type
                color_discrete_sequence=px.colors.qualitative.Pastel  # Palette pastel
            )
            st.plotly_chart(fig, use_container_width=True)  # Affiche le graphique


    # ============================================================
    # PAGE CRENEAUX
    # ============================================================
    elif page == "📅 Créneaux":
        st.title("📅 Gestion des Créneaux")            # Titre de la page
        creneaux = get_table("Creneaux")               # Récupère les créneaux via API
        if creneaux:                                   # Si des données existent
            df = pd.DataFrame(creneaux)                # Convertit en DataFrame
            statut = st.selectbox(                     # Filtre par statut
                "Filtrer par statut",
                ["Tous"] + df["Status"].unique().tolist()  # Options de filtre
            )
            if statut != "Tous":                       # Si un filtre est sélectionné
                df = df[df["Status"] == statut]        # Applique le filtre
            st.dataframe(df, use_container_width=True) # Affiche le tableau


    # ============================================================
    # PAGE FACTURES
    # ============================================================
    elif page == "💶 Factures":
        st.title("💶 Gestion des Factures")            # Titre de la page
        factures = get_table("Facture")                # Récupère les factures via API
        if factures:                                   # Si des données existent
            df = pd.DataFrame(factures)                # Convertit en DataFrame
            st.metric("💶 Total revenus", f"{df['Montant'].sum():.2f} €")  # KPI total
            st.metric("📊 Facture moyenne", f"{df['Montant'].mean():.2f} €")  # KPI moyenne
            st.dataframe(df, use_container_width=True) # Affiche le tableau


    # ============================================================
    # PAGE AVIONS
    # ============================================================
    elif page == "✈️ Avions":
        st.title("✈️ Flotte d'Avions")                 # Titre de la page
        avions = get_table("Avion")                    # Récupère les avions via API
        if avions:                                     # Si des données existent
            df = pd.DataFrame(avions)                  # Convertit en DataFrame
            col1, col2 = st.columns(2)                 # 2 colonnes
            col1.metric("Total avions", len(df))       # Nombre total d'avions
            col2.metric("Avions sans pilote",           # Avions non assignés
                        len(df[df["Id_pilote"].isna()]))
            st.dataframe(df, use_container_width=True) # Affiche le tableau


    # ============================================================
    # PAGE INFRASTRUCTURES
    # ============================================================
    elif page == "🏗️ Infrastructures":
        st.title("🏗️ Infrastructures")                 # Titre de la page
        infras = get_table("Infrastructure")           # Récupère les infrastructures via API
        if infras:                                     # Si des données existent
            df  = pd.DataFrame(infras)                 # Convertit en DataFrame
            fig = px.pie(df, names="Type_infra",       # Graphique camembert
                         title="Types d'infrastructures")
            st.plotly_chart(fig, use_container_width=True)  # Affiche le graphique
            st.dataframe(df, use_container_width=True) # Affiche le tableau


    # ============================================================
    # PAGE PILOTES
    # ============================================================
    elif page == "👤 Pilotes":
        st.title("👤 Pilotes")                         # Titre de la page
        pilotes = get_table("Pilote")                  # Récupère les pilotes via API
        if pilotes:                                    # Si des données existent
            df  = pd.DataFrame(pilotes)                # Convertit en DataFrame
            fig = px.bar(                              # Graphique barres
                df.groupby("License").size().reset_index(name="Total"),  # Groupe par licence
                x="License",                           # Axe X
                y="Total",                             # Axe Y
                title="Pilotes par type de licence",   # Titre
                color="License"                        # Couleur par licence
            )
            st.plotly_chart(fig, use_container_width=True)  # Affiche le graphique
            st.dataframe(df, use_container_width=True) # Affiche le tableau


# ============================================================
# POINT D'ENTREE
# ============================================================
if "connecte" not in st.session_state:                 # Si pas encore connecté
    login()                                            # Affiche la page de login
else:                                                  # Sinon
    dashboard()                                        # Affiche le dashboard
