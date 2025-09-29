from config import Config
from http import HTTPStatus

class Step:
    def __init__(self, id, step_name, step_order):
        self.id = id
        self.step_name = step_name
        self.step_order = step_order

    @staticmethod
    def create(step_name, step_order):
        """Crée une nouvelle étape dans la table steps."""
        db = Config.get_db_connection()
        if not db:
            raise Exception("Erreur de connexion à la base de données")

        cursor = db.cursor()
        try:
            query = """
                INSERT INTO steps (step_name, step_order)
                VALUES (%s, %s)
            """
            values = (step_name, step_order)
            cursor.execute(query, values)
            db.commit()
            return cursor.lastrowid
        except Exception as e:
            print(f"Erreur lors de la création de l'étape : {e}")
            db.rollback()
            raise Exception(f"Erreur lors de la création de l'étape : {e}")
        finally:
            cursor.close()
            db.close()

    @staticmethod
    def update(id, step_name=None, step_order=None):
        """Met à jour une étape dans la table steps."""
        db = Config.get_db_connection()
        if not db:
            raise Exception("Erreur de connexion à la base de données")

        cursor = db.cursor()
        try:
            updates = {}
            if step_name is not None:
                updates['step_name'] = step_name
            if step_order is not None:
                updates['step_order'] = step_order

            if updates:
                set_clause = ", ".join(f"{key} = %s" for key in updates.keys())
                query = f"UPDATE steps SET {set_clause} WHERE id = %s"
                values = list(updates.values()) + [id]
                cursor.execute(query, values)
                db.commit()
                return cursor.rowcount > 0
            else:
                return False
        except Exception as e:
            print(f"Erreur lors de la mise à jour de l'étape : {e}")
            db.rollback()
            raise Exception(f"Erreur lors de la mise à jour de l'étape : {e}")
        finally:
            cursor.close()
            db.close()

    @staticmethod
    def get_by_id(id):
        """Récupère une étape par son ID."""
        db = Config.get_db_connection()
        if not db:
            return None

        cursor = db.cursor(dictionary=True)
        try:
            query = """
                SELECT id, step_name, step_order
                FROM steps WHERE id = %s
            """
            cursor.execute(query, (id,))
            result = cursor.fetchone()
            return result if result else None
        except Exception as e:
            print(f"Erreur lors de la récupération de l'étape : {e}")
            return None
        finally:
            cursor.close()
            db.close()

    @staticmethod
    def get_all():
        """Récupère toutes les étapes."""
        db = Config.get_db_connection()
        if not db:
            return None

        cursor = db.cursor(dictionary=True)
        try:
            query = """
                SELECT id, step_name, step_order
                FROM steps
                ORDER BY step_order ASC
            """
            cursor.execute(query)
            results = cursor.fetchall()
            return results if results else []
        except Exception as e:
            print(f"Erreur lors de la récupération des étapes : {e}")
            return None
        finally:
            cursor.close()
            db.close()

    @staticmethod
    def delete(id):
        """Supprime une étape par son ID."""
        db = Config.get_db_connection()
        if not db:
            raise Exception("Erreur de connexion à la base de données")

        cursor = db.cursor()
        try:
            query = "DELETE FROM steps WHERE id = %s"
            cursor.execute(query, (id,))
            if cursor.rowcount == 0:
                raise Exception("Étape non trouvée")
            db.commit()
            return True
        except Exception as e:
            print(f"Erreur lors de la suppression de l'étape : {e}")
            db.rollback()
            raise Exception(f"Erreur lors de la suppression de l'étape : {e}")
        finally:
            cursor.close()
            db.close()