"""
Base de données SQLite en mémoire (données de démonstration) + helpers DB.
"""
import sqlite3
import pandas as pd
import streamlit as st

from .adapter import DBAdapter


@st.cache_resource
def get_connection():
    conn = sqlite3.connect(":memory:", check_same_thread=False)
    conn.executescript("""
    CREATE TABLE IF NOT EXISTS clients(id INTEGER PRIMARY KEY,nom TEXT,prenom TEXT,
      email TEXT,telephone TEXT,ville TEXT,pays TEXT,date_inscription TEXT,statut TEXT,
      num_carte_identite TEXT,date_expiration_ci TEXT,
      profession TEXT,employeur TEXT,situation_pro TEXT);
    INSERT INTO clients VALUES
    (1,'Lemaire','Sophie','sophie.lemaire@mail.fr','0612345678','Paris','France','2020-01-15','actif','9901234567890','2025-08-20','Ingénieure informatique','TechCorp SA','CDI'),
    (2,'Garnier','Thomas','t.garnier@mail.fr','0623456789','Lyon','France','2019-06-22','actif','9912345678901','2024-11-30','Consultant','McKinsey France','CDI'),
    (3,'Faure','Julie','julie.faure@mail.fr','0634567890','Marseille','France','2021-03-10','actif','9923456789012','2026-04-15','Médecin','CHU Marseille','Titulaire'),
    (4,'Chevalier','Marc','marc.chev@mail.fr','0645678901','Bordeaux','France','2018-11-05','inactif','9934567890123','2023-12-01','Directeur commercial','AutoParts SAS','CDI'),
    (5,'Morin','Lucie','lucie.morin@mail.fr','0656789012','Nantes','France','2022-07-30','actif','9945678901234','2027-06-20','Graphiste','Freelance','Indépendante'),
    (6,'Perrin','Antoine','a.perrin@mail.fr','0667890123','Toulouse','France','2020-09-14','actif','9956789012345','2025-03-10','Avocat','Cabinet Perrin & Associés','Libéral'),
    (7,'Blanc','Camille','c.blanc@mail.fr','0678901234','Strasbourg','France','2023-02-01','actif','9967890123456','2028-01-25','Architecte','Studio 42','CDI'),
    (8,'Renard','Nicolas','n.renard@mail.fr','0689012345','Lille','France','2017-05-18','inactif',NULL,NULL,'Retraité',NULL,'Retraité'),
    (9,'Vidal','Inès','ines.vidal@mail.fr','0690123456','Nice','France','2021-12-25','actif','9989012345678','2026-09-30','Chef de projet','BNP Paribas','CDI'),
    (10,'Roy','Kevin','kevin.roy@mail.fr','0601234567','Rennes','France','2022-04-03','actif','9990123456789','2027-04-03','Développeur full-stack','StartupXYZ','CDI'),
    (11,'Caron','Éléonore','e.caron@mail.fr','0611223344','Paris','France','2019-08-19','actif','9901122334455','2025-11-15','Professeure','Lycée Victor Hugo','Titulaire'),
    (12,'Picard','Bastien','b.picard@mail.fr','0622334455','Montpellier','France','2023-10-11','actif','9912233445566','2028-10-11','Étudiant','Université Paris-Dauphine','Alternance');

    CREATE TABLE IF NOT EXISTS passeports(
      id INTEGER PRIMARY KEY, client_id INTEGER,
      num_passeport TEXT, nationalite TEXT,
      date_emission TEXT, date_expiration TEXT,
      FOREIGN KEY(client_id) REFERENCES clients(id));
    INSERT INTO passeports VALUES
    (1,1,'FP100001','Française','2013-06-15','2018-06-15'),
    (2,1,'FP100002','Française','2023-07-01','2033-07-01'),
    (3,2,'FP200001','Française','2014-03-22','2019-03-22'),
    (4,2,'FP200002','Française','2024-04-01','2034-04-01'),
    (5,3,'FP300001','Française','2021-01-10','2031-01-10'),
    (6,4,'FP400001','Française','2010-09-05','2015-09-05'),
    (7,6,'FP600001','Française','2016-12-14','2021-12-14'),
    (8,6,'FP600002','Française','2026-01-01','2036-01-01'),
    (9,7,'FP700001','Française','2023-02-01','2033-02-01'),
    (10,8,'FP800001','Française','2009-05-18','2014-05-18'),
    (11,9,'FP900001','Française','2018-12-25','2028-12-25'),
    (12,11,'FP110001','Française','2017-08-19','2027-08-19');

    CREATE TABLE IF NOT EXISTS voyages(id INTEGER PRIMARY KEY,client_id INTEGER,
      destination TEXT,pays_destination TEXT,continent TEXT,
      date_depart TEXT,date_retour TEXT,duree_jours INTEGER,
      type_voyage TEXT,transport TEXT,hotel TEXT,
      budget REAL,statut TEXT,note INTEGER,groupe_voyage_id INTEGER,
      FOREIGN KEY(client_id) REFERENCES clients(id));
    INSERT INTO voyages VALUES
    (1,1,'Tokyo','Japon','Asie','2023-04-10','2023-04-24',14,'Tourisme','Avion','Grand Hyatt Tokyo',3200.00,'terminé',5,1001),
    (2,1,'Barcelone','Espagne','Europe','2022-07-15','2022-07-22',7,'Tourisme','Train','Hotel Arts',1100.00,'terminé',4,NULL),
    (3,2,'New York','États-Unis','Amérique','2023-08-01','2023-08-10',9,'Affaires','Avion','Marriott Times Square',2800.00,'terminé',4,NULL),
    (4,2,'Rome','Italie','Europe','2022-12-20','2022-12-27',7,'Tourisme','Avion','Hotel Eden',1350.00,'terminé',5,NULL),
    (5,3,'Bali','Indonésie','Asie','2023-06-01','2023-06-15',14,'Détente','Avion','Four Seasons Bali',2900.00,'terminé',5,1002),
    (6,3,'Lisbonne','Portugal','Europe','2024-03-10','2024-03-14',4,'City Break','Avion','Bairro Alto Hotel',750.00,'terminé',4,NULL),
    (7,4,'Dubai','Émirats Arabes Unis','Asie','2023-01-05','2023-01-12',7,'Luxe','Avion','Burj Al Arab',5500.00,'terminé',5,NULL),
    (8,5,'Marrakech','Maroc','Afrique','2023-10-20','2023-10-27',7,'Culturel','Avion','La Mamounia',1800.00,'terminé',5,NULL),
    (9,5,'Amsterdam','Pays-Bas','Europe','2024-05-01','2024-05-04',3,'City Break','Train','Hotel V Nesplein',620.00,'terminé',3,NULL),
    (10,6,'Maldives','Maldives','Asie','2023-02-14','2023-02-21',7,'Lune de miel','Avion','Conrad Maldives',6200.00,'terminé',5,1003),
    (11,6,'Prague','Tchéquie','Europe','2022-11-03','2022-11-06',3,'City Break','Avion','Augustine Hotel',580.00,'terminé',4,NULL),
    (12,7,'Sydney','Australie','Océanie','2023-12-22','2024-01-05',14,'Tourisme','Avion','Park Hyatt Sydney',4100.00,'terminé',5,NULL),
    (13,7,'Athènes','Grèce','Europe','2023-09-08','2023-09-15',7,'Culturel','Avion','Hotel Grande Bretagne',1250.00,'terminé',4,NULL),
    (14,8,'Reykjavik','Islande','Europe','2023-03-15','2023-03-20',5,'Aventure','Avion','Ion Adventure Hotel',1700.00,'terminé',4,NULL),
    (15,9,'Kyoto','Japon','Asie','2024-04-01','2024-04-10',9,'Culturel','Avion','The Ritz-Carlton Kyoto',3600.00,'terminé',5,NULL),
    (16,9,'Séville','Espagne','Europe','2023-05-18','2023-05-22',4,'City Break','Avion','Hotel Alfonso XIII',890.00,'terminé',4,NULL),
    (17,10,'Cancún','Mexique','Amérique','2023-07-01','2023-07-14',13,'Plage','Avion','Nizuc Resort',3100.00,'terminé',5,1004),
    (18,10,'Berlin','Allemagne','Europe','2022-10-29','2022-10-31',2,'City Break','Train','Hotel de Rome',410.00,'terminé',3,NULL),
    (19,11,'Cape Town','Afrique du Sud','Afrique','2023-11-10','2023-11-24',14,'Safari','Avion','The Silo Hotel',4800.00,'terminé',5,NULL),
    (20,11,'Bruges','Belgique','Europe','2024-02-14','2024-02-16',2,'Romantique','Train','Hotel Dukes Palace',490.00,'terminé',4,NULL),
    (21,12,'Costa Rica','Costa Rica','Amérique','2024-01-15','2024-01-28',13,'Aventure','Avion','Nayara Springs',3900.00,'terminé',5,NULL),
    (22,1,'Singapour','Singapour','Asie','2024-06-20','2024-06-28',8,'Affaires','Avion','Marina Bay Sands',3400.00,'à venir',NULL,NULL),
    (23,3,'New York','États-Unis','Amérique','2024-09-01','2024-09-08',7,'Tourisme','Avion','The Plaza',2600.00,'à venir',NULL,NULL),
    (24,5,'Tenerife','Espagne','Europe','2024-08-10','2024-08-17',7,'Plage','Avion','Royal Hideaway',1500.00,'à venir',NULL,NULL),
    (25,2,'Tokyo','Japon','Asie','2023-04-10','2023-04-24',14,'Tourisme','Avion','Grand Hyatt Tokyo',3200.00,'terminé',5,1001),
    (26,11,'Bali','Indonésie','Asie','2023-06-01','2023-06-15',14,'Détente','Avion','Four Seasons Bali',2900.00,'terminé',4,1002),
    (27,7,'Maldives','Maldives','Asie','2023-02-14','2023-02-21',7,'Lune de miel','Avion','Conrad Maldives',6200.00,'terminé',5,1003),
    (28,9,'Cancún','Mexique','Amérique','2023-07-01','2023-07-14',13,'Plage','Avion','Nizuc Resort',3100.00,'terminé',4,1004);

    CREATE TABLE IF NOT EXISTS employes(
      id INTEGER PRIMARY KEY, nom TEXT, prenom TEXT, poste TEXT,
      email TEXT, telephone TEXT, statut TEXT, date_embauche TEXT
    );
    INSERT INTO employes VALUES
    (1,'Dupont','Marie','Directeur Régional','m.dupont@agency.fr','0601110001','actif','2015-03-01'),
    (2,'Martin','Pierre','Agent Commercial','p.martin@agency.fr','0601110002','actif','2018-06-15'),
    (3,'Leblanc','Sophie','Responsable Visa','s.leblanc@agency.fr','0601110003','actif','2017-09-01'),
    (4,'Bernard','Thomas','Agent Commercial','t.bernard@agency.fr','0601110004','actif','2019-01-15'),
    (5,'Petit','Claire','Directeur Régional','c.petit@agency.fr','0601110005','actif','2016-04-01'),
    (6,'Robert','Julien','Responsable Opérations','j.robert@agency.fr','0601110006','actif','2020-02-01'),
    (7,'Richard','Anaïs','Agent Commercial','a.richard@agency.fr','0601110007','actif','2018-11-01'),
    (8,'Moreau','Kevin','Responsable Visa','k.moreau@agency.fr','0601110008','inactif','2016-03-01'),
    (9,'Simon','Lucie','Agent Commercial','l.simon@agency.fr','0601110009','actif','2021-07-01'),
    (10,'Laurent','Antoine','Directeur Régional','a.laurent@agency.fr','0601110010','actif','2014-09-01'),
    (11,'Michel','Emma','Responsable Opérations','e.michel@agency.fr','0601110011','actif','2019-05-15'),
    (12,'Garcia','Lucas','Agent Commercial','l.garcia@agency.fr','0601110012','actif','2022-01-01'),
    (13,'David','Nina','Responsable Visa','n.david@agency.fr','0601110013','actif','2017-08-01'),
    (14,'Bertrand','Maxime','Agent Commercial','m.bertrand@agency.fr','0601110014','actif','2020-10-01'),
    (15,'Roux','Chloé','Directeur Régional','c.roux@agency.fr','0601110015','actif','2015-12-01');

    CREATE TABLE IF NOT EXISTS affectations(
      id INTEGER PRIMARY KEY, employe_id INTEGER,
      agence TEXT, ville TEXT, pays TEXT, continent TEXT,
      date_debut TEXT, date_fin TEXT,
      FOREIGN KEY(employe_id) REFERENCES employes(id)
    );
    INSERT INTO affectations VALUES
    (1,1,'Agence Paris Opéra','Paris','France','Europe','2015-03-01','2019-08-31'),
    (2,1,'Agence Tokyo Shinjuku','Tokyo','Japon','Asie','2019-09-01','2021-12-31'),
    (3,1,'Agence Dubai Centre','Dubai','Émirats Arabes Unis','Asie','2022-01-01','2023-06-30'),
    (4,1,'Agence Paris Opéra','Paris','France','Europe','2023-07-01',NULL),
    (5,2,'Agence Lyon Centre','Lyon','France','Europe','2018-06-15','2020-12-31'),
    (6,2,'Agence Barcelone','Barcelone','Espagne','Europe','2021-01-01','2022-09-30'),
    (7,2,'Agence Lyon Centre','Lyon','France','Europe','2022-10-01',NULL),
    (8,3,'Agence Marseille','Marseille','France','Europe','2017-09-01','2020-06-30'),
    (9,3,'Agence New York','New York','États-Unis','Amérique','2020-07-01','2022-12-31'),
    (10,3,'Agence Singapour','Singapour','Singapour','Asie','2023-01-01',NULL),
    (11,4,'Agence Paris Montparnasse','Paris','France','Europe','2019-01-15','2021-03-31'),
    (12,4,'Agence Marrakech','Marrakech','Maroc','Afrique','2021-04-01','2023-03-31'),
    (13,4,'Agence Casablanca','Casablanca','Maroc','Afrique','2023-04-01',NULL),
    (14,5,'Agence Bordeaux','Bordeaux','France','Europe','2016-04-01','2020-11-30'),
    (15,5,'Agence Sydney','Sydney','Australie','Océanie','2021-01-01','2022-06-30'),
    (16,5,'Agence Melbourne','Melbourne','Australie','Océanie','2022-07-01',NULL),
    (17,6,'Agence Toulouse','Toulouse','France','Europe','2020-02-01','2021-09-30'),
    (18,6,'Agence Tokyo Ginza','Tokyo','Japon','Asie','2021-10-01','2023-09-30'),
    (19,6,'Agence Séoul','Séoul','Corée du Sud','Asie','2023-10-01',NULL),
    (20,7,'Agence Nice','Nice','France','Europe','2018-11-01','2021-12-31'),
    (21,7,'Agence Lisbonne','Lisbonne','Portugal','Europe','2022-01-01','2023-12-31'),
    (22,7,'Agence Nice','Nice','France','Europe','2024-01-01',NULL),
    (23,8,'Agence Paris Opéra','Paris','France','Europe','2016-03-01','2020-09-30'),
    (24,8,'Agence Dubai Marina','Dubai','Émirats Arabes Unis','Asie','2020-10-01','2022-12-31'),
    (25,9,'Agence Nantes','Nantes','France','Europe','2021-07-01','2022-12-31'),
    (26,9,'Agence Buenos Aires','Buenos Aires','Argentine','Amérique','2023-01-01','2023-12-31'),
    (27,9,'Agence Nantes','Nantes','France','Europe','2024-01-01',NULL),
    (28,10,'Agence Paris Champs-Élysées','Paris','France','Europe','2014-09-01','2019-12-31'),
    (29,10,'Agence Amsterdam','Amsterdam','Pays-Bas','Europe','2020-01-01','2021-11-30'),
    (30,10,'Agence Bangkok','Bangkok','Thaïlande','Asie','2021-12-01',NULL),
    (31,11,'Agence Strasbourg','Strasbourg','France','Europe','2019-05-15','2021-04-30'),
    (32,11,'Agence Rome','Rome','Italie','Europe','2021-05-01','2023-04-30'),
    (33,11,'Agence Madrid','Madrid','Espagne','Europe','2023-05-01',NULL),
    (34,12,'Agence Lille','Lille','France','Europe','2022-01-01','2023-06-30'),
    (35,12,'Agence Miami','Miami','États-Unis','Amérique','2023-07-01',NULL),
    (36,13,'Agence Rennes','Rennes','France','Europe','2017-08-01','2020-07-31'),
    (37,13,'Agence Cape Town','Cape Town','Afrique du Sud','Afrique','2020-08-01','2022-07-31'),
    (38,13,'Agence Nairobi','Nairobi','Kenya','Afrique','2022-08-01',NULL),
    (39,14,'Agence Montpellier','Montpellier','France','Europe','2020-10-01','2022-04-30'),
    (40,14,'Agence Montréal','Montréal','Canada','Amérique','2022-05-01','2023-09-30'),
    (41,14,'Agence Vancouver','Vancouver','Canada','Amérique','2023-10-01',NULL),
    (42,15,'Agence Paris Grands Boulevards','Paris','France','Europe','2015-12-01','2020-05-31'),
    (43,15,'Agence Mexico City','Mexico','Mexique','Amérique','2020-06-01','2022-05-31'),
    (44,15,'Agence Lima','Lima','Pérou','Amérique','2022-06-01',NULL);
    """)
    conn.commit()
    return conn


def _get_db() -> DBAdapter:
    """Retourne l'adaptateur SQLite de démonstration."""
    return DBAdapter("sqlite", get_connection(), "Démo SQLite")


@st.cache_data(ttl=300)
def get_table_summary(table_name: str, date_cols: tuple) -> dict:
    """
    Retourne un résumé de la table : nombre de lignes + dates min/max.
    """
    db = _get_db()
    summary: dict = {"row_count": 0, "date_info": {}}

    try:
        df_count = db.read_sql(f"SELECT COUNT(*) AS n FROM {table_name}")
        summary["row_count"] = int(df_count["n"].iloc[0])
    except Exception:
        return summary

    if date_cols:
        select_parts = []
        for col in date_cols:
            select_parts.append(f"MIN({col}) AS {col}__min")
            select_parts.append(f"MAX({col}) AS {col}__max")
        sql = f"SELECT {', '.join(select_parts)} FROM {table_name}"
        try:
            df_dates = db.read_sql(sql)
            row = df_dates.iloc[0]
            for col in date_cols:
                vmin = row[f"{col}__min"]
                vmax = row[f"{col}__max"]
                summary["date_info"][col] = {
                    "min": str(vmin) if pd.notna(vmin) else None,
                    "max": str(vmax) if pd.notna(vmax) else None,
                }
        except Exception:
            pass

    return summary
