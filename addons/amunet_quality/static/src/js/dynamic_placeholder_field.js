/** @odoo-module **/

import { registry } from "@web/core/registry";
import { FloatField, floatField } from "@web/views/fields/float/float_field";
import { HtmlField, htmlField } from "@web/views/fields/html/html_field";

/**
 * Float Field with Dynamic Placeholder
 *
 * Epic-032: Campo Float que lee placeholder desde un campo computed
 *
 * Uso:
 * <field name="additional_info_avg_length"
 *        widget="dynamic_placeholder_float"
 *        options="{'placeholder_field': 'placeholder_additional_info_avg_length'}"/>
 *
 * ARQUITECTURA CORRECTA (análisis senior OWL2):
 * - NO se puede usar getter para placeholder (no es reactivo en props)
 * - Placeholder debe pasarse como PROP desde extractProps
 * - extractProps se llama en cada render, puede leer record.data
 * - Template accede a props.placeholder (patrón estándar Odoo)
 */
export class DynamicPlaceholderFloatField extends FloatField {
    static template = "amunet_quality.DynamicPlaceholderFloatField";
    static props = {
        ...FloatField.props,
        placeholder: { type: String, optional: true },
    };
}

/**
 * Html Field with Dynamic Placeholder
 *
 * Epic-032: Campo Html que lee placeholder desde un campo computed
 */
export class DynamicPlaceholderHtmlField extends HtmlField {
    static template = "amunet_quality.DynamicPlaceholderHtmlField";
    static props = {
        ...HtmlField.props,
        placeholder: { type: String, optional: true },
    };
}

// Registrar Float Field con placeholder dinámico
registry.category("fields").add("dynamic_placeholder_float", {
    ...floatField,
    component: DynamicPlaceholderFloatField,
    extractProps: ({ attrs, options }, dynamicInfo) => {
        // Obtener props base del floatField
        const props = floatField.extractProps({ attrs, options });

        // Leer placeholder desde campo computed del record
        // extractProps recibe dynamicInfo.record con los datos actuales
        const placeholderFieldName = options.placeholder_field;
        let placeholder = "";
        if (placeholderFieldName && dynamicInfo && dynamicInfo.record) {
            placeholder = dynamicInfo.record.data[placeholderFieldName] || "";
        }

        return {
            ...props,
            placeholder: placeholder,
        };
    },
});

// Registrar Html Field con placeholder dinámico
registry.category("fields").add("dynamic_placeholder_html", {
    ...htmlField,
    component: DynamicPlaceholderHtmlField,
    extractProps: ({ attrs, options }, dynamicInfo) => {
        // Obtener props base del htmlField (ya maneja placeholder estándar)
        const props = htmlField.extractProps({ attrs, options, placeholder: "" });

        // Sobrescribir placeholder con valor dinámico
        const placeholderFieldName = options.placeholder_field;
        let placeholder = "";
        if (placeholderFieldName && dynamicInfo && dynamicInfo.record) {
            placeholder = dynamicInfo.record.data[placeholderFieldName] || "";
        }

        return {
            ...props,
            placeholder: placeholder,
        };
    },
});
