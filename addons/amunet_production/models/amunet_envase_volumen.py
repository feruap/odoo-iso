# -*- coding: utf-8 -*-
"""Consumir por volumen un material que se almacena por envase.

EL CASO. El agua se compra, se almacena y se entrega POR GALON de 20 L: el
producto se mide en Units y Almacen nunca reparte mililitros. Pero las 30 recetas
que la usan la piden en MILILITROS, porque eso es lo que se ocupa en la mesa. Y
Units y ml son unidades incompatibles, asi que ninguna de esas recetas se podia
fabricar: al 23-sep-2026 no habia UN SOLO consumo historico de agua tridestilada
en una orden cerrada.

Cambiar la unidad del producto no se puede -- Odoo lo bloquea porque ya se usaron
otras, hay 8 movimientos en litros cerrados desde mayo.

LA SOLUCION (Mery, 23-sep-2026): que el operador capture EL LOTE y LOS MILILITROS
que de verdad uso, y que el sistema convierta eso a la fraccion de envase que
corresponde y la descuente.

    el operador anota:  980 ml del lote ATR01082602
    el sistema descuenta:  980 / 20,000  =  0.049 galones

Asi el agua se queda en la receta -- que es lo que pide la trazabilidad, el lote
usado tiene que quedar en el expediente del lote -- y nadie hace cuentas a mano.

Sirve para cualquier material asi, no solo el agua: basta ponerle su contenido de
envase.
"""

from odoo import _, api, fields, models
from odoo.exceptions import UserError

# Cuanto puede apartarse lo anotado de la receta antes de preguntar. 25% deja
# pasar el ajuste normal de mesa y caza los errores de dedo, que siempre son
# de un orden de magnitud (98 o 9,800 en lugar de 980).
TOLERANCIA_VOLUMEN = 0.25


class ProductTemplate(models.Model):
    _inherit = 'product.template'

    amunet_contenido_envase = fields.Float(
        string='Contenido del envase',
        digits='Product Unit of Measure',
        help='Cuánto trae un envase, en la unidad de consumo. Para el agua: '
             '20000 si el galón es de 20 L y se consume en ml.\n\n'
             'Se usa cuando el material se almacena y se entrega por envase '
             'completo pero se consume por volumen: el operador anota los ml '
             'que usó y el sistema descuenta la fracción de envase.')
    amunet_uom_consumo_id = fields.Many2one(
        'uom.uom', string='Unidad de consumo',
        help='En qué unidad se anota lo que se usó (ml, g…). Debe ser distinta '
             'de la unidad de almacén.')


class StockMove(models.Model):
    _inherit = 'stock.move'

    amunet_consumo_por_volumen = fields.Boolean(
        string='Se consume por volumen',
        compute='_compute_amunet_consumo_por_volumen',
        help='Técnico: el material se guarda por envase pero se anota por '
             'volumen. Lo usa la vista para pedir los ml en vez de la fracción.')
    amunet_ml_usados = fields.Float(
        string='Cantidad usada (volumen)', digits='Product Unit of Measure',
        help='Lo que de verdad se ocupó, en la unidad de consumo del material '
             '(ml para el agua). El sistema convierte solo a la fracción de '
             'envase que se descuenta.')
    amunet_envase_equivalente = fields.Float(
        string='Equivale a', digits='Product Unit of Measure',
        compute='_compute_amunet_envase_equivalente',
        help='La fracción de envase que sale del volumen anotado.')
    amunet_ml_receta = fields.Float(
        string='Receta (ml)', digits='Product Unit of Measure',
        compute='_compute_amunet_ml_receta',
        help='Lo que la receta pide, en la unidad de consumo del material. Es '
             'el mismo dato que la cantidad a consumir, pero en mililitros en '
             'vez de en fracción de envase: 0.049 garrafones son 980 ml.\n\n'
             'El operador compara ESTE número contra lo que anotó; la fracción '
             'la usa el sistema para descontar del inventario.')

    @api.depends('product_id', 'product_id.amunet_contenido_envase')
    def _compute_amunet_consumo_por_volumen(self):
        for move in self:
            tmpl = move.product_id.product_tmpl_id
            move.amunet_consumo_por_volumen = bool(
                tmpl and tmpl.amunet_contenido_envase > 0)

    @api.depends('product_uom_qty', 'product_id.amunet_contenido_envase')
    def _compute_amunet_ml_receta(self):
        """La cantidad planeada, traducida a la unidad de consumo.

        Al operador la fraccion no le dice nada: su receta dice 980 ml y su
        garrafon dice 20 L. Ver 0.0490 lo obliga a adivinar, y no le deja con
        que darse cuenta si captura 98 o 9,800 por error -- a simple vista
        0.0049 y 0.0490 son el mismo numero. Peor: quien ve 0.0490 donde
        espera una cantidad de trabajo tiende a "corregirlo" a 1, y eso
        descarga el garrafon entero.
        """
        for move in self:
            contenido = move.product_id.product_tmpl_id.amunet_contenido_envase
            move.amunet_ml_receta = (move.product_uom_qty or 0.0) * contenido

    @api.depends('amunet_ml_usados', 'product_id.amunet_contenido_envase')
    def _compute_amunet_envase_equivalente(self):
        for move in self:
            contenido = move.product_id.product_tmpl_id.amunet_contenido_envase
            move.amunet_envase_equivalente = (
                move.amunet_ml_usados / contenido) if contenido else 0.0

    @api.onchange('amunet_ml_usados')
    def _onchange_amunet_ml_usados(self):
        """Al anotar el volumen, se llena sola la cantidad que se descuenta.

        Y si lo anotado se aparta mucho de la receta, se avisa antes de seguir.
        Es el unico control que tiene el operador: la cantidad planeada y la
        anotada van en unidades distintas, asi que no las puede comparar de un
        vistazo. Un cero de mas en 980 son 9,800 ml, casi medio garrafon.
        """
        for move in self:
            if not move.amunet_consumo_por_volumen:
                continue
            contenido = move.product_id.product_tmpl_id.amunet_contenido_envase
            if contenido:
                move.amunet_qty_used = move.amunet_ml_usados / contenido
            receta = move.amunet_ml_receta
            usado = move.amunet_ml_usados
            if receta and usado and abs(usado - receta) > receta * TOLERANCIA_VOLUMEN:
                unidad = move.product_id.product_tmpl_id.amunet_uom_consumo_id.name
                return {'warning': {
                    'title': _('Revisa la cantidad de %s') % move.product_id.display_name,
                    'message': _(
                        'La receta pide %(receta).0f %(unidad)s y anotaste '
                        '%(usado).0f %(unidad)s: %(veces)s.\n\n'
                        'Si de verdad usaste esa cantidad, déjala y sigue; el '
                        'sistema descontará %(fraccion).4f del envase. Si fue un '
                        'error de dedo, corrígela ahora.'
                    ) % {
                        'receta': receta, 'usado': usado, 'unidad': unidad,
                        'veces': (_('%.1f veces más') % (usado / receta)) if usado > receta
                                 else (_('%.0f%% de lo previsto') % (usado * 100.0 / receta)),
                        'fraccion': (usado / contenido) if contenido else 0.0,
                    },
                }}

    def _amunet_aplicar_consumo_por_volumen(self):
        """Pasa el volumen anotado a la cantidad que se descuenta del envase.

        Se llama al cerrar la orden, por si el operador capturo los ml y el
        onchange no corrio (captura por importacion, por kiosco o por codigo).
        """
        for move in self:
            if not move.amunet_consumo_por_volumen or not move.amunet_ml_usados:
                continue
            contenido = move.product_id.product_tmpl_id.amunet_contenido_envase
            if not contenido:
                continue
            esperado = move.amunet_ml_usados / contenido
            if abs((move.amunet_qty_used or 0.0) - esperado) > 1e-9:
                move.amunet_qty_used = esperado
            # El aviso de la pantalla no corre cuando se captura por kiosco o
            # por importacion, asi que la desviacion queda asentada en el
            # expediente de la orden. Es un registro, no un candado: la
            # cantidad que se uso es la que se uso.
            receta = move.amunet_ml_receta
            if receta and abs(move.amunet_ml_usados - receta) > receta * TOLERANCIA_VOLUMEN:
                unidad = move.product_id.product_tmpl_id.amunet_uom_consumo_id.name
                if move.raw_material_production_id:
                    move.raw_material_production_id.sudo().message_post(body=_(
                        '<b>%(prod)s</b>: se anotaron %(usado).0f %(unidad)s y la '
                        'receta pide %(receta).0f %(unidad)s. Se descontaron '
                        '%(fraccion).4f del envase.'
                    ) % {
                        'prod': move.product_id.display_name,
                        'usado': move.amunet_ml_usados, 'receta': receta,
                        'unidad': unidad, 'fraccion': esperado,
                    })

    @api.constrains('amunet_ml_usados')
    def _check_amunet_ml_usados(self):
        for move in self:
            if move.amunet_ml_usados < 0:
                raise UserError(_(
                    'La cantidad usada de %s no puede ser negativa.'
                ) % move.product_id.display_name)
