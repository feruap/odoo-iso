/** @odoo-module **/
import { Component } from "@odoo/owl";
import { registry } from "@web/core/registry";
import { useService } from "@web/core/utils/hooks";

class PruebasRapidasHub extends Component {
    static template = "amunet_documentos.PruebasRapidasHub";

    setup() {
        this.actionService = useService("action");
    }

    openAction(xmlId) {
        this.actionService.doAction(xmlId);
    }
}

registry.category("actions").add("amunet_documentos.pruebas_rapidas_hub", PruebasRapidasHub);
