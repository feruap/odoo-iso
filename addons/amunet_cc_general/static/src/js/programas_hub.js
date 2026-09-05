/** @odoo-module **/
import { Component } from "@odoo/owl";
import { registry } from "@web/core/registry";
import { useService } from "@web/core/utils/hooks";

class ProgramasHub extends Component {
    static template = "amunet_cc_general.ProgramasHub";
    static props = ["*"];

    setup() {
        this.actionService = useService("action");
    }

    abrirAccionXml(xmlId) {
        this.actionService.doAction(xmlId);
    }
}

registry.category("actions").add("amunet_programas_hub", ProgramasHub);
