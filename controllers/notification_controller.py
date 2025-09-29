from flask import Blueprint, request, jsonify
import jwt
from functools import wraps
from http import HTTPStatus
from models.notification_model import Notification
from config import Config

class NotificationController:
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
            token = NotificationController._get_token()
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
    @token_required
    def create_notification():
        """Crée une nouvelle notification pour un utilisateur."""
        try:
            data = request.get_json()
            required_fields = ['user_id', 'message']
            if not all(field in data for field in required_fields):
                return jsonify({"message": "Champs obligatoires manquants : user_id, message"}), HTTPStatus.BAD_REQUEST

            user_id = data.get('user_id')
            message = data.get('message')
            type = data.get('type', 'info')  # Par défaut 'info'

            if type not in ['warning', 'info', 'success']:
                return jsonify({"message": "Type invalide. Doit être 'warning', 'info' ou 'success'"}), HTTPStatus.BAD_REQUEST

            # Vérification du token pour s'assurer que l'utilisateur a le droit de créer cette notification
            token = NotificationController._get_token()
            decoded_token = jwt.decode(token, Config.SECRET_KEY, algorithms=['HS256'])
            if decoded_token.get('user_id') != user_id and decoded_token.get('role') != 'admin':
                return jsonify({"message": "Accès refusé. Vous ne pouvez créer une notification que pour vous-même ou en tant qu'administrateur."}), HTTPStatus.FORBIDDEN

            notification_id = Notification.create(user_id, message, type)
            return jsonify({
                'message': 'Notification créée avec succès',
                'notification_id': notification_id
            }), HTTPStatus.CREATED
        except Exception as e:
            return jsonify({"error": str(e)}), HTTPStatus.INTERNAL_SERVER_ERROR

    @staticmethod
    @token_required
    def update_notification():
        """Met à jour une notification existante."""
        try:
            data = request.get_json()
            if 'id' not in data:
                return jsonify({"message": "ID de la notification requis"}), HTTPStatus.BAD_REQUEST

            id = data.get('id')
            message = data.get('message')
            type = data.get('type')
            is_read = data.get('is_read')

            if type and type not in ['warning', 'info', 'success']:
                return jsonify({"message": "Type invalide. Doit être 'warning', 'info', 'success'"}), HTTPStatus.BAD_REQUEST

            # Vérification du token pour s'assurer que l'utilisateur a le droit de modifier cette notification
            token = NotificationController._get_token()
            decoded_token = jwt.decode(token, Config.SECRET_KEY, algorithms=['HS256'])
            notifications = Notification.get_by_user(data.get('user_id')) if data.get('user_id') else []
            notification = next((n for n in notifications if n['id'] == id), None)
            if not notification:
                return jsonify({"message": "Notification non trouvée"}), HTTPStatus.NOT_FOUND

            success = Notification.update(id, message, type, is_read)
            if not success:
                return jsonify({"message": "Notification non trouvée ou aucun changement effectué"}), HTTPStatus.NOT_FOUND

            return jsonify({'message': 'Notification mise à jour avec succès'}), HTTPStatus.OK
        except Exception as e:
            return jsonify({"error": str(e)}), HTTPStatus.INTERNAL_SERVER_ERROR

    @staticmethod
    @token_required
    def get_notifications_by_user():
        """Récupère toutes les notifications pour un utilisateur donné."""
        try:
            data = request.get_json()
            if 'user_id' not in data:
                return jsonify({"message": "ID utilisateur requis"}), HTTPStatus.BAD_REQUEST

            user_id = data.get('user_id')

            # Vérification du token pour s'assurer que l'utilisateur a le droit de voir ces notifications
            token = NotificationController._get_token()
            decoded_token = jwt.decode(token, Config.SECRET_KEY, algorithms=['HS256'])
            if decoded_token.get('user_id') != user_id and decoded_token.get('role') != 'admin':
                return jsonify({"message": "Accès refusé. Vous ne pouvez voir que vos propres notifications ou en tant qu'administrateur."}), HTTPStatus.FORBIDDEN

            notifications = Notification.get_by_user(user_id)
            if not notifications:
                return jsonify({"message": "Aucune notification trouvée pour cet utilisateur"}), HTTPStatus.NOT_FOUND

            return jsonify({
                "message": "Notifications récupérées avec succès",
                "notifications": notifications
            }), HTTPStatus.OK
        except Exception as e:
            return jsonify({"error": str(e)}), HTTPStatus.INTERNAL_SERVER_ERROR

    @staticmethod
    @token_required
    def mark_notification_as_read():
        """Marque une notification comme lue."""
        try:
            data = request.get_json()
            if 'id' not in data:
                return jsonify({"message": "ID de la notification requis"}), HTTPStatus.BAD_REQUEST

            id = data.get('id')

            # Vérification du token pour s'assurer que l'utilisateur a le droit de marquer cette notification comme lue
            token = NotificationController._get_token()
            decoded_token = jwt.decode(token, Config.SECRET_KEY, algorithms=['HS256'])
            notifications = Notification.get_by_user(data.get('user_id')) if data.get('user_id') else []
            notification = next((n for n in notifications if n['id'] == id), None)
            if not notification:
                return jsonify({"message": "Notification non trouvée"}), HTTPStatus.NOT_FOUND
            if decoded_token.get('user_id') != notification['user_id'] and decoded_token.get('role') != 'admin':
                return jsonify({"message": "Accès refusé. Vous ne pouvez marquer comme lue que vos propres notifications ou en tant qu'administrateur."}), HTTPStatus.FORBIDDEN

            success = Notification.mark_as_read(id)
            if not success:
                return jsonify({"message": "Notification non trouvée"}), HTTPStatus.NOT_FOUND

            return jsonify({'message': 'Notification marquée comme lue avec succès'}), HTTPStatus.OK
        except Exception as e:
            return jsonify({"error": str(e)}), HTTPStatus.INTERNAL_SERVER_ERROR

    @staticmethod
    @token_required
    def delete_notification():
        """Supprime une notification."""
        try:
            data = request.get_json()
            if 'id' not in data:
                return jsonify({"message": "ID de la notification requis"}), HTTPStatus.BAD_REQUEST

            id = data.get('id')

            # Vérification du token pour s'assurer que l'utilisateur a le droit de supprimer cette notification
            token = NotificationController._get_token()
            decoded_token = jwt.decode(token, Config.SECRET_KEY, algorithms=['HS256'])
            notifications = Notification.get_by_user(data.get('user_id')) if data.get('user_id') else []
            notification = next((n for n in notifications if n['id'] == id), None)
            if not notification:
                return jsonify({"message": "Notification non trouvée"}), HTTPStatus.NOT_FOUND
            if decoded_token.get('user_id') != notification['user_id'] and decoded_token.get('role') != 'admin':
                return jsonify({"message": "Accès refusé. Vous ne pouvez supprimer que vos propres notifications ou en tant qu'administrateur."}), HTTPStatus.FORBIDDEN

            success = Notification.delete(id)
            if not success:
                return jsonify({"message": "Notification non trouvée"}), HTTPStatus.NOT_FOUND

            return jsonify({'message': 'Notification supprimée avec succès'}), HTTPStatus.OK
        except Exception as e:
            return jsonify({"error": str(e)}), HTTPStatus.INTERNAL_SERVER_ERROR