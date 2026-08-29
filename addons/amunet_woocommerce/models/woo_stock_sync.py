# -*- coding: utf-8 -*-
"""Odoo manda el inventario de la tienda, y la tienda le regresa lo que vendio.

Son dos caminos, cada uno con su candado y los dos apagados de nacimiento:

  1) SINCRONIZAR (Odoo -> tienda).  Se lee el anaquel de piezas -solo lotes que
     Calidad ya libero- y se le manda a la tienda la lista completa por producto.
     La tienda no suma: deja su inventario IDENTICO al que se le mando, y antes de
     confirmar relee su propia base para comprobarlo. Si una sola familia no cuadra,
     deshace todo y no cambia nada.

  2) TRAER VENTAS (tienda -> Odoo).  Se leen las ventas que la tienda registro desde
     la ultima vez y se descuentan del anaquel con un movimiento de existencias real,
     con su lote. Cada movimiento de la tienda se consume UNA sola vez: queda
     asentado en amunet.woo.stock.consumo con el id que la tienda le dio.

Mientras el puente no este encendido, almacen sigue capturando en los dos lados.
"""

import logging
import re
from datetime import datetime, timedelta

import requests

from odoo import _, api, fields, models
from odoo.exceptions import UserError

_logger = logging.getLogger(__name__)


def _fecha_valida(texto):
    try:
        datetime.strptime(texto, FORMATO_FECHA)
        return True
    except (TypeError, ValueError):
        return False


def norm_lote(texto):
    """Mismo criterio que usa la tienda: sin espacios y en mayusculas.

    La tienda compara asi, y si aqui comparamos distinto un lote como
    '0426/01/ S5P' no se reconoceria y la venta se quedaria sin descontar.
    """
    return re.sub(r'\s+', '', (texto or '').strip().upper())

TIEMPO_LIMITE = 60
RUTA_SINCRONIZAR = '/wp-json/amunet-inv/v1/sincronizar'
RUTA_VENTAS = '/wp-json/amunet-inv/v1/ventas'
FORMATO_FECHA = '%Y-%m-%d %H:%M:%S'
# Espacio de nombres de los advisory locks de este puente.
CANDADO_ESPACIO = 0x414D554E  # 'AMUN'


class AmunetWooStockConsumo(models.Model):
    """Cada venta de la tienda que ya se descontó en Odoo. Evita descontarla dos veces."""

    _name = 'amunet.woo.stock.consumo'
    _description = 'Venta de la tienda ya descontada en Odoo'
    _order = 'id desc'

    backend_id = fields.Many2one('amunet.woo.backend', required=True, ondelete='cascade',
                                 index=True, string='Tienda')
    # La compania se copia AQUI y ya no se mueve. Si manana cambian la compania
    # del backend, este renglon debe seguir contando para la compania en la que
    # de verdad se movio el inventario.
    company_id = fields.Many2one('res.company', string='Compania', required=True,
                                 index=True, readonly=True)
    tienda_mov_id = fields.Integer('Movimiento en la tienda', required=True, index=True,
                                   help='El id que la tienda le dio a ese movimiento. '
                                        'Es la llave que impide descontarlo dos veces.')
    woo_product_id = fields.Integer('Producto en la tienda', index=True)
    product_id = fields.Many2one('product.product', string='Producto', ondelete='restrict',
                                 check_company=True)
    lot_id = fields.Many2one('stock.lot', string='Lote', ondelete='restrict',
                             check_company=True)
    lote_texto = fields.Char('Lote (como lo dijo la tienda)')
    cantidad = fields.Float('Piezas descontadas')
    pedido_tienda = fields.Integer('Pedido en la tienda')
    fecha_tienda = fields.Datetime('Fecha del movimiento en la tienda')
    # restrict, no set null: si el movimiento se borrara nos quedariamos con un
    # renglon que dice "descontado" sin poder ensenar de donde salio.
    move_id = fields.Many2one('stock.move', string='Movimiento de existencias',
                              ondelete='restrict', check_company=True)
    estado = fields.Selection([
        ('aplicado', 'Descontado'),
        ('sin_lote', 'Sin lote reconocible'),
        ('sin_producto', 'Sin producto mapeado'),
        ('sin_existencia', 'Sin existencia suficiente'),
        ('lote_retenido', 'Lote no liberado por Calidad'),
        ('sin_destino', 'Falta la ubicacion de Clientes'),
        ('error_tecnico', 'Fallo tecnico'),
    ], default='aplicado', required=True, string='Resultado',
        help='Solo "Descontado" es definitivo. Todos los demas se vuelven a '
             'intentar en la siguiente corrida hasta que alguien los resuelva.')
    intentos = fields.Integer('Intentos', default=1, readonly=True)
    ultimo_intento = fields.Datetime('Ultimo intento', readonly=True)
    nota = fields.Char('Nota')

    # Los estados que NO son definitivos: se reintentan.
    PENDIENTES = ('sin_lote', 'sin_producto', 'sin_existencia',
                  'lote_retenido', 'sin_destino', 'error_tecnico')

    # En Odoo 19 las restricciones de tabla se declaran asi. Con _sql_constraints
    # el servidor solo avisa y NO crea la restriccion, y sin ella una venta se
    # podria descontar dos veces: es el candado central de todo esto.
    _mov_unico_por_tienda = models.Constraint(
        'UNIQUE (backend_id, tienda_mov_id)',
        'Ese movimiento de la tienda ya se habia descontado.',
    )


class AmunetWooBackend(models.Model):
    _inherit = 'amunet.woo.backend'

    allow_stock_consume = fields.Boolean(
        string='Traer las ventas de la tienda a Odoo',
        default=False, copy=False,
        help='Cuando esta encendido, Odoo lee las ventas que registro la tienda y las '
             'descuenta del anaquel de piezas. Nace apagado a proposito: encenderlo '
             'mueve existencias reales.')
    apt_ultima_venta = fields.Datetime(
        string='Ultima venta traida',
        copy=False,
        help='Hasta donde se leyeron las ventas de la tienda. De aqui arranca la '
             'siguiente lectura.')
    apt_ultima_venta_id = fields.Integer(
        string='Ultimo movimiento traido', default=0, copy=False,
        help='El id que la tienda le dio al ultimo movimiento leido. Junto con la '
             'fecha forma el cursor: sin el, dos ventas del mismo segundo se '
             'perdian o se repetian.')
    apt_venta_cliente_location_id = fields.Many2one(
        'stock.location', string='Destino de las ventas de la tienda',
        domain="[('usage','in',('customer','inventory','production'))]",
        help='A donde se manda lo que la tienda vendio. Normalmente Clientes.')

    # ------------------------------------------------------------------
    # 1. Odoo -> tienda
    # ------------------------------------------------------------------

    def _anaquel_payload(self):
        """Lo que Odoo tiene en el anaquel de piezas, listo para mandarse.

        Un producto entra aunque no tenga lotes liberados: mandarlo con la lista
        vacia es como Odoo dice "de esto ya no hay". Lo que NUNCA se manda es un
        producto sin mapeo confirmado, porque de ese Odoo no es el dueno.
        """
        self.ensure_one()
        mapeos = self.env['amunet.woo.product.mapping'].search([
            ('backend_id', '=', self.id),
            ('relation_state', '=', 'confirmed'),
            ('product_id', '!=', False),
        ])
        salida = []
        for mapeo in mapeos:
            lotes = []
            for fila in self._read_released_piece_stock(mapeo):
                if not fila.get('expiration_month') or not fila.get('expiration_year'):
                    # sin caducidad no se puede clasificar en la tienda: se omite
                    # y se deja constancia, en vez de mandar una fecha inventada.
                    _logger.warning(
                        'Puente: lote %s de %s no tiene caducidad; no se publica.',
                        fila.get('lot_number'), mapeo.product_id.default_code)
                    continue
                lotes.append({
                    'lote': fila['lot_number'],
                    'cantidad': round(float(fila['quantity']), 2),
                    'mes': int(fila['expiration_month']),
                    'anio': int(fila['expiration_year']),
                })
            salida.append({
                'product_id': int(mapeo.woo_product_id),
                'lotes': lotes,
            })
        return salida

    def _puente_llamar(self, metodo, ruta, payload=None, params=None):
        self.ensure_one()
        if not self.apt_wp_user or not self.apt_wp_app_password:
            raise UserError(_(
                'Falta el usuario de WordPress y su Application Password para hablar '
                'con la tienda. Los da Fernando; ningun agente los genera.'))
        base = (self.store_url or '').strip().rstrip('/')
        if not base.lower().startswith('https://'):
            # Con http:// el usuario y la Application Password viajarian en claro.
            raise UserError(_(
                'La direccion de la tienda tiene que ser https. Con http la contrasena '
                'viaja en claro por la red.'))
        url = '%s%s' % (base, ruta)
        try:
            respuesta = requests.request(
                metodo, url, json=payload, params=params,
                auth=(self.apt_wp_user, self.apt_wp_app_password),
                timeout=TIEMPO_LIMITE, verify=True, allow_redirects=False)
        except requests.RequestException as exc:
            raise UserError(_('No se pudo hablar con la tienda: %s') % exc)
        try:
            datos = respuesta.json()
        except ValueError:
            datos = {}
        if respuesta.status_code >= 400:
            detalle = datos.get('motivo') or datos.get('message') or respuesta.text[:300]
            errores = datos.get('errores') or []
            if errores:
                detalle = '%s\n- %s' % (detalle, '\n- '.join(errores[:10]))
            raise UserError(_('La tienda rechazo la peticion (%(c)s): %(d)s') % {
                'c': respuesta.status_code, 'd': detalle})
        return datos

    def _exigir_admin(self):
        """Esconder el boton no es seguridad: quien llame al metodo tambien pasa por aqui."""
        if not self.env.user.has_group('amunet_woocommerce.group_woo_admin'):
            raise UserError(_(
                'Solo el administrador de la integracion con la tienda puede mover '
                'existencias desde aqui.'))

    def action_sincronizar_existencias(self):
        """Deja el inventario de la tienda igual al anaquel de Odoo. Requiere el candado."""
        self.ensure_one()
        self._exigir_admin()
        if not self.allow_stock_publish:
            raise UserError(_(
                'La publicacion de existencias no esta habilitada para esta tienda. '
                'Un administrador debe encender "Permitir publicar existencias".'))
        return self._sincronizar(aplicar=True)

    def action_simular_sincronizacion(self):
        """Lo mismo pero sin escribir: dice que cambiaria. No requiere candado."""
        self.ensure_one()
        self._exigir_admin()
        return self._sincronizar(aplicar=False)

    def _sincronizar(self, aplicar=False):
        self.ensure_one()
        if aplicar:
            self._tomar_candado()
        productos = self._anaquel_payload()
        if not productos:
            raise UserError(_('No hay ningun mapeo confirmado con producto; no hay que mandar.'))
        corrida = int(fields.Datetime.now().strftime('%Y%m%d'))
        datos = self._puente_llamar('POST', RUTA_SINCRONIZAR, payload={
            'aplicar': bool(aplicar),
            'corrida': corrida,
            'productos': productos,
        })
        mensaje = _(
            '%(modo)s: %(fam)s familias | actualiza %(act)s, a cero %(cero)s, altas %(alta)s | '
            'la tienda pasa de %(antes)s a %(desp)s piezas.') % {
            'modo': _('Sincronizado') if aplicar else _('Simulacro'),
            'fam': datos.get('familias'), 'act': datos.get('actualiza'),
            'cero': datos.get('a_cero'), 'alta': datos.get('altas'),
            'antes': datos.get('piezas_antes'), 'desp': datos.get('piezas_despues'),
        }
        self._anotar_bitacora('stock_publish', mensaje)
        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'title': _('Inventario sincronizado') if aplicar else _('Simulacro (no se escribio nada)'),
                'message': mensaje,
                'type': 'success' if aplicar else 'warning',
                'sticky': not aplicar,
            },
        }

    @api.model
    def _cron_sincronizar_existencias(self):
        for backend in self.search([('allow_stock_publish', '=', True), ('active', '=', True)]):
            try:
                backend._sincronizar(aplicar=True)
            except Exception as exc:  # noqa: BLE001  el cron nunca debe morir
                _logger.exception('Puente: fallo la sincronizacion de %s: %s', backend.display_name, exc)

    # ------------------------------------------------------------------
    # 2. tienda -> Odoo
    # ------------------------------------------------------------------

    @api.model
    def _cron_traer_ventas(self):
        for backend in self.search([('allow_stock_consume', '=', True), ('active', '=', True)]):
            try:
                backend.traer_ventas()
            except Exception as exc:  # noqa: BLE001
                _logger.exception('Puente: fallo traer ventas de %s: %s', backend.display_name, exc)

    def action_traer_ventas(self):
        """El boton. El cron llama a traer_ventas() directo, sin este filtro."""
        self.ensure_one()
        self._exigir_admin()
        mensaje = self.traer_ventas()
        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {'title': _('Ventas traidas'), 'message': mensaje,
                       'type': 'success', 'sticky': True},
        }

    def traer_ventas(self, limite=500, max_paginas=20):
        """Lee las ventas nuevas de la tienda y las descuenta del anaquel.

        Tres reglas que se ganaron a golpes:

        1. El cursor es la pareja (fecha, id), y solo avanza cuando la tienda
           devuelve las dos cosas y la pareja es ESTRICTAMENTE mayor que la que
           traiamos. Con solo la fecha, dos ventas del mismo segundo se perdian.
        2. El cursor solo avanza cuando de TODOS los movimientos de la pagina
           quedo constancia escrita. Si no se pudo dejar constancia de uno, se
           corta la pagina y el cursor se queda donde estaba: mas vale volver a
           leer que perder una venta.
        3. Lo que no se pudo descontar se vuelve a intentar en la corrida
           siguiente. Solo "aplicado" es definitivo.
        """
        self.ensure_one()
        if not self.allow_stock_consume:
            raise UserError(_(
                'Traer las ventas de la tienda no esta habilitado para esta tienda.'))
        if not self.apt_ultima_venta:
            # Arrancar en "hace un dia" se comeria en silencio todo lo anterior.
            raise UserError(_(
                'Falta decir desde cuando hay que traer las ventas. Pon una fecha en '
                '"Ultima venta traida" (el momento a partir del cual la tienda es la '
                'fuente) antes de encender esto.'))
        self._tomar_candado()

        Consumo = self.env['amunet.woo.stock.consumo']
        reintentados = self._reintentar_pendientes()

        desde_txt = fields.Datetime.to_string(self.apt_ultima_venta)
        desde_id = int(self.apt_ultima_venta_id or 0)
        # El techo de la ventana se fija UNA vez: si se recalculara en cada
        # pagina, la ventana se movería mientras la recorremos.
        hasta_txt = fields.Datetime.to_string(fields.Datetime.now())

        leidos = aplicados = pendientes = repetidos = 0
        paginas = 0
        aviso = ''
        while paginas < max_paginas:
            paginas += 1
            datos = self._puente_llamar('GET', RUTA_VENTAS, params={
                'desde': desde_txt,
                'desde_id': desde_id,
                'hasta': hasta_txt,
                'limite': limite,
            })
            movimientos = datos.get('movimientos') or []
            leidos += len(movimientos)

            ids_pagina = [int(m.get('id') or 0) for m in movimientos if m.get('id')]
            previos = {}
            if ids_pagina:
                for fila in Consumo.search([('backend_id', '=', self.id),
                                            ('tienda_mov_id', 'in', ids_pagina)]):
                    previos[fila.tienda_mov_id] = fila

            corto = False
            for mov in movimientos:
                mov_id = int(mov.get('id') or 0)
                if not mov_id:
                    aviso = _('La tienda mando un movimiento sin id.')
                    corto = True
                    break
                fila = previos.get(mov_id)
                if fila and fila.estado == 'aplicado':
                    repetidos += 1
                    continue
                estado = self._intentar_movimiento(mov, fila)
                if estado is None:
                    # No se pudo dejar constancia: no se avanza ni un paso mas.
                    aviso = _('No se pudo registrar el resultado del movimiento %s; '
                              'la corrida se detuvo sin mover el cursor.') % mov_id
                    corto = True
                    break
                if estado == 'aplicado':
                    aplicados += 1
                else:
                    pendientes += 1
            if corto:
                break

            # ---- avanzar el cursor, con la pareja completa y comprobada ----
            nueva_fecha = datos.get('ultima_fecha')
            nuevo_id = datos.get('ultimo_id')
            if not movimientos:
                break
            if not _fecha_valida(nueva_fecha) or nuevo_id in (None, False):
                aviso = _('La tienda devolvio un cursor incompleto o con una fecha '
                          'invalida; no se movio el cursor.')
                break
            nuevo_id = int(nuevo_id)
            if (nueva_fecha, nuevo_id) <= (desde_txt, desde_id):
                aviso = _('La tienda devolvio el mismo cursor otra vez; se detuvo la '
                          'corrida para no dar vueltas en falso.')
                break
            desde_txt, desde_id = nueva_fecha, nuevo_id
            self.write({
                'apt_ultima_venta': datetime.strptime(desde_txt, FORMATO_FECHA),
                'apt_ultima_venta_id': desde_id,
            })
            if not datos.get('hay_mas'):
                break

        mensaje = _('Ventas de la tienda: leidas %(n)s en %(p)s pagina(s) | descontadas '
                    '%(a)s | pendientes %(o)s | ya estaban %(r)s | reintentos previos '
                    '%(x)s.') % {
            'n': leidos, 'p': paginas, 'a': aplicados, 'o': pendientes,
            'r': repetidos, 'x': reintentados}
        if aviso:
            mensaje = '%s  AVISO: %s' % (mensaje, aviso)
        self._anotar_bitacora('stock_consume', mensaje)
        return mensaje

    def _reintentar_pendientes(self):
        """Vuelve a intentar lo que quedo sin descontar en corridas anteriores.

        Sin esto, una venta que fallo una vez se quedaria fuera para siempre:
        el cursor ya paso por encima de ella y nadie volveria a mirarla.
        """
        self.ensure_one()
        Consumo = self.env['amunet.woo.stock.consumo']
        pendientes = Consumo.search([
            ('backend_id', '=', self.id),
            ('estado', 'in', list(Consumo.PENDIENTES)),
        ], order='tienda_mov_id asc', limit=200)
        hechos = 0
        for fila in pendientes:
            mov = {
                'id': fila.tienda_mov_id,
                'product_id': fila.woo_product_id,
                'lote': fila.lote_texto,
                'cantidad': fila.cantidad,
                'order_id': fila.pedido_tienda,
                'fecha': fields.Datetime.to_string(fila.fecha_tienda) if fila.fecha_tienda else None,
            }
            if self._intentar_movimiento(mov, fila) == 'aplicado':
                hechos += 1
        return hechos

    def _intentar_movimiento(self, mov, fila=None):
        """Un movimiento de la tienda, aislado.

        Devuelve el estado con el que quedo, o None si NI SIQUIERA se pudo
        dejar constancia (y entonces quien llama debe detenerse).
        """
        self.ensure_one()
        try:
            with self.env.cr.savepoint():
                return self._descontar_venta(mov, fila).estado
        except Exception as exc:  # noqa: BLE001
            _logger.exception('Puente: fallo el movimiento %s: %s', mov.get('id'), exc)
        # El intento reventó: al menos hay que dejar escrito que reventó.
        try:
            with self.env.cr.savepoint():
                return self._guardar_resultado(mov, fila, 'error_tecnico',
                                               _('Fallo tecnico al descontar. Revisar el log del servidor.')).estado
        except Exception:  # noqa: BLE001
            _logger.exception('Puente: tampoco se pudo registrar el fallo del movimiento %s',
                              mov.get('id'))
            return None

    def _datos_comunes(self, mov):
        comun = {
            'backend_id': self.id,
            'company_id': self.company_id.id,
            'tienda_mov_id': int(mov.get('id') or 0),
            'woo_product_id': int(mov.get('product_id') or 0),
            'lote_texto': mov.get('lote') or '',
            'cantidad': abs(float(mov.get('cantidad') or 0.0)),
            'pedido_tienda': int(mov.get('order_id') or 0),
            'ultimo_intento': fields.Datetime.now(),
        }
        fecha = mov.get('fecha')
        if fecha and _fecha_valida(fecha):
            comun['fecha_tienda'] = datetime.strptime(fecha, FORMATO_FECHA)
        return comun

    def _guardar_resultado(self, mov, fila, estado, nota, extra=None):
        """Escribe el resultado: actualiza el renglon si ya existia, o lo crea."""
        Consumo = self.env['amunet.woo.stock.consumo']
        valores = self._datos_comunes(mov)
        valores.update(extra or {})
        valores['estado'] = estado
        valores['nota'] = nota
        if fila:
            valores['intentos'] = fila.intentos + 1
            fila.write(valores)
            return fila
        return Consumo.create(valores)

    def _descontar_venta(self, mov, fila=None):
        """Un movimiento de la tienda -> un movimiento de existencias en Odoo."""
        self.ensure_one()
        empresa = self.company_id
        comun = self._datos_comunes(mov)

        mapeo = self.env['amunet.woo.product.mapping'].search([
            ('backend_id', '=', self.id),
            ('woo_product_id', '=', comun['woo_product_id']),
            ('relation_state', '=', 'confirmed'),
            ('product_id', '!=', False),
        ], limit=1)
        if not mapeo:
            return self._guardar_resultado(
                mov, fila, 'sin_producto',
                _('La tienda vendio un producto que aqui no esta mapeado.'))
        producto = mapeo.product_id

        if not comun['cantidad']:
            return self._guardar_resultado(
                mov, fila, 'aplicado',
                _('Cantidad cero; no habia nada que descontar.'),
                {'product_id': producto.id})

        # ---- lote: se compara SIEMPRE normalizado, y tiene que haber uno solo ----
        buscado = norm_lote(comun['lote_texto'])
        if not buscado:
            return self._guardar_resultado(
                mov, fila, 'sin_lote',
                _('La tienda no dijo de que lote salio.'),
                {'product_id': producto.id})
        candidatos = self.env['stock.lot'].search([
            ('product_id', '=', producto.id),
            ('company_id', 'in', (empresa.id, False)),
        ])
        iguales = candidatos.filtered(lambda l: norm_lote(l.name) == buscado)
        if not iguales:
            return self._guardar_resultado(
                mov, fila, 'sin_lote',
                _('Aqui no existe el lote %s para ese producto.') % comun['lote_texto'],
                {'product_id': producto.id})
        if len(iguales) > 1:
            # Nunca escoger "el exacto": si al normalizar chocan, la tienda no
            # puede distinguirlos y adivinar seria peor que parar.
            return self._guardar_resultado(
                mov, fila, 'sin_lote',
                _('Hay %s lotes que al normalizar se llaman igual que %s; hay que '
                  'descontarlo a mano.') % (len(iguales), comun['lote_texto']),
                {'product_id': producto.id})
        lote = iguales
        comun['lot_id'] = lote.id

        # ---- Calidad manda tambien al descontar, no solo al publicar ----
        if getattr(lote, 'amunet_lot_release_state', 'released') != 'released':
            return self._guardar_resultado(
                mov, fila, 'lote_retenido',
                _('El lote %s ya no esta liberado por Calidad; no se descuenta solo.')
                % lote.name,
                {'product_id': producto.id, 'lot_id': lote.id})

        # ---- de donde sale y a donde va ----
        origen = self._apt_pieces_location()
        destino = self.apt_venta_cliente_location_id
        if destino and destino.usage != 'customer':
            destino = False
        if not destino:
            destino = self.env['stock.location'].search([
                ('usage', '=', 'customer'),
                ('company_id', 'in', (empresa.id, False)),
            ], limit=1)
        if not origen or not destino:
            return self._guardar_resultado(
                mov, fila, 'sin_destino',
                _('Falta la ubicacion del anaquel o la de Clientes.'),
                {'product_id': producto.id, 'lot_id': lote.id})

        # ---- existencia: se toma de la ubicacion EXACTA de cada quant ----
        # Comprobar en el padre y descontar del padre dejaba negativo arriba y
        # la existencia real intacta abajo. Y se bloquean los renglones para que
        # dos corridas no se lleven las mismas piezas.
        quants = self.env['stock.quant'].search([
            ('product_id', '=', producto.id),
            ('lot_id', '=', lote.id),
            ('location_id', 'child_of', origen.id),
            ('company_id', '=', empresa.id),
        ], order='id')
        if quants:
            self.env.cr.execute('SELECT id FROM stock_quant WHERE id IN %s FOR UPDATE',
                                (tuple(quants.ids),))
            quants.invalidate_recordset(['quantity', 'reserved_quantity', 'available_quantity'])

        falta = comun['cantidad']
        reparto = []
        for quant in quants:
            libre = quant.available_quantity
            if libre <= 0:
                continue
            toma = min(libre, falta)
            reparto.append((quant.location_id, toma))
            falta -= toma
            if falta <= 0.00001:
                break
        if falta > 0.00001:
            hay = comun['cantidad'] - falta
            return self._guardar_resultado(
                mov, fila, 'sin_existencia',
                _('En el anaquel hay %(hay)s libres del lote %(l)s y la tienda vendio '
                  '%(pide)s.') % {'hay': hay, 'l': lote.name, 'pide': comun['cantidad']},
                {'product_id': producto.id, 'lot_id': lote.id})

        # ---- el movimiento de existencias ----
        # En Odoo 19 stock.move ya no tiene 'name': la referencia va en 'origin',
        # y ahi se guarda el id de la tienda para poder rastrearlo despues.
        origen_txt = _('Tienda %(t)s mov %(m)s pedido %(p)s') % {
            't': self.name, 'm': comun['tienda_mov_id'],
            'p': comun['pedido_tienda'] or '-'}
        move = self.env['stock.move'].with_company(empresa).create({
            'product_id': producto.id,
            'product_uom': producto.uom_id.id,
            'product_uom_qty': comun['cantidad'],
            'location_id': origen.id,
            'location_dest_id': destino.id,
            'company_id': empresa.id,
            'origin': origen_txt[:250],
        })
        move._action_confirm()
        move.move_line_ids.unlink()
        for ubic, cantidad in reparto:
            self.env['stock.move.line'].with_company(empresa).create({
                'move_id': move.id,
                'product_id': producto.id,
                'lot_id': lote.id,
                'quantity': cantidad,
                'product_uom_id': producto.uom_id.id,
                'location_id': ubic.id,
                'location_dest_id': destino.id,
                'company_id': empresa.id,
            })
        move.picked = True
        move._action_done()
        if move.state != 'done':
            raise UserError(_('El movimiento de existencias quedo en "%s" y no en '
                              '"hecho".') % move.state)

        return self._guardar_resultado(
            mov, fila, 'aplicado',
            _('Descontado de %s ubicacion(es) del anaquel.') % len(reparto),
            {'product_id': producto.id, 'lot_id': lote.id, 'move_id': move.id})

    # ------------------------------------------------------------------

    def _tomar_candado(self):
        """Un solo proceso a la vez por tienda.

        Sin esto, el cron y el boton (o dos crones encimados) podrian descontar
        de mas o hacer retroceder el cursor. El candado se suelta solo al cerrar
        la transaccion.
        """
        self.ensure_one()
        self.env.cr.execute('SELECT pg_try_advisory_xact_lock(%s, %s)',
                            (CANDADO_ESPACIO, self.id))
        if not self.env.cr.fetchone()[0]:
            raise UserError(_(
                'Ya hay una corrida del puente en marcha para esta tienda. '
                'Espera a que termine.'))

    def _anotar_bitacora(self, operacion, mensaje):
        """Deja constancia sin guardar jamas credenciales.

        Va dentro de un savepoint: si la bitacora falla, PostgreSQL abortaria
        la transaccion entera y perderiamos el trabajo bueno que ya se hizo.
        """
        self.ensure_one()
        Log = self.env.get('amunet.woo.sync.log')
        if Log is None:
            _logger.info('Puente: %s', mensaje)
            return
        try:
            with self.env.cr.savepoint():
                Log.sudo().create({
                    'backend_id': self.id,
                    'operation': operacion,
                    'message': mensaje,
                })
        except Exception:  # noqa: BLE001  la bitacora nunca debe tumbar la operacion
            _logger.info('Puente (sin bitacora): %s', mensaje)
