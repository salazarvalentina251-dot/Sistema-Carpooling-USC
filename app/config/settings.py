import os


# Ruta principal del proyecto
BASE_DIR = os.path.abspath(
    os.path.join(os.path.dirname(__file__), "../../")
)


class Config:
    # Clave para proteger las sesiones de Flask
    SECRET_KEY = "carpooling-usc-clave-desarrollo"

    # Configuración de la base de datos SQLite
    SQLALCHEMY_DATABASE_URI = (
        "sqlite:///" + os.path.join(BASE_DIR, "carpooling.db")
    )

    # Desactivar notificaciones innecesarias de SQLAlchemy
    SQLALCHEMY_TRACK_MODIFICATIONS = False