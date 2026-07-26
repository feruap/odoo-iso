# -*- coding: utf-8 -*-

from odoo import api, fields, models, _
from odoo.exceptions import ValidationError


class AmunetWooSyncLog(models.Model):
    """Bitácora inmutable de lecturas e importaciones WooCommerce.

    Los registros se crean ya con su estado final y no se editan después:
    son inmutables para todos los usuarios (solo lectura vía ACL). El detalle
    nunca incluye credenciales ni secretos.
    """

    _name = 'amunet.woo.sync.log'
    _description = 'Bitácora de consulta WooCommerce'
    _order = 'id desc'
    _rec_name = 'display_label'

    backend_id = fields.Many2one(
        'amunet.woo.backend', string='Tienda',
        required=True, ondelete='restrict', index=True)
    company_id = fields.Many2one(
        'res.company', string='Compañía', required=True,
        default=lambda self: self.env.company, index=True)
    operation = fields.Selection([
        ('catalog_get', 'Lectura GET de catálogo'),
        ('csv_import', 'Importación CSV de mapeos'),
    ], string='Operación', required=True)
    state = fields.Selection([
        ('success', 'Correcto'),
        ('partial', 'Parcial'),
        ('error', 'Error'),
    ], string='Resultado', default='success', required=True)
    date_start = fields.Datetime(
        string='Inicio', default=fields.Datetime.now, required=True)
    date_end = fields.Datetime(string='Fin')
    total_count = fields.Integer(string='Total')
    done_count = fields.Integer(string='Correctos')
    failed_count = fields.Integer(string='Fallidos')
    message = fields.Text(string='Detalle')
    display_label = fields.Char(compute='_compute_display_label')

    @api.constrains('backend_id', 'company_id')
    def _check_backend_company(self):
        for log in self:
            if log.backend_id.company_id != log.company_id:
                raise ValidationError(_(
                    'La compañía de la bitácora debe coincidir con la tienda.'))

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
