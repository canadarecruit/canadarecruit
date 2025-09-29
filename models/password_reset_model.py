from config import Config
from datetime import datetime

class PasswordResetToken:
    def __init__(self, id, user_id, token, expires_at, created_at=None):
        self.id = id
        self.user_id = user_id
        self.token = token
        self.expires_at = expires_at
        self.created_at = created_at or datetime.now()

    @staticmethod
    def create(user_id, token, expires_at):
        """Crée un nouveau token de réinitialisation dans la table password_reset_tokens."""
        db = Config.get_db_connection()
        if not db:
            raise Exception("Erreur de connexion à la base de données")

        cursor = db.cursor()
        try:
            # Valider que expires_at est une date future
            
            query = """
                INSERT INTO password_reset_tokens (user_id, token, expires_at)
                VALUES (%s, %s, %s)
                RETURNING id, user_id, token, expires_at, created_at
            """
            values = (user_id, token, expires_at)
            cursor.execute(query, values)
            result = cursor.fetchone()
            db.commit()

            if result:
                return PasswordResetToken(
                    id=result[0],
                    user_id=result[1],
                    token=result[2],
                    expires_at=result[3],
                    created_at=result[4]
                )
            else:
                raise Exception("Échec de la création du token de réinitialisation")
        except Exception as e:
            print(f"Erreur lors de la création du token de réinitialisation : {e}")
            db.rollback()
            raise Exception(f"Erreur lors de la création du token de réinitialisation : {e}")
        finally:
            cursor.close()
            db.close()

    @staticmethod
    def get_by_token(token):
        """Récupère un token de réinitialisation par son token."""
        db = Config.get_db_connection()
        if not db:
            return None

        cursor = db.cursor(dictionary=True)
        try:
            query = """
                SELECT id, user_id, token, expires_at, created_at
                FROM password_reset_tokens
                WHERE token = %s
            """
            cursor.execute(query, (token,))
            result = cursor.fetchone()
            print(result)
            if result:
                return result
            return None
        except Exception as e:
            print(f"Erreur lors de la récupération du token de réinitialisation : {e}")
            return None
        finally:
            cursor.close()
            db.close()

    @staticmethod
    def delete(token):
        """Supprime un token de réinitialisation par son token."""
        db = Config.get_db_connection()
        if not db:
            raise Exception("Erreur de connexion à la base de données")

        cursor = db.cursor()
        try:
            query = "DELETE FROM password_reset_tokens WHERE token = %s"
            cursor.execute(query, (token,))
            if cursor.rowcount == 0:
                raise Exception("Token de réinitialisation non trouvé")
            db.commit()
            return True
        except Exception as e:
            print(f"Erreur lors de la suppression du token de réinitialisation : {e}")
            db.rollback()
            raise Exception(f"Erreur lors de la suppression du token de réinitialisation : {e}")
        finally:
            cursor.close()
            db.close()
