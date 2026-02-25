/** @odoo-module **/

import { Component, useState, onWillUpdateProps } from "@odoo/owl";
import { useService } from "@web/core/utils/hooks";

export class MGA0981Widget extends Component {
    static template = "amunet_quality.MGA0981Widget";
    static props = {
        name: { type: String, optional: true },
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
        this.orm = useService("orm");
        
        // Initialize state from props
        const data = this.props.record.data;
        this.state = useState({
            vol_declarado: data.mga0981_vol_declarado || "5ml",
            vol_obtenido: data.mga0981_vol_obtenido || 0.0,
            verdict: data.verdict || "pending",
            verdict_message: data.verdict_message || "",
        });

        onWillUpdateProps((nextProps) => {
            const data = nextProps.record.data;
            this.state.vol_declarado = data.mga0981_vol_declarado || "5ml";
            this.state.vol_obtenido = data.mga0981_vol_obtenido || 0.0;
            this.state.verdict = data.verdict || "pending";
            this.state.verdict_message = data.verdict_message || "";
        });
    }

    get isReadonly() {
        return this.props.readonly;
    }

    get resultMessage() {
        if (this.state.verdict === 'pass') {
            return "RESULTADO DE LA PRUEBA: Cumple con la variación de volumen permitida (± 0.5 ml).";
        } else if (this.state.verdict === 'fail') {
             return "RESULTADO DE LA PRUEBA: No cumple. La variación excede el límite permitido (± 0.5 ml).";
        }
        return "RESULTADO DE LA PRUEBA: Complete todos los puntos de la prueba";
    }

    get resultClass() {
        if (this.state.verdict === 'pass') return "alert-success";
        if (this.state.verdict === 'fail') return "alert-danger";
        return "alert-info";
    }
    
    get verdictLabel() {
        const labels = {
            pending: "⏳ PENDIENTE",
            pass: "✅ CUMPLE",
            fail: "❌ NO CUMPLE"
        };
        return labels[this.state.verdict] || "PENDIENTE";
    }

    get verdictClass() {
        const classes = {
            pending: "bg-warning text-dark",
            pass: "bg-success text-white",
            fail: "bg-danger text-white"
        };
        return classes[this.state.verdict] || "bg-secondary";
    }

    async updateValue(field, value) {
        if (this.isReadonly) return;

        // Optimistic UI update
        this.state[field === 'mga0981_vol_declarado' ? 'vol_declarado' : 'vol_obtenido'] = value;

        try {
            // Update record via props.record.update
            await this.updateRecord({ [field]: value });
        } catch (error) {
            console.error(`Error updating ${field}:`, error);
            // Revert on error? For now just log
        }
    }

    onDeclaradoChange(value) {
        this.updateValue("mga0981_vol_declarado", value);
    }

    onObtenidoChange(ev) {
        const val = parseFloat(ev.target.value);
        this.updateValue("mga0981_vol_obtenido", isNaN(val) ? 0.0 : val);
    }
}
