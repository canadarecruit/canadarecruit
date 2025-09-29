from flask import Flask
from flask_cors import CORS 
from config import Config
from routes.routes import auth_routes
from cloudinary_config import config_cloudinary

app = Flask(__name__)
app.config.from_object(Config)

# Autoriser toutes les origines (React peut accéder au backend)
CORS(app, resources={r"/*": {"origins": "*"}})

# Charger la config Cloudinary, même sur Vercel
config_cloudinary()  # <= TU DOIS LE METTRE HORS du if __name__ == '__main__'

# Enregistrer les routes d'authentification
app.register_blueprint(auth_routes, url_prefix='/api')

# En local uniquement, lancer le serveur
if __name__ == '__main__':
    app.run(debug=True) 