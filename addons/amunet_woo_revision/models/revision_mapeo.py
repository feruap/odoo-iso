# -*- coding: utf-8 -*-
"""Revision diaria del mapeo Woo <-> Odoo.

SOLO LECTURA sobre la tienda: unicamente hace GET al API de WooCommerce a
traves del backend existente. Nunca escribe en la tienda ni modifica
inventario, lotes ni ordenes de fabricacion.

Resultado: un registro de revision con sus lineas, clasificadas en
  - nuevo     : publicado en la tienda y sin mapeo en Odoo
  - huerfano  : mapeado en Odoo pero ya no existe en la tienda
  - cambio    : existe en ambos pero cambio SKU, nombre o estado
  - sin_sku   : publicado en la tienda sin SKU (no se puede emparejar)
"""

import logging
import unicodedata

from odoo import api, fields, models

_logger = logging.getLogger(__name__)

MAX_PAGINAS = 40
POR_PAGINA = 100

# Productos que NO se mapean en esta etapa (decision de Fernando, 21-ago-2026):
# los de caducidad corta / muy corta / cortesia son remanentes en liquidacion.
# No forman parte del catalogo vigente ni cuentan para demanda, asi que
# reportarlos cada noche como "no emparejados" solo genera ruido.
# La busqueda es sin acentos y en minusculas, sobre las categorias de Woo
# y sobre el nombre del producto.
EXCLUIR_PATRONES = ('caducidad', 'cortesia')


def _sin_acentos(texto):
    txt = unicodedata.normalize('NFKD', texto or '')
    return ''.join(c for c in txt if not unicodedata.combining(c)).lower()


def _esta_excluido(producto):
    """True si el producto no debe mapearse en esta etapa."""
    partes = [c.get('name') or '' for c in (producto.get('categories') or [])]
    partes.append(producto.get('name') or '')
    texto = _sin_acentos(' | '.join(partes))
    return any(pat in texto for pat in EXCLUIR_PATRONES)


class AmunetRevisionMapeo(models.Model):
    _name = 'amunet.revision.mapeo'
    _description = 'Revision del mapeo Woo <-> Odoo'
    _inherit = ['mail.thread']
    _order = 'fecha desc, id desc'

    name = fields.Char(string='Referencia', readonly=True, default='Nueva')
    fecha = fields.Datetime(string='Fecha', readonly=True, default=fields.Datetime.now)
    backend_id = fields.Many2one('amunet.woo.backend', string='Tienda', readonly=True)
    state = fields.Selection(
        [('ok', 'Sin pendientes'), ('atencion', 'Requiere atencion'), ('error', 'Error')],
        string='Resultado', default='ok', readonly=True,
    )
    total_tienda = fields.Integer(string='Productos en la tienda', readonly=True)
    total_publicados = fields.Integer(string='Publicados', readonly=True)
    total_mapeo = fields.Integer(string='Registros en el mapeo', readonly=True)
    n_emparejados = fields.Integer(string='Emparejados', readonly=True)
    n_nuevos = fields.Integer(string='Nuevos sin emparejar', readonly=True)
    n_huerfanos = fields.Integer(string='Huerfanos', readonly=True)
    n_cambios = fields.Integer(string='Con cambios', readonly=True)
    n_sin_sku = fields.Integer(string='Publicados sin SKU', readonly=True)
    n_clave_distinta = fields.Integer(string='Clave distinta pendiente', readonly=True)
    n_excluidos = fields.Integer(
        string='Omitidos (caducidad corta / cortesia)', readonly=True,
        help='Publicados sin mapeo que se omiten a proposito por ser de '
             'caducidad corta, muy corta o cortesia.',
    )
    mensaje = fields.Text(string='Detalle', readonly=True)
    line_ids = fields.One2many(
        'amunet.revision.mapeo.linea', 'revision_id', string='Hallazgos', readonly=True,
    )

    # ------------------------------------------------------------------
    # Lectura de la tienda (GET unicamente)
    # ------------------------------------------------------------------
    def _leer_catalogo(self, backend):
        productos = []
        pagina = 1
        while pagina <= MAX_PAGINAS:
            res = backend._wc_get('products', {
                'per_page': POR_PAGINA, 'page': pagina, 'status': 'any',
            })
            datos = res[0] if isinstance(res, tuple) else res
            if not datos:
                break
            productos.extend(datos)
            if len(datos) < POR_PAGINA:
                break
            pagina += 1
        return productos

    # ------------------------------------------------------------------
    # Revision
    # ------------------------------------------------------------------
    @api.model
    def cron_revisar(self):
        """Punto de entrada del cron de las 23:00."""
        backend = self.env['amunet.woo.backend'].search([], limit=1)
        if not backend:
            _logger.warning('Revision de mapeo: no hay backend de WooCommerce configurado.')
            return False
        return self.revisar(backend)

    @api.model
    def revisar(self, backend):
        rev = self.create({
            'name': 'REV/%s' % fields.Datetime.now().strftime('%Y%m%d-%H%M'),
            'backend_id': backend.id,
        })
        try:
            productos = self._leer_catalogo(backend)
        except Exception as err:  # noqa: BLE001 - se reporta, no se propaga
            rev.write({
                'state': 'error',
                'mensaje': 'No se pudo leer la tienda: %s' % err,
            })
            _logger.exception('Revision de mapeo: fallo la lectura de la tienda.')
            return rev

        Mapeo = self.env['amunet.woo.product.mapping']
        mapeos = Mapeo.search([])
        por_id = {}
        por_sku = {}
        for m in mapeos:
            if m.woo_product_id:
                por_id[int(m.woo_product_id)] = m
            sku = (m.woo_sku or '').strip().upper()
            if sku:
                por_sku[sku] = m

        ids_tienda = set()
        skus_tienda = set()
        lineas = []
        emparejados = 0
        nuevos = huerfanos = cambios = sin_sku = excluidos = 0

        for p in productos:
            wid = int(p.get('id') or 0)
            sku = (p.get('sku') or '').strip()
            ids_tienda.add(wid)
            if sku:
                skus_tienda.add(sku.upper())
            if p.get('status') != 'publish':
                continue
            m = por_id.get(wid) or (por_sku.get(sku.upper()) if sku else None)
            if not m:
                if _esta_excluido(p):
                    # Caducidad corta / cortesia: se cuentan pero no se reportan.
                    excluidos += 1
                    continue
                if not sku:
                    sin_sku += 1
                    lineas.append((0, 0, {
                        'tipo': 'sin_sku', 'woo_product_id': wid,
                        'woo_sku': '', 'woo_name': p.get('name') or '',
                        'detalle': 'Publicado en la tienda sin SKU: no se puede emparejar.',
                    }))
                else:
                    nuevos += 1
                    lineas.append((0, 0, {
                        'tipo': 'nuevo', 'woo_product_id': wid, 'woo_sku': sku,
                        'woo_name': p.get('name') or '',
                        'detalle': 'Publicado en la tienda y sin mapeo en Odoo.',
                    }))
                continue
            emparejados += 1
            difs = []
            # Solo es "cambio" si el mapeo TENIA un valor guardado y ahora difiere.
            # Si el mapeo nunca lo capturo, no es un cambio: es un dato faltante.
            if sku and (m.woo_sku or '').strip() and (m.woo_sku or '').strip() != sku:
                difs.append('SKU: mapeo=%s / tienda=%s' % (m.woo_sku or '-', sku))
            nombre = (p.get('name') or '').strip()
            if nombre and (m.woo_name or '').strip() and (m.woo_name or '').strip() != nombre:
                difs.append('Nombre cambio en la tienda')
            estado = p.get('status')
            if ('woo_status' in Mapeo._fields and (m.woo_status or '')
                    and estado and m.woo_status != estado):
                difs.append('Estado: mapeo=%s / tienda=%s' % (m.woo_status or '-', estado))
            if difs:
                cambios += 1
                lineas.append((0, 0, {
                    'tipo': 'cambio', 'woo_product_id': wid, 'woo_sku': sku,
                    'woo_name': nombre, 'mapping_id': m.id,
                    'detalle': ' | '.join(difs),
                }))

        for m in mapeos:
            wid = int(m.woo_product_id) if m.woo_product_id else 0
            sku = (m.woo_sku or '').strip().upper()
            if wid in ids_tienda or (sku and sku in skus_tienda):
                continue
            huerfanos += 1
            lineas.append((0, 0, {
                'tipo': 'huerfano', 'woo_product_id': wid, 'woo_sku': m.woo_sku or '',
                'woo_name': m.woo_name or '', 'mapping_id': m.id,
                'detalle': 'Mapeado en Odoo pero ya no aparece en la tienda.',
            }))

        clave_pend = Mapeo.search_count([
            ('clave_coincide', '=', False),
            ('clave_decidida', '=', 'pendiente'),
        ])

        publicados = len([p for p in productos if p.get('status') == 'publish'])
        pendientes = nuevos + huerfanos + cambios
        rev.write({
            'state': 'atencion' if pendientes else 'ok',
            'total_tienda': len(productos),
            'total_publicados': publicados,
            'total_mapeo': len(mapeos),
            'n_emparejados': emparejados,
            'n_nuevos': nuevos,
            'n_huerfanos': huerfanos,
            'n_cambios': cambios,
            'n_sin_sku': sin_sku,
            'n_clave_distinta': clave_pend,
            'n_excluidos': excluidos,
            'line_ids': lineas,
            'mensaje': (
                'Tienda: %s productos (%s publicados). Mapeo: %s registros.\n'
                'Emparejados: %s | Nuevos sin emparejar: %s | Huerfanos: %s | '
                'Con cambios: %s | Publicados sin SKU: %s\n'
                'Claves distintas pendientes de decidir: %s\n'
                'Omitidos a proposito (caducidad corta / cortesia): %s'
                % (len(productos), publicados, len(mapeos), emparejados,
                   nuevos, huerfanos, cambios, sin_sku, clave_pend, excluidos)
            ),
        })
        if pendientes:
            rev.message_post(body=rev.mensaje.replace('\n', '<br/>'))
        _logger.info('Revision de mapeo %s: %s', rev.name, rev.mensaje)
        return rev

    def action_revisar_ahora(self):
        self.ensure_one()
        return self.revisar(self.backend_id or self.env['amunet.woo.backend'].search([], limit=1))


class AmunetRevisionMapeoLinea(models.Model):
    _name = 'amunet.revision.mapeo.linea'
    _description = 'Hallazgo de la revision del mapeo'
    _order = 'tipo, woo_sku'

    revision_id = fields.Many2one(
        'amunet.revision.mapeo', string='Revision', required=True, ondelete='cascade', index=True,
    )
    tipo = fields.Selection(
        [
            ('nuevo', 'Nuevo sin emparejar'),
            ('huerfano', 'Huerfano (ya no esta en la tienda)'),
            ('cambio', 'Cambio detectado'),
            ('sin_sku', 'Publicado sin SKU'),
        ],
        string='Tipo', required=True, index=True,
    )
    woo_product_id = fields.Integer(string='ID en la tienda')
    woo_sku = fields.Char(string='SKU tienda')
    woo_name = fields.Char(string='Nombre')
    detalle = fields.Char(string='Detalle')
    mapping_id = fields.Many2one('amunet.woo.product.mapping', string='Mapeo')
