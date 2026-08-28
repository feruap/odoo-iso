# -*- coding: utf-8 -*-
"""La firma de calidad sobre una devolucion.

Quien decide si el material vuelve a la venta es Calidad, y lo firma. No basta
con que alguien apriete un boton: bajo ISO 13485 y CFR 21 Part 11 la decision
tiene que quedar atada a una persona que se identifico en ese momento.

Se reusa el PIN de firma que ya existe en amunet_quality -mismo PIN, mismas
reglas, mismo registro- en vez de inventar otra credencial. Si Calidad cambia
como firma, cambia en un solo lugar.
"""
from odoo import models, fields, api, _
from odoo.exceptions import UserError, ValidationError


class AmunetDevolucionFirma(models.TransientModel):
    _name = 'amunet.devolucion.firma'
    _description = 'Firma de calidad sobre una devolucion'

    devolucion_id = fields.Many2one('amunet.devolucion', string='Devolucion',
                                    required=True, readonly=True)
    decision = fields.Selection([
        ('liberar', 'Liberar para venta'),
        ('rechazar', 'Rechazar'),
    ], string='Decision', required=True)

    cantidad_recibida = fields.Float(related='devolucion_id.cantidad_recibida', readonly=True)
    cantidad_liberada = fields.Float(string='Piezas que se liberan',
                                     digits='Product Unit of Measure',
                                     help='Lo que no se libere se va a retenidos.')
    lote_nombre = fields.Char(related='devolucion_id.lot_id.name', string='Lote', readonly=True)
    condicion = fields.Selection(related='devolucion_id.condicion_al_volver',
                                 string='Condicion del lote hoy', readonly=True)
    destino_nombre = fields.Char(string='Vuelve a', compute='_compute_destino')

    dictamen = fields.Text(string='Dictamen', required=True,
                           help='Que se reviso y que se concluyo. Queda en el expediente.')
    pin = fields.Char(string='PIN de firma', required=True,
                      help='Tu PIN de firma de calidad, el mismo de los controles.')

    @api.depends('devolucion_id', 'decision')
    def _compute_destino(self):
        for w in self:
            if w.decision == 'rechazar':
                w.destino_nombre = _('Retenidos')
                continue
            destino = w.devolucion_id.lot_id._amunet_destino_esperado() \
                if w.devolucion_id.lot_id else False
            w.destino_nombre = destino.display_name if destino else _('(sin determinar)')

    @api.model
    def default_get(self, campos):
        valores = super().default_get(campos)
        devolucion = self.env['amunet.devolucion'].browse(
            self.env.context.get('active_id') or valores.get('devolucion_id'))
        if devolucion:
            valores['devolucion_id'] = devolucion.id
            valores['cantidad_liberada'] = devolucion.cantidad_recibida
        return valores

    @api.constrains('cantidad_liberada', 'decision')
    def _check_cantidad(self):
        for w in self:
            if w.decision != 'liberar':
                continue
            if w.cantidad_liberada <= 0 or w.cantidad_liberada > w.cantidad_recibida:
                raise ValidationError(_(
                    'Las piezas que se liberan tienen que estar entre 1 y %s.'
                ) % w.cantidad_recibida)

    def action_firmar(self):
        self.ensure_one()
        if not self.env.user.has_group('amunet_quality.group_quality_user'):
            raise UserError(_(
                'Solo Calidad puede dictaminar una devolucion. Si te toca hacerlo, '
                'pide que te den el rol.'))

        # Se valida con el mismo metodo que usan los controles de calidad: acepta
        # el PIN de firma o la contrasena del usuario, y deja su registro.
        firma = self.env['amunet.quality.signature.wizard'].new({})
        if not firma._validate_credentials(self.pin):
            raise UserError(_('El PIN no es correcto. La devolucion no se firmo.'))

        devolucion = self.devolucion_id
        if self.decision == 'liberar':
            devolucion._liberar(self.cantidad_liberada, self.dictamen)
        else:
            devolucion._rechazar(self.dictamen)
        return {'type': 'ir.actions.act_window_close'}
