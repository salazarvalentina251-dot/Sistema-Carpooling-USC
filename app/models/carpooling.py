import secrets
from datetime import datetime

from app.extensions import db

# Estados posibles de una reserva
PENDIENTE = "PENDIENTE"
ACEPTADA = "ACEPTADA"
COMPLETADA = "COMPLETADA"
CANCELADA = "CANCELADA"
RECHAZADA = "RECHAZADA"


def generar_codigo():
    """Código de abordaje de 6 caracteres (sin letras confusas como O/0, I/1)."""
    alfabeto = "ABCDEFGHJKLMNPQRSTUVWXYZ23456789"
    return "".join(secrets.choice(alfabeto) for _ in range(6))


class Trip(db.Model):
    """Viaje publicado por un conductor."""
    __tablename__ = "trips"

    id = db.Column(db.Integer, primary_key=True)
    # Ajusta "users.id" si tu tabla de usuarios tiene otro nombre
    driver_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False, index=True)
    origin = db.Column(db.String(120), nullable=False)
    destination = db.Column(db.String(120), nullable=False)
    departure_time = db.Column(db.DateTime, nullable=False, index=True)
    seats_total = db.Column(db.Integer, nullable=False, default=3)
    seats_available = db.Column(db.Integer, nullable=False, default=3)
    price = db.Column(db.Integer, nullable=False)  # aporte en COP
    status = db.Column(db.String(20), nullable=False, default="ABIERTO")  # ABIERTO | CERRADO | CANCELADO

    driver = db.relationship("User", foreign_keys=[driver_id])
    bookings = db.relationship("Booking", back_populates="trip", lazy="dynamic")


class Booking(db.Model):
    """Reserva (solicitud de un pasajero a un viaje)."""
    __tablename__ = "bookings"
    __table_args__ = (db.UniqueConstraint("trip_id", "passenger_id", name="uq_booking_trip_passenger"),)

    id = db.Column(db.Integer, primary_key=True)
    trip_id = db.Column(db.Integer, db.ForeignKey("trips.id"), nullable=False, index=True)
    passenger_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False, index=True)
    status = db.Column(db.String(20), nullable=False, default=PENDIENTE, index=True)
    boarding_code = db.Column(db.String(6), nullable=False, default=generar_codigo)
    rating = db.Column(db.Float, nullable=True)  # calificación que el pasajero da al conductor
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)

    trip = db.relationship("Trip", back_populates="bookings")
    passenger = db.relationship("User", foreign_keys=[passenger_id])
    messages = db.relationship("Message", back_populates="booking", lazy="dynamic",
                               cascade="all, delete-orphan")


class Message(db.Model):
    """Mensaje del chat asociado a una reserva (pasajero <-> conductor)."""
    __tablename__ = "messages"

    id = db.Column(db.Integer, primary_key=True)
    booking_id = db.Column(db.Integer, db.ForeignKey("bookings.id"), nullable=False, index=True)
    sender_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    text = db.Column(db.String(500), nullable=False)
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)

    booking = db.relationship("Booking", back_populates="messages")
