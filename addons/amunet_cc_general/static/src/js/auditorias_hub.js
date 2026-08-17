/** @odoo-module **/
import { Component, onWillStart, useState } from "@odoo/owl";
import { registry } from "@web/core/registry";
import { useService } from "@web/core/utils/hooks";
import { user } from "@web/core/user";

class AuditoriasHub extends Component {
    static template = "amunet_cc_general.AuditoriasHub";
    static props = ["*"];

    setup() {
        this.actionService = useService("action");
        this.orm = useService("orm");

        this.state = useState({
            loading: true,
            convocatorias: 0,
            programas: 0,
            planes: 0,
        });

        onWillStart(() => this._cargarConteos());
    }

    async _cargarConteos() {
        try {
            const [convocatorias, programas, planes] = await Promise.all([
                this.orm.searchCount("amunet.auditor.convocatoria", [
                    ["state", "in", ["publicada", "en_proceso"]],
                ]),
                this.orm.searchCount("amunet.programa.auditoria", [
                    ["state", "=", "vigente"],
                ]),
                this.orm.searchCount("amunet.plan.auditoria", [
                    ["state", "in", ["borrador", "emitido"]],
                ]),
            ]);
            Object.assign(this.state, { convocatorias, programas, planes, loading: false });
        } catch (e) {
            console.error("Error al cargar conteos de auditorías:", e);
            Object.assign(this.state, { loading: false });
        }
    }

    abrirAccionXml(xmlId) {
        this.actionService.doAction(xmlId);
    }
}

registry.category("actions").add("amunet_auditorias_hub", AuditoriasHub);
