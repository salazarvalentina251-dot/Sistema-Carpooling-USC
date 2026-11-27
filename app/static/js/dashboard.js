/* =========================================
   PANEL DEL CONDUCTOR - JavaScript general
========================================= */

(function () {
    "use strict";

    var SELECTOR_MENUS = "details.role-menu, details.notif-menu";

    // Cierra todos los menús desplegables (perfil y notificaciones)
    function cerrarMenus(excepto) {
        document.querySelectorAll(SELECTOR_MENUS).forEach(function (menu) {
            if (menu !== excepto) {
                menu.removeAttribute("open");
            }
        });
    }

    // Al abrir un menú, se cierra el otro
    document.querySelectorAll(SELECTOR_MENUS).forEach(function (menu) {
        menu.addEventListener("toggle", function () {
            if (menu.open) {
                cerrarMenus(menu);
            }
        });
    });

    // Clic fuera de un menú: se cierra
    document.addEventListener("click", function (evento) {
        document.querySelectorAll(SELECTOR_MENUS).forEach(function (menu) {
            if (!menu.contains(evento.target)) {
                menu.removeAttribute("open");
            }
        });
    });

    // Tecla Escape: se cierran
    document.addEventListener("keydown", function (evento) {
        if (evento.key === "Escape") {
            cerrarMenus(null);
        }
    });

    // Mensajes: mostrar siempre el último mensaje de la conversación
    var mensajes = document.querySelector("[data-chat-messages]");

    if (mensajes) {
        mensajes.scrollTop = mensajes.scrollHeight;
    }
})();