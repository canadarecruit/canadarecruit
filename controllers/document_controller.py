from flask import Blueprint, request, jsonify
from http import HTTPStatus
from functools import wraps
import jwt
from werkzeug.utils import secure_filename
import cloudinary.uploader
from models.document_model import Document
from models.notification_model import Notification
from config import Config
from models.utilisateurs_model import Utilisateurs
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.application import MIMEApplication
import requests


# Définir le Blueprint pour les routes des documents
document_routes = Blueprint('document_routes', __name__)

class DocumentController:
    ALLOWED_EXTENSIONS = {'pdf', 'png', 'jpg', 'jpeg'}

    @staticmethod
    def allowed_file(filename):
        """Vérifie si l'extension du fichier est valide."""
        return '.' in filename and filename.rsplit('.', 1)[1].lower() in DocumentController.ALLOWED_EXTENSIONS

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
            token = DocumentController._get_token()
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
    def create_document():
        """Crée un nouveau document pour un utilisateur avec téléversement vers Cloudinary."""
        try:
            # Récupérer les données du formulaire
            user_id = request.form.get('user_id')
            document_name = request.form.get('document_name', 'document_sans_nom')
            file = request.files.get('file')

            if not file:
                return jsonify({"message": "documents obligatoires"}), HTTPStatus.BAD_REQUEST

            # Vérifier si le fichier a une extension autorisée
            if not DocumentController.allowed_file(file.filename):
                return jsonify({"message": f"Format de fichier non autorisé. Types autorisés : {', '.join(DocumentController.ALLOWED_EXTENSIONS)}"}), HTTPStatus.BAD_REQUEST

            # Vérification des autorisations
            token = DocumentController._get_token()
            decoded_token = jwt.decode(token, Config.SECRET_KEY, algorithms=['HS256'])
            user_id =  decoded_token.get('user_id') 

            # Uploader le fichier vers Cloudinary
            upload_result = cloudinary.uploader.upload(
                file,
                folder=f"canada/documents/{user_id}",
                resource_type="auto"
            )
            file_url = upload_result.get('secure_url')

            # Enregistrer dans la base de données
            document_id = Document.create(
                user_id=user_id,
                document_name=document_name,
                file_path=file_url,
                status='pending'
            )

            # Récupérer les informations de l'utilisateur
            user = Utilisateurs.get_user_by_id(user_id)
            user_name = f"{user.get('firstName', '')} {user.get('lastName', '')}".strip() or "Utilisateur inconnu"

            # Envoyer un e-mail à l'administrateur
            smtp_server = Config.smtp_server
            smtp_port = Config.smtp_port
            username = Config.username
            password = Config.password

            # Créer le message e-mail
            msg = MIMEMultipart()
            msg['From'] = username
            msg['To'] = 'canadarecruit.00@gmail.com'
            msg['Subject'] = f"Nouveau document téléversé par {user_name}"

            # Contenu du message
            validation_url = f"{Config.BACKEND_URL}/api/admin/validate-document/{document_id}"
            rejection_url = f"{Config.BACKEND_URL}/api/admin/rejet-document/{document_id}"

            body = f"""Bonjour Directeur Canada Recruit,

L'utilisateur dont le nom est : {user_name} a ajouté son {document_name}.
Veuillez examiner le document en pièce jointe.

Si le document est valide, cliquez sur le bouton ci-dessous pour le valider :
<a href="{validation_url}" style="display: inline-block; padding: 10px 20px; color: #fff; background-color: #007bff; text-decoration: none; border-radius: 5px;">
    Valider le document
</a>

 <a href="{rejection_url}" style="display: inline-block; padding: 10px 20px; color: #fff !important; background-color: #dc3545; text-decoration: none; border-radius: 5px;">
                Rejeter le document
            </a>
<br>
Cordialement,
Équipe Canada Recruitment
"""
            msg.attach(MIMEText(body, 'html'))

            # Ajouter le document en pièce jointe
            response = requests.get(file_url)
            if response.status_code == 200:
                file_data = response.content
                file_name = file.filename or f"{document_name}.pdf"
                attachment = MIMEApplication(file_data, Name=file_name)
                attachment['Content-Disposition'] = f'attachment; filename="{file_name}"'
                msg.attach(attachment)

            # Connexion au serveur SMTP et envoi de l'e-mail
            with smtplib.SMTP(smtp_server, smtp_port) as server:
                server.starttls()
                server.login(username, password)
                server.send_message(msg)

            # Créer une notification pour l'utilisateur
            Notification.create(
                user_id=user_id,
                message="Etape 3: Votre document a été déposé avec succès ! Il est maintenant en cours de supervision.",
                type="success"
            )

            if document_id:
                return jsonify({
                    'message': 'Document créé avec succès',
                    'document_id': document_id,
                    'file_path': file_url,
                    'status': 'pending',
                    'uploaded_date': Document.get_by_id(document_id).get('uploaded_date')
                }), HTTPStatus.CREATED
            return jsonify({"message": "Erreur lors de l'enregistrement en base"}), HTTPStatus.INTERNAL_SERVER_ERROR
        except Exception as e:
            return jsonify({"error": str(e)}), HTTPStatus.INTERNAL_SERVER_ERROR

    @staticmethod
    @token_required
    def get_documents_by_user():
        """Récupère tous les documents pour un utilisateur donné."""
        try:
            data = request.get_json()
            if 'user_id' not in data:
                return jsonify({"message": "ID utilisateur requis"}), HTTPStatus.BAD_REQUEST

            user_id = data.get('user_id')

            # Vérification des autorisations
            token = DocumentController._get_token()
            decoded_token = jwt.decode(token, Config.SECRET_KEY, algorithms=['HS256'])
            if decoded_token.get('user_id') != user_id and decoded_token.get('role') != 'admin':
                return jsonify({"message": "Accès refusé. Vous ne pouvez voir que vos propres documents ou en tant qu'administrateur."}), HTTPStatus.FORBIDDEN

            documents = Document.get_by_user(user_id)
            return jsonify({
                "message": "Documents récupérés avec succès" if documents else "Aucun document trouvé",
                "documents": documents or []
            }), HTTPStatus.OK
        except Exception as e:
            return jsonify({"error": str(e)}), HTTPStatus.INTERNAL_SERVER_ERROR

    @staticmethod
    @token_required
    def get_document_by_id(id):
        """Récupère un document par son ID."""
        try:
            # Vérification des autorisations
            token = DocumentController._get_token()
            decoded_token = jwt.decode(token, Config.SECRET_KEY, algorithms=['HS256'])
            document = Document.get_by_id(id)
            if not document:
                return jsonify({"message": "Document non trouvé"}), HTTPStatus.NOT_FOUND
            if decoded_token.get('user_id') != document['user_id'] and decoded_token.get('role') != 'admin':
                return jsonify({"message": "Accès refusé. Vous ne pouvez voir que vos propres documents ou en tant qu'administrateur."}), HTTPStatus.FORBIDDEN

            return jsonify({
                "message": "Document récupéré avec succès",
                "document": document
            }), HTTPStatus.OK
        except Exception as e:
            return jsonify({"error": str(e)}), HTTPStatus.INTERNAL_SERVER_ERROR

    @staticmethod
    def update_document(id):
        """Met à jour un document existant."""
        try:
            data = request.get_json()
            document_name = data.get('document_name')
            status = data.get('status')
            file_path = data.get('file_path')

            if status and status not in ['validated', 'pending', 'missing']:
                return jsonify({"message": "Statut invalide. Doit être 'validated', 'pending' ou 'missing'"}), HTTPStatus.BAD_REQUEST


            document = Document.get_by_id(id)
            if not document:
                return jsonify({"message": "Document non trouvé"}), HTTPStatus.NOT_FOUND
            
            success = Document.update(id, document_name, status, file_path)
            if not success:
                return jsonify({"message": "Document non trouvé ou aucun changement effectué"}), HTTPStatus.NOT_FOUND

            return jsonify({'message': 'Document mis à jour avec succès'}), HTTPStatus.OK
        except Exception as e:
            return jsonify({"error": str(e)}), HTTPStatus.INTERNAL_SERVER_ERROR

    @staticmethod
    @token_required
    def delete_document(id):
        """Supprime un document."""
        try:
            # Vérification des autorisations
            token = DocumentController._get_token()
            decoded_token = jwt.decode(token, Config.SECRET_KEY, algorithms=['HS256'])
            document = Document.get_by_id(id)
            if not document:
                return jsonify({"message": "Document non trouvé"}), HTTPStatus.NOT_FOUND
            if decoded_token.get('user_id') != document['user_id'] and decoded_token.get('role') != 'admin':
                return jsonify({"message": "Accès refusé. Vous ne pouvez supprimer que vos propres documents ou en tant qu'administrateur."}), HTTPStatus.FORBIDDEN

            success = Document.delete(id)
            if not success:
                return jsonify({"message": "Document non trouvé"}), HTTPStatus.NOT_FOUND

            # Supprimer le fichier de Cloudinary
            public_id = f"documents/{document['user_id']}/{document['document_name']}"
            cloudinary.uploader.destroy(public_id, resource_type="raw")

            return jsonify({'message': 'Document supprimé avec succès'}), HTTPStatus.OK
        except Exception as e:
            return jsonify({"error": str(e)}), HTTPStatus.INTERNAL_SERVER_ERROR
        
    @staticmethod
    def validate_document(document_id):
        """Valide un document via un lien direct sans authentification."""
        try:
            document = Document.get_by_id(document_id)
            if not document:
                return jsonify({"message": "Document non trouvé"}), HTTPStatus.NOT_FOUND
            

            document = Document.update(document_id, status='validated')
            if not document:
                return jsonify({"message": "Erreur lors de la validation du document"}), HTTPStatus.INTERNAL_SERVER_ERROR
            else:
                return jsonify({"message": "Document validé avec succès"}), HTTPStatus.OK
        except Exception as e:
            return jsonify({"error": str(e)}), HTTPStatus.INTERNAL_SERVER_ERROR
        
    @staticmethod
    def rejet_document(document_id):
        """rejeter un document via un lien direct sans authentification."""
        try:
            document = Document.get_by_id(document_id)
            if not document:
                return jsonify({"message": "Document non trouvé"}), HTTPStatus.NOT_FOUND
            

            document = Document.delete(document_id)
            if not document:
                return jsonify({"message": "Erreur lors du rejet du document"}), HTTPStatus.INTERNAL_SERVER_ERROR
            else:
                return jsonify({"message": "Document rejeté avec succès"}), HTTPStatus.OK
        except Exception as e:
            return jsonify({"error": str(e)}), HTTPStatus.INTERNAL_SERVER_ERROR