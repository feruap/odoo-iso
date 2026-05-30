# -*- coding: utf-8 -*-
from odoo import models, fields, api, _
from odoo.exceptions import UserError


class MrpProduction(models.Model):
    _inherit = 'mrp.production'

    # ============================
    # Relacion con inspecciones
    # ============================
    process_inspection_ids = fields.One2many(
        'amunet.process.inspection', 'production_id',
        string='Inspecciones de proceso',
    )
    process_inspection_count = fields.Integer(
        string='Inspecciones',
        compute='_compute_process_inspection_count',
    )

    @api.depends('process_inspection_ids')
    def _compute_process_inspection_count(self):
        for rec in self:
            rec.process_inspection_count = len(rec.process_inspection_ids)

    # ============================
    # Linea (corta / larga)
    # ============================
    route_type = fields.Selection(
        selection=[
            ('short', 'Linea Corta'),
            ('long', 'Linea Larga / hoja'),
            ('solution', 'Soluciones'),
            ('resale', 'Compra y reventa'),
        ],
        string='Linea de produccion', default='short',
        tracking=True,
        help='Define el flujo SGC aplicable a esta orden. Por defecto '
             'Linea Corta.',
    )

    # ============================
    # Vinculacion con preflight
    # ============================
    preflight_ids = fields.One2many(
        'amunet.pilot.preflight', 'production_id',
        string='Preflights asociados',
    )
    preflight_approved = fields.Boolean(
        string='Preflight aprobado',
        compute='_compute_preflight_approved', store=False,
        help='True si existe al menos un preflight en estado '
             '"Aceptado para piloto" para esta orden.',
    )

    @api.depends('preflight_ids.state')
    def _compute_preflight_approved(self):
        for rec in self:
            rec.preflight_approved = any(
                p.state == 'accepted' for p in rec.preflight_ids
            )

    # ============================
    # Acciones
    # ============================
    def action_view_process_inspections(self):
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': _('Inspecciones de proceso'),
            'res_model': 'amunet.process.inspection',
            'view_mode': 'list,form',
            'domain': [('production_id', '=', self.id)],
            'context': {
                'default_production_id': self.id,
                'search_default_production_id': self.id,
            },
        }

    # ============================
    # Override action_confirm: gate preflight + generar inspecciones
    # ============================
    def action_confirm(self):
        for rec in self:
            if rec.route_type in ('short', 'long'):
                if not rec.preflight_approved:
                    raise UserError(_(
                        'No se puede confirmar la orden %s sin un '
                        'Preflight piloto aprobado.\n\n'
                        'Crea o ejecuta un preflight ANTES de confirmar '
                        'esta orden (Manufactura > Preflight piloto).'
                    ) % rec.name)
        res = super().action_confirm()
        # 3. Generar inspecciones de proceso basadas en el routing
        for rec in self:
            rec._generate_process_inspections()
        return res

    def _generate_process_inspections(self):
        """Crea las inspecciones de proceso necesarias para esta MO
        segun los workcenters definidos en su routing.

        Solo crea para workcenters con inspection_type definido y solo
        si la inspeccion no existe ya (idempotente).
        """
        self.ensure_one()
        if self.route_type not in ('short', 'long'):
            return
        Inspection = self.env['amunet.process.inspection'].sudo()
        for wo in self.workorder_ids:
            wc = wo.workcenter_id
            if not wc or not wc.inspection_type:
                continue
            # Idempotente: no duplicar
            existing = Inspection.search([
                ('production_id', '=', self.id),
                ('workorder_id', '=', wo.id),
            ], limit=1)
            if existing:
                continue
            Inspection.create({
                'production_id': self.id,
                'workcenter_id': wc.id,
                'workorder_id': wo.id,
                'inspection_type': wc.inspection_type,
                'inspector_id': self.env.user.id,
            })
        # Si el BOM no tiene routing (sin workorders), generar al menos
        # las inspecciones para los workcenters operativos con
        # inspection_type definido. (Caso edge: BOM sin operations.)
        if not self.workorder_ids:
            for wc in self.env['mrp.workcenter'].search([
                ('active', '=', True),
                ('inspection_type', '!=', False),
            ]):
                existing = Inspection.search([
                    ('production_id', '=', self.id),
                    ('workcenter_id', '=', wc.id),
                ], limit=1)
                if existing:
                    continue
                Inspection.create({
                    'production_id': self.id,
                    'workcenter_id': wc.id,
                    'inspection_type': wc.inspection_type,
                    'inspector_id': self.env.user.id,
                })
