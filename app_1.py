import streamlit as st  # Interface web interactive
import requests  # Pour les appels HTTP vers l'API
import pandas as pd  # Manipulation des données
import plotly.express as px  # Graphiques interactifs

API = "https://aerodrome-api.onrender.com"  # URL de base de l'API FastAPI

st.set_page_config(page_title="Aérodrome", page_icon="✈️", layout="wide")  # Configuration de la page

def get_headers():
    # Retourne les headers d'authentification depuis la session
    return {
        "x-identifiant": st.session_state.get("identifiant", ""),
        "x-mot-de-passe": st.session_state.get("mot_de_passe", "")
    }

def get_table(table):
    # Récupère une table complète depuis l'API avec authentification
    try:
        response = requests.get(f"{API}/table/{table}", headers=get_headers())
        if response.status_code == 200:
            return pd.DataFrame(response.json())
        return pd.DataFrame()
    except:
        return pd.DataFrame()

def api_get(endpoint):
    # Envoie une requête GET authentifiée vers un endpoint spécifique
    try:
        response = requests.get(f"{API}{endpoint}", headers=get_headers())
        if response.status_code == 200:
            return response.json()
        elif response.status_code == 403:
            st.warning("⛔ Accès refusé.")
        return None
    except:
        return None

def page_login():
    # Page de connexion centrée
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        st.title("✈️ Aérodrome — Connexion")
        st.divider()
        identifiant = st.text_input("Identifiant", placeholder="ex: pilot01")
        mot_de_passe = st.text_input("Mot de passe", type="password")
        if st.button("Se connecter", use_container_width=True):
            response = requests.post(
                f"{API}/login",
                params={"identifiant": identifiant, "mot_de_passe": mot_de_passe}
            )
            if response.status_code == 200:
                data = response.json()
                st.session_state["connecte"] = True
                st.session_state["identifiant"] = identifiant
                st.session_state["mot_de_passe"] = mot_de_passe
                st.session_state["role"] = data["role"]

                if data["role"] == "pilote":
                    # Cherche l'ID réel du pilote via son identifiant de compte
                    headers = {"x-identifiant": identifiant, "x-mot-de-passe": mot_de_passe}
                    # Charge tous les pilotes et filtre par identifiant
                    resp = requests.get(f"{API}/table/Pilote", headers=headers)
                    if resp.status_code == 200:
                        pilotes = resp.json()
                        user_id = identifiant  # Valeur par défaut
                        for p in pilotes:
                            if p.get("Identifiant") == identifiant:
                                user_id = p["Id_pilote"]  # Trouve l'ID réel ex: P001
                                break
                        st.session_state["user_id"] = user_id
                    else:
                        st.session_state["user_id"] = identifiant
                else:
                    st.session_state["user_id"] = identifiant
                st.rerun()
            else:
                st.error("❌ Identifiant ou mot de passe incorrect")
        st.divider()
        st.code("Pilotes : pilot01 à pilot11 / pass123\nAgents : agent01 à agent03 / pass123\nGestionnaires : gestion01, gestion02 / pass123")

def dashboard_pilote(identifiant, user_id):
    st.title("👨‍✈️ Dashboard Pilote")
    st.caption(f"Connecté : **{identifiant}** | ID : **{user_id}**")
    st.divider()

    page = st.sidebar.radio("Menu", ["🛫 Mes Créneaux", "💶 Mes Factures", "📋 Mes Avions"])

    if page == "🛫 Mes Créneaux":
        st.subheader("🛫 Mes Créneaux")
        creneaux = get_table("Creneaux")
        avions = get_table("Avion")
        if not creneaux.empty and not avions.empty:
            # Filtre les avions appartenant au pilote
            mes_immat = avions[avions["Id_pilote"] == user_id]["Immatriculation"].tolist()
            # Filtre les créneaux par immatriculation
            mes_creneaux = creneaux[creneaux["Immatriculation"].isin(mes_immat)]
            col1, col2, col3 = st.columns(3)
            col1.metric("Total", len(mes_creneaux))
            if not mes_creneaux.empty:
                col2.metric("Achevés", len(mes_creneaux[mes_creneaux["Status"] == "Acheve"]))
                col3.metric("Annulés", len(mes_creneaux[mes_creneaux["Status"] == "Annule"]))
                fig = px.pie(mes_creneaux["Status"].value_counts().reset_index(),
                             names="Status", values="count", title="Mes créneaux", hole=0.4)
                st.plotly_chart(fig, use_container_width=True)
                st.dataframe(mes_creneaux, use_container_width=True)
            else:
                st.info("Aucun créneau trouvé.")
        st.subheader("📅 Demander un créneau")
        with st.form("form_creneau_pilote"):
            id_cr = st.text_input("ID créneau", placeholder="CR200")
            date = st.text_input("Date", placeholder="2026-06-15")
            heure_debut = st.text_input("Heure début", placeholder="10:00")
            heure_fin = st.text_input("Heure fin", placeholder="11:30")
            immat = st.text_input("Immatriculation", placeholder="F-AAAA")
            submitted = st.form_submit_button("Envoyer")
            if submitted:
                resp = requests.post(
                    f"{API}/creneau/demander",
                    headers={**get_headers(), "Content-Type": "application/json"},
                    json={"data": {"id_creneaux": id_cr, "date": date,
                                   "heure_debut": heure_debut, "heure_fin": heure_fin,
                                   "status": "Demande", "immatriculation": immat}}
                )
                if resp.status_code == 200:
                    st.success("✅ Créneau demandé avec succès.")
                else:
                    st.error(f"❌ {resp.json().get('detail', 'Erreur')}")

    elif page == "💶 Mes Factures":
        st.subheader("💶 Mes Factures")
        factures = get_table("Facture")
        visualise = get_table("Visualise")
        if not factures.empty and not visualise.empty:
            mes_nums = visualise[visualise["Id_pilote"] == user_id]["Num_Facture"].tolist()
            mes_factures = factures[factures["Num_Facture"].isin(mes_nums)]
            if not mes_factures.empty:
                st.metric("Total facturé", f"{mes_factures['Montant'].sum():,.0f} €")
                st.dataframe(mes_factures, use_container_width=True)
            else:
                st.info("Aucune facture trouvée.")

    elif page == "📋 Mes Avions":
        st.subheader("📋 Mes Avions")
        avions = get_table("Avion")
        if not avions.empty:
            mes_avions = avions[avions["Id_pilote"] == user_id]
            if not mes_avions.empty:
                st.dataframe(mes_avions, use_container_width=True)
            else:
                st.info("Aucun avion trouvé.")

def dashboard_agent(identifiant):
    st.title("🛠️ Dashboard Agent d'Exploitation")
    st.caption(f"Connecté : **{identifiant}**")
    st.divider()

    page = st.sidebar.radio("Menu", ["🛫 Tous les Créneaux", "👥 Pilotes & Avions",
                                      "📬 Messagerie", "📅 Demander un créneau",
                                      "✈️ Rapport aéronef"])

    if page == "🛫 Tous les Créneaux":
        st.subheader("🛫 Tous les Créneaux")
        creneaux = get_table("Creneaux")
        if not creneaux.empty:
            col1, col2, col3 = st.columns(3)
            col1.metric("Total", len(creneaux))
            col2.metric("Achevés", len(creneaux[creneaux["Status"] == "Acheve"]))
            col3.metric("Annulés", len(creneaux[creneaux["Status"] == "Annule"]))
            st.divider()
            fig = px.bar(creneaux.groupby("Date").size().reset_index(name="Mouvements"),
                         x="Date", y="Mouvements", title="Mouvements par date",
                         color="Mouvements", color_continuous_scale="blues")
            st.plotly_chart(fig, use_container_width=True)
            st.dataframe(creneaux, use_container_width=True)

    elif page == "👥 Pilotes & Avions":
        st.subheader("👥 Pilotes")
        st.dataframe(get_table("Pilote"), use_container_width=True)
        st.subheader("✈️ Avions")
        st.dataframe(get_table("Avion"), use_container_width=True)

    elif page == "📬 Messagerie":
        st.subheader("📬 Messages")
        st.dataframe(get_table("Messagerie"), use_container_width=True)

    elif page == "📅 Demander un créneau":
        st.subheader("📅 Demander un créneau")
        with st.form("form_creneau_agent"):
            id_cr = st.text_input("ID créneau", placeholder="CR200")
            date = st.text_input("Date", placeholder="2026-06-15")
            heure_debut = st.text_input("Heure début", placeholder="10:00")
            heure_fin = st.text_input("Heure fin", placeholder="11:30")
            immat = st.text_input("Immatriculation", placeholder="F-AAAA")
            submitted = st.form_submit_button("Envoyer")
            if submitted:
                resp = requests.post(
                    f"{API}/creneau/demander",
                    headers={**get_headers(), "Content-Type": "application/json"},
                    json={"data": {"id_creneaux": id_cr, "date": date,
                                   "heure_debut": heure_debut, "heure_fin": heure_fin,
                                   "status": "Demande", "immatriculation": immat}}
                )
                if resp.status_code == 200:
                    st.success("✅ Créneau demandé.")
                else:
                    st.error(f"❌ {resp.json().get('detail', 'Erreur')}")

    elif page == "✈️ Rapport aéronef":
        st.subheader("✈️ Rapport aéronef")
        immat = st.text_input("Immatriculation", placeholder="F-AAAA")
        if st.button("Obtenir le rapport"):
            data = api_get(f"/reporting/aeronef/{immat}")
            if data:
                st.json(data)

def dashboard_gestionnaire(identifiant):
    st.title("📊 Dashboard Gestionnaire")
    st.caption(f"Connecté : **{identifiant}**")
    st.divider()

    page = st.sidebar.radio("Menu", ["📈 Reporting", "💰 Revenus",
                                      "🏗️ Infrastructures", "✅ Modifier statut",
                                      "👁️ Vue Complète"])

    if page == "📈 Reporting":
        st.subheader("📈 Reporting mouvements")
        creneaux = get_table("Creneaux")
        if not creneaux.empty:
            col1, col2, col3, col4 = st.columns(4)
            col1.metric("Total", len(creneaux))
            col2.metric("Achevés", len(creneaux[creneaux["Status"] == "Acheve"]))
            col3.metric("Confirmés", len(creneaux[creneaux["Status"] == "Confirme"]))
            col4.metric("Annulés", len(creneaux[creneaux["Status"] == "Annule"]))
            st.divider()
            col1, col2 = st.columns(2)
            with col1:
                fig = px.bar(creneaux.groupby("Date").size().reset_index(name="Mouvements"),
                             x="Date", y="Mouvements", title="Mouvements par date",
                             color="Mouvements", color_continuous_scale="blues")
                st.plotly_chart(fig, use_container_width=True)
            with col2:
                fig2 = px.pie(creneaux["Status"].value_counts().reset_index(),
                              names="Status", values="count",
                              title="Répartition des statuts", hole=0.4)
                st.plotly_chart(fig2, use_container_width=True)

    elif page == "💰 Revenus":
        st.subheader("💰 Revenus")
        factures = get_table("Facture")
        if not factures.empty:
            col1, col2, col3 = st.columns(3)
            col1.metric("Revenus totaux", f"{factures['Montant'].sum():,.0f} €")
            col2.metric("Factures", len(factures))
            col3.metric("Montant moyen", f"{factures['Montant'].mean():,.0f} €")
            st.divider()
            fig = px.line(factures.groupby("Date")["Montant"].sum().reset_index(),
                          x="Date", y="Montant", title="Évolution des revenus", markers=True)
            st.plotly_chart(fig, use_container_width=True)
            st.dataframe(factures, use_container_width=True)

    elif page == "🏗️ Infrastructures":
        st.subheader("🏗️ Infrastructures")
        infras = get_table("Infrastructure")
        if not infras.empty:
            col1, col2 = st.columns(2)
            with col1:
                fig = px.bar(infras["Type_infra"].value_counts().reset_index(),
                             x="Type_infra", y="count", title="Par type",
                             color="count", color_continuous_scale="teal")
                st.plotly_chart(fig, use_container_width=True)
            with col2:
                fig2 = px.pie(infras["Emplacement"].value_counts().reset_index(),
                              names="Emplacement", values="count",
                              title="Par zone", hole=0.4)
                st.plotly_chart(fig2, use_container_width=True)
            st.dataframe(infras, use_container_width=True)
        else:
            st.info("Aucune infrastructure trouvée.")

    elif page == "✅ Modifier statut":
        st.subheader("✅ Modifier statut d'un créneau")
        with st.form("form_statut"):
            id_cr = st.text_input("ID créneau", placeholder="CR001")
            statut = st.selectbox("Nouveau statut", ["Confirme", "Annule", "Acheve", "Autorise"])
            submitted = st.form_submit_button("Modifier")
            if submitted:
                resp = requests.put(
                    f"{API}/creneau/statut/{id_cr}",
                    headers={**get_headers(), "Content-Type": "application/json"},
                    json={"data": {"statut": statut}}
                )
                if resp.status_code == 200:
                    st.success(f"✅ Statut mis à jour : {statut}")
                elif resp.status_code == 403:
                    st.error("⛔ Accès refusé.")
                else:
                    st.error(f"❌ {resp.json().get('detail', 'Erreur')}")

    elif page == "👁️ Vue Complète":
        st.subheader("👁️ Vue Complète")
        tables = ["Pilote", "Avion", "Creneaux", "Facture", "Infrastructure",
                  "Messagerie", "Service_carburant", "Service_maintenance", "Service_parking"]
        table_choisie = st.selectbox("Choisir une table", tables)
        df = get_table(table_choisie)
        if not df.empty:
            st.dataframe(df, use_container_width=True)
        else:
            st.info("Aucune donnée ou accès refusé.")

# LOGIQUE PRINCIPALE
if "connecte" not in st.session_state:
    st.session_state["connecte"] = False

if st.session_state["connecte"]:
    st.sidebar.divider()
    role = st.session_state.get("role", "")
    couleur = {"pilote": "🟢", "agent": "🔵", "gestionnaire": "🟣"}.get(role, "⚪")
    st.sidebar.caption(f"{couleur} Rôle : **{role}**")
    if st.sidebar.button("🚪 Se déconnecter"):
        st.session_state.clear()
        st.rerun()

if not st.session_state["connecte"]:
    page_login()
else:
    role = st.session_state["role"]
    identifiant = st.session_state["identifiant"]
    user_id = st.session_state.get("user_id")

    if role == "pilote":
        dashboard_pilote(identifiant, user_id)
    elif role == "agent":
        dashboard_agent(identifiant)
    elif role == "gestionnaire":
        dashboard_gestionnaire(identifiant)
    else:
        st.error("Rôle non reconnu.")