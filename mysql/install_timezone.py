import mysql.connector
import os

# Configuration de la connexion MySQL
config = {
    'user': 'root',
    'password': '',
    'host': 'localhost',
    'database': 'mysql'
}

try:
    print("Tentative de connexion à MySQL...")
    # Connexion à MySQL
    conn = mysql.connector.connect(**config)
    cursor = conn.cursor()
    print("Connexion réussie!")

    # Lecture du fichier SQL des tables
    sql_file = os.path.join(os.path.dirname(__file__), 'timezone.sql')
    print(f"Lecture du fichier SQL des tables: {sql_file}")
    with open(sql_file, 'r') as file:
        sql_commands = file.read()

    # Exécution des commandes SQL pour créer les tables
    print("Création des tables...")
    for command in sql_commands.split(';'):
        if command.strip():
            print(f"Exécution de la commande: {command[:100]}...")
            cursor.execute(command)
            conn.commit()
            print("Commande exécutée avec succès!")

    # Lecture du fichier SQL des données
    data_file = os.path.join(os.path.dirname(__file__), 'timezone_data.sql')
    print(f"Lecture du fichier SQL des données: {data_file}")
    with open(data_file, 'r') as file:
        data_commands = file.read()

    # Exécution des commandes SQL pour insérer les données
    print("Insertion des données...")
    for command in data_commands.split(';'):
        if command.strip():
            print(f"Exécution de la commande: {command[:100]}...")
            cursor.execute(command)
            conn.commit()
            print("Commande exécutée avec succès!")

    print("Tables et données de fuseaux horaires installées avec succès!")

except mysql.connector.Error as err:
    print(f"Erreur MySQL: {err}")

except Exception as e:
    print(f"Erreur inattendue: {e}")

finally:
    if 'conn' in locals() and conn.is_connected():
        cursor.close()
        conn.close()
        print("Connexion MySQL fermée.") 