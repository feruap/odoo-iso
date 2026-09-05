/** @odoo-module **/
import { patch } from "@web/core/utils/patch";
import { DateTimePicker } from "@web/core/datetime/datetime_picker";

patch(DateTimePicker.prototype, {
    onWillRender() {
        super.onWillRender();
        for (const item of this.items) {
            if (!item.days) continue;
            for (const day of item.days) {
                if (day.range?.[0]?.weekday >= 6) {
                    const base = day.extraClass ? day.extraClass + " " : "";
                    day.extraClass = base + "o_amunet_weekend";
                }
            }
        }
    },
});
