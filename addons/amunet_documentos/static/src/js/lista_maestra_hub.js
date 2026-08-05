/** @odoo-module **/
import { Component } from "@odoo/owl";
import { registry } from "@web/core/registry";
import { useService } from "@web/core/utils/hooks";

class ListaMaestraHub extends Component {
    static template = "amunet_documentos.ListaMaestraHub";

    setup() {
        this.actionService = useService("action");
    }

    openAction(xmlId) {
        this.actionService.doAction(xmlId);
    }
}

registry.category("actions").add("amunet_documentos.lista_maestra_hub", ListaMaestraHub);
