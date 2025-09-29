from config import Config
from http import HTTPStatus
from datetime import datetime

class JobOffer:
    def __init__(self, id, title, company, location, type=None, salary=None, category=None, featured=None, description=None, requirements=None, posted=None):
        self.id = id
        self.title = title
        self.company = company
        self.location = location
        self.type = type
        self.salary = salary
        self.category = category
        self.featured = featured
        self.description = description
        self.requirements = requirements
        self.posted = posted

    @staticmethod
    def create(title, company, location, type=None, salary=None, category=None, featured=None, description=None, requirements=None):
        """Crée une nouvelle offre d'emploi dans la table jobs."""
        db = Config.get_db_connection()
        if not db:
            raise Exception("Erreur de connexion à la base de données")

        cursor = db.cursor()
        try:
            query = """
                INSERT INTO jobs (title, company, location, type, salary, category, featured, description, requirements, posted)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            """
            posted = datetime.now()
            values = (title, company, location, type, salary, category, featured, description, requirements, posted)
            cursor.execute(query, values)
            db.commit()
            return cursor.lastrowid
        except Exception as e:
            print(f"Erreur lors de la création de l'offre d'emploi : {e}")
            db.rollback()
            raise Exception(f"Erreur lors de la création de l'offre d'emploi : {e}")
        finally:
            cursor.close()
            db.close()

    @staticmethod
    def update(id, title=None, company=None, location=None, type=None, salary=None, category=None, featured=None, description=None, requirements=None):
        """Met à jour une offre d'emploi dans la table jobs."""
        db = Config.get_db_connection()
        if not db:
            raise Exception("Erreur de connexion à la base de données")

        cursor = db.cursor()
        try:
            updates = {}
            if title is not None:
                updates['title'] = title
            if company is not None:
                updates['company'] = company
            if location is not None:
                updates['location'] = location
            if type is not None:
                updates['type'] = type
            if salary is not None:
                updates['salary'] = salary
            if category is not None:
                updates['category'] = category
            if featured is not None:
                updates['featured'] = featured
            if description is not None:
                updates['description'] = description
            if requirements is not None:
                updates['requirements'] = requirements

            if updates:
                set_clause = ", ".join(f"{key} = %s" for key in updates.keys())
                query = f"UPDATE jobs SET {set_clause} WHERE id = %s"
                values = list(updates.values()) + [id]
                cursor.execute(query, values)
                db.commit()
                return cursor.rowcount > 0
            else:
                return False
        except Exception as e:
            print(f"Erreur lors de la mise à jour de l'offre d'emploi : {e}")
            db.rollback()
            raise Exception(f"Erreur lors de la mise à jour de l'offre d'emploi : {e}")
        finally:
            cursor.close()
            db.close()

    @staticmethod
    def get_by_id(id):
        """Récupère une offre d'emploi par son ID."""
        db = Config.get_db_connection()
        if not db:
            return None

        cursor = db.cursor(dictionary=True)
        try:
            query = """
                SELECT id, title, company, location, type, salary, category, featured, description, requirements, posted
                FROM jobs WHERE id = %s
            """
            cursor.execute(query, (id,))
            result = cursor.fetchone()
            return result if result else None
        except Exception as e:
            print(f"Erreur lors de la récupération de l'offre d'emploi : {e}")
            return None
        finally:
            cursor.close()
            db.close()

    @staticmethod
    def get_all():
        """Récupère toutes les offres d'emploi."""
        db = Config.get_db_connection()
        if not db:
            return None

        cursor = db.cursor(dictionary=True)
        try:
            query = """
                SELECT id, title, company, location, type, salary, category, featured, description, requirements, posted
                FROM jobs
                ORDER BY posted DESC
            """
            cursor.execute(query)
            results = cursor.fetchall()
            return results if results else []
        except Exception as e:
            print(f"Erreur lors de la récupération des offres d'emploi : {e}")
            return None
        finally:
            cursor.close()
            db.close()

    @staticmethod
    def delete(id):
        """Supprime une offre d'emploi par son ID."""
        db = Config.get_db_connection()
        if not db:
            raise Exception("Erreur de connexion à la base de données")

        cursor = db.cursor()
        try:
            query = "DELETE FROM jobs WHERE id = %s"
            cursor.execute(query, (id,))
            if cursor.rowcount == 0:
                raise Exception("Offre d'emploi non trouvée")
            db.commit()
            return True
        except Exception as e:
            print(f"Erreur lors de la suppression de l'offre d'emploi : {e}")
            db.rollback()
            raise Exception(f"Erreur lors de la suppression de l'offre d'emploi : {e}")
        finally:
            cursor.close()
            db.close()