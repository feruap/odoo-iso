# -*- coding: utf-8 -*-
from odoo import models, fields, api, _
from odoo.exceptions import UserError


class MarketplaceProductProposal(models.Model):
    _inherit = 'amunet.marketplace.product.proposal'

    # Clave propuesta (default_code) - hoy la propuesta creaba el producto SIN clave.
    clave_propuesta = fields.Char(
        string='Clave propuesta', tracking=True,
        help='Codigo interno con nomenclatura Amunet (DM inmunologica, DL molecular, '
             'PT terminado, MP materia prima, EQ equipo...). Se asigna al producto al crear.')
    supply_type = fields.Selection([
        ('fabricado', 'Fabricado'),
        ('comprado', 'Comprado (compra-venta)'),
        ('comprado_qc', 'Comprado con control de calidad'),
    ], string='Tipo de suministro', tracking=True,
        help='Como se abastece: define si nace vendible/comprable y si requiere QC.')
    origen_mapeo_id = fields.Many2one(
        'amunet.woo.product.mapping', string='Origen (mapeo Woo)',
        readonly=True, index=True,
        help='Mapeo Woo desde el que se propuso el alta (trazabilidad).')
    # Anti-duplicados: candidatos parecidos que YA existen (incluye archivados).
    duplicados_info = fields.Text(
        string='Posibles duplicados', compute='_compute_duplicados',
        help='Productos ya existentes parecidos por clave o nombre (incluye '
             'archivados). Revisar antes de aprobar para no duplicar.')
    tiene_duplicado_exacto = fields.Boolean(
        string='Duplicado exacto de clave', compute='_compute_duplicados')

    @api.depends('name', 'clave_propuesta')
    def _compute_duplicados(self):
        Product = self.env['product.product'].with_context(active_test=False).sudo()
        for rec in self:
            cands = Product.browse()
            exacto = False
            if rec.clave_propuesta:
                por_clave = Product.search(
                    [('default_code', '=ilike', rec.clave_propuesta)], limit=5)
                cands |= por_clave
                exacto = bool(por_clave)
            if rec.name and len(rec.name) >= 3:
                cands |= Product.search([('name', 'ilike', rec.name)], limit=5)
            lineas = []
            for p in cands[:10]:
                estado = 'ARCHIVADO' if not p.active else 'activo'
                lineas.append('- [%s] %s  (%s)' % (
                    p.default_code or '(sin clave)', p.display_name, estado))
            rec.duplicados_info = (
                '\n'.join(lineas) if lineas
                else 'Sin coincidencias por clave ni nombre. Parece un producto nuevo.')
            rec.tiene_duplicado_exacto = exacto

    def action_create_product(self):
        # Guarda anti-duplicado: no crear si la clave ya existe (incl. archivados).
        for rec in self:
            if rec.clave_propuesta:
                existe = self.env['product.product'].with_context(
                    active_test=False).sudo().search_count(
                    [('default_code', '=ilike', rec.clave_propuesta)])
                if existe:
                    raise UserError(_(
                        'Ya existe un producto con la clave "%s" (revisa activos y '
                        'archivados). Usa el existente o cambia la clave antes de crear.'
                    ) % rec.clave_propuesta)
        res = super().action_create_product()
        for rec in self:
            tmpl = rec.product_tmpl_id
            if not tmpl:
                continue
            vals = {}
            if rec.clave_propuesta:
                vals['default_code'] = rec.clave_propuesta
            # Producto de tienda: vendible. Compra/QC segun tipo de suministro.
            if rec.supply_type == 'fabricado':
                vals.update({'sale_ok': True, 'purchase_ok': False})
            elif rec.supply_type == 'comprado':
                vals.update({'sale_ok': True, 'purchase_ok': True})
            elif rec.supply_type == 'comprado_qc':
                vals.update({'sale_ok': True, 'purchase_ok': True})
                if 'qc_required' in tmpl._fields:
                    vals['qc_required'] = True
            if vals:
                tmpl.sudo().write(vals)
            # Enlazar el mapeo de origen al producto recien creado (trazabilidad).
            if rec.origen_mapeo_id and not rec.origen_mapeo_id.product_id:
                rec.origen_mapeo_id.sudo().product_id = tmpl.product_variant_id.id
        return res
