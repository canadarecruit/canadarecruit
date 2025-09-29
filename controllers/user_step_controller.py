from flask import Blueprint, request, jsonify
import jwt
from functools import wraps
from http import HTTPStatus
from models.user_step_model import UserStep
from config import Config

class UserStepController:
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
            token = UserStepController._get_token()
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
    def create_user_step():
        """Crée une nouvelle entrée pour un utilisateur et une étape."""
        try:
            data = request.get_json()
            required_fields = ['user_id', 'steps']
            if not all(field in data for field in required_fields):
                return jsonify({"message": "Champs obligatoires manquants : user_id, step_id"}), HTTPStatus.BAD_REQUEST

            user_id = data.get('user_id')
            steps = data.get('steps')
            status = data.get('status', 'pending')  # Par défaut 'pending'

            if status not in ['completed', 'current', 'pending']:
                return jsonify({"message": "Statut invalide. Doit être 'completed', 'current' ou 'pending'"}), HTTPStatus.BAD_REQUEST

            if not user_id or not steps:
                return jsonify({"message": "user_id et steps sont requis"}), HTTPStatus.BAD_REQUEST

            # Validate steps format
            required_fields = ['id', 'name', 'status', 'date']
            for step in steps:
                if not all(field in step for field in required_fields):
                    return jsonify({"message": "Chaque étape doit contenir id, name, status, et date"}), HTTPStatus.BAD_REQUEST

            # Insert steps into the database
            for step in steps:
                UserStep.create(
                    user_id=user_id,
                    step_id=step['id'],
                    status=step['status'],
                    completion_date	=step['date'] or None
                )
            return jsonify({
                'message': 'Entrée utilisateur-étape créée avec succès',
            }), HTTPStatus.CREATED
        except Exception as e:
            return jsonify({"error": str(e)}), HTTPStatus.INTERNAL_SERVER_ERROR

    @staticmethod
    @token_required
    def update_user_step():
        """Met à jour une entrée utilisateur-étape."""
        try:
            data = request.get_json()
            if 'id' not in data:
                return jsonify({"message": "ID de l'entrée requis"}), HTTPStatus.BAD_REQUEST

            id = data.get('id')
            status = data.get('status')
            completion_date = data.get('completion_date')

            if status and status not in ['completed', 'current', 'pending']:
                return jsonify({"message": "Statut invalide. Doit être 'completed', 'current' ou 'pending'"}), HTTPStatus.BAD_REQUEST

            # Vérification du token pour s'assurer que l'utilisateur a le droit de modifier cette entrée
            token = UserStepController._get_token()
            decoded_token = jwt.decode(token, Config.SECRET_KEY, algorithms=['HS256'])
            user_step = UserStep.get_by_user(data.get('user_id'))[0] if UserStep.get_by_user(data.get('user_id')) else None
            if not user_step:
                return jsonify({"message": "Entrée non trouvée"}), HTTPStatus.NOT_FOUND
            if decoded_token.get('user_id') != user_step['user_id'] and decoded_token.get('role') != 'admin':
                return jsonify({"message": "Accès refusé. Vous ne pouvez modifier que vos propres entrées ou en tant qu'administrateur."}), HTTPStatus.FORBIDDEN

            success = UserStep.update(id, status, completion_date)
            if not success:
                return jsonify({"message": "Entrée non trouvée ou aucun changement effectué"}), HTTPStatus.NOT_FOUND

            return jsonify({'message': 'Entrée utilisateur-étape mise à jour avec succès'}), HTTPStatus.OK
        except Exception as e:
            return jsonify({"error": str(e)}), HTTPStatus.INTERNAL_SERVER_ERROR

    @staticmethod
    @token_required
    def get_user_steps_by_user():
        """Récupère toutes les entrées pour un utilisateur donné."""
        try:

            # Vérification du token pour s'assurer que l'utilisateur a le droit de voir ces entrées
            token = UserStepController._get_token()
            decoded_token = jwt.decode(token, Config.SECRET_KEY, algorithms=['HS256'])
            user_id = decoded_token.get('user_id')

            user_steps = UserStep.get_by_user(user_id)
            if not user_steps:
                return jsonify({"message": "Aucune entrée trouvée pour cet utilisateur"}), HTTPStatus.NOT_FOUND

            return jsonify({
                "message": "Entrées récupérées avec succès",
                "user_steps": user_steps
            }), HTTPStatus.OK
        except Exception as e:
            return jsonify({"error": str(e)}), HTTPStatus.INTERNAL_SERVER_ERROR

    @staticmethod
    @token_required
    def get_user_steps_by_step():
        """Récupère toutes les entrées pour une étape donnée."""
        try:
            data = request.get_json()
            if 'step_id' not in data:
                return jsonify({"message": "ID de l'étape requis"}), HTTPStatus.BAD_REQUEST

            step_id = data.get('step_id')

            # Seuls les administrateurs peuvent voir les entrées par étape
            token = UserStepController._get_token()
            decoded_token = jwt.decode(token, Config.SECRET_KEY, algorithms=['HS256'])
            if decoded_token.get('role') != 'admin':
                return jsonify({"message": "Accès refusé. Seuls les administrateurs peuvent voir les entrées par étape."}), HTTPStatus.FORBIDDEN

            user_steps = UserStep.get_by_step(step_id)
            if not user_steps:
                return jsonify({"message": "Aucune entrée trouvée pour cette étape"}), HTTPStatus.NOT_FOUND

            return jsonify({
                "message": "Entrées récupérées avec succès",
                "user_steps": user_steps
            }), HTTPStatus.OK
        except Exception as e:
            return jsonify({"error": str(e)}), HTTPStatus.INTERNAL_SERVER_ERROR

    @staticmethod
    @token_required
    def delete_user_step():
        """Supprime une entrée utilisateur-étape."""
        try:
            data = request.get_json()
            if 'id' not in data:
                return jsonify({"message": "ID de l'entrée requis"}), HTTPStatus.BAD_REQUEST

            id = data.get('id')

            # Vérification du token pour s'assurer que l'utilisateur a le droit de supprimer cette entrée
            token = UserStepController._get_token()
            decoded_token = jwt.decode(token, Config.SECRET_KEY, algorithms=['HS256'])
            user_step = UserStep.get_by_user(data.get('user_id'))[0] if UserStep.get_by_user(data.get('user_id')) else None
            if not user_step:
                return jsonify({"message": "Entrée non trouvée"}), HTTPStatus.NOT_FOUND
            if decoded_token.get('user_id') != user_step['user_id'] and decoded_token.get('role') != 'admin':
                return jsonify({"message": "Accès refusé. Vous ne pouvez supprimer que vos propres entrées ou en tant qu'administrateur."}), HTTPStatus.FORBIDDEN

            success = UserStep.delete(id)
            if not success:
                return jsonify({"message": "Entrée non trouvée"}), HTTPStatus.NOT_FOUND

            return jsonify({'message': 'Entrée utilisateur-étape supprimée avec succès'}), HTTPStatus.OK
        except Exception as e:
            return jsonify({"error": str(e)}), HTTPStatus.INTERNAL_SERVER_ERROR