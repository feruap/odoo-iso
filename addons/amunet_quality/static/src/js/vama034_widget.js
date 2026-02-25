/** @odoo-module **/

import { Component } from "@odoo/owl";

/**
 * Widget VAMA-034: Two-step widget for Sample Type and Observed Result
 */
export class VAMA034Widget extends Component {
  static template = "amunet_quality.VAMA034Widget";
  static props = {
    record: { type: Object },
    readonly: { type: Boolean },
  };

  get detail() {
    return this.props.record.data;
  }

  onSampleChange(ev) {
    if (this.props.readonly) return;
    this.updateRecord({
      vama034_sample_type: ev.target.value,
    });
  }

  onResultChange(ev) {
    if (this.props.readonly) return;
    this.updateRecord({
      vama034_observed_result: ev.target.value,
    });
  }
}
