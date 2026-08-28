# -*- coding: utf-8 -*-
import logging

from odoo import models, _

_logger = logging.getLogger(__name__)


class StockPicking(models.Model):
    """Validar un traslado sin quedarse a medias.

    `button_validate()` no siempre valida: cuando algo necesita confirmacion
    devuelve una accion de ventana en lugar de terminar. El caso que nos toca es
    el de `product_expiry`, que pregunta si de veras se quiere mover un lote
    caducado o por caducar. Desde la interfaz aparece un dialogo y la persona
    contesta; desde codigo, si nadie contesta, el traslado se queda en
    'assigned' y el inventario no se mueve -en silencio, que es lo peor-.

    Aqui esa respuesta se da explicitamente: mover mercancia vencida a retenidos
    o a cuarentena es justo lo que se quiere hacer.
    """
    _inherit = 'stock.picking'

    def amunet_validar(self):
        self.ensure_one()
        resultado = self.button_validate()
        if not isinstance(resultado, dict):
            return self.state == 'done'

        modelo = resultado.get('res_model')
        if not modelo or modelo not in self.env:
            _logger.warning('Traslado %s: button_validate devolvio algo que no se pudo '
                            'atender (%s).', self.name, resultado.get('type'))
            return self.state == 'done'

        asistente = self.env[modelo].with_context(**(resultado.get('context') or {})).create({})
        for metodo in ('process', 'action_confirm', 'action_validate', 'confirm'):
            if hasattr(asistente, metodo):
                getattr(asistente, metodo)()
                break
        else:
            _logger.warning('Traslado %s: el asistente %s no tiene un metodo conocido '
                            'para confirmar.', self.name, modelo)
        return self.state == 'done'
