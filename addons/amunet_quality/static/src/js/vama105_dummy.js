/** @odoo-module **/

import { Component, useState, onWillUpdateProps } from "@odoo/owl";
import { registry } from "@web/core/registry";
import { useService } from "@web/core/utils/hooks";

export class VAMA105Widget extends Component {
    static template = "amunet_quality.VAMA105Widget";
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
        this.orm = useService("orm");
        
        // Initialize state from prop record data
        const data = this.props.record.data;
        // Parse json if it exists, or use default/separate fields if you prefer.
        // For this pattern 2-step, usually we store in separate fields if defined in model, 
        // OR a JSON field. The prompt says "utilizara una lista... y un campo numerico".
        // Assuming we map them to: 
        // 1. vama105_nominal_vol (Selection/Char)
        // 2. vama105_measured_vol (Float)
    }

    get nominalOptions() {
        // "volumen nominal" - logic from documentation not fully specified for list content,
        // but assuming typical pipette volumes based on context or "lista para seleccionar".
        // I will allow free selection or a standard list. 
        // Re-reading: "lista para seleccionar el volume nominal". 
        // I'll add common volumes and allow extending.
        return [
            { value: "0.5", label: "0.5 µl" },
            { value: "2", label: "2 µl" },
            { value: "10", label: "10 µl" },
            { value: "20", label: "20 µl" },
            { value: "50", label: "50 µl" },
            { value: "100", label: "100 µl" },
            { value: "200", label: "200 µl" },
            { value: "1000", label: "1000 µl" },
            // Add 'Other' or specific ones if found in doc. 
            // For now I'll use a generic list + standard ones.
            // Actually, MGA 0981 usually has 5ml, etc. 
            // VAMA-105 might be "Equipos" -> Pipettes?
            // "EQMIC01" sounds like Micropipeta.
        ];
    }
    
    // ... logic
}
