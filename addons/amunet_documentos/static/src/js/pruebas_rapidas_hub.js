/** @odoo-module **/
import { Component } from "@odoo/owl";
import { useService } from "@web/core/utils/hooks";
import { registry } from "@web/core/registry";

class PruebasRapidasHub extends Component {
    static template = "amunet_documentos.PruebasRapidasHub";

    setup() {
        this.actionService = useService("action");
    }

    abrirConRS() {
        this.actionService.doAction("amunet_documentos.action_prueba_rapida_con_rs");
    }

    abrirSinRS() {
        this.actionService.doAction("amunet_documentos.action_prueba_rapida_sin_rs");
    }
}

registry.category("actions").add("amunet_documentos.pruebas_rapidas_hub", PruebasRapidasHub);
