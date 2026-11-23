from flask import Blueprint, render_template

passenger_bp = Blueprint("passenger", __name__, url_prefix="/pasajero")

# Datos de ejemplo. Cuando el backend esté listo, reemplazar por datos reales
# (por ejemplo, el usuario logueado y consultas a la base de datos).
USUARIO = {"name": "Sofía Ortiz", "first_name": "Sofía", "initials": "SO"}


def vista(template, active, titulo, **datos):
    return render_template(
        f"passenger/{template}.html",
        active=active, page_title=titulo, user=USUARIO, **datos
    )


@passenger_bp.route("/inicio")
def inicio():
    viajes = [
        {"driver": "Laura Mejía", "initials": "LM", "color": "green", "rating": "4.9",
         "price": "$5.500", "route": "Ciudad Jardín → USC", "time": "7:10 a. m.", "seats": "2 puestos"},
        {"driver": "Diego Arango", "initials": "DA", "color": "slate", "rating": "4.8",
         "price": "$4.800", "route": "Valle del Lili → USC", "time": "7:25 a. m.", "seats": "1 puesto"},
    ]
    return vista("inicio", "inicio", "Inicio", viajes=viajes, rutas_hoy=128)


@passenger_bp.route("/buscar")
def buscar():
    # Pantalla pendiente: aún no hay diseño de "Buscar viajes".
    return vista("inicio", "buscar", "Buscar viajes", viajes=[], rutas_hoy=128)


@passenger_bp.route("/reservas")
def reservas():
    datos = [
        {"estado": "ACEPTADA", "group": "proximas", "price": "$5.500",
         "route": "Ciudad Jardín → Campus USC", "when": "Hoy · 7:10 a. m.", "driver": "Laura Mejía"},
        {"estado": "PENDIENTE", "group": "pendientes", "price": "$4.800",
         "route": "Valle del Lili → Campus USC", "when": "Mañana · 7:25 a. m.", "driver": "Diego Arango"},
    ]
    conteo = {"proximas": 2, "pendientes": 1, "completadas": 8}
    return vista("reservas", "reservas", "Mis reservas", reservas=datos, conteo=conteo)


@passenger_bp.route("/historial")
def historial():
    datos = [
        {"route": "Campus USC → Ciudad Jardín", "date": "10 may.", "driver": "Laura Mejía", "price": "$5.500", "rating": "5.0"},
        {"route": "Valle del Lili → Campus USC", "date": "8 may.", "driver": "Carlos Restrepo", "price": "$4.800", "rating": "4.8"},
        {"route": "Campus USC → San Fernando", "date": "3 may.", "driver": "Ana Lucía Pérez", "price": "$4.200", "rating": "5.0"},
    ]
    return vista("historial", "historial", "Historial", historial=datos)


@passenger_bp.route("/mensajes")
def mensajes():
    conversaciones = [
        {"name": "Laura Mejía", "initials": "LM", "preview": "Te espera en la portería..."},
        {"name": "Diego Arango", "initials": "DA", "preview": "Gracias, nos vemos mañana"},
    ]
    chat = [
        {"mine": False, "text": "Hola Sofía, te recojo en la entrada de Ciudad Jardín."},
        {"mine": True, "text": "Perfecto, estaré allí a las 7:05. Gracias."},
    ]
    return vista("mensajes", "mensajes", "Mensajes", conversaciones=conversaciones, mensajes=chat)
