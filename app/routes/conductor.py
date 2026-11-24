from datetime import date, datetime, timedelta
from app.routes.carpooling import Trip, Booking, Message
from app.services.conductor_service import responder_reserva
from flask import (
    Blueprint,
    current_app,
    render_template,
    request,
    session,
    redirect,
    url_for,
    flash,
)


# Blueprint del panel del conductor. Todas sus rutas empiezan por /conductor
conductor_bp = Blueprint("conductor", __name__, url_prefix="/conductor")


# =========================================
# PERFILES (ROLES)
# =========================================

ROLES = [
    ("pasajero", "Pasajero"),
    ("conductor", "Conductor"),
    ("administrador", "Administrador"),
]

# A qué página lleva cada perfil al elegirlo en el desplegable.
# El valor es el nombre de la ruta ("blueprint.función"). Si esa ruta no
# existe en la aplicación, se muestra el aviso "estará disponible pronto".
DESTINO_POR_ROL = {
    "conductor": "conductor.inicio",
    "pasajero": "passenger.inicio",
    "administrador": "administrador.inicio",
}

MAX_PARADAS = 4
APORTE_MAXIMO = 50000


# =========================================
# FILTROS PARA LAS PLANTILLAS
# =========================================

@conductor_bp.app_template_filter("pesos")
def filtro_pesos(valor):
    """5500 -> $5.500"""
    return "$" + "{:,.0f}".format(valor).replace(",", ".")


@conductor_bp.app_template_filter("iniciales")
def filtro_iniciales(nombre):
    """'Sofía Ortiz' -> 'SO'"""
    partes = (nombre or "").split()
    if not partes:
        return "?"
    if len(partes) == 1:
        return partes[0][:2].upper()
    return (partes[0][0] + partes[1][0]).upper()


@conductor_bp.app_template_filter("cuando")
def filtro_cuando(momento):
    """datetime -> 'Hoy · 7:10 a. m.' / 'Mañana · ...' / '24 nov. · ...'"""
    meses = ["ene.", "feb.", "mar.", "abr.", "may.", "jun.",
             "jul.", "ago.", "sep.", "oct.", "nov.", "dic."]
    hora = momento.hour % 12 or 12
    sufijo = "a. m." if momento.hour < 12 else "p. m."
    texto_hora = f"{hora}:{momento.minute:02d} {sufijo}"

    dia = momento.date()
    if dia == date.today():
        return f"Hoy · {texto_hora}"
    if dia == date.today() + timedelta(days=1):
        return f"Mañana · {texto_hora}"
    return f"{dia.day} {meses[dia.month - 1]} · {texto_hora}"


# =========================================
# FUNCIONES AUXILIARES
# =========================================

def requiere_sesion():
    """Redirige al login si no hay sesión iniciada; si la hay, devuelve None."""
    if "user_id" not in session:
        flash("Inicia sesión para continuar.", "error")
        return redirect(url_for("auth.login"))
    return None


def fecha_valida(texto):
    try:
        return datetime.strptime(texto, "%Y-%m-%d").date()
    except (TypeError, ValueError):
        return None


# =========================================================
# CONSULTAS DE DATOS
# ---------------------------------------------------------
# Hoy devuelven datos de EJEMPLO. TODO (backend): reemplazar
# el contenido de cada función por consultas reales a la base
# de datos (app/repositories). Las plantillas solo usan los
# campos que aparecen aquí: basta con respetar los nombres.
# =========================================================

def consultar_vehiculos():
    hoy = date.today()
    vehiculos = [
        {
            "id": 1,
            "marca_modelo": "Mazda 3",
            "color": "Gris",
            "placa_visible": "KLM 248",
            "capacidad": 4,
            "soat_vence": hoy + timedelta(days=400),
            "tecnomecanica_vence": hoy + timedelta(days=250),
        },
    ]
    for v in vehiculos:
        v["soat_vencido"] = v["soat_vence"] < hoy
        v["tecnomecanica_vencida"] = v["tecnomecanica_vence"] < hoy
        v["habilitado"] = not (v["soat_vencido"] or v["tecnomecanica_vencida"])
    return vehiculos


def consultar_solicitudes_pendientes():
    conductor_id = session.get("user_id")

    if not conductor_id:
        return []

    viaje = Trip.query.filter(
        Trip.driver_id == conductor_id,
        Trip.status == "ABIERTO",
        Trip.departure_time > datetime.now()
    ).order_by(Trip.departure_time, Trip.id).first()

    if not viaje:
        return []

    reservas = Booking.query.filter_by(
        trip_id=viaje.id,
        status="PENDIENTE"
    ).order_by(Booking.created_at).all()

    return [
        {
            "id": reserva.id,
            "pasajero": reserva.passenger.name,
            "calificacion": 0.0,
            "puestos": 1,
            "zona": "No registrada",
            "verificado": False
        }
        for reserva in reservas
    ]



def consultar_proximo_viaje():
    conductor_id = session.get("user_id")

    if not conductor_id:
        return None

    viaje = Trip.query.filter(
        Trip.driver_id == conductor_id,
        Trip.status == "ABIERTO",
        Trip.departure_time > datetime.now()
    ).order_by(Trip.departure_time, Trip.id).first()

    if not viaje:
        return None

    return {
        "estado": viaje.status.capitalize(),
        "origen": viaje.origin,
        "destino": viaje.destination,
        "salida": viaje.departure_time,
        "vehiculo": "No registrado",
        "placa": "No registrada",
        "confirmados": viaje.seats_total - viaje.seats_available,
        "disponibles": viaje.seats_available,
        "aporte": viaje.price
    }

def consultar_historial():
    conductor_id = session.get("user_id")

    if not conductor_id:
        return []

    reservas = Booking.query.join(Trip).filter(
        Trip.driver_id == conductor_id,
        Booking.status == "COMPLETADA"
    ).order_by(Trip.departure_time.desc()).all()

    return [
        {
            "origen": reserva.trip.origin,
            "destino": reserva.trip.destination,
            "fecha": reserva.trip.departure_time.strftime("%d/%m/%Y"),
            "pasajero": reserva.passenger.name,
            "aporte": reserva.trip.price,
            "calificacion": reserva.rating or 0.0,
            "estado": "Completado"
        }
        for reserva in reservas
    ]


def consultar_conversaciones():
    conductor_id = session.get("user_id")

    if not conductor_id:
        return []

    reservas = Booking.query.join(Trip).filter(
        Trip.driver_id == conductor_id,
        Booking.status == "ACEPTADA"
    ).order_by(Booking.id.desc()).all()

    conversaciones = []

    for reserva in reservas:
        mensajes = [
            {
                "propio": mensaje.sender_id == conductor_id,
                "texto": mensaje.text
            }
            for mensaje in reserva.messages.order_by(
                Message.id
            ).all()
        ]

        conversaciones.append({
            "id": reserva.id,
            "nombre": reserva.passenger.name,
            "en_linea": False,
            "mensajes": mensajes,
            "ultimo": mensajes[-1]["texto"] if mensajes else "Sin mensajes"
        })

    return conversaciones


# =========================================
# DATOS PARA TODAS LAS PÁGINAS DEL CONDUCTOR
# =========================================

@conductor_bp.context_processor
def datos_comunes():
    nombre = session.get("user_name", "Conductor")

    # TODO (backend): leer el último rol usado desde el modelo User
    rol_actual = session.get("rol", "conductor")

    return {
        "usuario": {
            "nombre": nombre,
            "iniciales": filtro_iniciales(nombre),
            "rol": dict(ROLES).get(rol_actual, "Conductor"),
        },
        "roles": ROLES,
        "rol_actual": rol_actual,
        "solicitudes_pendientes": len(consultar_solicitudes_pendientes()),
    }


# =========================================
# CAMBIAR DE PERFIL
# =========================================

@conductor_bp.route("/cambiar-perfil", methods=["POST"])
def cambiar_perfil():
    redireccion = requiere_sesion()
    if redireccion:
        return redireccion

    rol = request.form.get("rol", "")

    if rol not in dict(ROLES):
        flash("Perfil no válido.", "error")
        return redirect(url_for("conductor.inicio"))

    destino = DESTINO_POR_ROL.get(rol)

    # La ruta de destino solo se usa si existe en la aplicación
    if destino not in current_app.view_functions:
        flash(f"La vista de {dict(ROLES)[rol].lower()} estará disponible pronto.", "info")
        return redirect(url_for("conductor.inicio"))

    # TODO (backend): guardar el rol como "último rol usado" en User
    session["rol"] = rol
    return redirect(url_for(destino))


# =========================================
# INICIO
# =========================================

@conductor_bp.route("/inicio")
def inicio():
    redireccion = requiere_sesion()
    if redireccion:
        return redireccion

    solicitudes = consultar_solicitudes_pendientes()

    conductor_id = session["user_id"]
    ahora = datetime.now()

    viajes = Trip.query.filter_by(
        driver_id=conductor_id
    ).all()

    proximos = [
        v for v in viajes
        if v.status == "ABIERTO"
        and v.departure_time > ahora
    ]

    opiniones = Booking.query.join(Trip).filter(
        Trip.driver_id == conductor_id,
        Booking.status == "COMPLETADA",
        Booking.rating.isnot(None)
    ).all()

    estadisticas = {
        "viajes_publicados": len(viajes),
        "viajes_este_mes": sum(
            1 for v in viajes
            if v.departure_time.month == ahora.month
            and v.departure_time.year == ahora.year
        ),
        "solicitudes_pendientes": len(solicitudes),
        "puestos_disponibles": sum(
            v.seats_available for v in proximos
        ),
        "proximos_viajes": len(proximos),
        "calificacion": (
            sum(r.rating for r in opiniones) / len(opiniones)
            if opiniones else 0.0
        ),
        "opiniones": len(opiniones)
    }

    return render_template(
        "conductor/inicio.html",
        estadisticas=estadisticas,
        proximo_viaje=consultar_proximo_viaje(),
        solicitudes_recientes=solicitudes[:3],
    )


# =========================================
# PUBLICAR VIAJE
# =========================================

@conductor_bp.route("/publicar", methods=["GET", "POST"])
def publicar_viaje():
    redireccion = requiere_sesion()
    if redireccion:
        return redireccion

    vehiculos = []  # Pendiente de integracion
    datos, errores = {}, []

    if request.method == "POST":
        datos = request.form.to_dict()
        paradas = [p.strip() for p in request.form.getlist("paradas") if p.strip()]
        datos["paradas"] = paradas

        origen = datos.get("origen", "").strip()
        destino = datos.get("destino", "").strip()
        texto_ruta = (origen + " " + destino).lower()

        if not origen or not destino:
            errores.append("Indica el origen y el destino.")
        elif not any(p in texto_ruta for p in ("usc", "campus", "santiago de cali")):
            errores.append("El origen o el destino debe ser el Campus USC.")

        fecha = fecha_valida(datos.get("fecha"))
        if not fecha or fecha < date.today():
            errores.append("Elige una fecha válida (hoy o posterior).")
        if not datos.get("hora"):
            errores.append("Indica la hora de salida.")

        vehiculo = next((v for v in vehiculos if str(v["id"]) == datos.get("vehiculo_id")), None)
        if not vehiculo:
            errores.append("Selecciona un vehículo.")
        elif not vehiculo["habilitado"]:
            errores.append("Ese vehículo tiene documentos vencidos.")

        puestos = datos.get("puestos", "")
        if not puestos.isdigit() or int(puestos) < 1 or (vehiculo and int(puestos) > vehiculo["capacidad"]):
            errores.append("Los puestos deben estar entre 1 y la capacidad del vehículo.")

        if len(paradas) > MAX_PARADAS:
            errores.append(f"Máximo {MAX_PARADAS} paradas.")

        aporte = datos.get("aporte", "")
        if not aporte.isdigit() or int(aporte) > APORTE_MAXIMO:
            errores.append(f"El aporte debe ser un valor entre 0 y {APORTE_MAXIMO}.")

        if not errores:
            from app.services.conductor_service import guardar_viaje
            from sqlalchemy.exc import SQLAlchemyError

            try:
                salida = datetime.fromisoformat(
                    datos["fecha"] + "T" + datos["hora"]
                )

                guardar_viaje(
                    session["user_id"],
                    origen,
                    destino,
                    salida,
                    int(puestos),
                    int(aporte),
                    vehiculo["id"],
                    paradas
                )

            except ValueError as error:
                errores.append(str(error))

            except SQLAlchemyError:
                current_app.logger.exception("Error al publicar viaje")
                errores.append("No se pudo guardar el viaje.")

            else:
                flash("Viaje publicado correctamente.", "success")
                return redirect(url_for("conductor.inicio"))

    return render_template(
        "conductor/publicar.html",
        vehiculos=vehiculos,
        datos=datos,
        errores=errores,
        paradas=datos.get("paradas", []),
        hoy=date.today().isoformat(),
        max_paradas=MAX_PARADAS,
        aporte_maximo=APORTE_MAXIMO,
    )


# =========================================
# MIS VEHÍCULOS
# =========================================

@conductor_bp.route("/vehiculos")
def vehiculos():
    redireccion = requiere_sesion()
    if redireccion:
        return redireccion

    return render_template("conductor/vehiculos.html", vehiculos=consultar_vehiculos())


@conductor_bp.route("/vehiculos/nuevo", methods=["GET", "POST"])
def vehiculo_nuevo():
    redireccion = requiere_sesion()
    if redireccion:
        return redireccion

    datos, errores = {}, []

    if request.method == "POST":
        datos = request.form.to_dict()

        for campo in ("marca_modelo", "color", "placa", "capacidad", "soat_vence", "tecnomecanica_vence"):
            if not datos.get(campo, "").strip():
                errores.append("Completa todos los campos.")
                break

        if not errores:
            if not fecha_valida(datos["soat_vence"]) or not fecha_valida(datos["tecnomecanica_vence"]):
                errores.append("Las fechas de vencimiento no son válidas.")
            if not datos["capacidad"].isdigit() or not 1 <= int(datos["capacidad"]) <= 8:
                errores.append("La capacidad debe estar entre 1 y 8 pasajeros.")

        if not errores:
            # TODO (backend): guardar el vehículo asociado al usuario en sesión
            flash("Vehículo registrado correctamente.", "success")
            return redirect(url_for("conductor.vehiculos"))

    return render_template("conductor/vehiculo_nuevo.html", datos=datos, errores=errores)


# =========================================
# SOLICITUDES DE PASAJEROS
# =========================================

@conductor_bp.route("/solicitudes")
def solicitudes():
    redireccion = requiere_sesion()
    if redireccion:
        return redireccion

    return render_template(
        "conductor/solicitudes.html",
        solicitudes=consultar_solicitudes_pendientes(),
        viaje=consultar_proximo_viaje(),
    )


@conductor_bp.route("/solicitudes/<int:solicitud_id>", methods=["POST"])
def responder_solicitud(solicitud_id):
    redireccion = requiere_sesion()
    if redireccion:
        return redireccion

    accion = request.form.get("accion")

    exito, mensaje = responder_reserva(
        session["user_id"],
        solicitud_id,
        accion
    )

    flash(mensaje, "success" if exito else "error")
    return redirect(url_for("conductor.solicitudes"))

# =========================================
# HISTORIAL
# =========================================

@conductor_bp.route("/historial")
def historial():
    redireccion = requiere_sesion()
    if redireccion:
        return redireccion

    return render_template("conductor/historial.html", viajes=consultar_historial())


# =========================================
# MENSAJES
# =========================================

@conductor_bp.route("/mensajes")
def mensajes():
    redireccion = requiere_sesion()
    if redireccion:
        return redireccion

    conversaciones = consultar_conversaciones()
    seleccionada = request.args.get("con", type=int)
    activa = next((c for c in conversaciones if c["id"] == seleccionada), None)
    if activa is None and conversaciones:
        activa = conversaciones[0]

    return render_template("conductor/mensajes.html", conversaciones=conversaciones, activa=activa)


@conductor_bp.route("/mensajes/enviar", methods=["POST"])
def enviar_mensaje():
    from app.extensions import db
    from sqlalchemy.exc import SQLAlchemyError

    redireccion = requiere_sesion()
    if redireccion:
        return redireccion

    conductor_id = session["user_id"]
    conversacion_id = request.form.get("conversacion_id", type=int)
    texto = request.form.get("texto", "").strip()

    reserva = Booking.query.join(Trip).filter(
        Booking.id == conversacion_id,
        Trip.driver_id == conductor_id,
        Booking.status == "ACEPTADA"
    ).first()

    if not reserva:
        flash("Conversación no autorizada.", "error")
        return redirect(url_for("conductor.mensajes"))

    if not texto or len(texto) > 500:
        flash("Escribe un mensaje de 1 a 500 caracteres.", "error")
        return redirect(url_for(
            "conductor.mensajes", con=conversacion_id
        ))

    try:
        mensaje = Message(
            booking_id=reserva.id,
            sender_id=conductor_id,
            text=texto
        )

        db.session.add(mensaje)
        db.session.commit()

    except SQLAlchemyError:
        db.session.rollback()
        current_app.logger.exception("Error al guardar mensaje")
        flash("No se pudo enviar el mensaje.", "error")

    return redirect(url_for(
        "conductor.mensajes", con=conversacion_id
    ))
# =========================================
# CERRAR SESIÓN
# =========================================

@conductor_bp.route("/cerrar-sesion", methods=["POST"])
def cerrar_sesion():
    session.clear()
    flash("Has cerrado sesión.", "success")
    return redirect(url_for("auth.login"))