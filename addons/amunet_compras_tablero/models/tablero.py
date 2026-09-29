# -*- coding: utf-8 -*-
"""Tablero de compras: todo el circuito en una pantalla.

Hoy la informacion de "en que va cada compra" esta repartida:
  - las solicitudes de compra (SC) viven en el Marketplace Interno,
  - las ordenes de compra (P000xx) en Compras, todas en una sola lista
    revuelta: borradores, confirmadas, recibidas y canceladas juntas.

Este modelo no guarda nada. Arma, en una sola llamada, las tarjetas de cada
etapa para que la pantalla (static/src/js/tablero.js) las pinte:

    autorizar  -> SC que espera la firma del jefe del area (o sin enviar)
    comprar    -> autorizada y aun no comprada: SC aprobada sin OC, u OC en
                  borrador / enviada sin confirmar ni pagar
    pagada     -> OC confirmada por el proveedor o con anticipo/pago, que
                  todavia no sale (no hay fecha de llegada confirmada);
                  SC autorizada con comprobante de pago
    transito   -> ya viene: OC con llegada confirmada por el proveedor
                  (amunet_eta) o con algo ya recibido; SC comprada en tienda
    atrasada   -> no ha llegado todo y ya paso la fecha prometida
    recibida   -> llego completa en los ultimos 30 dias
    (Orden de columnas definido por Fernando, 29-sep-2026.)

Si una SC ya tiene orden de compra, NO se pinta aparte: la representa la
tarjeta de su OC (que muestra el folio SC de origen).

Seguridad:
  - Solo entra quien es de Compras, ve montos de compra general o es
    gerente de material (mismos grupos que el menu).
  - Se lee con sudo() porque la pantalla junta dos modelos con permisos
    distintos, pero los MONTOS se respetan por grupo:
      OC -> amunet_price_visibility.group_price_viewer
      SC -> amunet_compras_general.group_compras_monto
    Almacen no ve importes.
"""

from datetime import datetime, timedelta

from odoo import _, api, fields, models
from odoo.exceptions import AccessError

GRUPOS_ACCESO = (
    'purchase.group_purchase_user',
    'amunet_compras_general.group_compras_monto',
    'amunet_material_request.group_material_manager',
)
GRUPO_PRECIOS_OC = 'amunet_price_visibility.group_price_viewer'
GRUPO_MONTOS_SC = 'amunet_compras_general.group_compras_monto'
DIAS_RECIBIDAS = 30

ESTADOS_OC_BORRADOR = ('draft', 'sent', 'to approve')
ESTADOS_SC_VIVOS = ('draft', 'submitted', 'pending_approval', 'approved', 'purchased')

URGENCIA_PESO = {'normal': 0, 'urge': 1, 'linea_detenida': 2}


class AmunetComprasTablero(models.AbstractModel):
    _name = 'amunet.compras.tablero'
    _description = 'Tablero de compras'

    # ------------------------------------------------------------------
    @api.model
    def _tiene(self, xmlid):
        try:
            return self.env.user.has_group(xmlid)
        except Exception:  # grupo de un modulo no instalado
            return False

    @api.model
    def _etiqueta(self, record, campo):
        valor = record[campo]
        if not valor:
            return False
        return dict(record._fields[campo]._description_selection(self.env)).get(valor, valor)

    @api.model
    def _monto(self, importe, moneda):
        if not moneda:
            return '%s' % '{:,.2f}'.format(importe or 0.0)
        return '%s %s' % ('{:,.2f}'.format(importe or 0.0), moneda.name)

    @api.model
    def _fecha(self, valor):
        if not valor:
            return False
        if isinstance(valor, datetime):
            valor = fields.Datetime.context_timestamp(self, valor).date()
        return fields.Date.to_string(valor)

    # ------------------------------------------------------------------
    @api.model
    def get_datos(self):
        if not any(self._tiene(g) for g in GRUPOS_ACCESO):
            raise AccessError(_('El tablero de compras es solo para Compras y Direccion.'))

        hoy = fields.Date.context_today(self)
        ver_montos_oc = self._tiene(GRUPO_PRECIOS_OC)
        ver_montos_sc = self._tiene(GRUPO_MONTOS_SC)

        tarjetas = []
        tarjetas += self._tarjetas_oc(hoy, ver_montos_oc)
        tarjetas += self._tarjetas_sc(hoy, ver_montos_sc)

        return {
            'hoy': fields.Date.to_string(hoy),
            'ver_montos': ver_montos_oc or ver_montos_sc,
            'dias_recibidas': DIAS_RECIBIDAS,
            'tarjetas': tarjetas,
            'accion_oc': self.env.ref('purchase.purchase_rfq').id,
        }

    # -- ordenes de compra ---------------------------------------------
    @api.model
    def _tarjetas_oc(self, hoy, ver_montos):
        PO = self.env['purchase.order'].sudo()
        limite = fields.Datetime.now() - timedelta(days=DIAS_RECIBIDAS)
        ordenes = PO.search([
            '|',
            ('state', 'in', ESTADOS_OC_BORRADOR),
            '&', ('state', '=', 'purchase'),
            '|', '|',
            ('receipt_status', '=', False),
            ('receipt_status', '!=', 'full'),
            ('effective_date', '>=', limite),
        ])
        res = []
        for o in ordenes:
            lineas = o.order_line.filtered(lambda l: not l.display_type)
            pedido = sum(lineas.mapped('product_qty'))
            recibido = sum(min(l.qty_received, l.product_qty) for l in lineas)
            faltan = any(l.qty_received < l.product_qty for l in lineas)
            # Lo que manda es la recepcion de almacen, no solo la cantidad:
            #  - hay movimientos abiertos             -> sigue en camino
            #  - llego algo y el resto se cancelo     -> se da por recibida
            #    (backorder cancelado a proposito, p.ej. P00205)
            #  - no llego nada y no hay recepcion     -> sigue pendiente, pero
            #    marcada: almacen no tiene donde recibirla (P00161, P00184...).
            #    Ojo: hay recepciones "hechas" con cantidad cero (P00184,
            #    P00185, P00188, P00189): eso NO cuenta como recibido.
            movs = lineas.mapped('move_ids')
            abiertos = movs.filtered(lambda m: m.state not in ('done', 'cancel'))
            hechos = movs.filtered(lambda m: m.state == 'done')
            if not faltan:
                # ya llego todo lo pedido, aunque quede un movimiento colgado
                pendiente, sin_recepcion = False, False
            elif abiertos:
                pendiente, sin_recepcion = True, False
            elif hechos and recibido > 0:
                pendiente, sin_recepcion = False, False
            else:
                pendiente, sin_recepcion = faltan, faltan
            pct = int(round(100.0 * recibido / pedido)) if pedido else 0

            fecha_esperada = o.amunet_eta or (o.date_planned and
                                              fields.Datetime.context_timestamp(self, o.date_planned).date())
            dias_atraso = 0
            # Columnas definidas por Fernando (29-sep-2026). Atrasada gana
            # sobre pagada/transito: si ya se paso la fecha, eso es lo que hay
            # que perseguir primero (la tarjeta sigue mostrando el pago).
            pagada = o.amunet_estado_pago in ('anticipo', 'pagado')
            if o.state in ESTADOS_OC_BORRADOR:
                etapa = 'pagada' if pagada else 'comprar'
            elif pendiente:
                if fecha_esperada and fecha_esperada < hoy:
                    etapa = 'atrasada'
                    dias_atraso = (hoy - fecha_esperada).days
                elif o.amunet_eta or recibido > 0:
                    etapa = 'transito'
                else:
                    etapa = 'pagada'
            else:
                llegada = o.effective_date or o.date_approve
                if not llegada or llegada < limite:
                    continue
                etapa = 'recibida'

            solicitudes = o.amunet_solicitud_compra_ids
            origen = (o.origin or '').strip()
            es_general = bool(solicitudes) or origen.startswith(('SMP/', 'SC/'))

            productos = []
            for l in lineas[:3]:
                p = l.product_id
                productos.append(p.default_code or (p.name or l.name or '')[:40])
            if len(lineas) > 3:
                productos.append('+%d' % (len(lineas) - 3))

            fecha_orden = self._fecha(o.date_order)
            res.append({
                'key': 'po-%d' % o.id,
                'modelo': 'purchase.order',
                'res_id': o.id,
                'etapa': etapa,
                'tipo': 'general' if es_general else 'productivo',
                'folio': o.name,
                'titulo': o.partner_id.display_name,
                'subtitulo': origen or False,
                'solicitudes': ', '.join(solicitudes.mapped('name')) or False,
                'solicitante': ', '.join(solicitudes.mapped('requester_id.name')) or False,
                'responsable': o.user_id.name or False,
                'productos': ' · '.join(productos),
                'n_lineas': len(lineas),
                'estado': self._etiqueta(o, 'state'),
                'fecha_orden': fecha_orden,
                'edad_dias': (hoy - fields.Date.from_string(fecha_orden)).days if fecha_orden else 0,
                'fecha_esperada': fields.Date.to_string(fecha_esperada) if fecha_esperada else False,
                'eta_confirmada': bool(o.amunet_eta),
                'dias_atraso': dias_atraso,
                'fecha_llegada': self._fecha(o.effective_date) if etapa == 'recibida' else False,
                'pct': pct,
                'parcial': bool(pendiente and recibido > 0),
                'sin_recepcion': bool(o.state == 'purchase' and sin_recepcion),
                'urgencia': o.amunet_urgencia_maxima or 'normal',
                'urgencia_label': self._etiqueta(o, 'amunet_urgencia_maxima') if o.amunet_urgencia_maxima not in (False, 'normal') else False,
                'pago': o.amunet_estado_pago or False,
                'pago_label': self._etiqueta(o, 'amunet_estado_pago'),
                'via': self._etiqueta(o, 'amunet_via_embarque'),
                'via_code': o.amunet_via_embarque or False,
                'via_pref': o.amunet_via_preferida or False,
                'via_sug': 'aereo' if o.amunet_urgencia_maxima in ('urge', 'linea_detenida') else False,
                'monto': self._monto(o.amount_total, o.currency_id) if ver_montos else False,
                'buscar': ' '.join(filter(None, [
                    o.name, o.partner_id.display_name, origen,
                    ' '.join(solicitudes.mapped('name')),
                    ' '.join(solicitudes.mapped('requester_id.name')),
                    ' '.join(filter(None, lineas.mapped('product_id.default_code'))),
                    ' '.join(lineas.mapped('name')),
                ])),
            })
        return res

    # -- solicitudes de compra del marketplace -------------------------
    @api.model
    def _tarjetas_sc(self, hoy, ver_montos):
        SC = self.env['amunet.solicitud.compra'].sudo()
        solicitudes = SC.search([
            ('state', 'in', ESTADOS_SC_VIVOS),
            ('purchase_order_id', '=', False),
        ])
        res = []
        for s in solicitudes:
            if s.state in ('draft', 'submitted', 'pending_approval'):
                etapa = 'autorizar'
            elif s.state == 'approved':
                # con comprobante de transferencia ya esta pagada
                etapa = 'pagada' if s.amunet_comprobante_fecha else 'comprar'
            else:  # purchased, sin OC: se compro en tienda, ya viene en camino
                etapa = 'transito'

            lineas = s.line_ids
            productos = []
            for l in lineas[:3]:
                p = l.product_id
                productos.append((p.default_code if p else False) or (l.name or p.name or '')[:40])
            if len(lineas) > 3:
                productos.append('+%d' % (len(lineas) - 3))

            titulo = (lineas[:1].name or lineas[:1].product_id.name) if lineas else _('(sin renglones)')
            if len(lineas) > 1:
                titulo = '%s  +%d' % (titulo, len(lineas) - 1)

            fecha_sol = self._fecha(s.request_date)
            requerida = self._fecha(s.required_date)
            res.append({
                'key': 'sc-%d' % s.id,
                'modelo': 'amunet.solicitud.compra',
                'res_id': s.id,
                'etapa': etapa,
                'tipo': 'productivo' if s.marketplace_flow == 'production' else 'general',
                'folio': s.name,
                'titulo': titulo,
                'subtitulo': ' · '.join(filter(None, [s.requester_id.name, s.department_id.name])) or False,
                'solicitudes': False,
                'solicitante': s.requester_id.name or False,
                'responsable': s.amunet_autorizada_por_id.name or False,
                'productos': ' · '.join(productos),
                'n_lineas': len(lineas),
                'estado': self._etiqueta(s, 'state'),
                'borrador': s.state == 'draft',
                'fecha_orden': fecha_sol,
                'edad_dias': (hoy - fields.Date.from_string(fecha_sol)).days if fecha_sol else 0,
                'fecha_esperada': requerida,
                'eta_confirmada': False,
                'requerida': requerida,
                'dias_atraso': 0,
                'fecha_llegada': False,
                'pct': False,
                'parcial': False,
                'urgencia': s.amunet_urgencia or 'normal',
                'urgencia_label': self._etiqueta(s, 'amunet_urgencia') if s.amunet_urgencia not in (False, 'normal') else False,
                'urgencia_motivo': s.amunet_urgencia_motivo or False,
                'pago': 'pagado' if s.state == 'purchased' or etapa == 'pagada' else False,
                'pago_label': (_('Comprada') if s.state == 'purchased' else _('Pagada')) if (s.state == 'purchased' or etapa == 'pagada') else False,
                'forma_pago': self._etiqueta(s, 'amunet_forma_pago'),
                'via': False,
                'via_code': False,
                'via_pref': s.amunet_via_preferida or False,
                'via_sug': 'aereo' if s.amunet_urgencia in ('urge', 'linea_detenida') else False,
                'monto': self._monto(s.amunet_monto, s.amunet_currency_id) if (ver_montos and s.amunet_monto) else False,
                'buscar': ' '.join(filter(None, [
                    s.name, s.requester_id.name, s.department_id.name,
                    s.partner_id.display_name, s.amunet_titular,
                    ' '.join(filter(None, lineas.mapped('name'))),
                    ' '.join(filter(None, lineas.mapped('product_id.default_code'))),
                ])),
            })
        return res
