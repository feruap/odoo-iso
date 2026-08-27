/** @odoo-module **/
import { Component } from "@odoo/owl";
import { registry } from "@web/core/registry";
import { useService } from "@web/core/utils/hooks";

class AuditProvHub extends Component {
    static template = "amunet_cc_general.AuditProvHub";
    setup() {
        this.actionService = useService("action");
    }
    openAction(xmlId) {
        this.actionService.doAction(xmlId);
    }
}
registry.category("actions").add("amunet_cc_general.audit_prov_hub", AuditProvHub);
