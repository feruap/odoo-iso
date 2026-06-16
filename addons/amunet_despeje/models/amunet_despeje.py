# -*- coding: utf-8 -*-

import hashlib
import json

from odoo import api, fields, models, _
from odoo.exceptions import AccessError, UserError

OPERATOR_GROUP = 'amunet_despeje.group_despeje_operator'
SUPERVISOR_GROUP = 'amunet_despeje.group_despeje_supervisor'
INTERNAL_CTX = '_despeje_internal'

CHECKLIST_ESTANDAR = [
    'No hay producto ni material del lote anterior en el área',
    'No hay documentación del lote anterior en el área',
    'Equipos y superficies limpios y libres de residuos',
    'Área identificada con el nuevo lote / orden',
    'Insumos del nuevo lote verificados y conformes',
]


class AmunetDespeje(models.Model):
    _name = 'amunet.despeje'
    _description = 'Despeje de línea / área de fabricación'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'fecha desc, id desc'

    name = fields.Char(string='Folio', default='Nuevo', copy=False, readonly=True)
    area = fields.Char(string='Área / línea', required=True, tracking=True)
    production_id = fields.Many2one('mrp.production', string='Orden de producción')
    lote_nuevo = fields.Char(string='Lote / orden nuevo')
    fecha = fields.Datetime(string='Fecha/hora', default=fields.Datetime.now, required=True)
    turno = fields.Integer(string='Turno', default=1)
    operator_id = fields.Many2one('res.users', string='Realizado por', default=lambda s: s.env.user)

    line_ids = fields.One2many('amunet.despeje.line', 'despeje_id', string='Verificaciones')

    state = fields.Selection([
        ('draft', 'Borrador'),
        ('signed', 'Firmado'),
        ('cancelled', 'Cancelado'),
    ], string='Estado', default='draft', required=True, index=True, tracking=True)

    conforme = fields.Boolean(string='Despeje conforme', compute='_compute_conforme', store=True)
    signed_by = fields.Many2one('res.users', string='Firmado por', readonly=True)
    signed_on = fields.Datetime(string='Fecha de firma', readonly=True)
    snapshot_hash = fields.Char(string='Hash', readonly=True, copy=False)
    notas = fields.Text(string='Notas')

    LOCKED = {'area', 'production_id', 'lote_nuevo', 'fecha', 'turno', 'operator_id',
              'state', 'signed_by', 'signed_on', 'snapshot_hash', 'conforme'}

    @api.depends('line_ids.done')
    def _compute_conforme(self):
        for r in self:
            r.conforme = all(l.done for l in r.line_ids) if r.line_ids else False

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if vals.get('name', 'Nuevo') in (False, 'Nuevo'):
                vals['name'] = self.env['ir.sequence'].next_by_code('amunet.despeje') or 'DESP'
            if not vals.get('line_ids'):
                vals['line_ids'] = [(0, 0, {'name': t, 'sequence': (i + 1) * 10})
                                    for i, t in enumerate(CHECKLIST_ESTANDAR)]
        return super().create(vals_list)

    def write(self, vals):
        if not self.env.context.get(INTERNAL_CTX):
            mail_fields = {'message_main_attachment_id', 'message_ids',
                           'message_follower_ids', 'activity_ids'}
            for r in self:
                if r.state in ('signed', 'cancelled'):
                    illegal = set(vals.keys()) - mail_fields
                    if illegal:
                        raise UserError(_('El despeje "%s" está firmado y es inmutable.') % r.name)
        return super().write(vals)

    def unlink(self):
        for r in self:
            if r.state == 'signed' and not self.env.su:
                raise UserError(_('No se puede eliminar un despeje firmado.'))
        return super().unlink()

    def _build_hash(self, when):
        self.ensure_one()
        payload = {
            'folio': self.name, 'area': self.area, 'lote': self.lote_nuevo,
            'fecha': str(self.fecha), 'operador': self.operator_id.login,
            'lines': [(l.name, l.done, l.observacion or '') for l in self.line_ids],
            'firma': self.env.user.login, 'firma_fecha': str(when),
        }
        return hashlib.sha256(json.dumps(payload, sort_keys=True, ensure_ascii=False).encode()).hexdigest()

    def _do_sign(self):
        self.ensure_one()
        if self.state != 'draft':
            raise UserError(_('Solo se firman despejes en borrador.'))
        faltan = self.line_ids.filtered(lambda l: not l.done)
        if faltan and not self.notas:
            raise UserError(_('Hay verificaciones sin marcar. Complétalas o registra el motivo en Notas.'))
        now = fields.Datetime.now()
        h = self._build_hash(now)
        self.with_context(**{INTERNAL_CTX: True}).write({
            'state': 'signed', 'signed_by': self.env.user.id,
            'signed_on': now, 'snapshot_hash': h})
        self.message_post(body=_('Despeje firmado por %s.') % self.env.user.login)
        return True

    def action_open_sign_wizard(self):
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window', 'name': _('Firmar despeje'),
            'res_model': 'amunet.despeje.sign.wizard', 'view_mode': 'form',
            'target': 'new', 'context': {'default_despeje_id': self.id},
        }


class AmunetDespejeLine(models.Model):
    _name = 'amunet.despeje.line'
    _description = 'Verificación de despeje'
    _order = 'despeje_id, sequence, id'

    despeje_id = fields.Many2one('amunet.despeje', required=True, ondelete='cascade', index=True)
    sequence = fields.Integer(default=10)
    name = fields.Char(string='Punto a verificar', required=True)
    done = fields.Boolean(string='Verificado')
    observacion = fields.Char(string='Observación')

    def write(self, vals):
        if not self.env.context.get(INTERNAL_CTX):
            for r in self:
                if r.despeje_id.state in ('signed', 'cancelled'):
                    raise UserError(_('El despeje está firmado; es inmutable.'))
        return super().write(vals)

    def unlink(self):
        for r in self:
            if r.despeje_id.state == 'signed':
                raise UserError(_('No se pueden eliminar verificaciones de un despeje firmado.'))
        return super().unlink()
