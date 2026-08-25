# -*- coding: utf-8 -*-
from odoo import models, api, _
from odoo.exceptions import ValidationError

PT_ROOT = 'Producto terminado'
DIST_ROOT = 'Distribucion'


class ProductTemplate(models.Model):
    _inherit = 'product.template'

    def _categ_root_name(self):
        """Nombre de la categoria raiz del arbol al que pertenece el producto."""
        self.ensure_one()
        c = self.categ_id
        while c and c.parent_id:
            c = c.parent_id
        return c.name if c else ''

    @api.constrains('categ_id', 'sale_ok')
    def _check_no_compraventa_en_pt(self):
        """Raiz de la segregacion: un producto VENDIBLE sin lista de materiales
        (no se fabrica, es compra-venta) NO puede quedar en 'Producto terminado';
        va en 'Distribucion'. Bypass con contexto skip_dist_check para flujos
        controlados (alta que crea el BoM despues, imports)."""
        if self.env.context.get('skip_dist_check'):
            return
        for p in self:
            if not p.sale_ok:
                continue
            if p._categ_root_name() != PT_ROOT:
                continue
            if p.bom_count == 0:
                raise ValidationError(_(
                    "El producto '%(producto)s' es vendible y no tiene lista de "
                    "materiales (no se fabrica), por lo que NO puede quedar en "
                    "'%(pt)s'. Debe ir en la categoria '%(dist)s'.\n\n"
                    "Si SI se fabrica, primero cargale su lista de materiales (BoM)."
                ) % {
                    'producto': p.display_name,
                    'pt': PT_ROOT,
                    'dist': DIST_ROOT,
                })
