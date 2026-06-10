# ✈️ Aérodrome Dashboard — Système de Gestion d'Aérodrome avec API REST

> Projet de fin de cycle Bachelor · IPSA Paris · Spécialisation IA & Data Science

[![Dashboard Live](https://img.shields.io/badge/Dashboard-Live-brightgreen?style=for-the-badge)](https://aerodrome-dashboard.onrender.com/)
[![API Docs](https://img.shields.io/badge/API-Swagger%20Docs-blue?style=for-the-badge&logo=fastapi)](https://aerodrome-api.onrender.com/docs#/)
[![Python](https://img.shields.io/badge/Python-3.10+-blue?style=for-the-badge&logo=python)](https://python.org)
[![FastAPI](https://img.shields.io/badge/FastAPI-Backend-teal?style=for-the-badge&logo=fastapi)](https://fastapi.tiangolo.com)

---

## 📌 Présentation

**Aérodrome Dashboard** est une application web full-stack simulant le système d'information d'un aérodrome. Elle combine une API REST sécurisée (FastAPI) et un dashboard interactif multi-rôles (Streamlit), permettant la gestion des mouvements d'aéronefs, le suivi financier en temps réel et le contrôle d'accès par rôle utilisateur.

---

## 🏗️ Architecture

```
┌──────────────────────────────────────────────┐
│              Interface Streamlit              │
│   (Dashboard multi-rôles · Plotly · Filtres) │
└──────────────────┬───────────────────────────┘
                   │ HTTP Requests
                   ▼
┌──────────────────────────────────────────────┐
│               API REST FastAPI                │
│   Endpoints sécurisés · Auth par rôle        │
│   Swagger UI accessible /docs                │
└──────────────────┬───────────────────────────┘
                   │ ORM / Requêtes
                   ▼
┌──────────────────────────────────────────────┐
│              Base SQLite                      │
│   316 mouvements · Vols · Finances · Users   │
└──────────────────────────────────────────────┘
```

---

## ✨ Fonctionnalités

### 📊 Dashboard
- Visualisation en temps réel des mouvements d'aéronefs (316 entrées)
- Reporting financier : revenus, taxes, redevances
- Filtres dynamiques par date, type d'aéronef, destination
- Graphiques interactifs (Plotly)

### 🔐 Contrôle d'Accès Multi-Rôles
| Rôle          | Permissions                                      |
|---------------|--------------------------------------------------|
| `admin`       | Accès complet : lecture, écriture, suppression   |
| `controleur`  | Consultation des mouvements et horaires          |
| `comptable`   | Accès aux données financières uniquement         |
| `visiteur`    | Lecture seule, données agrégées                  |

### ⚙️ API REST
- Documentation interactive Swagger : `/docs`
- Endpoints CRUD pour mouvements, aéronefs, utilisateurs
- Authentification par token
- Réponses JSON normalisées

---

## ⚙️ Stack Technique

| Composant        | Technologie       |
|------------------|-------------------|
| Backend API      | FastAPI           |
| Interface        | Streamlit         |
| Base de données  | SQLite            |
| Visualisation    | Plotly            |
| Auth             | JWT / Token       |
| Déploiement      | Render            |
| Versioning       | Git / GitHub      |

---

## 🚀 Installation & Lancement Local

```bash
# 1. Cloner le dépôt
git clone https://github.com/gari237/aerodrome-dashboard
cd aerodrome-dashboard

# 2. Créer un environnement virtuel
python -m venv venv
source venv/bin/activate   # Windows : venv\Scripts\activate

# 3. Installer les dépendances
pip install -r requirements.txt

# 4. Lancer l'API FastAPI
uvicorn api.main:app --reload --port 8000

# 5. Dans un second terminal, lancer le dashboard
streamlit run dashboard/app.py
```

L'API sera accessible sur `http://localhost:8000`  
Le dashboard sur `http://localhost:8501`

---

##  Structure du Projet

```
aerodrome-dashboard/
├── api/
│   ├── main.py             # Point d'entrée FastAPI
│   ├── routers/            # Endpoints par domaine
│   ├── models.py           # Modèles de données
│   └── auth.py             # Gestion de l'authentification
├── dashboard/
│   └── app.py              # Interface Streamlit multi-rôles
├── database/
│   └── aerodrome.db        # Base SQLite (316 mouvements)
├── requirements.txt
└── README.md
```

---

##  Liens

| Ressource         | URL                                             |
|-------------------|-------------------------------------------------|
| Dashboard live    | https://aerodrome-dashboard.onrender.com/       |
| Documentation API | https://aerodrome-api.onrender.com/docs#/       |





---

*Disponible pour stage immédiat (3–4 mois) et alternance dès septembre 2026 en Île-de-France.*
