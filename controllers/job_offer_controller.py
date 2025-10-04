from flask import Blueprint, request, jsonify
import jwt
from functools import wraps
from http import HTTPStatus
from models.job_offer_model import JobOffer
from config import Config

class JobOfferController:
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
            token = JobOfferController._get_token()
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
    def create_job_offer():
        """Crée une nouvelle offre d'emploi."""
        try:
            data = request.get_json()
            required_fields = ['title', 'company', 'location']
            if not all(field in data for field in required_fields):
                return jsonify({"message": "Champs obligatoires manquants : title, company, location"}), HTTPStatus.BAD_REQUEST

            title = data.get('title')
            company = data.get('company')
            location = data.get('location')
            type = data.get('type')
            salary = data.get('salary')
            category = data.get('category')
            featured = data.get('featured')
            description = data.get('description')
            requirements = data.get('requirements')
            
            job_offer_id = JobOffer.create(title, company, location, type, salary, category, featured, description, requirements)
            return jsonify({
                'message': 'Offre d\'emploi créée avec succès',
                'job_offer_id': job_offer_id
            }), HTTPStatus.CREATED
        except Exception as e:
            return jsonify({"error": str(e)}), HTTPStatus.INTERNAL_SERVER_ERROR

    @staticmethod
    @token_required
    def update_job_offer():
        """Met à jour une offre d'emploi existante."""
        try:
            data = request.get_json()
            if 'id' not in data:
                return jsonify({"message": "ID de l'offre d'emploi requis"}), HTTPStatus.BAD_REQUEST

            id = data.get('id')
            title = data.get('title')
            company = data.get('company')
            location = data.get('location')
            type = data.get('type')
            salary = data.get('salary')
            category = data.get('category')
            featured = data.get('featured')
            description = data.get('description')
            requirements = data.get('requirements')

            # Vérification du token pour s'assurer que seul un administrateur peut modifier une offre
            token = JobOfferController._get_token()
            decoded_token = jwt.decode(token, Config.SECRET_KEY, algorithms=['HS256'])
            if decoded_token.get('role') != 'admin':
                return jsonify({"message": "Accès refusé. Seuls les administrateurs peuvent modifier des offres d'emploi."}), HTTPStatus.FORBIDDEN

            job_offer = JobOffer.get_by_id(id)
            if not job_offer:
                return jsonify({"message": "Offre d'emploi non trouvée"}), HTTPStatus.NOT_FOUND

            success = JobOffer.update(id, title, company, location, type, salary, category, featured, description, requirements)
            if not success:
                return jsonify({"message": "Offre d'emploi non trouvée ou aucun changement effectué"}), HTTPStatus.NOT_FOUND

            return jsonify({'message': 'Offre d\'emploi mise à jour avec succès'}), HTTPStatus.OK
        except Exception as e:
            return jsonify({"error": str(e)}), HTTPStatus.INTERNAL_SERVER_ERROR

    @staticmethod
    @token_required
    def get_job_offer_by_id():
        """Récupère une offre d'emploi par son ID."""
        try:
            data = request.get_json()
            if 'id' not in data:
                return jsonify({"message": "ID de l'offre d'emploi requis"}), HTTPStatus.BAD_REQUEST

            id = data.get('id')

            job_offer = JobOffer.get_by_id(id)
            if not job_offer:
                return jsonify({"message": "Offre d'emploi non trouvée"}), HTTPStatus.NOT_FOUND

            return jsonify({
                "message": "Offre d'emploi récupérée avec succès",
                "job_offer": job_offer
            }), HTTPStatus.OK
        except Exception as e:
            return jsonify({"error": str(e)}), HTTPStatus.INTERNAL_SERVER_ERROR

    @staticmethod
    def get_all_job_offers():
        """Récupère toutes les offres d'emploi."""
        try:
            job_offers = JobOffer.get_all()
            if not job_offers:
                return jsonify({"message": "Aucune offre d'emploi trouvée"}), HTTPStatus.NOT_FOUND

            return jsonify({
                "message": "Offres d'emploi récupérées avec succès",
                "job_offers": job_offers
            }), HTTPStatus.OK
        except Exception as e:
            return jsonify({"error": str(e)}), HTTPStatus.INTERNAL_SERVER_ERROR

    @staticmethod
    def delete_job_offer():
        """Supprime une offre d'emploi."""
        try:
            data = request.get_json()
            if 'id' not in data:
                return jsonify({"message": "ID de l'offre d'emploi requis"}), HTTPStatus.BAD_REQUEST

            id = data.get('id')
            
            job_offer = JobOffer.get_by_id(id)
            if not job_offer:
                return jsonify({"message": "Offre d'emploi non trouvée"}), HTTPStatus.NOT_FOUND

            success = JobOffer.delete(id)
            if not success:
                return jsonify({"message": "Offre d'emploi non trouvée"}), HTTPStatus.NOT_FOUND

            return jsonify({'message': 'Offre d\'emploi supprimée avec succès'}), HTTPStatus.OK
        except Exception as e:
            return jsonify({"error": str(e)}), HTTPStatus.INTERNAL_SERVER_ERROR