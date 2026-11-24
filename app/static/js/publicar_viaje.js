/* =========================================
   PUBLICAR VIAJE - formulario de 5 pasos

   Muestra un paso a la vez, valida cada paso antes de avanzar,
   maneja las paradas dinámicas y arma el resumen final.
   Si este archivo no carga, el formulario sigue funcionando completo
   (el servidor valida todo igualmente).
========================================= */

(function () {
    "use strict";

    var form = document.getElementById("form-viaje");

    if (!form) {
        return;
    }

    var pasos = Array.prototype.slice.call(form.querySelectorAll(".wizard-step"));
    var indicadores = Array.prototype.slice.call(document.querySelectorAll("[data-step-indicator]"));
    var btnAnterior = form.querySelector("[data-prev]");
    var btnSiguiente = form.querySelector("[data-next]");
    var btnPublicar = form.querySelector("[data-submit]");

    var listaParadas = document.getElementById("lista-paradas");
    var plantillaParada = document.getElementById("plantilla-parada");
    var btnAgregarParada = document.getElementById("agregar-parada");
    var maxParadas = parseInt(listaParadas.getAttribute("data-max"), 10) || 4;

    var selectVehiculo = form.elements["vehiculo_id"];
    var campoPuestos = form.elements["puestos"];

    var REGEX_CAMPUS = /\b(usc|campus)\b|santiago de cali/i;
    var ultimo = pasos.length - 1;
    var actual = 0;


    /* ---------- Validación ---------- */

    function validarRuta() {
        var origen = form.elements["origen"];
        var destino = form.elements["destino"];

        destino.setCustomValidity("");

        if (origen.value.trim() && destino.value.trim() &&
            !REGEX_CAMPUS.test(origen.value) && !REGEX_CAMPUS.test(destino.value)) {
            destino.setCustomValidity("El origen o el destino debe ser el Campus USC.");
        }
    }

    function validarPaso(indice) {
        if (indice === 0) {
            validarRuta();
        }

        var campos = pasos[indice].querySelectorAll("input, select, textarea");

        for (var i = 0; i < campos.length; i++) {
            if (!campos[i].checkValidity()) {
                mostrarPaso(indice);
                campos[i].reportValidity();
                return false;
            }
        }

        return true;
    }


    /* ---------- Navegación entre pasos ---------- */

    function mostrarPaso(indice) {
        actual = indice;

        pasos.forEach(function (paso, i) {
            paso.hidden = i !== indice;
        });

        indicadores.forEach(function (indicador, i) {
            indicador.classList.toggle("is-active", i === indice);
            indicador.classList.toggle("is-done", i < indice);
        });

        btnAnterior.hidden = false;
        btnAnterior.disabled = indice === 0;
        btnSiguiente.hidden = indice === ultimo;
        btnPublicar.hidden = indice !== ultimo;

        if (indice === ultimo) {
            llenarResumen();
        }
    }

    btnSiguiente.addEventListener("click", function () {
        if (validarPaso(actual)) {
            mostrarPaso(actual + 1);
        }
    });

    btnAnterior.addEventListener("click", function () {
        if (actual > 0) {
            mostrarPaso(actual - 1);
        }
    });

    // Enter avanza de paso (no envía el formulario antes de tiempo)
    form.addEventListener("keydown", function (evento) {
        if (evento.key === "Enter" && evento.target.tagName !== "TEXTAREA" && actual < ultimo) {
            evento.preventDefault();
            btnSiguiente.click();
        }
    });

    // Al publicar, se revisan todos los pasos
    form.addEventListener("submit", function (evento) {
        for (var i = 0; i < ultimo; i++) {
            if (!validarPaso(i)) {
                evento.preventDefault();
                return;
            }
        }
    });


    /* ---------- Vehículo: limitar puestos a la capacidad ---------- */

    function ajustarPuestos() {
        var opcion = selectVehiculo.options[selectVehiculo.selectedIndex];
        var capacidad = opcion && opcion.getAttribute("data-capacidad")
            ? parseInt(opcion.getAttribute("data-capacidad"), 10)
            : 8;

        campoPuestos.max = capacidad;

        if (parseInt(campoPuestos.value, 10) > capacidad) {
            campoPuestos.value = capacidad;
        }
    }

    selectVehiculo.addEventListener("change", ajustarPuestos);
    ajustarPuestos();


    /* ---------- Paradas dinámicas ---------- */

    function filasParadas() {
        return listaParadas.querySelectorAll(".stop-row");
    }

    function actualizarBotonParada() {
        btnAgregarParada.hidden = filasParadas().length >= maxParadas;
    }

    btnAgregarParada.addEventListener("click", function () {
        if (filasParadas().length >= maxParadas) {
            return;
        }

        var fila = plantillaParada.content.firstElementChild.cloneNode(true);
        listaParadas.appendChild(fila);
        fila.querySelector("input").focus();
        actualizarBotonParada();
    });

    listaParadas.addEventListener("click", function (evento) {
        var boton = evento.target.closest("[data-quitar-parada]");

        if (!boton) {
            return;
        }

        var fila = boton.closest(".stop-row");

        if (filasParadas().length > 1) {
            fila.remove();
        } else {
            fila.querySelector("input").value = "";
        }

        actualizarBotonParada();
    });

    actualizarBotonParada();


    /* ---------- Resumen final ---------- */

    function valor(nombre) {
        return form.elements[nombre] ? form.elements[nombre].value.trim() : "";
    }

    function poner(clave, texto) {
        var elemento = form.querySelector('[data-resumen="' + clave + '"]');

        if (elemento) {
            elemento.textContent = texto || "—";
        }
    }

    function llenarResumen() {
        var salida = "";

        if (valor("fecha") && valor("hora")) {
            var momento = new Date(valor("fecha") + "T" + valor("hora"));

            salida = momento.toLocaleDateString("es-CO", { weekday: "long", day: "numeric", month: "long" }) +
                ", " + momento.toLocaleTimeString("es-CO", { hour: "numeric", minute: "2-digit" });
        }

        var opcion = selectVehiculo.options[selectVehiculo.selectedIndex];
        var paradas = Array.prototype.map.call(listaParadas.querySelectorAll("input"), function (campo) {
            return campo.value.trim();
        }).filter(Boolean);

        poner("ruta", valor("origen") + " → " + valor("destino"));
        poner("salida", salida);
        poner("vehiculo", selectVehiculo.value ? opcion.textContent.replace(/\s+/g, " ").trim() : "");
        poner("puestos", valor("puestos"));
        poner("paradas", paradas.join(" → "));
        poner("aporte", valor("aporte") !== "" ? "$" + Number(valor("aporte")).toLocaleString("es-CO") : "");
        poner("observaciones", valor("observaciones"));
    }


    /* ---------- Inicio ---------- */

    mostrarPaso(0);
})();