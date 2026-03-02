/** @odoo-module **/

import { Component, onWillStart, onWillUpdateProps, useState } from "@odoo/owl";
import { registry } from "@web/core/registry";
import { useService } from "@web/core/utils/hooks";
import { standardFieldProps } from "@web/views/fields/standard_field_props";

/**
 * VAMAMultiCheckWidget - Versión Odoo 19.0
 * 
 * Gestiona múltiples puntos de verificación en un solo widget.
 * Sincroniza multi_check_results_json y result_text_pattern.
 */
export class VAMAMultiCheckWidget extends Component {
    static template = "amunet_quality.VAMAMultiCheckWidget";
    static props = {
        record: { type: Object },
        readonly: { type: Boolean, optional: true },
        updateRecord: { type: Function, optional: true },
    };

    async updateRecord(values) {
        if (this.props.readonly) return;
        if (this.props.updateRecord) {
            await this.props.updateRecord(values);
        } else if (this.props.record && this.props.record.update) {
            await this.props.record.update(values);
        }
    }

    setup() {
        this.notification = useService("notification");
        this.state = useState({
            positions: [],
            results: {}
        });
        
        onWillStart(async () => {
            await this._loadMapping(this.props);
            this._loadResults(this.props);
        });

        onWillUpdateProps(async (nextProps) => {
            const oldData = this.props.record.data;
            const newData = nextProps.record.data;

            // Recargar mapeo si el campo cambia (ej: cambio de especificación)
            if (newData.text_phrase_mapping !== oldData.text_phrase_mapping) {
                await this._loadMapping(nextProps);
            }
            
            // Recargar resultados si cambian externamente (ej: descarte de cambios)
            if (newData.multi_check_results_json !== oldData.multi_check_results_json) {
                this._loadResults(nextProps);
            }
        });
    }

    async _loadMapping(props) {
        try {
            // Leer directamente desde text_phrase_mapping del detalle
            const rawMapping = props.record.data.text_phrase_mapping;
            if (rawMapping) {
                const mapping = JSON.parse(rawMapping);
                this.state.positions = mapping.positions || [];
            }
        } catch (e) {
            console.error("VAMA Widget: Error parsing mapping", e);
        }
    }

    _loadResults(props) {
        try {
            const rawResults = props.record.data.multi_check_results_json;
            if (rawResults) {
                this.state.results = JSON.parse(rawResults);
            } else {
                // Fallback a result_text_pattern (legacy)
                const pattern = props.record.data.result_text_pattern || "";
                if (pattern) {
                    const legacyResults = {};
                    pattern.split(",").forEach((val, i) => {
                        legacyResults[String(i)] = val.trim().toUpperCase();
                    });
                    this.state.results = legacyResults;
                }
            }
        } catch (e) {
            console.error("VAMA Widget: Error loading results", e);
        }
    }

    getValue(index) {
        const val = this.state.results[String(index)];
        // Normalizar valores vacíos
        if (val === undefined || val === null) return "";
        return String(val);
    }

    async updateValue(index, value) {
        // 1. Actualizar estado local inmediato para respuesta UI fluida
        const idxStr = String(index);
        if (this.state.results[idxStr] === value) return; // Sin cambios reales
        
        this.state.results[idxStr] = value;
        const jsonResults = JSON.stringify(this.state.results);
        
        // 2. Sincronizar patrón legacy (A,B,N)
        const patternParts = [];
        for (let i = 0; i < this.state.positions.length; i++) {
            const v = this.state.results[String(i)];
            const pos = this.state.positions[i];
            const pType = pos.type || 'binary';
            if (pType === 'binary' || pType === 'select') {
                patternParts.push(v || "N");
            } else {
                patternParts.push(v || "0");
            }
        }
        
        // 3. Notificar al registro de Odoo
        // IMPORTANTE: En Odoo 19.0 esto debe ser await
        try {
            await this.updateRecord({
                multi_check_results_json: jsonResults,
                result_text_pattern: patternParts.join(",")
            });
            
            // Forzar notificación de cambio al widget mismo si es necesario
            // Aunque props.record.update debería disparar re-render
        } catch (err) {
            this.notification.add("Error al guardar selección: " + err.message, { type: "danger" });
        }
    }
}

VAMAMultiCheckWidget.fieldDependencies = [
    "multi_check_results_json",
    "evaluation_type",
    "verdict",
    "verdict_message",
    "text_phrase_mapping",
    "result_text_pattern"
];

registry.category("fields").add("vama_multi_check_widget", {
    component: VAMAMultiCheckWidget,
    supportedTypes: ["text"],
});
