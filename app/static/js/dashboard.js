/* =========================================
   PANEL DEL CONDUCTOR - JavaScript general
========================================= */

(function () {
    "use strict";

    // Menú de perfil: se cierra al hacer clic fuera o al presionar Escape
    function cerrarMenus() {
        document.querySelectorAll("details.role-menu[open]").forEach(function (menu) {
            menu.removeAttribute("open");
        });
    }

    document.addEventListener("click", function (evento) {
        document.querySelectorAll("details.role-menu[open]").forEach(function (menu) {
            if (!menu.contains(evento.target)) {
                menu.removeAttribute("open");
            }
        });
    });

    document.addEventListener("keydown", function (evento) {
        if (evento.key === "Escape") {
            cerrarMenus();
        }
    });

    // Mensajes: mostrar siempre el último mensaje de la conversación
    var mensajes = document.querySelector("[data-chat-messages]");

    if (mensajes) {
        mensajes.scrollTop = mensajes.scrollHeight;
    }
})();