import unittest
import pandas as pd
from pymongo import MongoClient
import os
from dotenv import load_dotenv

load_dotenv()
class TestMigration(unittest.TestCase):

    def setUp(self): 
        self.df = pd.read_csv('data/healthcare_dataset.csv') 
        client = MongoClient(
            host=os.getenv('MONGO_HOST'), 
            port=int(os.getenv('MONGO_PORT')),
            username=os.getenv('MONGO_USER'),
            password=os.getenv('MONGO_PASSWORD')
        )
        self.db = client['medical_p5']
        self.db_admin = client['admin']

    def test_colonnes_migrees(self):
        colonnes_attendues = [
            'Name', 'Age', 'Gender', 'Blood Type', 'Medical Condition',
            'Date of Admission', 'Doctor', 'Hospital', 'Insurance Provider',
            'Billing Amount', 'Room Number', 'Admission Type',
            'Discharge Date', 'Medication', 'Test Results'
        ]
        for col in colonnes_attendues:
            self.assertIn(col, self.df.columns)

    def test_types_colonnes(self):
        df = self.df.copy()
        df['Date of Admission'] = pd.to_datetime(df['Date of Admission'])
        df['Discharge Date'] = pd.to_datetime(df['Discharge Date'])
        self.assertTrue(pd.api.types.is_datetime64_any_dtype(df['Date of Admission']))
        self.assertTrue(pd.api.types.is_datetime64_any_dtype(df['Discharge Date']))
        self.assertTrue(pd.api.types.is_integer_dtype(df['Age']))
        self.assertTrue(pd.api.types.is_float_dtype(df['Billing Amount']))

    def test_pas_de_valeurs_manquantes(self):
        self.assertEqual(self.df.isnull().sum().sum(), 0)

    def test_volume_mdb(self):
        df = self.df.drop_duplicates()
        nb_patients_csv = len(df.drop_duplicates(subset=['Name', 'Age', 'Gender', 'Blood Type']))
        nb_facilities_csv = len(df.drop_duplicates(subset=['Hospital']))
        nb_encounters_csv = len(df)

        self.assertEqual(self.db['patients'].count_documents({}), nb_patients_csv)
        self.assertEqual(self.db['healthcare_facility'].count_documents({}), nb_facilities_csv)
        self.assertEqual(self.db['encounters'].count_documents({}), nb_encounters_csv)

    def test_indexation(self):
        index_patients = self.db["patients"].index_information()
        self.assertIn("patient_id_1", index_patients)
        self.assertIn("Medical Condition_1", index_patients)
        index_facility = self.db["healthcare_facility"].index_information()
        self.assertIn("facility_id_1", index_facility)
        index_encounters = self.db["encounters"].index_information()
        self.assertIn("patient_id_1", index_encounters)
        self.assertIn("Date of Admission_1", index_encounters)
        self.assertIn("Room Number_1", index_encounters)

    def test_users(self):
        result = self.db_admin.command("usersInfo")
        usernames = [u["user"] for u in result["users"]]
        self.assertIn(os.getenv("MONGO_USER_READ"), usernames)
        self.assertIn(os.getenv("MONGO_USER_READWRITE"), usernames)
        self.assertIn(os.getenv("MONGO_USER_ADMIN"), usernames)

    def tearDown(self):
        self.db.client.close()

if __name__ == "__main__":
    unittest.main(verbosity=2)

