/** @odoo-module **/ /* v2 */
import { Component, onWillStart, useState } from "@odoo/owl";
import { registry } from "@web/core/registry";
import { useService } from "@web/core/utils/hooks";
import { user } from "@web/core/user";

class ListaMaestraHub extends Component {
    static template = "amunet_documentos.ListaMaestraHub";

    setup() {
        this.actionService = useService("action");
        this.state = useState({ isPruebaRapidaEditor: false, isManager: false });
        onWillStart(async () => {
            [this.state.isPruebaRapidaEditor, this.state.isManager] = await Promise.all([
                user.hasGroup("amunet_documentos.group_prueba_rapida_editor"),
                user.hasGroup("amunet_documentos.group_documentos_manager"),
            ]);
        });
    }

    openAction(xmlId) {
        this.actionService.doAction(xmlId);
    }
}

registry.category("actions").add("amunet_documentos.lista_maestra_hub", ListaMaestraHub);
