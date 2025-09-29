import os
from dotenv import load_dotenv
import mysql.connector
from mysql.connector import Error
import datetime


# Charger le fichier .env au moment de l'import
load_dotenv()

class Config:
    """Classe de configuration globale pour l'application."""

    SECRET_KEY = 'canadarecruitment'
    JWT_EXPIRATION_DELTA = datetime.timedelta(hours=24)
    APP_URL = '#'  # Remplacez par votre URL réelle
    EMAIL_USER = '#'
    EMAIL_PASSWORD = '#'  # Utilisez un mot de passe d'application pour Gmail
    SMTP_SERVER = '#'
    # SMTP_PORT = 

    DB_HOST = os.getenv('DB_HOST')
    DB_USER = os.getenv('DB_USER')
    DB_PASSWORD = os.getenv('DB_PASSWORD')
    DB_NAME = os.getenv('DB_NAME')

    FRONTEND_URL = os.getenv('FRONTEND_URL', 'https://6e78297843f7.ngrok-free.app')   
    BACKEND_URL = os.getenv('BACKEND_URL', 'https://471abceb70e4.ngrok-free.app')

    CLOUDINARY_CLOUD_NAME = os.getenv('CLOUDINARY_CLOUD_NAME')
    CLOUDINARY_API_KEY = os.getenv('CLOUDINARY_API_KEY')
    CLOUDINARY_API_SECRET = os.getenv('CLOUDINARY_API_SECRET')

    smtp_server = os.getenv("SMTP_SERVER")
    smtp_port = int(os.getenv("SMTP_PORT"))
    username = os.getenv("SMTP_USERNAME")
    password = os.getenv("SMTP_PASSWORD")


    @staticmethod
    def get_db_connection():
        """Crée et retourne une connexion à la base de données."""
        try:
            connection = mysql.connector.connect(
                host=Config.DB_HOST,
                user=Config.DB_USER,
                password=Config.DB_PASSWORD,
                database=Config.DB_NAME
            )
            return connection
        except Error as e:
            print(f"Erreur de connexion MySQL : {e}")
            return None
