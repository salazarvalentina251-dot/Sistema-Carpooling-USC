
from flask import Flask, render_template

from app.config.settings import Config
from app.extensions import db


def create_app():

    app = Flask(__name__)

    # Cargar configuración
    app.config.from_object(Config)

    # Inicializar base de datos
    db.init_app(app)

    # Importar modelos
    from app.models import User

    # Importar rutas
    from app.routes.auth import auth_bp
    from app.routes.conductor import conductor_bp

    # Registrar Blueprint
    app.register_blueprint(auth_bp)
    app.register_blueprint(conductor_bp)  

    # Crear tablas
    with app.app_context():
        db.create_all()

    # Página principal
    @app.route("/")
    def home():
        return render_template("home.html")
    from app.routes.passenger import passenger_bp
    app.register_blueprint(passenger_bp)

    return app
