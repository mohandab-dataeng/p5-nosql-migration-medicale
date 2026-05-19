# P05 - Healthcare Data Migration - MongoDB & Docker

![Python](https://img.shields.io/badge/Python-3.12-blue)  
![MongoDB](https://img.shields.io/badge/MongoDB-8.0-green)  
![Docker](https://img.shields.io/badge/Docker-29.x-blue)  
![Docker Compose](https://img.shields.io/badge/Docker_Compose-v2-blue)

* * *

## 1\. Présentation

Un client privé a une problématique de volume croissant pour ses données de santé. Ces données semblent être de type relationnel une fois mis à plat, elles nous sont fournies au format .csv. La solution retenue est de migrer les données en NoSQL. L'ensemble des services ; pipeline, service NoSQL et bases sont intégrés dans des containers Docker afin de permettre une meilleure scalabilité face à la croissance.

**Infrastructure :**

- Docker ; 3 containers, 2 éphémères pour la migration et 1 persistant pour le service NoSQL.
- MongoDB ; une base NoSQL plus flexible pour la croissance, **sharding** et **scalabilité horizontale** pour le futur (*pas plus de puissance mais plus de partage entre les nœuds*). La structure des données est conservée, c'est lié à la nature métier donc pas d'embedding (3 collections).
- Python et pymongo ; pour les scripts de migration et de tests pour l'idempotence, garanties de répétabilité et de reproductibilité à travers les systèmes.

* * *

## 2\. Architecture
```
$ docker compose up
        │
        ▼
┌────────────────────┐          ┌──────────────┐
│ docker-compose.yml │──────── ►│  Dockerfile  │
└─────────┬──────────┘          └──────┬───────┘
          │                            │
          ├────────────────────────────┼───────────────────────────┐
          │ (Docker Hub)               │ (build)                   │ (build)
          ▼                            ▼                           ▼
┌───────────────────────┐  ┌───────────────────────┐  ┌───────────────────────┐
│ PERSISTANT            │  │ ÉPHÉMÈRE              │  │ ÉPHÉMÈRE              │
│                       │  │                       │  │                       │
│ service: mongodb      │  │ service: migration    │  │ service: migration-   │
│ image: mongo:8        │  │                       │  │          test         │
│                       │◄ ┤ script_migration.py   │  │                       │
│ container-p5-mdb      │  │                       │  │ script_test_          │
│                       │  │ depends_on: mongodb   │  │   migration.py        │
│                       │  │                       │  │                       │
│                       │  │   ▲                   │  │ depends_on:           │
│                       │  │   │                   │  │   migration           │
│                       │  │ healthcare_           │  │                       │
│                       │  │ dataset.csv           │  │                       │
│                       │  │ (bind mount)          │  │                       │ 
└───────────┬───────────┘  └───────────────────────┘  └───────────────────────┘
            │
     27017:localhost
            │
┌───────────┴────────────┐
│                        │
│                        │
│  ┌──────────┐ ┌──────┐ │
│  │ volume-  │ │volume│ │
│  │ p5-config│ │p5-db │ │
│  │ (config) │ │(data)│ │
│  └──────────┘ └──────┘ │
└────────────────────────┘
```

**Collections :**

| Collection | Rôle | Clé de référence |
| --- | --- | --- |
| `patients` | Fiche d'identité des patients | `patient_id` |
| `healthcare_facility` | Établissement de prise en charge des soins | `facility_id` |
| `encounters` | Consultation, rencontre clinique | `encounters_id` |

* * *

## 3\. Prérequis

| Outil | Version minimum | Remarque |
| --- | --- | --- |
| `Git` | git version 2.43.0 | sudo apt install git |
| `Docker` | Docker version 29.5.0, build 98f1464 | Voir doc officielle |
| `Docker compose` | Docker Compose version v5.1.3 | Inclus dans Docker |

* * *

## 4\. Variables d'environnement

**Pour les accès Docker :**

| Variable | Description | Exemple |
| --- | --- | --- |
| `MONGO_USER` | Utilisateur racine du localhost | `root` |
| `MONGO_PASSWORD` | Mot de passe racine du localhost | `Mot_de_passe` |
| `MONGO_HOST` | Nom du service mongodb | `mongodb` |
| `MONGO_PORT` | Le port d'accès au container depuis localhost | `00000` |

**Dans le service MongoDB seulement :**

| Variable | Description | Exemple |
| --- | --- | --- |
| `MONGO_USER_READ` | Le personnel ne devant pas modifier la base | `personnel_medical_acces_lecture_seulement` |
| `MONGO_PASSWORD_READ` | Mot de passe pour le personnel | `mot_de_passe` |
| `MONGO_USER_READWRITE` | L'administrateur de la base de données, personnel technique pour modifier la base | `administrateur_database_lecture_ecriture` |
| `MONGO_PASSWORD_READWRITE` | Mot de passe pour l'administrateur | `mot_de_passe` |
| `MONGO_USER_ADMIN` | Utilisateur racine du localhost | `administrateur_creation_utilisateur` |
| `MONGO_PASSWORD_ADMIN` | Mot de passe de l'administrateur des utilisateurs | `mot_de_passe` |

> **Ne jamais committer le fichier `.env`** il contient des credentials à mettre dans le gitignore avant de pousser  
> **Séparer les rôles entre l'administrateur data et utilisateur** La sécurité peut être compromise sinon.

* * *

## 5\. Installation

```bash
# Terminal linux - bash

# 1. Cloner le repo depuis git vers sa machine
git clone <url>

# 2. Se placer dans le répertoire, toutes les commandes partent de là
cd <nom_du_repertoire>

# 3. Créer le fichier d'environnement pour les credentials. Ils ne s'entrent qu'une fois, ici.
cp .env.example .env # <- copie l'exemple il faut ensuite le modifier et le renommer .env
nano .env # <- Commande pour accéder et modifier les credentials (ctrl+o pour enregistrer, ctrl+x pour quitter)

# 4. Lancer le pipeline
docker compose up
```

* * *

## 6\. Utilisation

| Commande | Description |
| --- | --- |
| `` `docker compose up` `` | Lance le pipeline complet |
| `` `docker compose down` `` | Stoppe les containers |
| `` `docker compose down -v` `` | Stoppe et supprime les volumes |

> Voir notebooks/CRUD-mdb.ipynb pour les opérations CRUD et les requêtes d'agrégation.

* * *

## 7\. Structure du projet

```
├── docker-compose.yml            # Orchestration des 3 services
├── Dockerfile                    # Image Python des containers éphémères
├── requirements.txt              # Dépendances Python
├── .env                          # Credentials (non versionné)
├── .env.example                  # Template credentials (versionné)
├── README.md
├── data/
│   └── healthcare_dataset.csv    # Dataset source
├── src/
│   ├── script_migration.py       # Pipeline de migration
│   └── script_test_migration.py  # Tests d'intégrité
├── notebooks/
│   └── CRUD-mdb.ipynb            # Démo opérations CRUD
└── reports/
    └── p5_rapport_profiling.html  # Rapport de profiling
```

* * *


## 8\. Tests

**Tests d'intégrité réalisés :**

1.  Colonnes du CSV présentes et complètes
2.  Types des colonnes (dates, entiers, flottants)
3.  Aucune valeur manquante dans le dataset
4.  Volume de documents cohérent entre CSV et MongoDB
5.  Index correctement créés sur les champs
6.  Users MongoDB créés avec les bons rôles

**Outputs attendus aux tests :**

```
...
migration-test-1  | test_colonnes_migrees (__main__.TestMigration.test_colonnes_migrees) ... ok
...
migration-test-1  | test_indexation (__main__.TestMigration.test_indexation) ... ok
...
migration-test-1  | test_pas_de_valeurs_manquantes (__main__.TestMigration.test_pas_de_valeurs_manquantes) ... ok
...
migration-test-1  | test_types_colonnes (__main__.TestMigration.test_types_colonnes) ... ok
...
migration-test-1  | test_users (__main__.TestMigration.test_users) ... ok
...
migration-test-1  | test_volume_mdb (__main__.TestMigration.test_volume_mdb) ... ok
...
migration-test-1  | 
migration-test-1  | ----------------------------------------------------------------------
migration-test-1  | Ran 6 tests in 2.488s
migration-test-1  | 
migration-test-1  | OK
...
migration-test-1 exited with code 0
```

* * *

## 9\. Limites connues

**Limite 1 Structure des données** 

Dans la base de données NoSQL, la structure des données est de type référencée, et non pas embedding. Pour des données médicales cette structure est souhaitable, l'avantage de MongoDB est sa flexibilité, le sharding par nœuds qui permet l'incrémentation de documents sans coupure de service, ce qui est courant dans le médical. Sinon PostgreSQL ou une autre base relationnelle est meilleure sur tous les points. Pour une équivalence, il faut obligatoirement JSON Schema Validation ainsi que la formule payante de MongoDB la version entreprise pour le logging ce qui est de base sur PostgreSQL.

**Limite 2 Clé primaire sur la collection patient**  

La clé primaire patient est basée sur l'agrégation des caractéristiques patients ce qui est dangereux en milieu médical. En prod. il faut impérativement une clé plus fiable le numéro de sécurité sociale ou l'identifiant national de santé. Sinon il faudra trouver l'ensemble de variables le plus solide avec les référents métiers.

**Limite 3 Idempotence partielle pour la première migration** 

Le script de migration pousse les collections avec `insert_many`. L'objectif étant pour la 1ère migration d'insérer la totalité rapidement, mais elle s'accompagne d'un `if db[" "].count_documents({}) == 0` pour bloquer l'accumulation, si le docker compose est lancé à plusieurs reprises en cas d'erreur lors de la construction du pipeline. Toutefois cela rigidifie la migration et empêche toute mise à jour future, ce qui est contradictoire avec le métier et le choix même de MongoDB qui permet cette plasticité. Par conséquent le prochain script python devra être modifié avec des upsert ; `...collection.update_one(...upsert=True)`.

* * *

## 10\. Auteur

Mohamed Abaran - Data Engineer - Expert en ingénierie et science des données - code NSF 326  
GitHub : https://github.com/mohandab-dataeng/p5-nosql-migration-medicale
