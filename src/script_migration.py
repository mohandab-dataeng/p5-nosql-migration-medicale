# SCRIPT DE MIGRATION (P5)

# On charche les drivers (classe des librairies) pour parler à .env et mongodb et à l'os(natif python)
import os
import pandas as pd 
from dotenv import load_dotenv 
from pymongo import MongoClient 
from bson import ObjectId # Génère les ID pour lier les collectioins sur MDB

# 0) Initiation du script dans une fonction

def main():

    # 1) Chargement des credentials et conexion à MongoDB
    
    # On se connecte à l'.env dans la racine du projet detecter auto
    load_dotenv()
    # On va chercher les credentials sur le .env en indiquant le client
    client = MongoClient(
        host = os.getenv('MONGO_HOST'),
        port = int(os.getenv('MONGO_PORT')),
        username = os.getenv('MONGO_USER'),
        password = os.getenv('MONGO_PASSWORD')
    )
    # Creation de la variable = base de donnée sur MDB
    db = client ["medical_p5"]

    # 2) Un if qui permet de ne pas cumuler la migration si elle a déjà eu lieu(uniqument dans ce projet car on peut faire des ajout dans ce cas ca ne marchera pas)
    if db["patients"].count_documents({}) == 0:

        # 3) Lecture du CSV - à partir de maintenant l'ensemble est danas une fonction

        # Charge le fichier et lit le contenu
        df = pd.read_csv('data/healthcare_dataset.csv')
        print(f"Lignes : {len(df)}")
        print(df.columns.tolist())

    # 4) Preparation du dataset 

        # On fait attention aux types 
        df['Date of Admission'] =  pd.to_datetime(df['Date of Admission'])
        df['Discharge Date'] = pd.to_datetime(df['Discharge Date'])
        # Suppression des doublons (534 selon sweetviz)
        df = df.drop_duplicates()

    # 5) Génération des Ids (clé primaire) pour les collections avant chaque insertions

        # On doit créer un ID unique par patient et facility AVANT d'éclater le df sinon jointure impossible sur mdb
        # Pour la collection "patients"
        patient_id_map = {
            (row["Name"], row["Age"], row["Gender"], row["Blood Type"]): ObjectId()
            for _, row in df.drop_duplicates(subset=["Name", "Age", "Gender", "Blood Type"]).iterrows()
        }

        # Injection du patient_id dans chaque ligne du df
        df["patient_id"] = df.apply(
            lambda row: patient_id_map[(row["Name"], row["Age"], row["Gender"], row["Blood Type"])],
            axis = 1   
        )

        # Pour la collection "healthcare_facility"
        facility_id_map = { 
            (row["Hospital"]): ObjectId()
            for _, row in df.drop_duplicates(subset = ["Hospital"]).iterrows()
        }

        df["facility_id"] = df.apply(
            lambda row: facility_id_map[(row["Hospital"])],
            axis = 1
        )

    # 6) Extraction des collections souhaitées en liste et 

        # Conversion DataFrame en dictionnaire avec nettoyage afin de conserver l'unicité (on créer des fiche d'identité)
        patients_cols = ["patient_id", "Name", "Age", "Gender", "Blood Type", "Medical Condition", "Insurance Provider"]
        facility_cols = ["facility_id", "Hospital",]
        encounters_cols = ["patient_id", "facility_id", "Date of Admission", "Admission Type", "Room Number", "Doctor", "Test Results", "Medication", "Billing Amount", "Discharge Date"]

        df_patients = df[patients_cols].drop_duplicates() # Ca doit être unique !
        df_facility = df[facility_cols].drop_duplicates() # Pareil, ce sont des Id
        df_encounters = df[encounters_cols] 

        # On convertit sinon illisible par mongodb : orient = 'records' transforme chaque lignes en dict (pour le json)
        patients_docs = df_patients.to_dict(orient = 'records')
        facility_docs = df_facility.to_dict(orient = 'records')
        encounters_docs = df_encounters.to_dict(orient = 'records')

    # 7) Insertion dans MongoDB

        db["patients"].insert_many(patients_docs)
        print(f" Collection patients insérée:{db['patients'].count_documents({})}")

        db["healthcare_facility"].insert_many(facility_docs)
        print(f" Collection healthcare_facility insérée: {db['healthcare_facility'].count_documents({})}")

        db["encounters"].insert_many(encounters_docs)
        print(f" Collection encounters insérée: {db['encounters'].count_documents({})}")

    # 8) Création des index

        db["patients"].create_index([("patient_id", 1)])
        db["healthcare_facility"].create_index([("facility_id", 1)])
        db["encounters"].create_index([("patient_id", 1)])
        db["encounters"].create_index([("Room Number", 1)])
        db["encounters"].create_index([("Date of Admission", 1)])
        db["patients"].create_index([("Medical Condition", 1)]) 

    # 9) Test de la migration

        # On affiche un document pour chaque collection qui a bien migré
        sample_patients = db['patients'].find_one({})
        sample_healthcare_facility = db['healthcare_facility'].find_one({})
        sample_encounters = db['encounters'].find_one({})
        print(sample_patients,sample_healthcare_facility,sample_encounters)
    
    # 10) Creation des utilisateurs et leur droits

          # Accès à la base admin mongoDB qui gère les utilisateurs et leurs droits
        db_admin = client["admin"]

        # try: except = Pour bloquer la creation d'autres utilisateurs si ils existent déjà         
        # Le personnel medical uniquement en lecture
        try:
            db_admin.command(
                "createUser", os.getenv('MONGO_USER_READ'),
                pwd = os.getenv('MONGO_PASSWORD_READ'),
                roles = [{"role":"read", "db":"medical_p5"}]
                )
        except Exception as e:
            print(f"Utilisateur déjà existant ou erreur : {e}")
        # L'administrateur de la base de données
        try:
            db_admin.command(
                "createUser", os.getenv('MONGO_USER_READWRITE'),
                pwd = os.getenv('MONGO_PASSWORD_READWRITE'),
                roles = [{"role":"readWrite", "db":"medical_p5"}]
                )
        except Exception as e:
            print(f"Utilisateur déjà existant ou erreur : {e}")
        # L'administrateur des utilisateurs
        try:
            db_admin.command(
                "createUser", os.getenv('MONGO_USER_ADMIN'),
                pwd = os.getenv('MONGO_PASSWORD_ADMIN'),
                roles = [{"role": "userAdmin", "db":"medical_p5"}]
                )
        except Exception as e:
            print(f"Utilisateur déjà existant ou erreur : {e}")

    # 2.1) Si la migration à déjà eu lieu retourne le message suivant: 
    else:
        print("Données déjà présentes, migration ignorée")

if __name__ == "__main__":
    main()