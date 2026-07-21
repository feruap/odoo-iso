/** @odoo-module **/

import { patch } from "@web/core/utils/patch";
import { DateTimeField } from "@web/views/fields/datetime/datetime_field";

// Odoo 19 oculta el anio cuando la fecha es del anio en curso: el template
// pinta el valor con getFormattedValue(valueIndex) usando props.numeric=false
// (formato condensado "1 jun") y deja el formato completo solo en el tooltip
// (getFormattedValue(valueIndex, true)).
//
// En Amunet (ISO 13485 / Cofepris) las fechas no deben ser ambiguas. Forzamos
// que el default de numeric sea true, de modo que el valor mostrado use siempre
// el formato completo del idioma (configurado como %d.%m.%y -> 01.06.26), con
// anio siempre visible. Como ListDateTimeField extiende DateTimeField, el
// parche cubre formularios y vistas de lista.
patch(DateTimeField.prototype, {
    getFormattedValue(valueIndex, numeric = true) {
        return super.getFormattedValue(valueIndex, numeric);
    },
});
