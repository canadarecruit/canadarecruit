from config import Config
from http import HTTPStatus
from datetime import datetime

class UserStep:
    def __init__(self, id, user_id, step_id, status, completion_date=None):
        self.id = id
        self.user_id = user_id
        self.step_id = step_id
        self.status = status
        self.completion_date = completion_date

    @staticmethod
    def create(user_id, step_id, completion_date,status='pending'):
        """Crée une nouvelle entrée dans la table user_application_progress."""
        db = Config.get_db_connection()
        if not db:
            raise Exception("Erreur de connexion à la base de données")

        cursor = db.cursor()
        try:
            query = """
                INSERT INTO user_application_progress (user_id, step_id, status, completion_date)
                VALUES (%s, %s, %s, %s)
            """
            values = (user_id, step_id, status, completion_date)
            cursor.execute(query, values)
            db.commit()
            return cursor.lastrowid
        except Exception as e:
            print(f"Erreur lors de la création de l'entrée : {e}")
            db.rollback()
            raise Exception(f"Erreur lors de la création de l'entrée : {e}")
        finally:
            cursor.close()
            db.close()

    @staticmethod
    def update(id, status=None, completion_date=None):
        """Met à jour une entrée dans la table user_application_progress."""
        db = Config.get_db_connection()
        if not db:
            raise Exception("Erreur de connexion à la base de données")

        cursor = db.cursor()
        try:
            updates = {}
            if status is not None:
                updates['status'] = status
            if completion_date is not None:
                updates['completion_date'] = completion_date

            if updates:
                set_clause = ", ".join(f"{key} = %s" for key in updates.keys())
                query = f"UPDATE user_application_progress SET {set_clause} WHERE id = %s"
                values = list(updates.values()) + [id]
                cursor.execute(query, values)
                db.commit()
                return cursor.rowcount > 0
            else:
                return False
        except Exception as e:
            print(f"Erreur lors de la mise à jour de l'entrée : {e}")
            db.rollback()
            raise Exception(f"Erreur lors de la mise à jour de l'entrée : {e}")
        finally:
            cursor.close()
            db.close()

    @staticmethod
    def get_id(user_id, step_id):
        """Récupère toutes les entrées pour une étape donnée."""
        db = Config.get_db_connection()
        if not db:
            return None

        cursor = db.cursor(dictionary=True)
        try:
            query = """
                SELECT id, user_id, step_id, status, completion_date
                FROM user_application_progress WHERE user_id = %s AND step_id = %s
            """
            cursor.execute(query, (user_id,step_id,))
            results = cursor.fetchall()
            return results if results else []
        except Exception as e:
            print(f"Erreur lors de la récupération des entrées : {e}")
            return None
        finally:
            cursor.close()
            db.close()

    @staticmethod
    def get_by_user(user_id):
        """Récupère toutes les entrées pour un utilisateur donné."""
        db = Config.get_db_connection()
        if not db:
            return None

        cursor = db.cursor(dictionary=True)
        try:
            query = """
                SELECT 
                    uap.id,
                    uap.user_id,
                    uap.step_id,
                    s.step_name as name,
                    s.step_order,
                    uap.status as status,
                    uap.completion_date as date
                FROM 
                    user_application_progress AS uap
                JOIN 
                    steps AS s
                    ON uap.step_id = s.id
                WHERE 
                    uap.user_id = %s
                ORDER BY 
                    s.step_order ASC;

            """
            cursor.execute(query, (user_id,))
            results = cursor.fetchall()
            return results if results else []
        except Exception as e:
            print(f"Erreur lors de la récupération des entrées : {e}")
            return None
        finally:
            cursor.close()
            db.close()

    @staticmethod
    def get_by_step(step_id):
        """Récupère toutes les entrées pour une étape donnée."""
        db = Config.get_db_connection()
        if not db:
            return None

        cursor = db.cursor(dictionary=True)
        try:
            query = """
                SELECT id, user_id, step_id, status, completion_date
                FROM user_application_progress WHERE step_id = %s
            """
            cursor.execute(query, (step_id,))
            results = cursor.fetchall()
            return results if results else []
        except Exception as e:
            print(f"Erreur lors de la récupération des entrées : {e}")
            return None
        finally:
            cursor.close()
            db.close()

    @staticmethod
    def delete(id):
        """Supprime une entrée de la table user_application_progress par son ID."""
        db = Config.get_db_connection()
        if not db:
            raise Exception("Erreur de connexion à la base de données")

        cursor = db.cursor()
        try:
            query = "DELETE FROM user_application_progress WHERE id = %s"
            cursor.execute(query, (id,))
            if cursor.rowcount == 0:
                raise Exception("Entrée non trouvée")
            db.commit()
            return True
        except Exception as e:
            db.rollback()
            raise Exception(f"Erreur lors de la suppression de l'entrée : {e}")
        finally:
            cursor.close()
            db.close()