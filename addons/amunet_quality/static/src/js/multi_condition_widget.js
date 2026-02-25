/** @odoo-module **/

import { Component } from "@odoo/owl";
import { registry } from "@web/core/registry";

export class MultiConditionWidget extends Component {
    static template = "amunet_quality.MultiConditionWidget";
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

    onBinaryChange(ev) {
        this.updateRecord({
            multi_cond_binary: ev.target.value,
        });
    }

    onNum1Change(ev) {
        this.updateRecord({
            multi_cond_num1: parseInt(ev.target.value) || 0,
        });
    }

    onNum2Change(ev) {
        this.updateRecord({
            multi_cond_num2: parseFloat(ev.target.value) || 0.0,
        });
    }

    get isCondition1Pass() {
        return this.props.record.data.multi_cond_binary === "correct";
    }

    get isCondition2Pass() {
        const num1 = this.props.record.data.multi_cond_num1 || 0;
        const min = this.props.record.data.multi_cond_num1_min || 5;
        return num1 >= min;
    }

    get isCondition3Pass() {
        const num2 = this.props.record.data.multi_cond_num2 || 0;
        const min = this.props.record.data.multi_cond_num2_min || 40.0;
        const max = this.props.record.data.multi_cond_num2_max || 50.0;
        return num2 >= min && num2 <= max;
    }
}

registry.category("fields").add("multi_condition_widget", {
    component: MultiConditionWidget,
});
