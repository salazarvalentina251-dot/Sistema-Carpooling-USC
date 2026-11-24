from datetime import datetime
from app.extensions import db
from app.routes.carpooling import Booking, Trip


def responder_reserva(conductor_id, solicitud_id, accion):
    if accion not in ("aceptar", "rechazar"):
        return False, "Acción no válida."

    try:
        reserva = Booking.query.join(Trip).filter(
            Booking.id == solicitud_id,
            Trip.driver_id == conductor_id
        ).first()

        if not reserva:
            return False, "Solicitud no encontrada."

        if reserva.status != "PENDIENTE":
            return False, "Solicitud ya procesada."

        viaje = reserva.trip

        if viaje.status != "ABIERTO":
            return False, "El viaje no está abierto."

        if viaje.departure_time <= datetime.now():
            return False, "El viaje ya inició."

        nuevo_estado = (
            "ACEPTADA" if accion == "aceptar"
            else "RECHAZADA"
        )

        actualizado = Booking.query.filter_by(
            id=solicitud_id,
            status="PENDIENTE"
        ).update({"status": nuevo_estado})

        if actualizado != 1:
            db.session.rollback()
            return False, "Solicitud ya procesada."

        if accion == "aceptar":
            actualizado = Trip.query.filter(
                Trip.id == viaje.id,
                Trip.status == "ABIERTO",
                Trip.seats_available > 0
            ).update({
                Trip.seats_available:
                    Trip.seats_available - 1
            })

            if actualizado != 1:
                db.session.rollback()
                return False, "No hay cupos disponibles."

        db.session.commit()
        return True, "Solicitud procesada correctamente."

    except Exception:
        db.session.rollback()
        return False, "Error al procesar la solicitud."