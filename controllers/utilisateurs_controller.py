from flask import Blueprint, request, jsonify
import jwt
from functools import wraps
import smtplib
from email.mime.text import MIMEText
from werkzeug.security import check_password_hash, generate_password_hash
from models.utilisateurs_model import Utilisateurs
from models.password_reset_model import PasswordResetToken
from models.notification_model import Notification
from http import HTTPStatus
import datetime
import uuid
from config import Config
from email.mime.multipart import MIMEMultipart
from models.document_model import Document  # Assurez-vous que ce modèle existe
from models.payment_model import Payment    # Assurez-vous que ce modèle existe
from models.user_step_model import UserStep  # Assurez-vous que ce modèle existe

class UsersController:
    @staticmethod
    def _get_token():
        """Extrait le token JWT de l'en-tête Authorization."""
        auth_header = request.headers.get('Authorization')
        if not auth_header:
            return None
        try:
            return auth_header.split(" ")[1]  # Format : "Bearer <token>"
        except IndexError:
            return None
        
    @staticmethod
    def create_user():
        """Crée un utilisateur et envoie un email de confirmation via AlwaysData."""
        try:
            data = request.get_json()
            required_fields = ['email', 'password', 'firstName', 'lastName', 'acceptTerms']

            # Vérifie la présence des champs obligatoires
            if not all(field in data for field in required_fields):
                return jsonify({"message": "Champs obligatoires manquants"}), HTTPStatus.BAD_REQUEST

            # Extraire les champs
            email = data.get('email')
            password = data.get('password')
            firstName = data.get('firstName')
            lastName = data.get('lastName')
            acceptTerms = 1 if data.get('acceptTerms') else 0
            phone = data.get('phone')
            birthDate = data.get('birthDate')
            nationality = data.get('nationality')
            currentCountry = data.get('currentCountry')
            currentCity = data.get('currentCity')
            preferredProvince = data.get('preferredProvince')
            currentJob = data.get('currentJob')
            experience = data.get('experience')
            education = data.get('education')
            languages = data.get('languages')
            newsletter = 1 if data.get('newsletter') else 0

            user = Utilisateurs.get_user_by_email(email)
            if user:
                return jsonify({"message": "Utilisateur déjà existant"}), HTTPStatus.CONFLICT

            # Validation supplémentaire
            if not email or not email.strip() or '@' not in email:
                return jsonify({"message": "Adresse email invalide"}), HTTPStatus.BAD_REQUEST
            if not password or len(password) < 8:
                return jsonify({"message": "Le mot de passe doit contenir au moins 8 caractères"}), HTTPStatus.BAD_REQUEST

            # Créer l'utilisateur
            user_id = Utilisateurs.create( 
                email=email,
                password=password,
                firstName=firstName,
                lastName=lastName,
                phone=phone,
                birthDate=birthDate,
                nationality=nationality,
                currentCountry=currentCountry,
                currentCity=currentCity,
                preferredProvince=preferredProvince,
                currentJob=currentJob,
                experience=experience,
                education=education,
                languages=languages,
                acceptTerms=acceptTerms,
                newsletter=newsletter
            )

            # Configuration SMTP AlwaysData
            smtp_server = Config.smtp_server
            smtp_port = Config.smtp_port
            username = Config.username
            password = Config.password

            # Contenu de l'e-mail
            subject = "Confirmation de création de votre compte Canada Recruitment"
            body = f"""Bonjour {firstName or 'Utilisateur'},

Votre compte sur Canada Recruitment a été créé avec succès.
Vous pouvez maintenant vous connecter en utilisant votre adresse e-mail et votre mot de passe.

Nous vous souhaitons la bienvenue !

L'équipe Canada Recruitment
"""

            # Création du message
            message = MIMEMultipart()
            message["From"] = username
            message["To"] = email
            message["Subject"] = subject
            message.attach(MIMEText(body, "plain"))

            # Envoi de l'email
            with smtplib.SMTP(smtp_server, smtp_port) as server:
                server.starttls()
                server.login(username, password)
                server.send_message(message)

            print("✅ Email de confirmation envoyé via AlwaysData")

            # Créer une notification
            Notification.create(
                user_id=user_id,
                message="Etape 1: Compté créé avec succès.",
                type="success"
            )
            Notification.create(
                user_id=user_id,
                message="Etape 2: Formulaire complété avec succès.",
                type="success"
            )

            return jsonify({
                'message': 'Votre compte a été créé avec succès. Un e-mail de confirmation vous a été envoyé.',
                'user_id': user_id
            }), HTTPStatus.CREATED

        except Exception as e:
            return jsonify({"message": f"Erreur lors de la création de l'utilisateur : {str(e)}"}), HTTPStatus.INTERNAL_SERVER_ERROR

    @staticmethod
    def update_user():
        """Met à jour un utilisateur."""
        token = UsersController._get_token()
        if not token:
            return jsonify({"message": "Token manquant"}), HTTPStatus.UNAUTHORIZED

        try:
            decoded_token = jwt.decode(token, Config.SECRET_KEY, algorithms=['HS256'])
            user_id = decoded_token.get('user_id')
            if not user_id:
                return jsonify({"message": "ID utilisateur manquant dans le token"}), HTTPStatus.BAD_REQUEST

            data = request.get_json()
            user = Utilisateurs(user_id, None, None, None, None, None, None, None, None, None, None, None, None, None, None, None, None)  # Instance avec l'ID pour update
            user.update(
                data.get('email'),
                data.get('password'),
                data.get('firstName'),
                data.get('lastName'),
                data.get('phone'),
                data.get('birthDate'),
                data.get('nationality'),
                data.get('currentCountry'),
                data.get('currentCity'),
                data.get('preferredProvince'),
                data.get('currentJob'),
                data.get('experience'),
                data.get('education'),
                data.get('languages'),
                data.get('acceptTerms'),
                data.get('newsletter')
            )
            return jsonify({'message': 'Utilisateur mis à jour avec succès'}), HTTPStatus.OK
        except jwt.ExpiredSignatureError:
            return jsonify({"message": "Token expiré"}), HTTPStatus.UNAUTHORIZED
        except jwt.InvalidTokenError:
            return jsonify({"message": "Token invalide"}), HTTPStatus.UNAUTHORIZED
        except Exception as e:
            return jsonify({"error": str(e)}), HTTPStatus.INTERNAL_SERVER_ERROR

    @staticmethod
    def login():
        """Gestion de la connexion de l'utilisateur avec génération de token JWT."""
        try:
            data = request.get_json()
            if not data:
                return jsonify({"message": "Aucune donnée fournie"}), HTTPStatus.BAD_REQUEST

            if "email" not in data or "password" not in data:
                return jsonify({"message": "Email et mot de passe requis"}), HTTPStatus.BAD_REQUEST

            email = data["email"]
            password = data["password"]

            user = Utilisateurs.get_user_by_email(email)
            if not user:
                return jsonify({"message": "Utilisateur non trouvé"}), HTTPStatus.NOT_FOUND

            if not check_password_hash(user.get('password'), password):
                return jsonify({"message": "Mot de passe incorrect"}), HTTPStatus.UNAUTHORIZED

            payload = {
                'user_id': user.get('id'),
                'email': user.get('email'),
                "nom": user.get('firstName'),
                "prenoms": user.get('lastName'),
                'exp': datetime.datetime.now(datetime.timezone.utc) + Config.JWT_EXPIRATION_DELTA,
                'iat': datetime.datetime.now(datetime.timezone.utc)
            }
            token = jwt.encode(payload, Config.SECRET_KEY, algorithm='HS256')

            return jsonify({
                "message": "Connexion réussie",
                "token": token,
                "user": {
                    "id": user.get('id'),
                    "email": user.get('email'),
                    "firstName": user.get('firstName'),
                    "lastName": user.get('lastName'),
                    "phone": user.get('phone'),
                    "birthDate": user.get('birthDate'),
                    "nationality": user.get('nationality'),
                    "currentCountry": user.get('currentCountry'),
                    "currentCity": user.get('currentCity'),
                    "preferredProvince": user.get('preferredProvince'),
                    "currentJob": user.get('currentJob'),
                    "experience": user.get('experience'),
                    "education": user.get('education'),
                    "languages": user.get('languages'),
                    "is_verified": user.get('is_verified')
                },
            }), HTTPStatus.OK
        except Exception as e:
            return jsonify({"error": f"Erreur serveur : {str(e)}"}), HTTPStatus.INTERNAL_SERVER_ERROR

    @staticmethod
    def get_user_by_id():
        """Récupère un utilisateur par son ID."""
        token = UsersController._get_token()
        if not token:
            return jsonify({"message": "Token manquant"}), HTTPStatus.UNAUTHORIZED

        try:
            decoded_token = jwt.decode(token, Config.SECRET_KEY, algorithms=['HS256'])
            user_id = decoded_token.get('user_id')
            if not user_id:
                return jsonify({"message": "ID utilisateur manquant dans le token"}), HTTPStatus.BAD_REQUEST

            user = Utilisateurs.get_user_by_id(user_id)
            if not user:
                return jsonify({"message": "Utilisateur non trouvé"}), HTTPStatus.NOT_FOUND

            return jsonify({
                "message": "Utilisateur récupéré avec succès",
                "user": {
                    "id": user.get('id'),
                    "email": user.get('email'),
                    "firstName": user.get('firstName'),
                    "lastName": user.get('lastName'),
                    "phone": user.get('phone'),
                    "birthDate": user.get('birthDate'),
                    "nationality": user.get('nationality'),
                    "currentCountry": user.get('currentCountry'),
                    "currentCity": user.get('currentCity'),
                    "preferredProvince": user.get('preferredProvince'),
                    "currentJob": user.get('currentJob'),
                    "experience": user.get('experience'),
                    "education": user.get('education'),
                    "languages": user.get('languages'),
                    "date": user.get('created_at')
                }
            }), HTTPStatus.OK
        except jwt.ExpiredSignatureError:
            return jsonify({"message": "Token expiré"}), HTTPStatus.UNAUTHORIZED
        except jwt.InvalidTokenError:
            return jsonify({"message": "Token invalide"}), HTTPStatus.UNAUTHORIZED
        except Exception as e:
            return jsonify({"error": str(e)}), HTTPStatus.INTERNAL_SERVER_ERROR

    @staticmethod
    def get_all_users():
        """Récupère la liste de tous les utilisateurs."""
        
        try:
            users = Utilisateurs.get_all_users()
            if not users:
                return jsonify({"message": "Aucun utilisateur trouvé"}), HTTPStatus.NOT_FOUND

            return jsonify({
                "message": "Liste des utilisateurs récupérée avec succès",
                "users": users
            }), HTTPStatus.OK
        except jwt.ExpiredSignatureError:
            return jsonify({"message": "Token expiré"}), HTTPStatus.UNAUTHORIZED
        except jwt.InvalidTokenError:
            return jsonify({"message": "Token invalide"}), HTTPStatus.UNAUTHORIZED
        except Exception as e:
            return jsonify({"error": str(e)}), HTTPStatus.INTERNAL_SERVER_ERROR

    @staticmethod
    def delete_user():
        """Supprime un utilisateur."""
        token = UsersController._get_token()
        if not token:
            return jsonify({"message": "Token manquant"}), HTTPStatus.UNAUTHORIZED

        try:
            decoded_token = jwt.decode(token, Config.SECRET_KEY, algorithms=['HS256'])
            user_id = decoded_token.get('user_id')
            if not user_id:
                return jsonify({"message": "ID utilisateur manquant dans le token"}), HTTPStatus.BAD_REQUEST

            success = Utilisateurs.delete_user(user_id)
            if not success:
                return jsonify({"message": "Utilisateur non trouvé"}), HTTPStatus.NOT_FOUND

            return jsonify({'message': 'Utilisateur supprimé avec succès'}), HTTPStatus.OK
        except jwt.ExpiredSignatureError:
            return jsonify({"message": "Token expiré"}), HTTPStatus.UNAUTHORIZED
        except jwt.InvalidTokenError:
            return jsonify({"message": "Token invalide"}), HTTPStatus.UNAUTHORIZED
        except Exception as e:
            return jsonify({"error": str(e)}), HTTPStatus.INTERNAL_SERVER_ERROR

    @staticmethod
    def token_required(f):
        """Décorateur pour vérifier la validité du token JWT."""
        @wraps(f)
        def decorated(*args, **kwargs):
            token = UsersController._get_token()
            if not token:
                return jsonify({"message": "Token manquant"}), HTTPStatus.UNAUTHORIZED
            try:
                jwt.decode(token, Config.SECRET_KEY, algorithms=['HS256'])
            except jwt.ExpiredSignatureError:
                return jsonify({"message": "Token expiré"}), HTTPStatus.UNAUTHORIZED
            except jwt.InvalidTokenError:
                return jsonify({"message": "Token invalide"}), HTTPStatus.UNAUTHORIZED
            return f(*args, **kwargs)
        return decorated
    
    
    @staticmethod
    def send_reset_email(email, token):
        """Envoie un email de réinitialisation de mot de passe via AlwaysData."""
        try:
            # Configuration SMTP AlwaysData
            smtp_server = Config.smtp_server
            smtp_port = Config.smtp_port
            username = Config.username
            password = Config.password

            # Contenu de l'e-mail
            reset_url = f"{Config.FRONTEND_URL}/reset-password?token={token}&email={email}"
            subject = "Réinitialisation de votre mot de passe - Canada Recruitment"
            body = f"""Bonjour,

                <h2>Réinitialisation de mot de passe</h2>
                <p>Bonjour,</p>
                <p>Vous avez demandé à réinitialiser votre mot de passe. Cliquez sur le lien ci-dessous pour procéder :</p>
                <a href="{reset_url}" style="display: inline-block; padding: 10px 20px; color: #fff; background-color: #007bff; text-decoration: none; border-radius: 5px;">
                    Réinitialiser mon mot de passe
                </a>
                <p>Ce lien expire dans 1 heure.</p>
                <p>Si vous n'avez pas demandé cette réinitialisation, ignorez cet email.</p>
                <p>Équipe d'assistance</p>
"""

            # Création du message
            message = MIMEMultipart()
            message["From"] = username
            message["To"] = email
            message["Subject"] = subject
            message.attach(MIMEText(body, "html"))

            # Envoi de l'email
            with smtplib.SMTP(smtp_server, smtp_port) as server:
                server.starttls()
                server.login(username, password)
                server.send_message(message)

            print("✅ Email de réinitialisation envoyé via AlwaysData")
            return True
        except Exception as e:
            print(f"Échec de l'envoi de l'email de réinitialisation : {str(e)}")
            return False

    @staticmethod
    def forgot_password():
        """Gère la demande de réinitialisation de mot de passe."""
        try:
            data = request.get_json()
            email = data.get('email')

            if not email or not email.strip() or '@' not in email:
                return jsonify({"message": "Adresse email invalide"}), HTTPStatus.BAD_REQUEST

            user = Utilisateurs.get_user_by_email(email)
            if not user:
                # Retourne un succès pour éviter de révéler l'existence de l'utilisateur
                return jsonify({"message": "Si l'email existe, un lien de réinitialisation a été envoyé"}), HTTPStatus.OK

            # Générer un token unique
            token = str(uuid.uuid4())
            expires_at = datetime.datetime.now(datetime.timezone.utc) + datetime.timedelta(hours=1)

            # Créer le token
            PasswordResetToken.create(user_id=user.get('id'), token=token, expires_at=expires_at)

            # Envoyer l'email
            if not UsersController.send_reset_email(email, token):
                return jsonify({"message": "Erreur lors de l'envoi de l'email de réinitialisation"}), HTTPStatus.INTERNAL_SERVER_ERROR

            return jsonify({"message": "Un lien de réinitialisation a été envoyé"}), HTTPStatus.OK
        except Exception as e:
            return jsonify({"message": f"Erreur lors de la demande de réinitialisation : {str(e)}"}), HTTPStatus.INTERNAL_SERVER_ERROR

    @staticmethod
    def reset_password():
        """Réinitialise le mot de passe de l'utilisateur."""
        try:
            data = request.get_json()
            token = data.get('token')
            new_password = data.get('new_password')

            if not all([token, new_password]):
                return jsonify({"message": "Token et nouveau mot de passe requis"}), HTTPStatus.BAD_REQUEST

            if len(new_password) < 8:
                return jsonify({"message": "Le mot de passe doit contenir au moins 8 caractères"}), HTTPStatus.BAD_REQUEST

            # Valider le token
            reset_token = PasswordResetToken.get_by_token(token)
            print(reset_token) 
            # if not reset_token or reset_token.expires_at.replace(tzinfo=datetime.timezone.utc) < datetime.datetime.now(datetime.timezone.utc):
            #     return jsonify({"message": "Token invalide ou expiré"}), HTTPStatus.BAD_REQUEST
            print(reset_token['user_id'])
            # Mettre à jour le mot de passe
            hashed_password = new_password
            Utilisateurs.update(id=reset_token['user_id'], password=hashed_password)

            # Supprimer le token
            PasswordResetToken.delete(token)

            # Créer une notification
            Notification.create(
                user_id=reset_token['user_id'],
                message="Mot de passe réinitialisé avec succès",
                type="success"
            )

            return jsonify({"message": "Mot de passe réinitialisé avec succès"}), HTTPStatus.OK
        except Exception as e:
            return jsonify({"message": f"Erreur lors de la réinitialisation du mot de passe : {str(e)}"}), HTTPStatus.INTERNAL_SERVER_ERROR
        
    @staticmethod
    def check_documents_and_progress():
        """Vérifie si les 5 documents d'un utilisateur sont validés et progresse à l'étape suivante."""
        token = UsersController._get_token()
        if not token:
            return jsonify({"message": "Token manquant"}), HTTPStatus.UNAUTHORIZED

        try:
            decoded_token = jwt.decode(token, Config.SECRET_KEY, algorithms=['HS256'])
            user_id = decoded_token.get('user_id')
            if not user_id:
                return jsonify({"message": "ID utilisateur manquant dans le token"}), HTTPStatus.BAD_REQUEST

            # Vérifier si l'étape 3 est déjà terminée pour éviter les duplications
            existing_notification = Notification.get_by_user_and_message(
                user_id=user_id,
                message="Super ! L'étape 3 est validée. Votre document sont traité avec succès."
            )
            if existing_notification:
                return jsonify({"message": "Étape 3 déjà terminée"}), HTTPStatus.OK

            # Récupérer tous les documents de l'utilisateur
            documents = Document.get_by_user(user_id)

            # Vérifier si exactement 5 documents existent
            if len(documents) != 5:
                return jsonify({"message": f"Nombre de documents incorrect : {len(documents)} au lieu de 5"}), HTTPStatus.BAD_REQUEST

            # Vérifier si tous les documents ont le statut 'validated'
            all_validated = all(doc.get('status') == 'validated' for doc in documents)
            if not all_validated:
                return jsonify({"message": "Tous les documents ne sont pas validés"}), HTTPStatus.BAD_REQUEST

            # Créer les notifications et le paiement
            Notification.create(
                user_id=user_id,
                message="Super ! L'étape 3 est validée. Votre document sont traité avec succès.",
                type="success"
            )
            step = UserStep.get_id(user_id=user_id, step_id=3)
            if step:
                # Access the step_id from the first (and likely only) result
                step_id_from_db = step[0]['id']
                UserStep.update(id=step_id_from_db, status='completed', completion_date=datetime.datetime.now(datetime.timezone.utc))                
            else:
                print("No step found for the given user and step ID.")

            Notification.create(
                user_id=user_id,
                message="Etape 4: en cours",
                type="info"
            )
            UserStep.update(id=step_id_from_db + 1 , status='current', completion_date=datetime.datetime.now(datetime.timezone.utc))
            Payment.create(
                user_id=user_id,
                description="Frais d'évaluation",
                amount=150,
                currency="USD",
                status="pending"
            )
            Notification.create(
                user_id=user_id,
                message="Paiement en attente, Frais d'évaluation 150 USD",
                type="info"
            )

            return jsonify({"message": "Étape 3 terminée, progression à l'étape 4 initiée"}), HTTPStatus.OK
        except jwt.ExpiredSignatureError:
            return jsonify({"message": "Token expiré"}), HTTPStatus.UNAUTHORIZED
        except jwt.InvalidTokenError:
            return jsonify({"message": "Token invalide"}), HTTPStatus.UNAUTHORIZED
        except Exception as e:
            return jsonify({"error": str(e)}), HTTPStatus.INTERNAL_SERVER_ERROR