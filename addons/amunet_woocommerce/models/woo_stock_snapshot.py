# -*- coding: utf-8 -*-

from odoo import api, fields, models, _
from odoo.exceptions import ValidationError


class AmunetWooStockSnapshot(models.Model):
    """Snapshot del inventario Woo de un artículo mapeado.

    Es la única fuente del "inventario Woo por estado": disponible, reservado,
    caducado y dañado. Cada categoría tiene una bandera explícita que distingue
    un cero real de un dato desconocido. Nunca se infiere ni se escribe hacia
    WooCommerce.
    """

    _name = 'amunet.woo.stock.snapshot'
    _description = 'Snapshot de inventario WooCommerce'
    _inherit = ['mail.thread']
    _order = 'date desc, id desc'

    mapping_id = fields.Many2one(
        'amunet.woo.product.mapping', string='Mapeo', required=True,
        ondelete='restrict', index=True)
    company_id = fields.Many2one(
        'res.company', string='Compañía',
        related='mapping_id.company_id', store=True, index=True)
    backend_id = fields.Many2one(
        'amunet.woo.backend', string='Tienda',
        related='mapping_id.backend_id', store=True)
    date = fields.Datetime(
        string='Fecha del snapshot', default=fields.Datetime.now,
        required=True, tracking=True)
    source = fields.Selection([
        ('manual', 'Carga manual'),
        ('api', 'Lectura GET de inventario'),
        ('csv', 'CSV de mapeo'),
    ], string='Fuente', default='manual', required=True, tracking=True)
    available_known = fields.Boolean(
        string='Disponible conocido', default=False, tracking=True)
    qty_available = fields.Float(
        string='Disponible (valor)', default=0.0, tracking=True)
    reserved_known = fields.Boolean(
        string='Reservado conocido', default=False, tracking=True)
    qty_reserved = fields.Float(
        string='Reservado (valor)', default=0.0, tracking=True)
    expired_known = fields.Boolean(
        string='Caducado conocido', default=False, tracking=True)
    qty_expired = fields.Float(
        string='Caducado (valor)', default=0.0, tracking=True)
    damaged_known = fields.Boolean(
        string='Dañado conocido', default=False, tracking=True)
    qty_damaged = fields.Float(
        string='Dañado (valor)', default=0.0, tracking=True)
    available_display = fields.Char(
        string='Disponible', compute='_compute_displays')
    reserved_display = fields.Char(
        string='Reservado', compute='_compute_displays')
    expired_display = fields.Char(
        string='Caducado', compute='_compute_displays')
    damaged_display = fields.Char(
        string='Dañado', compute='_compute_displays')
    notes = fields.Text(string='Notas')

    @api.depends(
        'available_known', 'qty_available',
        'reserved_known', 'qty_reserved',
        'expired_known', 'qty_expired',
        'damaged_known', 'qty_damaged',
    )
    def _compute_displays(self):
        for rec in self:
            rec.available_display = rec._display(
                rec.qty_available, rec.available_known)
            rec.reserved_display = rec._display(
                rec.qty_reserved, rec.reserved_known)
            rec.expired_display = rec._display(
                rec.qty_expired, rec.expired_known)
            rec.damaged_display = rec._display(
                rec.qty_damaged, rec.damaged_known)

    @api.model
    def _display(self, quantity, known):
        return ('%g' % quantity) if known else _('No calculable')

    @api.constrains(
        'qty_available', 'qty_reserved', 'qty_expired', 'qty_damaged')
    def _check_nonnegative_quantities(self):
        for rec in self:
            if min(
                    rec.qty_available, rec.qty_reserved,
                    rec.qty_expired, rec.qty_damaged) < 0:
                raise ValidationError(_(
                    'Las cantidades del snapshot no pueden ser negativas.'))
