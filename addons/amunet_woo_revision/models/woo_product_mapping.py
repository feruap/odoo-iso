# -*- coding: utf-8 -*-
"""Columnas para decidir la clave unica (pagina vs Odoo).

Objetivo de negocio: hoy un mismo producto puede tener una clave en la
tienda (woo_sku) y otra en Odoo (default_code). Almacen debe decidir cual
es la buena; al final ambas deben quedar IGUALES. Aqui se registra la
decision, quien la tomo y cuando, sin modificar todavia ningun sistema.
"""

from odoo import api, fields, models


class AmunetWooProductMapping(models.Model):
    _inherit = 'amunet.woo.product.mapping'

    clave_coincide = fields.Boolean(
        string='Claves iguales',
        compute='_compute_clave_coincide',
        store=True,
        help='La clave de la tienda (SKU) y la de Odoo son identicas.',
    )
    clave_decidida = fields.Selection(
        [
            ('pendiente', 'Por decidir'),
            ('web', 'Usar la clave de la pagina'),
            ('odoo', 'Usar la clave de Odoo'),
            ('otra', 'Usar otra clave (indicar abajo)'),
        ],
        string='Clave que se va a usar',
        default='pendiente',
        required=True,
        tracking=True,
        help='Decision de Almacen sobre cual clave queda como unica.',
    )
    clave_manual = fields.Char(
        string='Clave nueva (manual)',
        help='Solo si se eligio "Usar otra clave".',
    )
    clave_final = fields.Char(
        string='Clave final',
        compute='_compute_clave_final',
        store=True,
        help='Clave que debera quedar en AMBOS sistemas.',
    )
    clave_aplicada = fields.Boolean(
        string='Ya aplicada en ambos',
        default=False,
        tracking=True,
        help='Marcar cuando la clave final ya quedo igual en la tienda y en Odoo.',
    )
    clave_decidida_por = fields.Many2one(
        'res.users', string='Decidio', readonly=True, copy=False,
    )
    clave_decidida_fecha = fields.Datetime(
        string='Fecha de decision', readonly=True, copy=False,
    )
    clave_notas = fields.Char(string='Notas de la clave')

    @api.depends('woo_sku', 'default_code')
    def _compute_clave_coincide(self):
        for rec in self:
            a = (rec.woo_sku or '').strip().upper()
            b = (rec.default_code or '').strip().upper()
            rec.clave_coincide = bool(a) and a == b

    @api.depends('clave_decidida', 'clave_manual', 'woo_sku', 'default_code')
    def _compute_clave_final(self):
        for rec in self:
            if rec.clave_decidida == 'web':
                rec.clave_final = (rec.woo_sku or '').strip()
            elif rec.clave_decidida == 'odoo':
                rec.clave_final = (rec.default_code or '').strip()
            elif rec.clave_decidida == 'otra':
                rec.clave_final = (rec.clave_manual or '').strip()
            else:
                rec.clave_final = False

    def write(self, vals):
        """Sellar quien decidio y cuando, cada vez que cambia la decision."""
        if 'clave_decidida' in vals and vals.get('clave_decidida') != 'pendiente':
            vals = dict(vals)
            vals.setdefault('clave_decidida_por', self.env.user.id)
            vals.setdefault('clave_decidida_fecha', fields.Datetime.now())
        return super().write(vals)

    def action_clave_usar_web(self):
        return self.write({'clave_decidida': 'web'})

    def action_clave_usar_odoo(self):
        return self.write({'clave_decidida': 'odoo'})
