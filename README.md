#  Carpooling USC – Sistema de Carpooling Universitario

##  Sobre el proyecto

Actualmente estamos desarrollando **Carpooling USC**, una plataforma web de movilidad colaborativa dirigida a la comunidad universitaria de la Universidad Santiago de Cali (USC).

Este proyecto nace como una propuesta para dar solución a algunas de las dificultades de movilidad que enfrentan diariamente los estudiantes, docentes y personal administrativo, como la congestión vehicular, los largos tiempos de desplazamiento y los costos del transporte.

La plataforma busca conectar a los integrantes de la universidad que cuentan con un vehículo y desean compartir sus recorridos con otras personas que se dirigen hacia la misma zona o hacia la institución.

De esta manera, buscamos aprovechar mejor los vehículos particulares, facilitar los desplazamientos, reducir los gastos de transporte y promover una cultura de colaboración dentro de la comunidad universitaria.

## Objetivo del proyecto

Desarrollar un sistema web que permita a los integrantes de la Universidad Santiago de Cali compartir viajes de manera organizada, facilitando la conexión entre conductores y pasajeros mediante la publicación, consulta y solicitud de recorridos.

##  Tecnologías utilizadas

- **Python:** lenguaje de programación.
- **Flask:** framework para el desarrollo de la aplicación web.
- **HTML5:** estructura de las páginas.
- **CSS3:** diseño y estilos de la interfaz.
- **SQLite:** sistema de base de datos.
- **Flask-SQLAlchemy:** gestión de la comunicación con la base de datos.
- **Git y GitHub:** control de versiones y trabajo colaborativo.

## 📂 Estructura del proyecto

El proyecto está organizado mediante una estructura modular que separa las responsabilidades de la aplicación:

- `app/config`: configuración del proyecto.
- `app/models`: modelos de datos.
- `app/repositories`: acceso y gestión de datos.
- `app/routes`: rutas y control de solicitudes.
- `app/services`: lógica de negocio.
- `app/templates`: plantillas HTML.
- `app/static`: archivos CSS, imágenes y recursos estáticos.
- `migrations`: migraciones de la base de datos.
- `tests`: pruebas del proyecto.

---

## Instalación y configuración del proyecto

Para ejecutar Carpooling USC en tu computador, sigue estos pasos:

### 1. Requisitos previos

Antes de comenzar, debes tener instalado:

- Python 3.14 o compatible con las dependencias del proyecto.
- Visual Studio Code.
- Git.

### 2. Clonar el repositorio

Abre una terminal y ejecuta:

```bash
git clone https://github.com/salazarvalentina251-dot/Sistema-Carpooling-USC.git
```

Ingresa a la carpeta del proyecto:

```bash
cd Sistema-Carpooling-USC
```

### 3. Crear el entorno virtual

```bash
python -m venv venv
```

Activar el entorno virtual en Windows PowerShell:

```powershell
.\venv\Scripts\Activate.ps1
```

### 4. Instalar las dependencias

Con el entorno virtual activado, ejecuta:

```bash
python -m pip install -r requirements.txt
```

Este comando instala automáticamente las librerías necesarias para ejecutar el proyecto.

### 5. Configurar las variables de entorno

Verifica que exista el archivo `.env` y configura las variables necesarias si el proyecto las requiere. No compartas claves secretas ni contraseñas personales.

### 6. Ejecutar la aplicación

Desde la terminal, ejecuta:

```bash
python run.py
```

Abre el navegador e ingresa a:

http://127.0.0.1:5000

---

## Base de datos

Carpooling USC utiliza **SQLite** como sistema de gestión de base de datos.

El archivo de base de datos se llama:

```text
carpooling.db
```

Este archivo se genera localmente al iniciar la aplicación con la configuración actual de Flask-SQLAlchemy.

### Visualizar la base de datos desde Visual Studio Code

Para consultar las tablas y los registros de SQLite:

1. Abre Visual Studio Code.
2. Ingresa a la sección de extensiones.
3. Busca **SQLite Viewer**.
4. Instala la extensión.
5. Abre el archivo `carpooling.db`.
6. Utiliza el visor para explorar las tablas y los registros almacenados.

**Importante:** cada integrante debe generar su propia base de datos local al ejecutar el proyecto. El archivo `carpooling.db` no necesita compartirse en el repositorio.

---



**Proyecto:** Sistema de Carpooling Universitario USC.

