/** @odoo-module **/
import { Component, onWillStart, useState } from "@odoo/owl";
import { registry } from "@web/core/registry";
import { useService } from "@web/core/utils/hooks";

class VigenciasHub extends Component {
    static template = "amunet_vencimientos.VigenciasHub";
    static props = ["*"];

    setup() {
        this.actionService = useService("action");
        this.orm = useService("orm");

        this.state = useState({
            loading: true,
            por_vencer: 0,
            vencidos: 0,
        });

        onWillStart(() => this._cargarConteos());
    }

    async _cargarConteos() {
        try {
            const [por_vencer, vencidos] = await Promise.all([
                this.orm.searchCount("amunet.vencimiento", [["estado", "=", "por_vencer"]]),
                this.orm.searchCount("amunet.vencimiento", [["estado", "=", "vencido"]]),
            ]);
            Object.assign(this.state, { por_vencer, vencidos, loading: false });
        } catch (e) {
            console.error("Error al cargar conteos de vigencias:", e);
            Object.assign(this.state, { loading: false });
        }
    }

    openAction(xmlId) {
        this.actionService.doAction(xmlId);
    }
}

registry.category("actions").add("amunet_vencimientos_hub", VigenciasHub);
