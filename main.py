import streamlit as st
from pymongo import MongoClient
from datetime import datetime
import os
import pandas as pd
import bcrypt
import csv
import seaborn as sns
import matplotlib.pyplot as plt
import openai
import json


# --- Connexion MongoDB ---
client = MongoClient("mongodb://localhost:27017/")
db = client['ocp_db']
users_col = db['users']
files_col = db['files']

# --- Session Streamlit ---
if "authenticated" not in st.session_state:
    st.session_state.authenticated = False
    st.session_state.email = None
    st.session_state.name = None

# --- Authentification Sécurisée ---
def register_user(name, email, password):
    if users_col.find_one({"email": email}):
        return False
    hashed_pw = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt())
    user_data = {
        "name": name,
        "email": email,
        "password": hashed_pw,
        "created_at": datetime.now()
    }
    users_col.insert_one(user_data)
    return True



def show_kpis(df):
    st.subheader("📊 KPI")
    st.write("Nombre total de lignes :", len(df))
    st.write("Colonnes disponibles :", list(df.columns))
    st.write("Valeurs manquantes par colonne :")
    st.dataframe(df.isnull().sum())

def clean_data(df):
    st.subheader("🧹 Nettoyage des données")

    if df.empty:
        st.warning("Le fichier est vide.")
        return

    st.write("Aperçu du dataset avant nettoyage :")
    st.dataframe(df.head())

    # 1. Suppression des colonnes vides
    if st.checkbox("🔸 Supprimer les colonnes entièrement vides"):
        df = df.dropna(axis=1, how='all')
        st.success("Colonnes vides supprimées.")

    # 2. Suppression des lignes avec valeurs manquantes
    if st.checkbox("🔸 Supprimer les lignes contenant des valeurs manquantes"):
        df = df.dropna()
        st.success("Lignes contenant des NaN supprimées.")

    # 3. Remplir les valeurs manquantes
    if st.checkbox("🔸 Remplir les valeurs manquantes avec une méthode au choix"):
        method = st.selectbox("Méthode de remplissage :", ["Moyenne", "Médiane", "Valeur constante"])
        
        if method == "Valeur constante":
            constant_value = st.text_input("Entrez la valeur à utiliser pour le remplissage :", value="Inconnu")

        for col in df.columns:
            if df[col].isnull().any():
                if df[col].dtype in ['int64', 'float64']:
                    if method == "Moyenne":
                        df[col].fillna(df[col].mean(), inplace=True)
                    elif method == "Médiane":
                        df[col].fillna(df[col].median(), inplace=True)
                    elif method == "Valeur constante":
                        try:
                            val = float(constant_value)
                            df[col].fillna(val, inplace=True)
                        except ValueError:
                            df[col].fillna(constant_value, inplace=True)
                else:
                    df[col].fillna(constant_value if method == "Valeur constante" else "Inconnu", inplace=True)

        st.success(f"Valeurs manquantes remplies avec la méthode : {method}")

    # 4. Suppression des doublons
    if st.checkbox("🔸 Supprimer les lignes dupliquées"):
        df = df.drop_duplicates()
        st.success("Doublons supprimés.")

    # Résultat final
    st.write("Aperçu du dataset après nettoyage :")
    st.dataframe(df.head())
    st.write(f"🔢 Forme finale du dataset : {df.shape[0]} lignes, {df.shape[1]} colonnes")


def ai_interpretation(df):
    st.subheader("🤖 Interprétation IA ")
    

    openai.api_key = st.secrets["OPENAI_API_KEY"]
    with st.spinner("Analyse en cours par l'IA..."):
        try:
            sample=df.head(10).to_dict(orient="records")
            prompt =f""" Voici les premières lignes d'un fichier CSV chargé par un utilisateur :

{json.dumps(sample, indent=2)}

Peux-tu fournir une interprétation automatique de ce jeu de données ?
Explique brièvement :
1. Ce que représente probablement ce jeu de données,
2. Les types de colonnes présentes (numériques, catégorielles...),
3. Toute anomalie ou insight visible dans ces lignes."""
           
             
            prompt = (
                "Voici les premières lignes d'un fichier CSV chargé par un utilisateur :\n\n"
                f"{json.dumps(sample, indent=2)}\n\n"
                "Peux-tu fournir une interprétation automatique de ce jeu de données ? "
                "Explique brièvement :\n"
                "1. Ce que représente probablement ce jeu de données,\n"
                "2. Les types de colonnes présentes (numériques, catégorielles, booléennes...),\n"
                "3. Toute anomalie ou insight visible dans ces lignes."
            )

            response = openai.ChatCompletion.create(
                model="gpt-4",
                messages=[
                    {"role": "system", "content": "Tu es un expert en data science et analyse de données tabulaires."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.5,
                max_tokens=700
            )

            result = response['choices'][0]['message']['content']
            st.success("✅ Analyse IA terminée.")
            st.markdown(result)

        except openai.error.OpenAIError as e:
            st.error(f"❌ Erreur OpenAI : {e}")
        except Exception as e:
            st.error(f"❌ Erreur inattendue : {e}")
    
def visualize_data(df):
    st.subheader("📈 Visualisation des données")

    if df.empty:
        st.warning("Le fichier est vide.")
        return

    numeric_cols = df.select_dtypes(include=['int64', 'float64']).columns.tolist()
    categorical_cols = df.select_dtypes(include=['object', 'category']).columns.tolist()

    if not numeric_cols and not categorical_cols:
        st.warning("Pas de colonnes numériques ou catégorielles détectées.")
        return

    st.markdown("### Choisissez le type de graphique")

    chart_type = st.selectbox("Type de graphique", [
        "Histogramme",
        "Boxplot",
        "Nuage de points (Scatter plot)",
        "Camembert (Pie chart)",
        "Heatmap des corrélations"
    ])

    if chart_type == "Histogramme":
        column = st.selectbox("Choisissez une colonne numérique", numeric_cols)
        bins = st.slider("Nombre d'intervalles (bins)", 5, 100, 20)
        fig, ax = plt.subplots()
        sns.histplot(df[column], bins=bins, kde=True, ax=ax)
        st.pyplot(fig)

    elif chart_type == "Boxplot":
        column = st.selectbox("Choisissez une colonne numérique", numeric_cols)
        fig, ax = plt.subplots()
        sns.boxplot(x=df[column], ax=ax)
        st.pyplot(fig)

    elif chart_type == "Nuage de points (Scatter plot)":
        x_col = st.selectbox("Axe X", numeric_cols, key="x_scatter")
        y_col = st.selectbox("Axe Y", numeric_cols, key="y_scatter")
        fig, ax = plt.subplots()
        sns.scatterplot(x=df[x_col], y=df[y_col], ax=ax)
        st.pyplot(fig)

    elif chart_type == "Camembert (Pie chart)":
        column = st.selectbox("Choisissez une colonne catégorielle", categorical_cols)
        pie_data = df[column].value_counts()
        fig, ax = plt.subplots()
        ax.pie(pie_data, labels=pie_data.index, autopct='%1.1f%%', startangle=90)
        ax.axis("equal")
        st.pyplot(fig)

    elif chart_type == "Heatmap des corrélations":
        if len(numeric_cols) < 2:
            st.warning("Pas assez de colonnes numériques pour une heatmap.")
        else:
            corr = df[numeric_cols].corr()
            fig, ax = plt.subplots()
            sns.heatmap(corr, annot=True, cmap="coolwarm", ax=ax)
            st.pyplot(fig)


def login_user(email, password):
    user = users_col.find_one({"email": email})
    if user and bcrypt.checkpw(password.encode('utf-8'), user['password']):
        st.session_state.name = user['name']
        return True
    return False

# --- Interface Utilisateur ---
def show_register():
    st.title("Inscription")
    name = st.text_input("Nom complet")
    email = st.text_input("Adresse e-mail")
    password = st.text_input("Mot de passe", type="password")
    if st.button("S'inscrire"):
        if register_user(name, email, password):
            st.success("Inscription réussie ! Veuillez vous connecter.")
        else:
            st.error("Un utilisateur avec cet e-mail existe déjà.")

def show_login():
    st.title("Connexion")
    email = st.text_input("E-mail")
    password = st.text_input("Mot de passe", type="password")
    if st.button("Se connecter"):
        if login_user(email, password):
            st.success("Connexion réussie")
            st.session_state.authenticated = True
            st.session_state.email = email
        else:
            st.error("Identifiants invalides")


def read_csv_with_best_separator(file_path):
    potential_separators = [",", ";", "\t", "|",":::"]
    best_df = None
    max_columns = 0

    for sep in potential_separators:
        try:
            df = pd.read_csv(file_path, sep=sep)
            if df.shape[1] > max_columns:
                best_df = df
                max_columns = df.shape[1]
        except Exception:
            continue

    return best_df

def read_csv_with_auto_separator(filepath):
    separators = [';', ',', '\t']
    for sep in separators:
        try:
            df = pd.read_csv(filepath, sep=sep)
            if df.shape[1] > 1:  # Si plusieurs colonnes détectées, on suppose que c'est bon
                return df
        except Exception:
            continue
    raise ValueError("Aucun séparateur valide détecté. Veuillez vérifier le format du fichier.")


import os
from datetime import datetime
import streamlit as st

def upload_and_analyze_page():
    st.title("📊 Traitement de vos fichiers CSV")

    choice = st.radio("Que souhaitez-vous faire ?", ["📂 Uploader un nouveau fichier", "🕓 Traiter un fichier déjà uploadé"])

    if choice == "📂 Uploader un nouveau fichier":
        uploaded_files = st.file_uploader("Uploader un ou plusieurs fichiers CSV", type="csv", accept_multiple_files=True)

        if uploaded_files:
            os.makedirs("uploads", exist_ok=True)

            for uploaded_file in uploaded_files:
                file_path = os.path.join("uploads", uploaded_file.name)

                # Vérifier si le fichier existe déjà pour cet utilisateur
                existing = files_col.find_one({
                    "email": st.session_state.email,
                    "filename": uploaded_file.name
                })

                if existing:
                    st.warning(f"⚠️ Le fichier `{uploaded_file.name}` a déjà été uploadé.")
                    continue

                with open(file_path, "wb") as f:
                    f.write(uploaded_file.getbuffer())

                # Stocker les métadonnées dans MongoDB
                files_col.insert_one({
                    "email": st.session_state.email,
                    "filename": uploaded_file.name,
                    "timestamp": datetime.now()
                })

            st.success(f"{len(uploaded_files)} fichier(s) uploadé(s) avec succès.")
            st.rerun()  # Recharge pour passer à "traiter un fichier existant"

    elif choice == "🕓 Traiter un fichier déjà uploadé":
        user_files = list(files_col.find({"email": st.session_state.email}).sort("timestamp", -1))

        # Ne garder que les fichiers qui existent sur le disque
        existing_files = [f for f in user_files if os.path.exists(os.path.join("uploads", f["filename"]))]

        if not existing_files:
            st.info("Aucun fichier valide trouvé.")
            return

        file_names = [f["filename"] for f in existing_files]
        selected_filename = st.selectbox("📁 Choisir un fichier à traiter :", file_names)
        file_path = os.path.join("uploads", selected_filename)

        col1, col2 = st.columns([3, 1])
        with col1:
            st.write(f"**Fichier sélectionné** : `{selected_filename}`")
        with col2:
            if st.button("🗑️ Supprimer ce fichier"):
                if os.path.exists(file_path):
                    os.remove(file_path)
                files_col.delete_one({
                    "email": st.session_state.email,
                    "filename": selected_filename
                })
                st.success("✅ Fichier supprimé.")
                st.rerun()

        if os.path.exists(file_path):
            try:
                df = read_csv_with_auto_separator(file_path)
                st.success(f"✅ Le fichier contient {df.shape[0]} lignes et {df.shape[1]} colonnes.")
                st.dataframe(df.head())

                action = st.selectbox("🧭 Choisir une action", [
                    "Afficher des KPI",
                    "Nettoyer les données",
                    "Interprétation avec l'IA",
                    "Visualisation des données"
                ])

                if action == "Afficher des KPI":
                    show_kpis(df)
                elif action == "Nettoyer les données":
                    clean_data(df)
                elif action == "Interprétation avec l'IA":
                    ai_interpretation(df)
                elif action == "Visualisation des données":
                    visualize_data(df)

            except Exception as e:
                st.error(f"❌ Erreur lors de la lecture du fichier : {e}")
        else:
            st.warning("⚠️ Le fichier n'existe plus dans le dossier `uploads/`.")

def show_history():
    st.title("Historique des fichiers uploadés")
    history = files_col.find({"email": st.session_state.email})
    data = [{"Fichier": h["filename"], "Date d'upload": h["timestamp"].strftime("%Y-%m-%d %H:%M:%S")} for h in history]
    if data:
        st.dataframe(pd.DataFrame(data))
    else:
        st.info("Aucun historique d’upload trouvé.")

# --- Application principale ---
def main():
    if not st.session_state.authenticated:
        menu = st.sidebar.selectbox("Menu", ["Connexion", "Inscription"])
        if menu == "Connexion":
            show_login()
        elif menu == "Inscription":
            show_register()
    else:
        st.sidebar.success(f"Connecté en tant que : {st.session_state.name}")
        menu = st.sidebar.selectbox("Options", ["Uploader un fichier", "Voir l'historique", "Déconnexion"])

        if menu == "Uploader un fichier":
            upload_and_analyze_page()
        elif menu == "Voir l'historique":
            show_history()
        elif menu == "Déconnexion":
            st.session_state.authenticated = False
            st.session_state.email = None
            st.session_state.name = None
            st.experimental_rerun()

if __name__ == "__main__":
    main()
