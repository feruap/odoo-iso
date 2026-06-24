# -*- coding: utf-8 -*-
import re
from odoo import models, fields, api

CLASIF_REGISTRO = [
    ('MP', 'MP - Materia Prima'),
    ('MI', 'MI - Material Impreso'),
    ('SP', 'SP - Producto Semiprocesado'),
    ('ST', 'ST - Producto Semiterminado'),
    ('PT', 'PT - Producto Terminado'),
    ('OT', 'Otro / histórico'),
]


class AmunetClaveRegistro(models.Model):
    _name = 'amunet.clave.registro'
    _description = 'Registro / documentación de claves de productos'
    _order = 'clave'
    _rec_name = 'clave'

    clave = fields.Char(string='Clave', required=True, index=True)
    name = fields.Char(string='Nombre / Analito')
    area = fields.Char(string='Categoría / Área',
                       help="Grupo o área de la clave (cartucho, hoja maestra, gotero...).")
    clasificacion = fields.Selection(CLASIF_REGISTRO, string='Clasificación')
    product_tmpl_id = fields.Many2one('product.template', string='Producto en sistema',
                                      ondelete='set null')
    fecha_alta = fields.Date(string='Fecha de alta')
    origen = fields.Selection([
        ('historico', 'Histórico (carga inicial)'),
        ('sistema', 'Generado por el sistema'),
    ], string='Origen', default='historico')
    notas = fields.Char(string='Notas')

    @api.model
    def _amunet_siguiente_clave(self, prefijo, padding=2):
        """Siguiente clave gap-free para un prefijo (clasificacion+abreviatura).

        Continua del MAXIMO consecutivo existente para ese prefijo, mirando tanto
        el registro como los default_code de productos (asi respeta lo historico y
        no repite). Ej: si existe hasta MPCAR62, devuelve MPCAR63.
        """
        prefijo = (prefijo or '').upper()
        if not prefijo:
            return False
        pat = re.compile(r'^%s(\d+)$' % re.escape(prefijo))
        maxn = 0
        for clave in self.search([('clave', '=like', prefijo + '%')]).mapped('clave'):
            m = pat.match((clave or '').upper())
            if m:
                maxn = max(maxn, int(m.group(1)))
        prods = self.env['product.template'].with_context(active_test=False).search(
            [('default_code', '=like', prefijo + '%')]).mapped('default_code')
        for code in prods:
            m = pat.match((code or '').upper())
            if m:
                maxn = max(maxn, int(m.group(1)))
        return '%s%0*d' % (prefijo, padding, maxn + 1)
