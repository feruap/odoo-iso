/** @odoo-module **/

import { Component } from "@odoo/owl";
import { registry } from "@web/core/registry";

export class MAVI07Widget extends Component {
    static template = "amunet_quality.MAVI07Widget";
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

    get sampleTypeOptions() {
        return [
            { value: "negative", label: "Muestra Negativa (Esperado: #5)" },
            { value: "positive", label: "Muestra Positiva (Esperado: #1, #2, #3 o #4)" },
        ];
    }

    get resultOptions() {
        return [
            { value: "result_1", label: "#1" },
            { value: "result_2", label: "#2" },
            { value: "result_3", label: "#3" },
            { value: "result_4", label: "#4" },
            { value: "result_5", label: "#5" },
        ];
    }

    onSampleTypeChange(ev) {
        this.updateRecord({
            mavi07_sample_type: ev.target.value,
        });
    }

    onObservedResultChange(ev) {
        this.updateRecord({
            mavi07_observed_result: ev.target.value,
        });
    }
}

registry.category("fields").add("mavi07_widget", {
    component: MAVI07Widget,
});
