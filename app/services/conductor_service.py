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

class TripDetails(db.Model):
    __tablename__ = "conductor_trip_details"

    trip_id = db.Column(
        db.Integer,
        db.ForeignKey("trips.id"),
        primary_key=True
    )
    vehicle_id = db.Column(
        db.Integer, nullable=False
    )
    stops = db.Column(
        db.JSON, nullable=False, default=list
    )


class TripNote(db.Model):
    _tablename_ = "conductor_trip_notes"

    trip_id = db.Column(
        db.Integer,
        db.ForeignKey("trips.id"),
        primary_key=True
    )
    text = db.Column(db.String(300), nullable=False)


def guardar_viaje(conductor_id, origen, destino,
                  salida, puestos, aporte,
                  vehiculo_id, paradas, observaciones=''):

    observaciones = observaciones.strip()

    if len(observaciones) > 300:
        raise ValueError("Maximo 300 caracteres en las observaciones.")

    if not origen or not destino:
        raise ValueError("Origen y destino obligatorios.")

    if len(origen) > 120 or len(destino) > 120:
        raise ValueError("Origen o destino demasiado largo.")

    if salida <= datetime.now():
        raise ValueError("La salida debe ser futura.")

    if not 1 <= puestos <= 8:
        raise ValueError("Cantidad de puestos no valida.")

    if not 0 <= aporte <= 50000:
        raise ValueError("Aporte no valido.")

    if len(paradas) > 4:
        raise ValueError("Maximo cuatro paradas.")

    try:
        viaje = Trip(
            driver_id=conductor_id,
            origin=origen,
            destination=destino,
            departure_time=salida,
            seats_total=puestos,
            seats_available=puestos,
            price=aporte,
            status="ABIERTO"
        )

        db.session.add(viaje)
        db.session.flush()

        detalle = TripDetails(
            trip_id=viaje.id,
            vehicle_id=vehiculo_id,
            stops=paradas
        )

        db.session.add(detalle)

        if observaciones:
            db.session.add(TripNote(
                trip_id=viaje.id,
                text=observaciones
            ))
        viaje_id = viaje.id
        db.session.commit()

        return viaje_id

    except Exception:
        db.session.rollback()
        raise