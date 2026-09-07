# -*- coding: utf-8 -*-
"""El enlace Odoo <-> tienda de un producto NUEVO, sin que nadie lo persiga.

Cuando en la tienda se publica un producto nuevo, el mu-plugin de la tienda le
crea su pieza -R y sus gemelos de caducidad corta y cortesia. Del lado de Odoo
faltaba el otro extremo: el renglon en la tabla de mapeo (accion 1109) que dice
"este producto de Odoo es aquel de la tienda". Sin ese renglon confirmado el
puente no publica su anaquel.

Este proceso diario hace las dos cosas que antes eran manuales:

  1. Lee el catalogo de la tienda (GET, como el boton "Leer catalogo Woo") para
     que los productos nuevos aparezcan como mapeos pendientes.
  2. Confirma solos los pendientes que cumplen TODO esto:
       - la sugerencia fue por SKU EXACTO y unico (default_code == SKU Woo),
       - nadie los ha revisado (sin reviewer_id),
       - el producto Woo es simple o variable, publicado, y no es un gemelo
         (el nombre no empieza con "Caducidad Corta" / "Cortesia"),
       - el producto Odoo esta activo y no tiene ya otro mapeo confirmado.
     Queda constancia en el chatter del mapeo.

Todo lo demas (SKU que no coincide, dos productos con el mismo codigo, un
gemelo, un producto ya revisado) se queda como esta, para que lo decida una
persona. Parametro amunet_woocommerce.auto_mapeo = 'off' lo apaga.
"""
import logging

from odoo import api, fields, models, _

_logger = logging.getLogger(__name__)

PARAM_AUTO = 'amunet_woocommerce.auto_mapeo'
METODO_AUTO = 'SKU exacto (sugerencia automática)'


class AmunetWooBackendAutoMapeo(models.Model):
    _inherit = 'amunet.woo.backend'

    def _amunet_es_gemelo(self, nombre):
        n = (nombre or '').strip().lower()
        return n.startswith('caducidad corta') or n.startswith('caducidad muy corta') \
            or n.startswith('cortesia') or n.startswith('cortesía')

    def _amunet_auto_confirmar_mapeos(self):
        """Confirma los pendientes que son un SKU exacto y nadie ha tocado."""
        self.ensure_one()
        Mapping = self.env['amunet.woo.product.mapping']
        pendientes = Mapping.search([
            ('backend_id', '=', self.id),
            ('active', '=', True),
            ('relation_state', '=', 'pending'),
            ('product_id', '!=', False),
            ('reviewer_id', '=', False),
            ('match_method', '=', METODO_AUTO),
            ('woo_parent_id', '=', 0),
            ('woo_type', 'in', ('simple', 'variable')),
            ('woo_status', '=', 'publish'),
        ])
        confirmados = Mapping.browse()
        for m in pendientes:
            if self._amunet_es_gemelo(m.woo_name):
                continue
            if not m.product_id.active:
                continue
            sku = (m.woo_sku or '').strip()
            if not sku or (m.product_id.default_code or '').strip() != sku:
                continue
            # el mismo SKU en dos productos Odoo: que lo decida una persona
            iguales = self.env['product.product'].search_count([
                ('default_code', '=', sku),
                ('company_id', 'in', [False, self.company_id.id]),
            ])
            if iguales != 1:
                continue
            otro = Mapping.search_count([
                ('backend_id', '=', self.id),
                ('active', '=', True),
                ('relation_state', '=', 'confirmed'),
                ('product_id', '=', m.product_id.id),
                ('id', '!=', m.id),
            ])
            if otro:
                continue
            m.with_context(skip_review_stamp=True).write({
                'relation_state': 'confirmed',
                'confidence': 'high',
                'match_method': _('SKU exacto (confirmado automáticamente)'),
                'review_date': fields.Datetime.now(),
            })
            m.message_post(body=_(
                'Vinculado automáticamente: el SKU %(sku)s es exacto y único en Odoo '
                '(%(producto)s). Si no es correcto, cámbialo aquí y quedará como revisado a mano.',
                sku=sku, producto=m.product_id.display_name))
            confirmados |= m
        return confirmados

    @api.model
    def _cron_amunet_auto_mapeo(self):
        if (self.env['ir.config_parameter'].sudo().get_param(PARAM_AUTO, 'on') or 'on').lower() == 'off':
            return True
        for backend in self.search([('active', '=', True)]):
            try:
                backend.action_import_catalog()
            except Exception as exc:  # noqa: BLE001  el cron nunca debe morir
                _logger.warning('Auto-mapeo: no se pudo leer el catalogo de %s: %s', backend.display_name, exc)
                continue
            try:
                confirmados = backend._amunet_auto_confirmar_mapeos()
                if confirmados:
                    backend.message_post(body=_(
                        'Auto-mapeo: %(n)s producto(s) nuevo(s) vinculados por SKU exacto: %(lista)s',
                        n=len(confirmados), lista=', '.join(confirmados.mapped('woo_sku'))))
            except Exception as exc:  # noqa: BLE001
                _logger.exception('Auto-mapeo: fallo al confirmar en %s: %s', backend.display_name, exc)
        return True
