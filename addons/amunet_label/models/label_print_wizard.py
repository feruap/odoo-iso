# -*- coding: utf-8 -*-
from odoo import models, fields, api, _
from odoo.exceptions import UserError


class AmunetLabelPrintWizard(models.TransientModel):
    """Wizard para generar el PDF de etiquetas de caja.

    El usuario elige un producto (de donde se toma nombre, REF y la
    lista "Contiene de la caja"), captura el numero de lote, la
    caducidad como texto libre, y la cantidad de etiquetas a imprimir.
    El reporte arma hojas Tabloid 11x17" con grid 3x6 (18 etiquetas
    por hoja); si la cantidad excede 18, se generan paginas adicionales.
    """
    _name = 'amunet.label.print.wizard'
    _description = 'Generador de etiquetas de caja'

    product_id = fields.Many2one(
        'product.product',
        string='Producto',
        required=True,
        domain="[('is_storable', '=', True)]",
        help='Producto al que pertenece el lote a etiquetar. De aqui se '
             'toman el nombre comercial, el REF (codigo interno) y la '
             'lista "Contiene de la caja".',
    )
    lot_name = fields.Char(
        string='Lote',
        required=True,
        help='Numero de lote tal como aparecera en la etiqueta. '
             'Ejemplo: 0526/01/CAB',
    )
    expiration_date_text = fields.Char(
        string='Caducidad',
        required=True,
        help='Fecha de caducidad tal como aparecera en la etiqueta. '
             'Ejemplo: 2028-02',
    )
    quantity = fields.Integer(
        string='Cantidad de etiquetas',
        required=True,
        default=18,
        help='Cuantas etiquetas se generan. Cada hoja Tabloid lleva 18 '
             'etiquetas; si la cantidad es mayor, se imprimen hojas '
             'adicionales.',
    )

    # Campos derivados solo lectura (preview en el form)
    product_name = fields.Char(
        related='product_id.name', string='Nombre comercial', readonly=True)
    product_ref = fields.Char(
        related='product_id.default_code', string='REF (catalogo)', readonly=True)
    product_caja_contiene = fields.Text(
        related='product_id.caja_contiene', string='Contenido de la caja',
        readonly=True,
        help='Esta lista se imprime en la etiqueta. Para cambiarla, '
             'editar el campo "Contenido de la caja (etiqueta)" en la '
             'ficha del producto.',
    )

    @api.constrains('quantity')
    def _check_quantity(self):
        for rec in self:
            if rec.quantity <= 0:
                raise UserError(_('La cantidad de etiquetas debe ser '
                                  'mayor a 0.'))
            if rec.quantity > 1000:
                raise UserError(_('Por seguridad no se permiten mas de '
                                  '1000 etiquetas en una sola corrida.'))

    def action_print_labels(self):
        """Devuelve la accion de reporte para generar el PDF."""
        self.ensure_one()
        if not self.product_id.default_code:
            raise UserError(_(
                'El producto %s no tiene REF (default_code) configurado. '
                'Captura la referencia en la ficha del producto antes '
                'de imprimir.'
            ) % self.product_id.display_name)
        if not self.product_id.caja_contiene:
            raise UserError(_(
                'El producto %s no tiene "Contenido de la caja" '
                'configurado. Capturalo en la ficha del producto antes '
                'de imprimir.'
            ) % self.product_id.display_name)
        return self.env.ref(
            'amunet_label.action_report_caja_label'
        ).report_action(self)

    def get_label_data(self):
        """Devuelve la info que el reporte QWeb usa para renderizar
        cada etiqueta. La lista 'contiene' viene como lista de strings
        ya separada por linea (sin guiones ni vacios)."""
        self.ensure_one()
        contiene_raw = self.product_caja_contiene or ''
        contiene_lines = [
            line for line in contiene_raw.splitlines() if line.strip()
        ]
        # range(N) sirve para que QWeb itere N veces con t-foreach
        labels = list(range(self.quantity))
        return {
            'product_name': self.product_id.name,
            'product_ref': self.product_id.default_code,
            'lot_name': self.lot_name,
            'expiration': self.expiration_date_text,
            'contiene_lines': contiene_lines,
            'labels': labels,
            'total': self.quantity,
        }
