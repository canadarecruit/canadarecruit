from config import Config
from http import HTTPStatus
from datetime import datetime

class Document:
    def __init__(self, id, user_id, document_name, status, uploaded_date=None, file_path=None):
        self.id = id
        self.user_id = user_id
        self.document_name = document_name
        self.status = status
        self.uploaded_date = uploaded_date
        self.file_path = file_path

    @staticmethod
    def create(user_id, document_name, file_path=None, status='pending'):
        """Crée un nouveau document dans la table documents."""
        db = Config.get_db_connection()
        if not db:
            raise Exception("Erreur de connexion à la base de données")

        cursor = db.cursor()
        try:
            if status not in ['validated', 'pending', 'missing']:
                raise Exception("Statut invalide. Doit être 'validated', 'pending' ou 'missing'")

            query = """
                INSERT INTO documents (user_id, document_name, status, uploaded_date, file_path)
                VALUES (%s, %s, %s, %s, %s)
            """
            uploaded_date = datetime.now()
            values = (user_id, document_name, status, uploaded_date, file_path)
            cursor.execute(query, values)
            db.commit()
            return cursor.lastrowid
        except Exception as e:
            print(f"Erreur lors de la création du document : {e}")
            db.rollback()
            raise Exception(f"Erreur lors de la création du document : {e}")
        finally:
            cursor.close()
            db.close()

    @staticmethod
    def update(id, document_name=None, status=None, file_path=None):
        """Met à jour un document dans la table documents."""
        db = Config.get_db_connection()
        if not db:
            raise Exception("Erreur de connexion à la base de données")

        cursor = db.cursor()
        try:
            updates = {}
            if document_name is not None:
                updates['document_name'] = document_name
            if status is not None:
                if status not in ['validated', 'pending', 'missing']:
                    raise Exception("Statut invalide. Doit être 'validated', 'pending' ou 'missing'")
                updates['status'] = status
            if file_path is not None:
                updates['file_path'] = file_path

            if updates:
                set_clause = ", ".join(f"{key} = %s" for key in updates.keys())
                query = f"UPDATE documents SET {set_clause} WHERE id = %s"
                values = list(updates.values()) + [id]
                cursor.execute(query, values)
                db.commit()
                return cursor.rowcount
            else:
                return False
        except Exception as e:
            print(f"Erreur lors de la mise à jour du document : {e}")
            db.rollback()
            raise Exception(f"Erreur lors de la mise à jour du document : {e}")
        finally:
            cursor.close()
            db.close()

    @staticmethod
    def get_by_user(user_id):
        """Récupère tous les documents pour un utilisateur donné."""
        db = Config.get_db_connection()
        if not db:
            return None

        cursor = db.cursor(dictionary=True)
        try:
            query = """
                SELECT id, user_id, document_name, status, uploaded_date, file_path
                FROM documents WHERE user_id = %s
                ORDER BY uploaded_date DESC
            """
            cursor.execute(query, (user_id,))
            results = cursor.fetchall()
            return results if results else []
        except Exception as e:
            print(f"Erreur lors de la récupération des documents : {e}")
            return None
        finally:
            cursor.close()
            db.close()

    @staticmethod
    def get_by_id(id):
        """Récupère un document par son ID."""
        db = Config.get_db_connection()
        if not db:
            return None

        cursor = db.cursor(dictionary=True)
        try:
            query = """
                SELECT id, user_id, document_name, status, uploaded_date, file_path
                FROM documents WHERE id = %s
            """
            cursor.execute(query, (id,))
            result = cursor.fetchone()
            return result if result else None
        except Exception as e:
            print(f"Erreur lors de la récupération du document : {e}")
            return None
        finally:
            cursor.close()
            db.close()

    @staticmethod
    def delete(id):
        """Supprime un document par son ID."""
        db = Config.get_db_connection()
        if not db:
            raise Exception("Erreur de connexion à la base de données")

        cursor = db.cursor()
        try:
            query = "DELETE FROM documents WHERE id = %s"
            cursor.execute(query, (id,))
            if cursor.rowcount == 0:
                raise Exception("Document non trouvé")
            db.commit()
            return True
        except Exception as e:
            print(f"Erreur lors de la suppression du document : {e}")
            db.rollback()
            raise Exception(f"Erreur lors de la suppression du document : {e}")
        finally:
            cursor.close()
            db.close()