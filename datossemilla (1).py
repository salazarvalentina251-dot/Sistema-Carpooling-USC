"""Datos de prueba para el módulo de pasajero.

Uso (desde la raíz del proyecto, con al menos 2 usuarios ya registrados):
    python seed.py

El primer usuario será el pasajero y el segundo el conductor.
"""
from datetime import datetime, timedelta

from app import create_app
from app.extensions import db
from app.models import User
from app.models.carpooling import ACEPTADA, COMPLETADA, PENDIENTE, Booking, Message, Trip

app = create_app()

with app.app_context():
    usuarios = User.query.order_by(User.id).limit(2).all()
    if len(usuarios) < 2:
        raise SystemExit("Registra al menos 2 usuarios antes de ejecutar el seed.")
    pasajero, conductor = usuarios

    hoy = datetime.now().replace(minute=0, second=0, microsecond=0)
    manana = hoy + timedelta(days=1)

    def viaje(origen, destino, salida, precio, puestos=3):
        t = Trip(driver_id=conductor.id, origin=origen, destination=destino,
                 departure_time=salida, seats_total=puestos, seats_available=puestos, price=precio)
        db.session.add(t)
        return t

    # Viajes futuros
    t1 = viaje("Ciudad Jardín", "Universidad Santiago de Cali", hoy.replace(hour=23) + timedelta(minutes=10), 5500, 2)
    t2 = viaje("Valle del Lili", "Universidad Santiago de Cali", manana.replace(hour=7, minute=25), 4800, 1)
    t3 = viaje("San Fernando", "Universidad Santiago de Cali", manana.replace(hour=8), 4200)
    # Viajes pasados (para el historial)
    p1 = viaje("Universidad Santiago de Cali", "Ciudad Jardín", hoy - timedelta(days=4), 5500)
    p2 = viaje("Valle del Lili", "Universidad Santiago de Cali", hoy - timedelta(days=6), 4800)
    db.session.flush()

    b1 = Booking(trip_id=t1.id, passenger_id=pasajero.id, status=ACEPTADA)
    t1.seats_available -= 1
    b2 = Booking(trip_id=t2.id, passenger_id=pasajero.id, status=PENDIENTE)
    b3 = Booking(trip_id=p1.id, passenger_id=pasajero.id, status=COMPLETADA, rating=5.0)
    b4 = Booking(trip_id=p2.id, passenger_id=pasajero.id, status=COMPLETADA, rating=4.8)
    db.session.add_all([b1, b2, b3, b4])
    db.session.flush()

    db.session.add_all([
        Message(booking_id=b1.id, sender_id=conductor.id, text="Hola, te recojo en la entrada de Ciudad Jardín."),
        Message(booking_id=b1.id, sender_id=pasajero.id, text="Perfecto, estaré allí a las 7:05. Gracias."),
    ])
    db.session.commit()
    print("Datos de prueba creados.")
