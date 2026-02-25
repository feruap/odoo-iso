/** @odoo-module **/

import { Component } from "@odoo/owl";
import { registry } from "@web/core/registry";

export class VAMA112Widget extends Component {
    static template = "amunet_quality.VAMA112Widget";
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

    get cond1Options() {
        return [
            { value: "adequate", label: "Adecuado" },
            { value: "inadequate", label: "No adecuado" },
        ];
    }

    get cond2Options() {
        return [
            { value: "no_abrupt", label: "Sin movimientos bruscos" },
            { value: "abrupt", label: "Con movimientos bruscos" },
        ];
    }

    get cond3Options() {
        return [
            { value: "correct", label: "Correcta" },
            { value: "incorrect", label: "Incorrecta" },
        ];
    }

    get cond4Options() {
        return [
            { value: "complete", label: "Completa" },
            { value: "incomplete", label: "Incompleta" },
        ];
    }

    get cond5Options() {
        return [
            { value: "no_heat", label: "Sin calentar" },
            { value: "heating", label: "Calentando" },
        ];
    }

    get record() {
        return this.props.record.data;
    }

    get condition1Pass() {
        return this.record.vama112_cond1 === 'adequate';
    }

    get condition2Pass() {
        return this.record.vama112_cond2 === 'no_abrupt';
    }

    get condition3Pass() {
        return this.record.vama112_cond3 === 'correct';
    }

    get condition4Pass() {
        return this.record.vama112_cond4 === 'complete';
    }

    get condition5Pass() {
        return this.record.vama112_cond5 === 'no_heat';
    }

    get allConditionsPass() {
        return this.condition1Pass && this.condition2Pass && 
               this.condition3Pass && this.condition4Pass && this.condition5Pass;
    }

    onCond1Change(ev) {
        this.updateRecord({ vama112_cond1: ev.target.value });
    }

    onCond2Change(ev) {
        this.updateRecord({ vama112_cond2: ev.target.value });
    }

    onCond3Change(ev) {
        this.updateRecord({ vama112_cond3: ev.target.value });
    }

    onCond4Change(ev) {
        this.updateRecord({ vama112_cond4: ev.target.value });
    }

    onCond5Change(ev) {
        this.updateRecord({ vama112_cond5: ev.target.value });
    }
}

registry.category("fields").add("vama112_widget", {
    component: VAMA112Widget,
});
