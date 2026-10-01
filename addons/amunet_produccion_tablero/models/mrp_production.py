from odoo import api, fields, models


class MrpProduction(models.Model):
    _inherit = 'mrp.production'

    # Odoo reescribe date_start/date_finished al iniciar y al terminar la orden;
    # aquí se congela el fin planeado mientras la orden no ha arrancado.
    amunet_plan_fecha_fin = fields.Datetime(
        string='Fin planeado (congelado)',
        compute='_compute_amunet_plan_fecha_fin', store=True, readonly=True,
        copy=False, index=True,
        help='Fin programado de la orden antes de empezar a producir. '
             'No cambia cuando la orden se inicia o se termina.')

    @api.depends('date_finished', 'state')
    def _compute_amunet_plan_fecha_fin(self):
        for mo in self:
            iniciada = (
                any(s in ('progress', 'done') for s in mo.workorder_ids.mapped('state'))
                or (mo.product_uom_id and not mo.product_uom_id.is_zero(mo.qty_producing))
            )
            if mo.state in ('draft', 'confirmed') and not iniciada and mo.date_finished:
                mo.amunet_plan_fecha_fin = mo.date_finished
            # si ya arrancó o terminó se conserva el valor anterior
