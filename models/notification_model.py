from config import Config
from http import HTTPStatus
from datetime import datetime

class Notification:
    def __init__(self, id, user_id, message, type, created_at=None, is_read=0):
        self.id = id
        self.user_id = user_id
        self.message = message
        self.type = type
        self.created_at = created_at
        self.is_read = is_read

    @staticmethod
    def create(user_id, message, type='info'):
        """Crée une nouvelle notification dans la table notifications."""
        db = Config.get_db_connection()
        if not db:
            raise Exception("Erreur de connexion à la base de données")

        cursor = db.cursor()
        try:
            if type not in ['warning', 'info', 'success']:
                raise Exception("Type invalide. Doit être 'warning', 'info' ou 'success'")

            query = """
                INSERT INTO notifications (user_id, message, type, is_read)
                VALUES (%s, %s, %s, %s)
            """
            values = (user_id, message, type, 0)
            cursor.execute(query, values)
            db.commit()
            return cursor.lastrowid
        except Exception as e:
            print(f"Erreur lors de la création de la notification : {e}")
            db.rollback()
            raise Exception(f"Erreur lors de la création de la notification : {e}")
        finally:
            cursor.close()
            db.close()

    @staticmethod
    def update(id, message=None, type=None, is_read=None):
        """Met à jour une notification dans la table notifications."""
        db = Config.get_db_connection()
        if not db:
            raise Exception("Erreur de connexion à la base de données")

        cursor = db.cursor()
        try:
            updates = {}
            if message is not None:
                updates['message'] = message
            if type is not None:
                if type not in ['warning', 'info', 'success']:
                    raise Exception("Type invalide. Doit être 'warning', 'info' ou 'success'")
                updates['type'] = type
            if is_read is not None:
                updates['is_read'] = is_read

            if updates:
                set_clause = ", ".join(f"{key} = %s" for key in updates.keys())
                query = f"UPDATE notifications SET {set_clause} WHERE id = %s"
                values = list(updates.values()) + [id]
                cursor.execute(query, values)
                db.commit()
                return cursor.rowcount > 0
            else:
                return False
        except Exception as e:
            print(f"Erreur lors de la mise à jour de la notification : {e}")
            db.rollback()
            raise Exception(f"Erreur lors de la mise à jour de la notification : {e}")
        finally:
            cursor.close()
            db.close()

    @staticmethod
    def get_by_user(user_id):
        """Récupère toutes les notifications pour un utilisateur donné."""
        db = Config.get_db_connection()
        if not db:
            return None

        cursor = db.cursor(dictionary=True)
        try:
            query = """
                SELECT id, user_id, message, type, created_at, is_read
                FROM notifications WHERE user_id = %s
                ORDER BY created_at DESC
            """
            cursor.execute(query, (user_id,))
            results = cursor.fetchall()
            return results if results else []
        except Exception as e:
            print(f"Erreur lors de la récupération des notifications : {e}")
            return None
        finally:
            cursor.close()
            db.close()

    @staticmethod
    def mark_as_read(id):
        """Marque une notification comme lue."""
        db = Config.get_db_connection()
        if not db:
            raise Exception("Erreur de connexion à la base de données")

        cursor = db.cursor()
        try:
            query = "UPDATE notifications SET is_read = 1 WHERE id = %s"
            cursor.execute(query, (id,))
            db.commit()
            return cursor.rowcount > 0
        except Exception as e:
            print(f"Erreur lors du marquage de la notification comme lue : {e}")
            db.rollback()
            raise Exception(f"Erreur lors du marquage de la notification comme lue : {e}")
        finally:
            cursor.close()
            db.close()

    @staticmethod
    def delete(id):
        """Supprime une notification par son ID."""
        db = Config.get_db_connection()
        if not db:
            raise Exception("Erreur de connexion à la base de données")

        cursor = db.cursor()
        try:
            query = "DELETE FROM notifications WHERE id = %s"
            cursor.execute(query, (id,))
            if cursor.rowcount == 0:
                raise Exception("Notification non trouvée")
            db.commit()
            return True
        except Exception as e:
            print(f"Erreur lors de la suppression de la notification : {e}")
            db.rollback()
            raise Exception(f"Erreur lors de la suppression de la notification : {e}")
        finally:
            cursor.close()
            db.close()

    @staticmethod
    def get_by_user_and_message(user_id, message):
        db = Config.get_db_connection()
        cursor = db.cursor(dictionary=True)
        try:
            query = "SELECT * FROM notifications WHERE user_id = %s AND message = %s"
            cursor.execute(query, (user_id, message))
            return cursor.fetchone()
        except Exception as e:
            return None
        finally:
            cursor.close()
            db.close()