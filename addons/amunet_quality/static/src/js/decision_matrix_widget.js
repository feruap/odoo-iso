/** @odoo-module **/

import { Component } from "@odoo/owl";
import { registry } from "@web/core/registry";

export class DecisionMatrixWidget extends Component {
    static template = "amunet_quality.DecisionMatrixWidget";
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

    get concentrationOptions() {
        return [
            { value: "low", label: "Baja" },
            { value: "medium", label: "Intermedia" },
            { value: "high", label: "Alta" },
        ];
    }

    get controlVisibleOptions() {
        return [
            { value: "yes", label: "Sí, visible" },
            { value: "no", label: "No, no visible" },
        ];
    }

    get comparisonOptions() {
        return [
            { value: "t_neq_r", label: "T ≠ R (Diferente)" },
            { value: "t_lt_r", label: "T < R (Menor)" },
            { value: "t_eq_r", label: "T ~ R (Aproximadamente igual)" },
            { value: "t_gt_r", label: "T > R (Mayor)" },
        ];
    }

    get record() {
        return this.props.record.data;
    }

    get step1Complete() {
        return Boolean(this.record.result_dm_step1_concentration);
    }

    get step2_1Complete() {
        return Boolean(this.record.result_dm_step2_1_control_visible);
    }

    get step2_2Complete() {
        return Boolean(this.record.result_dm_step2_2_comparison);
    }

    get showStep2_1() {
        return this.step1Complete;
    }

    get showStep2_2() {
        return this.step1Complete && this.step2_1Complete && 
               this.record.result_dm_step2_1_control_visible === 'yes';
    }

    get currentStep() {
        if (!this.step1Complete) return 1;
        if (!this.step2_1Complete) return 2;
        if (this.record.result_dm_step2_1_control_visible === 'no') return 'final';
        if (!this.step2_2Complete) return 3;
        return 'final';
    }

    onConcentrationChange(ev) {
        this.updateRecord({
            result_dm_step1_concentration: ev.target.value,
        });
    }

    onControlVisibleChange(ev) {
        this.updateRecord({
            result_dm_step2_1_control_visible: ev.target.value,
            // Reset step 2.2 if control is not visible
            result_dm_step2_2_comparison: ev.target.value === 'no' ? false : this.record.result_dm_step2_2_comparison,
        });
    }

    onComparisonChange(ev) {
        this.updateRecord({
            result_dm_step2_2_comparison: ev.target.value,
        });
    }
}

registry.category("fields").add("decision_matrix_widget", {
    component: DecisionMatrixWidget,
});
