
# Chargement des lib pour le traitement des db, pandas et surtout ydata_profiling qui crée des rapports complets des base de données
import pandas as pd 
import sweetviz as sv

#Charger et récuperer le dataset au format .csv
df = pd.read_csv('../data/healthcare_dataset.csv')

#Générer le rapport et le mettre dans le dossier source
profile = sv.analyze(df)
profile.show_html("reports/p5_rapport_profiling.html")