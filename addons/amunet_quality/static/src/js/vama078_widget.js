/** @odoo-module **/

import { Component } from "@odoo/owl";
import { registry } from "@web/core/registry";

export class VAMA078Widget extends Component {
    static template = "amunet_quality.VAMA078Widget";
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

    get colorOptions() {
        return [
            { value: "yellow", label: "Amarillo", icon: "🟡" },
            { value: "white", label: "Blanco", icon: "⚪" },
        ];
    }

    get formaOptions() {
        return [
            { value: "deformed", label: "Deformado", icon: "⚠️" },
            { value: "compact", label: "Compacto", icon: "✅" },
        ];
    }

    get texturaOptions() {
        return [
            { value: "no_sticky", label: "Sin textura pegajosa", icon: "✅" },
            { value: "sticky", label: "Con textura pegajosa", icon: "⚠️" },
        ];
    }

    get humedadOptions() {
        return [
            { value: "no_moisture", label: "Sin humedad aparente", icon: "✅" },
            { value: "moisture", label: "Con humedad aparente", icon: "💧" },
        ];
    }

    get record() {
        return this.props.record.data;
    }

    get colorPass() {
        return this.record.vama078_color === 'white';
    }

    get formaPass() {
        return this.record.vama078_forma === 'compact';
    }

    get texturaPass() {
        return this.record.vama078_textura === 'no_sticky';
    }

    get humedadPass() {
        return this.record.vama078_humedad === 'no_moisture';
    }

    get allConditionsPass() {
        return this.colorPass && this.formaPass && 
               this.texturaPass && this.humedadPass;
    }

    onColorChange(ev) {
        this.updateRecord({ vama078_color: ev.target.value });
    }

    onFormaChange(ev) {
        this.updateRecord({ vama078_forma: ev.target.value });
    }

    onTexturaChange(ev) {
        this.updateRecord({ vama078_textura: ev.target.value });
    }

    onHumedadChange(ev) {
        this.updateRecord({ vama078_humedad: ev.target.value });
    }
}

registry.category("fields").add("vama078_widget", {
    component: VAMA078Widget,
});
