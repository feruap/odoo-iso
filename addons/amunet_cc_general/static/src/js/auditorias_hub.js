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
            planes: 0,
            actas: 0,
            listas: 0,
            informes: 0,
            isManager: false,
        });

        onWillStart(() => this._cargarConteos());
    }

    async _cargarConteos() {
        try {
            const [convocatorias, planes, actas, listas, informes, isManager] = await Promise.all([
                this.orm.searchCount("amunet.auditor.convocatoria", [
                    ["state", "in", ["publicada", "en_proceso"]],
                ]),
                this.orm.searchCount("amunet.plan.auditoria", [
                    ["state", "in", ["borrador", "emitido"]],
                ]),
                this.orm.searchCount("amunet.acta.auditoria", [
                    ["state", "=", "borrador"],
                ]),
                this.orm.searchCount("amunet.lista.verificacion", [
                    ["state", "=", "borrador"],
                ]),
                this.orm.searchCount("amunet.informe.auditoria", [
                    ["state", "=", "borrador"],
                ]),
                user.hasGroup("amunet_documentos.group_documentos_manager"),
            ]);
            Object.assign(this.state, { convocatorias, planes, actas, listas, informes, isManager, loading: false });
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
