from flask import Blueprint, request, jsonify
from functools import wraps
import jwt
from http import HTTPStatus
from config import Config
from controllers.utilisateurs_controller import UsersController
from controllers.document_controller import DocumentController
from controllers.job_offer_controller import JobOfferController
from controllers.notification_controller import NotificationController
from controllers.payment_controller import PaymentController
from controllers.step_controller import StepController
from controllers.user_step_controller import UserStepController

auth_routes = Blueprint("auth_routes", __name__)

# Routes pour UsersController
@auth_routes.route('/hasher_password', methods=['POST'])
def hasher_password_route():
    return UsersController.hasher_mot_de_passe_route()

@auth_routes.route('/users', methods=['POST'])
def create_user_route():
    return UsersController.create_user()

@auth_routes.route('/users', methods=['PUT'])
@UsersController.token_required
def update_user_route():
    return UsersController.update_user()

@auth_routes.route('/login', methods=['POST'])
def login_route():
    return UsersController.login()

@auth_routes.route('/users_by_id', methods=['GET'])
@UsersController.token_required
def get_user_by_id_route():
    return UsersController.get_user_by_id()

@auth_routes.route('/users', methods=['GET'])
def get_all_users_route():
    return UsersController.get_all_users()

@auth_routes.route('/users', methods=['DELETE'])
@UsersController.token_required
def delete_user_route():
    return UsersController.delete_user()

@auth_routes.route('/forgot-password', methods=['POST'])
def forgot_password_route():
    return UsersController.forgot_password()

@auth_routes.route('/reset-password', methods=['POST'])
def reset_password_route():
    return UsersController.reset_password()

@auth_routes.route('/check-documents', methods=['POST'])
@UsersController.token_required
def check_documents_and_progress_route():
    return UsersController.check_documents_and_progress()

# Routes pour DocumentController
@auth_routes.route('/documents', methods=['POST'])
@DocumentController.token_required
def create_document_route():
    return DocumentController.create_document()

@auth_routes.route('/documents', methods=['PUT'])
def update_document_route():
    return DocumentController.update_document()

@auth_routes.route('/documents/user', methods=['POST'])
@DocumentController.token_required
def get_documents_by_user_route():
    return DocumentController.get_documents_by_user()

@auth_routes.route('/documents/id', methods=['POST'])
@DocumentController.token_required
def get_document_by_id_route():
    return DocumentController.get_document_by_id()

@auth_routes.route('/documents', methods=['DELETE'])
@DocumentController.token_required
def delete_document_route():
    return DocumentController.delete_document()

@auth_routes.route('/admin/validate-document/<string:document_id>', methods=['GET'])
def validate_document_route(document_id):
    return DocumentController.validate_document(document_id)

@auth_routes.route('/admin/rejet-document/<string:document_id>', methods=['GET'])
def rejet_document_route(document_id):
    return DocumentController.rejet_document(document_id)

# Routes pour JobOfferController
@auth_routes.route('/job_offers', methods=['POST'])
def create_job_offer_route():
    return JobOfferController.create_job_offer()

@auth_routes.route('/job_offers', methods=['PUT'])
@JobOfferController.token_required
def update_job_offer_route():
    return JobOfferController.update_job_offer()

@auth_routes.route('/job_offers/id', methods=['POST'])
@JobOfferController.token_required
def get_job_offer_by_id_route():
    return JobOfferController.get_job_offer_by_id()

@auth_routes.route('/job_offers', methods=['GET'])
def get_all_job_offers_route():
    return JobOfferController.get_all_job_offers()

@auth_routes.route('/job_offers', methods=['DELETE'])
def delete_job_offer_route():
    return JobOfferController.delete_job_offer()

# Routes pour NotificationController
@auth_routes.route('/notifications', methods=['POST'])
@NotificationController.token_required
def create_notification_route():
    return NotificationController.create_notification()

@auth_routes.route('/notifications', methods=['PUT'])
@NotificationController.token_required
def update_notification_route():
    return NotificationController.update_notification()

@auth_routes.route('/notifications/user', methods=['POST'])
@NotificationController.token_required
def get_notifications_by_user_route():
    return NotificationController.get_notifications_by_user()

@auth_routes.route('/notifications/read', methods=['PUT'])
@NotificationController.token_required
def mark_notification_as_read_route():
    return NotificationController.mark_notification_as_read()

@auth_routes.route('/notifications', methods=['DELETE'])
@NotificationController.token_required
def delete_notification_route():
    return NotificationController.delete_notification()

# Routes pour PaymentController
@auth_routes.route('/payments', methods=['POST'])
def create_payment_route():
    return PaymentController.create_payment()

@auth_routes.route('/payments', methods=['PUT'])
@PaymentController.token_required
def update_payment_route():
    return PaymentController.update_payment()

@auth_routes.route('/payments/user', methods=['POST'])
@PaymentController.token_required
def get_payments_by_user_route():
    return PaymentController.get_payments_by_user()

@auth_routes.route('/payments/id', methods=['POST'])
@PaymentController.token_required
def get_payment_by_id_route():
    return PaymentController.get_payment_by_id()

@auth_routes.route('/payments', methods=['DELETE'])
@PaymentController.token_required
def delete_payment_route():
    return PaymentController.delete_payment()

@auth_routes.route('/envoie-infos-client-paiement', methods=['POST'])
@PaymentController.token_required
def send_payment_info_route():
    return PaymentController.send_payment_info()

@auth_routes.route('/payments/all', methods=['POST'])
def get_all_payments_route():
    return PaymentController.get_all_payments()

# Routes pour StepController
@auth_routes.route('/steps', methods=['POST'])
@StepController.token_required
def create_step_route():
    return StepController.create_step()

@auth_routes.route('/steps', methods=['PUT'])
@StepController.token_required
def update_step_route():
    return StepController.update_step()

@auth_routes.route('/steps/id', methods=['POST'])
@StepController.token_required
def get_step_by_id_route():
    return StepController.get_step_by_id()

@auth_routes.route('/steps', methods=['GET'])
@StepController.token_required
def get_all_steps_route():
    return StepController.get_all_steps()

@auth_routes.route('/steps', methods=['DELETE'])
@StepController.token_required
def delete_step_route():
    return StepController.delete_step()

# Routes pour UserStepController
@auth_routes.route('/user_steps', methods=['POST'])
def create_user_step_route():
    return UserStepController.create_user_step()

@auth_routes.route('/user_steps', methods=['PUT'])
@UserStepController.token_required
def update_user_step_route():
    return UserStepController.update_user_step()

@auth_routes.route('/user_steps/user', methods=['POST'])
@UserStepController.token_required
def get_user_steps_by_user_route():
    return UserStepController.get_user_steps_by_user()

@auth_routes.route('/user_steps/step', methods=['POST'])
@UserStepController.token_required
def get_user_steps_by_step_route():
    return UserStepController.get_user_steps_by_step()

@auth_routes.route('/user_steps', methods=['DELETE'])
@UserStepController.token_required
def delete_user_step_route():
    return UserStepController.delete_user_step()