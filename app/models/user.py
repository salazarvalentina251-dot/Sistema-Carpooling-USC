
from app.extensions import db
from datetime import datetime


class User(db.Model):

    # Nombre de la tabla
    __tablename__ = "users"

    # Identificador único
    id = db.Column(db.Integer, primary_key=True)

    # Información personal
    name = db.Column(db.String(100), nullable=False)

    email = db.Column(db.String(120), unique=True, nullable=False)

    # Contraseña cifrada (nunca guardaremos la contraseña original)
    password_hash = db.Column(db.String(255), nullable=False)

    # Rol del usuario dentro de la plataforma
    role = db.Column(db.String(20), default="usuario", nullable=False)

    # Estado de la cuenta
    is_active = db.Column(db.Boolean, default=True, nullable=False)

    # Fecha de creación
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def __repr__(self):
        return f"<User {self.email}>"
