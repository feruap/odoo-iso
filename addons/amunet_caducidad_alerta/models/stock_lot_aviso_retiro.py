# -*- coding: utf-8 -*-
"""Aviso directo a almacen: "tienes que mover este material".

El semaforo ya sabe que un lote de producto terminado entro en RETIRAR (menos de
2 meses de vida) o ya VENCIO y sigue en el anaquel de Existencias. Hasta ahora
eso solo se veia si alguien abria la lista de lotes con el filtro "Debe
moverse". Aqui se le avisa a la persona del almacen de PT sin que tenga que ir
a buscarlo:

  * una ACTIVIDAD "Para hacer" en el lote, asignada a cada usuario con acceso
    al almacen APT (aparece en su reloj de actividades y en el chatter del lote),
  * y un CORREO con la lista completa de lo que hay que mover.

Se avisa la primera vez y se vuelve a avisar cada N dias (parametro) mientras el
material siga sin moverse. Cuando almacen confirma el movimiento con el asistente
(traslado interno a Retenidos), el lote deja de estar pendiente y el aviso se
apaga solo.

Parametros del sistema (Ajustes > Tecnico):
  amunet_caducidad.aviso_retiro_usuarios   logins separados por coma. Si esta
                                           vacio: los usuarios con acceso activo
                                           al almacen APT (amunet.warehouse.access).
  amunet_caducidad.aviso_retiro_dias       cada cuantos dias se repite el aviso
                                           mientras siga pendiente (7).
"""
from datetime import timedelta

from odoo import models, fields, api, _
from odoo.tools import html_escape

PARAM_USUARIOS = 'amunet_caducidad.aviso_retiro_usuarios'
PARAM_DIAS = 'amunet_caducidad.aviso_retiro_dias'
CODIGO_ALMACEN_PT = 'APT'


class StockLotAvisoRetiro(models.Model):
    _inherit = 'stock.lot'

    amunet_aviso_retiro_fecha = fields.Datetime(
        string='Ultimo aviso de retiro', readonly=True, copy=False,
        help='Cuando se le aviso por ultima vez a almacen que este lote debe '
             'salir del anaquel (retirar o vencido).')

    # ------------------------------------------------------------------
    @api.model
    def _amunet_usuarios_aviso_retiro(self):
        """A quien se le avisa. Parametro > acceso al almacen APT > nadie."""
        Users = self.env['res.users'].sudo()
        logins = (self.env['ir.config_parameter'].sudo().get_param(PARAM_USUARIOS) or '').strip()
        if logins:
            lista = [l.strip() for l in logins.split(',') if l.strip()]
            return Users.search([('login', 'in', lista), ('active', '=', True)])
        if 'amunet.warehouse.access' in self.env:
            accesos = self.env['amunet.warehouse.access'].sudo().search([
                ('active', '=', True),
                ('warehouse_id.code', '=', CODIGO_ALMACEN_PT),
            ])
            usuarios = accesos.mapped('user_id').filtered('active')
            if usuarios:
                return usuarios
        return Users.browse()

    @api.model
    def _amunet_lotes_por_retirar(self):
        """Lotes de producto terminado que deben salir del anaquel y siguen ahi."""
        lotes = self.search([
            ('amunet_condicion_caducidad', 'in', ('retirar', 'vencido')),
            ('amunet_requiere_movimiento', '=', True),
        ])
        return lotes.filtered(lambda l: l._amunet_es_producto_terminado())

    def _amunet_piezas_en_anaquel(self):
        self.ensure_one()
        destino = self._amunet_destino_esperado()
        return sum(self._amunet_quants_movibles(destino).mapped('quantity'))

    @api.model
    def _amunet_avisar_retiro(self):
        """Actividad en cada lote + un correo con la lista. Idempotente por dia."""
        usuarios = self._amunet_usuarios_aviso_retiro()
        if not usuarios:
            return self.browse()
        try:
            cada = int(self.env['ir.config_parameter'].sudo().get_param(PARAM_DIAS, 7))
        except (TypeError, ValueError):
            cada = 7
        ahora = fields.Datetime.now()
        limite = ahora - timedelta(days=max(cada, 1))
        lotes = self._amunet_lotes_por_retirar().filtered(
            lambda l: not l.amunet_aviso_retiro_fecha or l.amunet_aviso_retiro_fecha <= limite)
        if not lotes:
            return lotes

        tipo_todo = self.env.ref('mail.mail_activity_data_todo', raise_if_not_found=False)
        filas = []
        for lote in lotes:
            piezas = lote._amunet_piezas_en_anaquel()
            caduca = fields.Date.to_string(lote.expiration_date) if lote.expiration_date else '-'
            estado = dict(lote._fields['amunet_condicion_caducidad'].selection).get(
                lote.amunet_condicion_caducidad, lote.amunet_condicion_caducidad)
            resumen = _('Retirar del anaquel: %(producto)s lote %(lote)s (%(estado)s, caduca %(fecha)s)',
                        producto=lote.product_id.default_code or lote.product_id.display_name,
                        lote=lote.name, estado=estado, fecha=caduca)
            nota = _('Hay %(piezas)s piezas de este lote en el anaquel de Existencias y ya no se '
                     'venden (%(estado)s). Mueve las cajas al anaquel de Retenidos y confirmalo en '
                     'Inventario > Lotes > filtro "Debe moverse" > Confirmar movimiento de anaquel: '
                     'Odoo genera el traslado con folio, fecha y usuario.',
                     piezas=int(piezas) if piezas == int(piezas) else piezas, estado=estado)
            for usuario in usuarios:
                # una actividad abierta por usuario y lote basta
                abierta = lote.activity_ids.filtered(
                    lambda a: a.user_id == usuario and a.summary == resumen)
                if abierta:
                    continue
                if tipo_todo:
                    lote.activity_schedule(
                        act_type_xmlid='mail.mail_activity_data_todo',
                        date_deadline=fields.Date.context_today(self),
                        summary=resumen, note=nota, user_id=usuario.id)
            filas.append((lote, piezas, estado, caduca))

        self._amunet_correo_retiro(usuarios, filas)
        lotes.sudo().write({'amunet_aviso_retiro_fecha': ahora})
        return lotes

    @api.model
    def _amunet_correo_retiro(self, usuarios, filas):
        correos = [u.email or u.partner_id.email for u in usuarios]
        correos = [c for c in correos if c]
        if not correos or not filas:
            return False
        base = self.env['ir.config_parameter'].sudo().get_param('web.base.url') or ''
        cuerpo = [
            '<p>Hola,</p>',
            '<p>Este material ya <b>no se vende</b> (le quedan menos de %s meses o ya vencio) y sigue en el '
            'anaquel de Existencias. <b>Tienes que moverlo a Retenidos</b> y confirmarlo en Odoo '
            '(Inventario &gt; Lotes &gt; filtro "Debe moverse" &gt; Confirmar movimiento de anaquel).</p>'
            % html_escape(str(self._amunet_umbrales().get('amunet_caducidad.meses_retiro', 2))),
            '<table border="1" cellpadding="4" cellspacing="0" style="border-collapse:collapse">',
            '<tr><th>Producto</th><th>Lote</th><th>Piezas en anaquel</th><th>Condicion</th><th>Caduca</th></tr>',
        ]
        for lote, piezas, estado, caduca in filas:
            url = '%s/odoo/action-stock.action_production_lot_form/%s' % (base, lote.id)
            cuerpo.append(
                '<tr><td>%s</td><td><a href="%s">%s</a></td><td align="right">%s</td><td>%s</td><td>%s</td></tr>' % (
                    html_escape(lote.product_id.display_name), html_escape(url), html_escape(lote.name),
                    html_escape(str(int(piezas) if piezas == int(piezas) else piezas)),
                    html_escape(estado), html_escape(caduca)))
        cuerpo.append('</table>')
        cuerpo.append('<p>Este aviso se repite mientras el material siga en el anaquel. '
                      'Se apaga solo cuando confirmas el movimiento.</p>')
        self.env['mail.mail'].sudo().create({
            'subject': _('Almacen PT: %s lote(s) por retirar del anaquel') % len(filas),
            'email_to': ','.join(correos),
            'body_html': ''.join(cuerpo),
            'auto_delete': True,
        }).send()
        return True

    # ------------------------------------------------------------------
    @api.model
    def _cron_amunet_semaforo_caducidad(self):
        res = super()._cron_amunet_semaforo_caducidad()
        # despues de recalcular, se avisa lo que quedo pendiente de retirar
        self._amunet_avisar_retiro()
        return res
