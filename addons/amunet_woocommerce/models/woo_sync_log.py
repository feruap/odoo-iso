# -*- coding: utf-8 -*-

from odoo import fields, models


class AmunetWooSyncLog(models.Model):
    _name = 'amunet.woo.sync.log'
    _description = 'Bitacora de sincronizacion WooCommerce'
    _order = 'id desc'
    _rec_name = 'display_label'

    backend_id = fields.Many2one(
        'amunet.woo.backend', string='Tienda', required=True,
        ondelete='cascade', index=True)
    operation = fields.Selection([
        ('import', 'Importar catalogo'),
        ('stock', 'Publicar existencias'),
    ], string='Operacion', required=True)
    state = fields.Selection([
        ('running', 'En proceso'),
        ('success', 'Correcto'),
        ('partial', 'Parcial'),
        ('error', 'Error'),
    ], string='Resultado', default='running', required=True)
    date_start = fields.Datetime(
        string='Inicio', default=fields.Datetime.now, required=True)
    date_end = fields.Datetime(string='Fin')
    total_count = fields.Integer(string='Total')
    done_count = fields.Integer(string='Correctos')
    failed_count = fields.Integer(string='Fallidos')
    message = fields.Text(string='Detalle')
    display_label = fields.Char(compute='_compute_display_label')

    def _compute_display_label(self):
        labels = dict(self._fields['operation'].selection)
        for log in self:
            log.display_label = '%s - %s' % (
                labels.get(log.operation, log.operation), log.date_start)

    def _action_open(self):
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'res_model': self._name,
            'res_id': self.id,
            'view_mode': 'form',
            'target': 'current',
        }
