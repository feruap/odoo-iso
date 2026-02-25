/** @odoo-module **/

import { Component } from "@odoo/owl";
import { registry } from "@web/core/registry";

export class VAMA044Widget extends Component {
    static template = "amunet_quality.VAMA044Widget";
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

    get unionOptions() {
        return [
            { value: "adequate", label: "Unión adecuada" },
            { value: "inadequate", label: "Unión inadecuada" },
        ];
    }

    get record() {
        return this.props.record.data;
    }

    get condition1Pass() {
        return this.record.vama044_num_gotas >= (this.record.vama044_num_gotas_min || 5);
    }

    get condition2Pass() {
        const vol = this.record.vama044_vol_gota;
        const min = this.record.vama044_vol_gota_min || 40.0;
        const max = this.record.vama044_vol_gota_max || 50.0;
        return vol >= min && vol <= max;
    }

    get condition3Pass() {
        return this.record.vama044_union === 'adequate';
    }

    get condition4Pass() {
        const vol = this.record.vama044_vol_llenado;
        const min = this.record.vama044_vol_llenado_min || 1540.0;
        const max = this.record.vama044_vol_llenado_max || 1560.0;
        return vol >= min && vol <= max;
    }

    get allConditionsPass() {
        return this.condition1Pass && this.condition2Pass && 
               this.condition3Pass && this.condition4Pass;
    }

    onNumGotasChange(ev) {
        this.updateRecord({
            vama044_num_gotas: parseInt(ev.target.value) || 0,
        });
    }

    onVolGotaChange(ev) {
        this.updateRecord({
            vama044_vol_gota: parseFloat(ev.target.value) || 0,
        });
    }

    onUnionChange(ev) {
        this.updateRecord({
            vama044_union: ev.target.value,
        });
    }

    onVolLlenadoChange(ev) {
        this.updateRecord({
            vama044_vol_llenado: parseFloat(ev.target.value) || 0,
        });
    }
}

registry.category("fields").add("vama044_widget", {
    component: VAMA044Widget,
});
