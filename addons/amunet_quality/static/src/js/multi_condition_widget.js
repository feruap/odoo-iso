/** @odoo-module **/

import { Component, useState, onWillUnmount } from "@odoo/owl";
import { registry } from "@web/core/registry";

export class MultiConditionWidget extends Component {
    static template = "amunet_quality.MultiConditionWidget";
    static props = {
        record: { type: Object },
        readonly: { type: Boolean, optional: true },
        updateRecord: { type: Function, optional: true },
    };

    setup() {
        this.state = useState({
            num1Value: this.props.record.data.multi_cond_num1 || '',
            num2Value: this.props.record.data.multi_cond_num2 || '',
        });
        this.debounceTimers = {};
        onWillUnmount(() => {
            Object.values(this.debounceTimers).forEach(timer => clearTimeout(timer));
        });
    }

    debounce(key, callback, delay = 800) {
        if (this.debounceTimers[key]) {
            clearTimeout(this.debounceTimers[key]);
        }
        this.debounceTimers[key] = setTimeout(() => {
            callback();
            delete this.debounceTimers[key];
        }, delay);
    }

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
        const value = ev.target.value;
        this.state.num1Value = value;
        this.debounce('num1', () => {
            this.updateRecord({
                multi_cond_num1: parseInt(value) || 0,
            });
        });
    }

    onNum1Blur(ev) {
        const value = ev.target.value;
        if (this.debounceTimers['num1']) {
            clearTimeout(this.debounceTimers['num1']);
            delete this.debounceTimers['num1'];
        }
        this.updateRecord({
            multi_cond_num1: parseInt(value) || 0,
        });
    }

    onNum2Change(ev) {
        const value = ev.target.value;
        this.state.num2Value = value;
        this.debounce('num2', () => {
            this.updateRecord({
                multi_cond_num2: parseFloat(value) || 0.0,
            });
        });
    }

    onNum2Blur(ev) {
        const value = ev.target.value;
        if (this.debounceTimers['num2']) {
            clearTimeout(this.debounceTimers['num2']);
            delete this.debounceTimers['num2'];
        }
        this.updateRecord({
            multi_cond_num2: parseFloat(value) || 0.0,
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
