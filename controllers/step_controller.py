from flask import Blueprint, request, jsonify
import jwt
from functools import wraps
from http import HTTPStatus
from models.step_model import Step
from config import Config

class StepController:
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
            token = StepController._get_token()
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
    def create_step():
        """Crée une nouvelle étape."""
        try:
            data = request.get_json()
            required_fields = ['step_name', 'step_order']
            if not all(field in data for field in required_fields):
                return jsonify({"message": "Champs obligatoires manquants : step_name, step_order"}), HTTPStatus.BAD_REQUEST

            step_name = data.get('step_name')
            step_order = data.get('step_order')

            # Vérification du token pour s'assurer que seul un administrateur peut créer une étape
            token = StepController._get_token()
            decoded_token = jwt.decode(token, Config.SECRET_KEY, algorithms=['HS256'])
            if decoded_token.get('role') != 'admin':
                return jsonify({"message": "Accès refusé. Seuls les administrateurs peuvent créer des étapes."}), HTTPStatus.FORBIDDEN

            step_id = Step.create(step_name, step_order)
            return jsonify({
                'message': 'Étape créée avec succès',
                'step_id': step_id
            }), HTTPStatus.CREATED
        except Exception as e:
            return jsonify({"error": str(e)}), HTTPStatus.INTERNAL_SERVER_ERROR

    @staticmethod
    @token_required
    def update_step():
        """Met à jour une étape existante."""
        try:
            data = request.get_json()
            if 'id' not in data:
                return jsonify({"message": "ID de l'étape requis"}), HTTPStatus.BAD_REQUEST

            id = data.get('id')
            step_name = data.get('step_name')
            step_order = data.get('step_order')

            # Vérification du token pour s'assurer que seul un administrateur peut modifier une étape
            token = StepController._get_token()
            decoded_token = jwt.decode(token, Config.SECRET_KEY, algorithms=['HS256'])
            if decoded_token.get('role') != 'admin':
                return jsonify({"message": "Accès refusé. Seuls les administrateurs peuvent modifier des étapes."}), HTTPStatus.FORBIDDEN

            step = Step.get_by_id(id)
            if not step:
                return jsonify({"message": "Étape non trouvée"}), HTTPStatus.NOT_FOUND

            success = Step.update(id, step_name, step_order)
            if not success:
                return jsonify({"message": "Étape non trouvée ou aucun changement effectué"}), HTTPStatus.NOT_FOUND

            return jsonify({'message': 'Étape mise à jour avec succès'}), HTTPStatus.OK
        except Exception as e:
            return jsonify({"error": str(e)}), HTTPStatus.INTERNAL_SERVER_ERROR

    @staticmethod
    @token_required
    def get_step_by_id():
        """Récupère une étape par son ID."""
        try:
            data = request.get_json()
            if 'id' not in data:
                return jsonify({"message": "ID de l'étape requis"}), HTTPStatus.BAD_REQUEST

            id = data.get('id')

            step = Step.get_by_id(id)
            if not step:
                return jsonify({"message": "Étape non trouvée"}), HTTPStatus.NOT_FOUND

            return jsonify({
                "message": "Étape récupérée avec succès",
                "step": step
            }), HTTPStatus.OK
        except Exception as e:
            return jsonify({"error": str(e)}), HTTPStatus.INTERNAL_SERVER_ERROR

    @staticmethod
    @token_required
    def get_all_steps():
        """Récupère toutes les étapes."""
        try:
            steps = Step.get_all()
            if not steps:
                return jsonify({"message": "Aucune étape trouvée"}), HTTPStatus.NOT_FOUND

            return jsonify({
                "message": "Étapes récupérées avec succès",
                "steps": steps
            }), HTTPStatus.OK
        except Exception as e:
            return jsonify({"error": str(e)}), HTTPStatus.INTERNAL_SERVER_ERROR

    @staticmethod
    @token_required
    def delete_step():
        """Supprime une étape."""
        try:
            data = request.get_json()
            if 'id' not in data:
                return jsonify({"message": "ID de l'étape requis"}), HTTPStatus.BAD_REQUEST

            id = data.get('id')

            # Vérification du token pour s'assurer que seul un administrateur peut supprimer une étape
            token = StepController._get_token()
            decoded_token = jwt.decode(token, Config.SECRET_KEY, algorithms=['HS256'])
            if decoded_token.get('role') != 'admin':
                return jsonify({"message": "Accès refusé. Seuls les administrateurs peuvent supprimer des étapes."}), HTTPStatus.FORBIDDEN

            step = Step.get_by_id(id)
            if not step:
                return jsonify({"message": "Étape non trouvée"}), HTTPStatus.NOT_FOUND

            success = Step.delete(id)
            if not success:
                return jsonify({"message": "Étape non trouvée"}), HTTPStatus.NOT_FOUND

            return jsonify({'message': 'Étape supprimée avec succès'}), HTTPStatus.OK
        except Exception as e:
            return jsonify({"error": str(e)}), HTTPStatus.INTERNAL_SERVER_ERROR