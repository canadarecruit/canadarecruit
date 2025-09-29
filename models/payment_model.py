from config import Config
from http import HTTPStatus
from datetime import datetime

class Payment:
    def __init__(self, id, user_id, description, amount, currency, status, payment_date=None):
        self.id = id
        self.user_id = user_id
        self.description = description
        self.amount = amount
        self.currency = currency
        self.status = status
        self.payment_date = payment_date

    @staticmethod
    def create(user_id, description, amount, currency, status='pending'):
        """Crée un nouveau paiement dans la table payments."""
        db = Config.get_db_connection()
        if not db:
            raise Exception("Erreur de connexion à la base de données")

        cursor = db.cursor()
        try:
            if status not in ['paid', 'pending']:
                raise Exception("Statut invalide. Doit être 'paid' ou 'pending'")
            if amount <= 0:
                raise Exception("Le montant doit être supérieur à 0")
            if not currency:
                raise Exception("La devise est requise")

            query = """
                INSERT INTO payments (user_id, description, amount, currency, status, payment_date)
                VALUES (%s, %s, %s, %s, %s, %s)
            """
            payment_date = datetime.now() if status == 'paid' else None
            values = (user_id, description, amount, currency, status, payment_date)
            cursor.execute(query, values)
            db.commit()
            return cursor.lastrowid
        except Exception as e:
            print(f"Erreur lors de la création du paiement : {e}")
            db.rollback()
            raise Exception(f"Erreur lors de la création du paiement : {e}")
        finally:
            cursor.close()
            db.close()

    @staticmethod
    def update(id, description=None, amount=None, currency=None, status=None, payment_date=None):
        """Met à jour un paiement dans la table payments."""
        db = Config.get_db_connection()
        if not db:
            raise Exception("Erreur de connexion à la base de données")

        cursor = db.cursor()
        try:
            updates = {}
            if description is not None:
                updates['description'] = description
            if amount is not None:
                if amount <= 0:
                    raise Exception("Le montant doit être supérieur à 0")
                updates['amount'] = amount
            if currency is not None:
                if not currency:
                    raise Exception("La devise est requise")
                updates['currency'] = currency
            if status is not None:
                if status not in ['paid', 'pending']:
                    raise Exception("Statut invalide. Doit être 'paid' ou 'pending'")
                updates['status'] = status
                if status == 'paid' and 'payment_date' not in updates:
                    updates['payment_date'] = datetime.now()
                elif status == 'pending':
                    updates['payment_date'] = None
            if payment_date is not None:
                updates['payment_date'] = payment_date

            if updates:
                set_clause = ", ".join(f"{key} = %s" for key in updates.keys())
                query = f"UPDATE payments SET {set_clause} WHERE id = %s"
                values = list(updates.values()) + [id]
                cursor.execute(query, values)
                db.commit()
                return cursor.rowcount > 0
            else:
                return False
        except Exception as e:
            print(f"Erreur lors de la mise à jour du paiement : {e}")
            db.rollback()
            raise Exception(f"Erreur lors de la mise à jour du paiement : {e}")
        finally:
            cursor.close()
            db.close()

    @staticmethod
    def get_by_user(user_id):
        """Récupère tous les paiements pour un utilisateur donné."""
        db = Config.get_db_connection()
        if not db:
            return None

        cursor = db.cursor(dictionary=True)
        try:
            query = """
                SELECT id, user_id, description, amount, currency, status, payment_date
                FROM payments WHERE user_id = %s
                ORDER BY payment_date DESC
            """
            cursor.execute(query, (user_id,))
            results = cursor.fetchall()
            return results if results else []
        except Exception as e:
            print(f"Erreur lors de la récupération des paiements : {e}")
            return None
        finally:
            cursor.close()
            db.close()

    @staticmethod
    def get_by_id(id):
        """Récupère un paiement par son ID."""
        db = Config.get_db_connection()
        if not db:
            return None

        cursor = db.cursor(dictionary=True)
        try:
            query = """
                SELECT id, user_id, description, amount, currency, status, payment_date
                FROM payments WHERE id = %s
            """
            cursor.execute(query, (id,))
            result = cursor.fetchone()
            return result if result else None
        except Exception as e:
            print(f"Erreur lors de la récupération du paiement : {e}")
            return None
        finally:
            cursor.close()
            db.close()

    @staticmethod
    def delete(id):
        """Supprime un paiement par son ID."""
        db = Config.get_db_connection()
        if not db:
            raise Exception("Erreur de connexion à la base de données")

        cursor = db.cursor()
        try:
            query = "DELETE FROM payments WHERE id = %s"
            cursor.execute(query, (id,))
            if cursor.rowcount == 0:
                raise Exception("Paiement non trouvé")
            db.commit()
            return True
        except Exception as e:
            print(f"Erreur lors de la suppression du paiement : {e}")
            db.rollback()
            raise Exception(f"Erreur lors de la suppression du paiement : {e}")
        finally:
            cursor.close()
            db.close()