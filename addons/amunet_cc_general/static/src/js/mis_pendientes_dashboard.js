/** @odoo-module **/
import { Component, onWillStart, useState } from "@odoo/owl";
import { registry } from "@web/core/registry";
import { useService } from "@web/core/utils/hooks";
import { user } from "@web/core/user";

class MisPendientesDashboard extends Component {
    static template = "amunet_cc_general.MisPendientesDashboard";
    static props = ["*"];

    setup() {
        this.actionService = useService("action");
        this.orm = useService("orm");

        this.state = useState({
            loading: true,
            corregir: 0,
            revisar: 0,
            autorizar: 0,
            acusar: 0,
            cc_firma: 0,
        });

        onWillStart(() => this._cargarConteos());
    }

    async _cargarConteos() {
        const uid = user.userId;
        try {
            const [corregir, revisar, autorizar, acusar, cc_firma] = await Promise.all([
                this.orm.searchCount("amunet.documento", [
                    ["state", "=", "borrador"], ["elabora_id", "=", uid],
                ]),
                this.orm.searchCount("amunet.documento", [
                    ["state", "=", "en_revision"], ["revisor_id", "=", uid],
                    ["firma_revisa_id", "=", false],
                ]),
                this.orm.searchCount("amunet.documento", [
                    ["state", "=", "en_revision"], ["autorizador_id", "=", uid],
                    ["firma_revisa_id", "!=", false], ["firma_aprueba_id", "=", false],
                ]),
                this.orm.searchCount("amunet.documento.distribucion", [
                    ["usuario_id", "=", uid], ["acuse", "=", false],
                ]),
                this.orm.searchCount("amunet.cc.general", [
                    ["pendientes_para_ids", "in", [uid]],
                ]),
            ]);
            Object.assign(this.state, { corregir, revisar, autorizar, acusar, cc_firma, loading: false });
        } catch (e) {
            console.error("Error al cargar pendientes:", e);
            Object.assign(this.state, { loading: false });
        }
    }

    abrirAccion(actionId) {
        this.actionService.doAction(actionId);
    }

    abrirAccionXml(xmlId) {
        this.actionService.doAction(xmlId);
    }
}

registry.category("actions").add("amunet_mis_pendientes_dashboard", MisPendientesDashboard);
