import re
from datetime import date, datetime, time, timedelta
from functools import wraps

from flask import (Blueprint, abort, flash, jsonify, redirect, render_template,
                   request, session, url_for)
from sqlalchemy import desc, func

from app.extensions import db
from app.models import User
from app.models.carpooling import (ACEPTADA, CANCELADA, COMPLETADA, PENDIENTE,
                                   RECHAZADA, Booking, Message, Trip)

passenger_bp = Blueprint("passenger", __name__, url_prefix="/pasajero")

MESES = ["ene.", "feb.", "mar.", "abr.", "may.", "jun.",
         "jul.", "ago.", "sep.", "oct.", "nov.", "dic."]
COLORES = ["green", "slate", "blue"]

GRUPO_POR_ESTADO = {
    ACEPTADA: "proximas",
    PENDIENTE: "pendientes",
    COMPLETADA: "completadas",
    CANCELADA: "canceladas",
    RECHAZADA: "canceladas",
}


# ---------------------------------------------------------------- Sesión
def login_required(f):
    @wraps(f)
    def wrapper(*args, **kwargs):
        # Asume que el login guarda session["user_id"]. Ajústalo si usas otro mecanismo.
        if not session.get("user_id"):
            return redirect(url_for("auth.login"))
        return f(*args, **kwargs)
    return wrapper


def usuario_actual():
    user = db.session.get(User, session["user_id"])
    if user is None:
        session.clear()
        abort(401)
    return user


def nombre_de(user):
    """Obtiene el nombre del usuario sin depender de cómo se llame la columna."""
    for attr in ("full_name", "name", "nombre", "username"):
        valor = getattr(user, attr, None)
        if valor:
            return valor
    email = getattr(user, "email", None)
    return email.split("@")[0] if email else "Usuario"


def iniciales_de(nombre):
    partes = nombre.split()
    return "".join(p[0] for p in partes[:2]).upper() or "U"


def contexto_usuario(user):
    nombre = nombre_de(user)
    return {"name": nombre, "first_name": nombre.split()[0], "initials": iniciales_de(nombre)}


def vista(template, active, titulo, **datos):
    user = usuario_actual()
    return render_template(
        f"passenger/{template}.html",
        active=active, page_title=titulo, user=contexto_usuario(user), **datos
    )


# ------------------------------------------------------------ Formateo
def fmt_precio(valor):
    return "$" + f"{valor:,}".replace(",", ".")


def fmt_hora(dt):
    return f"{dt.hour % 12 or 12}:{dt.minute:02d} {'a. m.' if dt.hour < 12 else 'p. m.'}"


def fmt_fecha(d):
    return f"{d.day} {MESES[d.month - 1]}"


def fmt_cuando(dt):
    hoy = date.today()
    if dt.date() == hoy:
        dia = "Hoy"
    elif dt.date() == hoy + timedelta(days=1):
        dia = "Mañana"
    else:
        dia = fmt_fecha(dt.date())
    return f"{dia} · {fmt_hora(dt)}"


def fmt_puestos(n):
    return f"{n} puesto" if n == 1 else f"{n} puestos"


def rating_conductor(driver_id):
    promedio = (db.session.query(func.avg(Booking.rating))
                .join(Trip, Booking.trip_id == Trip.id)
                .filter(Trip.driver_id == driver_id, Booking.rating.isnot(None))
                .scalar())
    return f"{promedio:.1f}" if promedio else "Nuevo"


def viaje_dict(trip):
    nombre = nombre_de(trip.driver)
    return {
        "id": trip.id,
        "driver": nombre,
        "initials": iniciales_de(nombre),
        "color": COLORES[trip.driver_id % len(COLORES)],
        "rating": rating_conductor(trip.driver_id),
        "price": fmt_precio(trip.price),
        "route": f"{trip.origin} → {trip.destination}",
        "time": fmt_hora(trip.departure_time),
        "seats": fmt_puestos(trip.seats_available),
    }


# ------------------------------------------------- Parseo de la búsqueda
def parse_fecha(texto):
    hoy = date.today()
    t = (texto or "").lower()
    if not t or "hoy" in t:
        return hoy
    if "mañana" in t:
        return hoy + timedelta(days=1)
    m = re.search(r"(\d{1,2})\s*([a-z]{3})", t)
    if m:
        mes = next((i + 1 for i, n in enumerate(MESES) if n[:3] == m.group(2)), None)
        if mes:
            try:
                return date(hoy.year, mes, int(m.group(1)))
            except ValueError:
                pass
    return hoy


def parse_hora(texto):
    m = re.search(r"(\d{1,2}):(\d{2})\s*([ap])", (texto or "").lower())
    if not m:
        return None
    h = int(m.group(1)) % 12 + (12 if m.group(3) == "p" else 0)
    return time(h, int(m.group(2)))


def buscar_viajes(user, origen="", destino="", fecha=None, hora=None, limite=None):
    fecha = fecha or date.today()
    inicio = max(datetime.combine(fecha, time.min), datetime.now())
    fin = datetime.combine(fecha, time.min) + timedelta(days=1)

    q = Trip.query.filter(
        Trip.status == "ABIERTO",
        Trip.seats_available > 0,
        Trip.driver_id != user.id,
        Trip.departure_time >= inicio,
        Trip.departure_time < fin,
    )
    # "Ciudad Jardín, Cali" -> se busca por "Ciudad Jardín"
    origen = origen.split(",")[0].strip()
    destino = destino.split(",")[0].strip()
    if origen:
        q = q.filter(Trip.origin.ilike(f"%{origen}%"))
    if destino:
        q = q.filter(Trip.destination.ilike(f"%{destino}%"))

    viajes = q.all()
    if hora:
        objetivo = hora.hour * 60 + hora.minute
        viajes.sort(key=lambda t: abs(t.departure_time.hour * 60 + t.departure_time.minute - objetivo))
    else:
        viajes.sort(key=lambda t: t.departure_time)
    return viajes[:limite] if limite else viajes


# ------------------------------------------------------------------ Vistas
@passenger_bp.route("/inicio")
@login_required
def inicio():
    user = usuario_actual()

    proxima = (Booking.query.join(Trip)
               .filter(Booking.passenger_id == user.id, Booking.status == ACEPTADA,
                       Trip.departure_time >= datetime.now())
               .order_by(Trip.departure_time).first())
    proximo_viaje = None
    if proxima:
        proximo_viaje = viaje_dict(proxima.trip)
        proximo_viaje.update({"booking_id": proxima.id, "estado": "Aceptada"})

    frecuente = (db.session.query(Trip.origin, Trip.destination)
                 .join(Booking, Booking.trip_id == Trip.id)
                 .filter(Booking.passenger_id == user.id,
                         Booking.status.in_((ACEPTADA, COMPLETADA)))
                 .group_by(Trip.origin, Trip.destination)
                 .order_by(desc(func.count(Booking.id))).first())

    rutas_hoy = Trip.query.filter(
        Trip.status == "ABIERTO",
        func.date(Trip.departure_time) == date.today().isoformat(),
    ).count()

    viajes = [viaje_dict(t) for t in buscar_viajes(user, limite=3)]
    return vista("inicio", "inicio", "Inicio", viajes=viajes, proximo_viaje=proximo_viaje,
                 ruta_frecuente=frecuente, rutas_hoy=rutas_hoy)


@passenger_bp.route("/buscar")
@login_required
def buscar():
    user = usuario_actual()
    origen = request.args.get("origen", "")
    destino = request.args.get("destino", "")
    fecha_txt = request.args.get("fecha", "")
    hora_txt = request.args.get("hora", "")

    trips = buscar_viajes(user, origen, destino, parse_fecha(fecha_txt), parse_hora(hora_txt))
    ya_reservados = {b.trip_id for b in Booking.query.filter(
        Booking.passenger_id == user.id, Booking.status.in_((PENDIENTE, ACEPTADA))).all()}

    viajes = []
    for t in trips:
        d = viaje_dict(t)
        d["reservado"] = t.id in ya_reservados
        viajes.append(d)

    return vista("buscar", "buscar", "Buscar viajes", viajes=viajes,
                 filtros={"origen": origen, "destino": destino, "fecha": fecha_txt, "hora": hora_txt})


@passenger_bp.route("/viajes/<int:trip_id>/reservar", methods=["POST"])
@login_required
def reservar(trip_id):
    user = usuario_actual()
    trip = db.get_or_404(Trip, trip_id)

    if trip.driver_id == user.id:
        flash("No puedes reservar tu propio viaje.", "error")
    elif trip.status != "ABIERTO" or trip.seats_available < 1 or trip.departure_time < datetime.now():
        flash("Este viaje ya no está disponible.", "error")
    else:
        existente = Booking.query.filter_by(trip_id=trip.id, passenger_id=user.id).first()
        if existente and existente.status in (PENDIENTE, ACEPTADA):
            flash("Ya tienes una solicitud para este viaje.", "error")
        elif existente:  # estaba cancelada o rechazada: se reactiva
            existente.status = PENDIENTE
            db.session.commit()
            flash("Solicitud enviada. Espera la respuesta del conductor.", "ok")
        else:
            db.session.add(Booking(trip_id=trip.id, passenger_id=user.id))
            db.session.commit()
            flash("Solicitud enviada. Espera la respuesta del conductor.", "ok")
    return redirect(url_for("passenger.reservas"))


@passenger_bp.route("/reservas")
@login_required
def reservas():
    user = usuario_actual()
    bookings = (Booking.query.join(Trip).filter(Booking.passenger_id == user.id)
                .order_by(Trip.departure_time.desc()).all())

    datos = []
    conteo = {"proximas": 0, "pendientes": 0, "completadas": 0}
    for b in bookings:
        grupo = GRUPO_POR_ESTADO.get(b.status, "canceladas")
        if grupo in conteo:
            conteo[grupo] += 1
        datos.append({
            "id": b.id,
            "estado": b.status,
            "group": grupo,
            "price": fmt_precio(b.trip.price),
            "route": f"{b.trip.origin} → {b.trip.destination}",
            "when": fmt_cuando(b.trip.departure_time),
            "driver": nombre_de(b.trip.driver),
        })
    return vista("reservas", "reservas", "Mis reservas", reservas=datos, conteo=conteo)


@passenger_bp.route("/reservas/<int:booking_id>/cancelar", methods=["POST"])
@login_required
def cancelar(booking_id):
    user = usuario_actual()
    b = Booking.query.filter_by(id=booking_id, passenger_id=user.id).first_or_404()

    if b.status not in (PENDIENTE, ACEPTADA):
        flash("Esta reserva ya no se puede cancelar.", "error")
    else:
        if b.status == ACEPTADA:  # liberar el puesto que ocupaba
            b.trip.seats_available = min(b.trip.seats_total, b.trip.seats_available + 1)
        b.status = CANCELADA
        db.session.commit()
        flash("Reserva cancelada.", "ok")
    return redirect(url_for("passenger.reservas"))


@passenger_bp.route("/reservas/<int:booking_id>/codigo")
@login_required
def codigo_abordaje(booking_id):
    user = usuario_actual()
    b = Booking.query.filter_by(id=booking_id, passenger_id=user.id).first_or_404()
    if b.status != ACEPTADA:
        return jsonify(error="El código solo está disponible para reservas aceptadas."), 403
    return jsonify(codigo=b.boarding_code, ruta=f"{b.trip.origin} → {b.trip.destination}",
                   cuando=fmt_cuando(b.trip.departure_time))


@passenger_bp.route("/reservas/<int:booking_id>/calificar", methods=["POST"])
@login_required
def calificar(booking_id):
    user = usuario_actual()
    b = Booking.query.filter_by(id=booking_id, passenger_id=user.id).first_or_404()
    try:
        valor = float(request.form.get("rating", ""))
    except ValueError:
        abort(400)
    if b.status != COMPLETADA or not 1 <= valor <= 5:
        abort(400)
    b.rating = round(valor, 1)
    db.session.commit()
    return redirect(url_for("passenger.historial"))


@passenger_bp.route("/historial")
@login_required
def historial():
    user = usuario_actual()
    bookings = (Booking.query.join(Trip)
                .filter(Booking.passenger_id == user.id, Booking.status == COMPLETADA)
                .order_by(Trip.departure_time.desc()).all())
    datos = [{
        "route": f"{b.trip.origin} → {b.trip.destination}",
        "date": fmt_fecha(b.trip.departure_time.date()),
        "driver": nombre_de(b.trip.driver),
        "price": fmt_precio(b.trip.price),
        "rating": f"{b.rating:.1f}" if b.rating else "—",
    } for b in bookings]
    return vista("historial", "historial", "Historial", historial=datos)


# ------------------------------------------------------------------ Chat
def _reserva_chat(booking_id, user):
    """Reserva del pasajero con chat habilitado (solo reservas aceptadas)."""
    return Booking.query.filter_by(id=booking_id, passenger_id=user.id, status=ACEPTADA).first_or_404()


def _mensaje_dict(m, user):
    return {"id": m.id, "mine": m.sender_id == user.id, "text": m.text,
            "time": fmt_hora(m.created_at)}


@passenger_bp.route("/mensajes")
@login_required
def mensajes():
    user = usuario_actual()
    bookings = (Booking.query.join(Trip)
                .filter(Booking.passenger_id == user.id, Booking.status == ACEPTADA)
                .order_by(Trip.departure_time).all())

    conversaciones = []
    for b in bookings:
        nombre = nombre_de(b.trip.driver)
        ultimo = b.messages.order_by(Message.id.desc()).first()
        conversaciones.append({
            "id": b.id, "name": nombre, "initials": iniciales_de(nombre),
            "preview": (ultimo.text[:30] + "…") if ultimo and len(ultimo.text) > 30
            else (ultimo.text if ultimo else "Sin mensajes aún"),
        })

    # Conversación abierta: ?reserva=<id> o la primera
    elegida = request.args.get("reserva", type=int) or (conversaciones[0]["id"] if conversaciones else None)
    chat = []
    if elegida and any(c["id"] == elegida for c in conversaciones):
        b = _reserva_chat(elegida, user)
        chat = [_mensaje_dict(m, user) for m in b.messages.order_by(Message.id).all()]
    else:
        elegida = None

    return vista("mensajes", "mensajes", "Mensajes",
                 conversaciones=conversaciones, mensajes=chat, reserva_activa=elegida)


@passenger_bp.route("/api/conversaciones/<int:booking_id>/mensajes", methods=["GET", "POST"])
@login_required
def api_mensajes(booking_id):
    user = usuario_actual()
    b = _reserva_chat(booking_id, user)

    if request.method == "POST":
        data = request.get_json(silent=True) or {}
        texto = (data.get("text") or "").strip()
        if not texto or len(texto) > 500:
            return jsonify(error="El mensaje debe tener entre 1 y 500 caracteres."), 400
        m = Message(booking_id=b.id, sender_id=user.id, text=texto)
        db.session.add(m)
        db.session.commit()
        return jsonify(_mensaje_dict(m, user)), 201

    desde = request.args.get("desde", 0, type=int)
    msgs = b.messages.filter(Message.id > desde).order_by(Message.id).all()
    return jsonify([_mensaje_dict(m, user) for m in msgs])
