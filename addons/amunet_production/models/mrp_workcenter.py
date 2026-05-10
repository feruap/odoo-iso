# -*- coding: utf-8 -*-
from odoo import _, api, fields, models
from odoo.exceptions import UserError


class MrpWorkcenter(models.Model):
    _inherit = 'mrp.workcenter'

    amunet_equipment_ids = fields.Many2many(
        comodel_name='amunet.equipment',
        relation='amunet_workcenter_equipment_rel',
        column1='workcenter_id',
        column2='equipment_id',
        string='Equipos vinculados',
        help=(
            'Equipos fisicos del catalogo Amunet que pertenecen a este centro '
            'de trabajo. Cuando se inicia una orden de trabajo (button_start) '
            'el sistema valida que TODOS los equipos vinculados tengan un '
            'certificado de calibracion vigente (state=done y expiration_date '
            '>= hoy). Si alguno no cumple, la WO no inicia.'
        ),
    )

    amunet_equipment_count = fields.Integer(
        compute='_compute_amunet_equipment_count',
        string='# Equipos',
    )

    @api.depends('amunet_equipment_ids')
    def _compute_amunet_equipment_count(self):
        for wc in self:
            wc.amunet_equipment_count = len(wc.amunet_equipment_ids)

    def _amunet_check_equipment_calibration(self):
        """Validar que cada equipo del WC tenga calibracion vigente.

        Recorre los equipos vinculados; para cada uno busca al menos una
        amunet.equipment.calibration con state='done' y expiration_date >= hoy.
        Si falta alguna, levanta UserError listando los equipos sin cert.
        Devuelve True si todo OK.
        """
        today = fields.Date.context_today(self)
        problemas = []
        for wc in self:
            for eq in wc.amunet_equipment_ids:
                cal = self.env['amunet.equipment.calibration'].search([
                    ('equipment_id', '=', eq.id),
                    ('state', '=', 'done'),
                    ('expiration_date', '>=', today),
                ], limit=1)
                if not cal:
                    last = self.env['amunet.equipment.calibration'].search([
                        ('equipment_id', '=', eq.id),
                    ], order='expiration_date desc', limit=1)
                    if last:
                        problemas.append(
                            ' - %s (%s) en %s: ultima calibracion vence %s '
                            '(state=%s)' % (
                                eq.serial_number, eq.name, wc.code or wc.name,
                                last.expiration_date, last.state,
                            )
                        )
                    else:
                        problemas.append(
                            ' - %s (%s) en %s: sin calibracion registrada' % (
                                eq.serial_number, eq.name, wc.code or wc.name,
                            )
                        )
        if problemas:
            raise UserError(_(
                'No se puede iniciar la orden de trabajo: hay equipos sin '
                'certificado de calibracion vigente:\n%s\n\n'
                'Sube los certificados al modulo de calibracion antes de '
                'arrancar produccion.'
            ) % '\n'.join(problemas))
        return True
