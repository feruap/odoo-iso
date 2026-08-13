/** @odoo-module **/
import { Component } from "@odoo/owl";
import { registry } from "@web/core/registry";
import { useService } from "@web/core/utils/hooks";

class RegistrosHub extends Component {
    static template = "amunet_registros.RegistrosHub";

    setup() {
        this.actionService = useService("action");
    }

    openAction(xmlId) {
        this.actionService.doAction(xmlId);
    }
}

registry.category("actions").add("amunet_registros.registros_hub", RegistrosHub);
