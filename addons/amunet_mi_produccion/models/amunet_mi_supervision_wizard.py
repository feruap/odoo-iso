# -*- coding: utf-8 -*-
from odoo import models, fields, api, _
from odoo.exceptions import UserError, AccessError


class AmunetMiSupervisionWizard(models.TransientModel):
    """Wizard de firma de supervision con PIN, desde Mi produccion.
    El supervisor de produccion avala una actividad YA CULMINADA
    capturando el resultado y confirmando su identidad con su PIN
    (el mismo de su ficha de empleado).
    """
    _name = 'amunet.mi.supervision.wizard'
    _description = 'Firmar supervisión con PIN'

    workorder_id = fields.Many2one('mrp.workorder', required=True, readonly=True)
    inspection_id = fields.Many2one(
        'amunet.process.inspection', required=True, readonly=True)

    lote = fields.Char(
        string='Lote', related='workorder_id.production_id.name', readonly=True)
    actividad = fields.Char(
        string='Actividad', related='workorder_id.display_name', readonly=True)

    result = fields.Selection(
        selection=[
            ('conforme', 'Conforme'),
            ('conforme_con_retiros', 'Conforme con retiros'),
            ('detener', 'Detener proceso (escalar)'),
        ],
        string='Resultado', default='conforme')
    qty_inspected = fields.Float(
        string='Piezas revisadas', digits='Product Unit')
    qty_removed = fields.Float(
        string='Piezas retiradas', digits='Product Unit')
    notes = fields.Text(string='Observaciones')
    pin = fields.Char(string='PIN del supervisor', password=True)

    def action_firmar(self):
        self.ensure_one()
        wo = self.workorder_id
        ins = self.inspection_id

        # 1. Solo se supervisa una actividad culminada.
        if wo.state != 'done':
            raise UserError(_(
                'Solo se puede supervisar una actividad culminada '
                '(terminada). "%s" aun no esta terminada.') % wo.display_name)

        # 1b. Segregacion de funciones: no se firma lo propio.
        if self.env.user in wo.time_ids.mapped('user_id'):
            raise UserError(_(
                'No puedes supervisar una actividad que tu mismo ejecutaste '
                '(segregacion de funciones). Debe firmarla otro supervisor.'))

        # 2. Solo supervisor de produccion (o de calidad).
        if not (
            self.env.user.has_group('amunet_production.group_production_supervisor')
            or self.env.user.has_group('amunet_quality.group_quality_supervisor')
        ):
            raise AccessError(_(
                'Solo el supervisor de produccion puede firmar la supervision.'))

        # 3. Verificacion de identidad con PIN (ficha de empleado).
        emp = self.env.user.employee_id
        if not emp:
            raise UserError(_(
                'Tu usuario no tiene ficha de empleado, no se puede '
                'validar el PIN. Acude con Recursos Humanos.'))
        if not emp.pin:
            raise UserError(_(
                'No tienes un PIN configurado en tu ficha de empleado. '
                'Pidele a RH/Sistemas que te asigne uno.'))
        if (self.pin or '').strip() != emp.pin.strip():
            raise UserError(_('PIN incorrecto. Intenta de nuevo.'))

        # 4. Capturar datos (en borrador, permitido) y firmar.
        ins.sudo().write({
            'result': self.result,
            'qty_inspected': self.qty_inspected,
            'qty_removed': self.qty_removed,
            'notes': self.notes,
        })
        ins.sudo().with_context(amunet_process_signature_write=True).write({
            'state': 'signed',
            'signed_by_id': self.env.user.id,
            'signed_date': fields.Datetime.now(),
        })
        ins.sudo().message_post(body=_(
            'Supervision firmada con PIN por %(u)s.'
        ) % {'u': self.env.user.display_name})
        return {'type': 'ir.actions.act_window_close'}
