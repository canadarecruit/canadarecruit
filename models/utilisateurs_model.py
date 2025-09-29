from werkzeug.security import generate_password_hash
from config import Config

class Utilisateurs:
    def __init__(self, id, firstName, lastName, email, password, phone=None, birthDate=None, nationality=None, 
                 currentCountry=None, currentCity=None, preferredProvince=None, currentJob=None, 
                 experience=None, education=None, languages=None, acceptTerms=0, newsletter=0):
        self.id = id
        self.firstName = firstName
        self.lastName = lastName
        self.email = email
        self.password = password  # Stores hashed password
        self.phone = phone
        self.birthDate = birthDate
        self.nationality = nationality
        self.currentCountry = currentCountry
        self.currentCity = currentCity
        self.preferredProvince = preferredProvince
        self.currentJob = currentJob
        self.experience = experience
        self.education = education
        self.languages = languages
        self.acceptTerms = acceptTerms
        self.newsletter = newsletter

    @staticmethod
    def create(email, password, firstName=None, lastName=None, phone=None, birthDate=None, nationality=None, 
               currentCountry=None, currentCity=None, preferredProvince=None, currentJob=None, 
               experience=None, education=None, languages=None, acceptTerms=0, newsletter=0):
        print(f"Création de l'utilisateur avec email : {email}")  # Debugging line
        """Crée un nouvel utilisateur dans la base de données."""
        db = Config.get_db_connection()
        if not db:
            raise Exception("Erreur de connexion à la base de données")
        
        cursor = db.cursor()
        try:
            password_hash = generate_password_hash(password)
            query = """
                INSERT INTO users (
                    firstName, lastName, email, password, phone, birthDate, nationality, 
                    currentCountry, currentCity, preferredProvince, currentJob, experience, 
                    education, languages, acceptTerms, newsletter
                )
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                RETURNING id
            """
            values = (
                firstName, lastName, email, password_hash, phone, birthDate, nationality, 
                currentCountry, currentCity, preferredProvince, currentJob, experience, 
                education, languages, acceptTerms, newsletter
            )

            
            cursor.execute(query, values)
            user_id = cursor.fetchone()[0]
            db.commit()
            return user_id
        except Exception as e:
            print(f"Erreur lors de la création de l'utilisateur : {e}")
            db.rollback()
            raise Exception(f"Erreur lors de la création de l'utilisateur : {e}")
        finally:
            cursor.close()
            db.close()

    def update(id, email=None, password=None, firstName=None, lastName=None, phone=None, birthDate=None, 
               nationality=None, currentCountry=None, currentCity=None, preferredProvince=None, 
               currentJob=None, experience=None, education=None, languages=None, acceptTerms=None, 
               newsletter=None):
        """Met à jour les informations de l'utilisateur dans la base de données."""
        db = Config.get_db_connection()
        if not db:
            raise Exception("Erreur de connexion à la base de données")
        
        cursor = db.cursor()
        try:
            updates = {}
            if firstName is not None:
                updates['firstName'] = firstName
            if lastName is not None:
                updates['lastName'] = lastName
            if email is not None:
                updates['email'] = email
            if password is not None:
                updates['password'] = generate_password_hash(password)
            if phone is not None:
                updates['phone'] = phone
            if birthDate is not None:
                updates['birthDate'] = birthDate
            if nationality is not None:
                updates['nationality'] = nationality
            if currentCountry is not None:
                updates['currentCountry'] = currentCountry
            if currentCity is not None:
                updates['currentCity'] = currentCity
            if preferredProvince is not None:
                updates['preferredProvince'] = preferredProvince
            if currentJob is not None:
                updates['currentJob'] = currentJob
            if experience is not None:
                updates['experience'] = experience
            if education is not None:
                updates['education'] = education
            if languages is not None:
                updates['languages'] = languages
            if acceptTerms is not None:
                updates['acceptTerms'] = acceptTerms
            if newsletter is not None:
                updates['newsletter'] = newsletter

            if updates:
                set_clause = ", ".join(f"{key} = %s" for key in updates.keys())
                query = f"UPDATE users SET {set_clause}, created_at = CURRENT_TIMESTAMP WHERE id = %s"
                values = list(updates.values()) + [id]
                cursor.execute(query, values)
                db.commit()

                
        except Exception as e:
            db.rollback()
            raise Exception(f"Erreur lors de la mise à jour de l'utilisateur : {e}")
        finally:
            cursor.close()
            db.close()

    @staticmethod
    def get_user_by_email(email):
        """Récupère un utilisateur par son email."""
        db = Config.get_db_connection()
        if not db:
            return None
        
        cursor = db.cursor(dictionary=True)
        try:
            query = """
                SELECT id, firstName, lastName, email, password, phone, birthDate, nationality, 
                       currentCountry, currentCity, preferredProvince, currentJob, experience, 
                       education, languages, acceptTerms, newsletter
                FROM users WHERE email = %s
            """
            cursor.execute(query, (email,))
            result = cursor.fetchone()
            if result:
                return result
            return None
        except Exception as e:
            print(f"Erreur lors de la récupération de l'utilisateur : {e}")
            return None
        finally:
            cursor.close()
            db.close()

    @staticmethod
    def get_user_by_id(user_id):
        """Récupère un utilisateur par son ID."""
        db = Config.get_db_connection()
        if not db:
            return None
        
        cursor = db.cursor(dictionary=True)
        try:
            query = """
                SELECT id, firstName, lastName, email, password, phone, birthDate, nationality, 
                       currentCountry, currentCity, preferredProvince, currentJob, experience, 
                       education, languages, acceptTerms, newsletter
                FROM users WHERE id = %s
            """
            cursor.execute(query, (user_id,))
            result = cursor.fetchone()
            if result:
                return result
            return None
        except Exception as e:
            print(f"Erreur lors de la récupération de l'utilisateur : {e}")
            return None
        finally:
            cursor.close()
            db.close()

    @staticmethod
    def get_all_users():
        """Récupère la liste de tous les utilisateurs."""
        db = Config.get_db_connection()
        if not db:
            return None
        
        cursor = db.cursor(dictionary=True)
        try:
            query = """
                SELECT id, firstName, lastName, email, password, phone, birthDate, nationality, 
                       currentCountry, currentCity, preferredProvince, currentJob, experience, 
                       education, languages, acceptTerms, newsletter
                FROM users
            """
            cursor.execute(query)
            results = cursor.fetchall()
            return results if results else []
        except Exception as e:
            print(f"Erreur lors de la récupération des utilisateurs : {e}")
            return None
        finally:
            cursor.close()
            db.close()

    @staticmethod
    def delete_user(user_id):
        """Supprime un utilisateur par son ID."""
        db = Config.get_db_connection()
        if not db:
            raise Exception("Erreur de connexion à la base de données")
        
        cursor = db.cursor()
        try:
            query = "DELETE FROM users WHERE id = %s"
            cursor.execute(query, (user_id,))
            if cursor.rowcount == 0:
                raise Exception("Utilisateur non trouvé")
            db.commit()
            return True
        except Exception as e:
            db.rollback()
            raise Exception(f"Erreur lors de la suppression de l'utilisateur : {e}")
        finally:
            cursor.close()
            db.close()