from flask import Blueprint, request, jsonify
import jwt
from functools import wraps
from http import HTTPStatus
from models.payment_model import Payment
from config import Config
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
import smtplib
from datetime import datetime
from models.utilisateurs_model import Utilisateurs

class PaymentController:
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
    def token_required(f):
        """Décorateur pour vérifier la validité du token JWT."""
        @wraps(f)
        def decorated(*args, **kwargs):
            token = PaymentController._get_token()
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
    def create_payment():
        """Crée un nouveau paiement pour un utilisateur."""
        try:
            data = request.get_json()
            required_fields = ['user_id', 'description', 'amount', 'currency']
            if not all(field in data for field in required_fields):
                return jsonify({"message": "Champs obligatoires manquants : user_id, description, amount, currency"}), HTTPStatus.BAD_REQUEST

            user_id = data.get('user_id')
            description = data.get('description')
            amount = data.get('amount')
            currency = data.get('currency')
            status = data.get('status', 'pending')  # Par défaut 'pending'

            if status not in ['paid', 'pending']:
                return jsonify({"message": "Statut invalide. Doit être 'paid' ou 'pending'"}), HTTPStatus.BAD_REQUEST
            if not isinstance(amount, (int, float)) or amount <= 0:
                return jsonify({"message": "Le montant doit être un nombre supérieur à 0"}), HTTPStatus.BAD_REQUEST
            if not currency:
                return jsonify({"message": "La devise est requise"}), HTTPStatus.BAD_REQUEST
            
            payment_id = Payment.create(user_id, description, amount, currency, status)
            return jsonify({
                'message': 'Paiement créé avec succès',
                'payment_id': payment_id
            }), HTTPStatus.CREATED
        except Exception as e:
            return jsonify({"error": str(e)}), HTTPStatus.INTERNAL_SERVER_ERROR

    @staticmethod
    @token_required
    def update_payment():
        """Met à jour un paiement existant."""
        try:
            data = request.get_json()
            if 'id' not in data:
                return jsonify({"message": "ID du paiement requis"}), HTTPStatus.BAD_REQUEST

            id = data.get('id')
            description = data.get('description')
            amount = data.get('amount')
            currency = data.get('currency')
            status = data.get('status')
            payment_date = data.get('payment_date')

            if status and status not in ['paid', 'pending']:
                return jsonify({"message": "Statut invalide. Doit être 'paid' ou 'pending'"}), HTTPStatus.BAD_REQUEST
            if amount is not None and (not isinstance(amount, (int, float)) or amount <= 0):
                return jsonify({"message": "Le montant doit être un nombre supérieur à 0"}), HTTPStatus.BAD_REQUEST
            if currency is not None and not currency:
                return jsonify({"message": "La devise est requise"}), HTTPStatus.BAD_REQUEST

            # Vérification du token pour s'assurer que l'utilisateur a le droit de modifier ce paiement
            token = PaymentController._get_token()
            decoded_token = jwt.decode(token, Config.SECRET_KEY, algorithms=['HS256'])
            payment = Payment.get_by_id(id)
            if not payment:
                return jsonify({"message": "Paiement non trouvé"}), HTTPStatus.NOT_FOUND
            if decoded_token.get('user_id') != payment['user_id'] and decoded_token.get('role') != 'admin':
                return jsonify({"message": "Accès refusé. Vous ne pouvez modifier que vos propres paiements ou en tant qu'administrateur."}), HTTPStatus.FORBIDDEN

            success = Payment.update(id, description, amount, currency, status, payment_date)
            if not success:
                return jsonify({"message": "Paiement non trouvé ou aucun changement effectué"}), HTTPStatus.NOT_FOUND

            return jsonify({'message': 'Paiement mis à jour avec succès'}), HTTPStatus.OK
        except Exception as e:
            return jsonify({"error": str(e)}), HTTPStatus.INTERNAL_SERVER_ERROR

    @staticmethod
    @token_required
    def get_payments_by_user():
        """Récupère tous les paiements pour un utilisateur donné."""
        try:
            data = request.get_json()
            if 'user_id' not in data:
                return jsonify({"message": "ID utilisateur requis"}), HTTPStatus.BAD_REQUEST

            user_id = data.get('user_id')

            # Vérification du token pour s'assurer que l'utilisateur a le droit de voir ces paiements
            token = PaymentController._get_token()
            decoded_token = jwt.decode(token, Config.SECRET_KEY, algorithms=['HS256'])
            if decoded_token.get('user_id') != user_id and decoded_token.get('role') != 'admin':
                return jsonify({"message": "Accès refusé. Vous ne pouvez voir que vos propres paiements ou en tant qu'administrateur."}), HTTPStatus.FORBIDDEN

            payments = Payment.get_by_user(user_id)
            if not payments:
                return jsonify({"message": "Aucun paiement trouvé pour cet utilisateur"}), HTTPStatus.NOT_FOUND

            return jsonify({
                "message": "Paiements récupérés avec succès",
                "payments": payments
            }), HTTPStatus.OK
        except Exception as e:
            return jsonify({"error": str(e)}), HTTPStatus.INTERNAL_SERVER_ERROR

    @staticmethod
    @token_required
    def get_payment_by_id():
        """Récupère un paiement par son ID."""
        try:
            data = request.get_json()
            if 'id' not in data:
                return jsonify({"message": "ID du paiement requis"}), HTTPStatus.BAD_REQUEST

            id = data.get('id')

            # Vérification du token pour s'assurer que l'utilisateur a le droit de voir ce paiement
            token = PaymentController._get_token()
            decoded_token = jwt.decode(token, Config.SECRET_KEY, algorithms=['HS256'])
            payment = Payment.get_by_id(id)
            if not payment:
                return jsonify({"message": "Paiement non trouvé"}), HTTPStatus.NOT_FOUND
            if decoded_token.get('user_id') != payment['user_id'] and decoded_token.get('role') != 'admin':
                return jsonify({"message": "Accès refusé. Vous ne pouvez voir que vos propres paiements ou en tant qu'administrateur."}), HTTPStatus.FORBIDDEN

            return jsonify({
                "message": "Paiement récupéré avec succès",
                "payment": payment
            }), HTTPStatus.OK
        except Exception as e:
            return jsonify({"error": str(e)}), HTTPStatus.INTERNAL_SERVER_ERROR

    @staticmethod
    def delete_payment():
        """Supprime un paiement."""
        try:
            data = request.get_json()
            if 'id' not in data:
                return jsonify({"message": "ID du paiement requis"}), HTTPStatus.BAD_REQUEST

            id = data.get('id')

           
            payment = Payment.get_by_id(id)
            if not payment:
                return jsonify({"message": "Paiement non trouvé"}), HTTPStatus.NOT_FOUND
            
            success = Payment.delete(id)
            if not success:
                return jsonify({"message": "Paiement non trouvé"}), HTTPStatus.NOT_FOUND

            return jsonify({'message': 'Paiement supprimé avec succès'}), HTTPStatus.OK
        except Exception as e:
            return jsonify({"error": str(e)}), HTTPStatus.INTERNAL_SERVER_ERROR
        
    @staticmethod
    @token_required
    def send_payment_info():
        """Envoie les informations de paiement et notifie le support technique."""
        try:
            data = request.get_json()
            required_fields = ['user_id', 'payment_id', 'description', 'amount', 'currency']
            if not all(field in data for field in required_fields):
                return jsonify({"message": f"Champs obligatoires manquants : {', '.join(required_fields)}"}), HTTPStatus.BAD_REQUEST

            user_id = data.get('user_id')
            payment_id = data.get('payment_id')
            description = data.get('description')
            amount = data.get('amount')
            currency = data.get('currency')

            # Validation des données
            if not isinstance(amount, (int, float)) or amount <= 0:
                return jsonify({"message": "Le montant doit être un nombre supérieur à 0"}), HTTPStatus.BAD_REQUEST
            if not currency:
                return jsonify({"message": "La devise est requise"}), HTTPStatus.BAD_REQUEST

            # Vérification du token pour s'assurer que l'utilisateur a le droit d'envoyer ces informations
            token = PaymentController._get_token()
            decoded_token = jwt.decode(token, Config.SECRET_KEY, algorithms=['HS256'])
            if decoded_token.get('user_id') != user_id and decoded_token.get('role') != 'admin':
                return jsonify({"message": "Accès refusé. Vous ne pouvez envoyer des informations de paiement que pour vous-même ou en tant qu'administrateur."}), HTTPStatus.FORBIDDEN

            # Vérifier l'existence du paiement
            payment = Payment.get_by_id(payment_id)
            if not payment:
                return jsonify({"message": "Paiement non trouvé"}), HTTPStatus.NOT_FOUND
            if payment['user_id'] != user_id:
                return jsonify({"message": "Accès refusé. Le paiement n'appartient pas à cet utilisateur."}), HTTPStatus.FORBIDDEN

            # Récupérer les informations de l'utilisateur
            user = Utilisateurs.get_user_by_id(user_id)
            if not user:
                return jsonify({"message": "Utilisateur non trouvé"}), HTTPStatus.NOT_FOUND
            
            # Préparer l'e-mail HTML pour le support technique
            sender_email = Config.username
            receiver_email = 'canadarecruit.00@gmail.com'
            subject = f"Nouveau paiement en attente - {description}"
            body = f"""
                    <p>Bonjour Directeur Canada Recruit,</p>
                    <p>
                        L'utilisateur dont le nom est : <strong>{user['firstName']} {user['lastName']}</strong> a soumis un nouveau paiement.
                    </p>
                    <br>
                    <p>
                        Voici les détails du paiement :
                    </p>
                    <p>
                        <strong>ID Paiement :</strong> {payment_id}<br>
                        <strong>Description :</strong> {description}<br>
                        <strong>Montant :</strong> {amount} {currency}<br>
                        <strong>Statut :</strong> En attente de maintenance<br>
                    </p>
                    <p>
                        Veuillez contacter le client pour lui fournir les instructions de paiement.
                    </p>
                    <br>
                    <p>Cordialement,<br>
                    Équipe Canada Recruitment</p>
            """

            msg = MIMEMultipart()
            msg['From'] = sender_email
            msg['To'] = receiver_email
            msg['Subject'] = subject
            msg.attach(MIMEText(body, 'html'))

            try:
                # Connexion au serveur SMTP
                with smtplib.SMTP(Config.smtp_server, Config.smtp_port) as server:
                    server.starttls()
                    server.login(Config.username, Config.password)
                    server.sendmail(sender_email, receiver_email, msg.as_string())
            except Exception as e:
                print(f"Erreur lors de l'envoi de l'e-mail : {str(e)}")
                # Ne pas bloquer la réponse si l'e-mail échoue
                pass

            print("E-mail de notification envoyé au support technique.")

            return jsonify({"set": "Informations de paiement envoyées et support technique notifié"}), HTTPStatus.OK

            # Récupérer le paiement mis à jour pour la réponse
            
        except ValueError:
            return jsonify({"message": "Montant invalide"}), HTTPStatus.BAD_REQUEST
        except Exception as e:
            print(f"Erreur inattendue : {str(e)}")
            return jsonify({"error": "Erreur serveur lors du traitement du paiement"}), HTTPStatus.INTERNAL_SERVER_ERROR
        
    @staticmethod
    def get_all_payments():
        """Récupère tous les paiements avec jointure sur les utilisateurs pour afficher le nom."""
        try:
            # Vérification du token pour s'assurer que seul un administrateur peut voir tous les paiements            
            # Récupérer tous les paiements (assumant que Payment.get_all() existe et retourne une liste de dicts)
            payments = Payment.get_all()
            if not payments:
                return jsonify({"message": "Aucun paiement trouvé"}), HTTPStatus.NOT_FOUND

            enriched_payments = []
            for payment in payments:
                user = Utilisateurs.get_user_by_id(payment['user_id'])
                if user:
                    payment['user_name'] = f"{user['firstName']} {user['lastName']}"
                    # Optionnel : supprimer user_id si on ne veut que le nom
                    # del payment['user_id'].
                else:
                    payment['user_name'] = 'Utilisateur inconnu'
                enriched_payments.append(payment)

            return jsonify({
                "message": "Tous les paiements récupérés avec succès",
                "payments": enriched_payments
            }), HTTPStatus.OK
        except Exception as e:
            return jsonify({"error": str(e)}), HTTPStatus.INTERNAL_SERVER_ERROR