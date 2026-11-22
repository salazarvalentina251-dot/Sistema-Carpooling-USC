
from flask import Blueprint, render_template, request, redirect, url_for, flash, session

from app.extensions import db
from app.models.user import User

from werkzeug.security import generate_password_hash, check_password_hash


# Crear el Blueprint de autenticación
auth_bp = Blueprint("auth", __name__)


# =========================================
# REGISTRO DE USUARIOS
# =========================================

@auth_bp.route("/register", methods=["GET", "POST"])
def register():

    # Si el usuario envía el formulario
    if request.method == "POST":

        # Obtener los datos del formulario
        name = request.form.get("name", "").strip()
        email = request.form.get("email", "").strip().lower()
        password = request.form.get("password", "")
        confirm_password = request.form.get("confirm_password", "")
        terms = request.form.get("terms")

        # Validar campos obligatorios
        if not name or not email or not password or not confirm_password:
            flash("Todos los campos son obligatorios.", "error")
            return redirect(url_for("auth.register"))

        # Validar aceptación de términos
        if not terms:
            flash("Debes aceptar los términos y condiciones.", "error")
            return redirect(url_for("auth.register"))

        # Validar correo institucional
        if not email.endswith("@usc.edu.co"):
            flash("Debes utilizar un correo institucional USC.", "error")
            return redirect(url_for("auth.register"))

        # Validar coincidencia de contraseñas
        if password != confirm_password:
            flash("Las contraseñas no coinciden.", "error")
            return redirect(url_for("auth.register"))

        # Validar longitud de contraseña
        if len(password) < 8:
            flash("La contraseña debe tener al menos 8 caracteres.", "error")
            return redirect(url_for("auth.register"))

        # Comprobar si el correo ya está registrado
        existing_user = User.query.filter_by(email=email).first()

        if existing_user:
            flash("Este correo ya se encuentra registrado.", "error")
            return redirect(url_for("auth.register"))

        # Proteger la contraseña
        password_hash = generate_password_hash(password)

        # Crear el nuevo usuario
        new_user = User(
            name=name,
            email=email,
            password_hash=password_hash
        )

        try:
            # Guardar el usuario en la base de datos
            db.session.add(new_user)
            db.session.commit()

            flash("¡Tu cuenta ha sido creada correctamente!", "success")

            return redirect(url_for("auth.login"))

        except Exception:
            db.session.rollback()
            flash("Ocurrió un error al crear tu cuenta.", "error")
            return redirect(url_for("auth.register"))

    # Si es una petición GET, mostrar el formulario
    return render_template("auth/register.html")



# =========================================
# INICIO DE SESIÓN
# =========================================

@auth_bp.route("/login", methods=["GET", "POST"])
def login():

    # Si el usuario envía el formulario
    if request.method == "POST":

        # Obtener los datos del formulario
        email = request.form.get("email", "").strip().lower()
        password = request.form.get("password", "")

        # Buscar el usuario por su correo
        user = User.query.filter_by(email=email).first()

        # Comprobar si existe y si la contraseña es correcta
        if user and check_password_hash(user.password_hash, password):

            # Comprobar si la cuenta está activa
            if not user.is_active:
                flash("Tu cuenta se encuentra desactivada.", "error")
                return redirect(url_for("auth.login"))

            # Limpiar la sesión anterior
            session.clear()

            # Guardar los datos necesarios en la sesión
            session["user_id"] = user.id
            session["user_name"] = user.name

            # Recordar la sesión si el usuario marcó la casilla
            session.permanent = request.form.get("recordarme") == "on"

            # Redirigir a la página principal
            return redirect(url_for("home"))

        else:
            flash("Correo o contraseña incorrectos.", "error")
            return redirect(url_for("auth.login"))

    # Si es GET, mostrar el formulario
    return render_template("auth/login.html")

