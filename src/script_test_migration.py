import unittest
import pandas as pd
from pymongo import MongoClient
import os
from dotenv import load_dotenv

load_dotenv()

class TestMigration(unittest.TestCase):

    def setUp(self): # Indispensable unitest recherche la méthode setUp
        self.df = pd.read_csv('data/healthcare_dataset.csv') # Pandas recupere le csv
        client = MongoClient(
            host=os.getenv('MONGO_HOST'), # Comme pour le script de migration on prends se connecteà l'image
            port=int(os.getenv('MONGO_PORT')),
            username=os.getenv('MONGO_USER'),
            password=os.getenv('MONGO_PASSWORD')
        )
        self.db = client['medical_p5']

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

    def tearDown(self):
        self.db.client.close()

if __name__ == "__main__":
    unittest.main(verbosity=2)

