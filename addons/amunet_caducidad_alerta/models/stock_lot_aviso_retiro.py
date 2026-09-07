# -*- coding: utf-8 -*-
"""Aviso directo a almacen: "tienes que mover este material".

El semaforo ya sabe cuando un lote cambio de condicion por el calendario y la
mercancia sigue en el anaquel anterior (`amunet_requiere_movimiento`). Hasta
ahora eso solo se veia si alguien abria la lista de lotes con el filtro "Debe
moverse". Aqui se le avisa a la persona del almacen de PT sin que tenga que ir
a buscarlo:

  * una ACTIVIDAD "Para hacer" en el lote, para cada usuario con acceso al
    almacen APT, que dice a que anaquel hay que moverlo,
  * y un CORREO con la lista completa de lo que hay que mover.

Se avisa la primera vez y se vuelve a avisar cada N dias (parametro) mientras el
material siga sin moverse. Cuando almacen confirma el movimiento con el
asistente (traslado interno real, con folio), el lote deja de estar pendiente y
el aviso se apaga solo.

07-sep-2026: antes esto solo avisaba de lo que habia que RETIRAR. Con la
cortesia extendida hasta el final de la vida del lote (umbral de retiro 0), lo
que hay que mover casi siempre es material que pasa a caducidad corta o a
cortesias, no material que se retira. Asi que el aviso cubre cualquier
movimiento pendiente y dice a donde va. Si la condicion de un lote vuelve a
cambiar, la actividad vieja se reemplaza para que nunca diga algo que ya no es
cierto.

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
PREFIJOS_AVISO = ('Retirar del anaquel:', 'Mover de anaquel:')


class StockLotAvisoRetiro(models.Model):
    _inherit = 'stock.lot'

    # El nombre del campo se conserva (habia datos desde el 07-sep por la
    # manana); hoy marca el ultimo aviso de movimiento, sea del cubo que sea.
    amunet_aviso_retiro_fecha = fields.Datetime(
        string='Ultimo aviso de movimiento', readonly=True, copy=False,
        help='Cuando se le aviso por ultima vez a almacen que este lote debe '
             'cambiar de anaquel.')

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
    def _amunet_lotes_por_mover(self):
        """Lotes de producto terminado que deben cambiar de anaquel y no lo han hecho."""
        lotes = self.search([('amunet_requiere_movimiento', '=', True)])
        return lotes.filtered(lambda l: l._amunet_es_producto_terminado())

    # compatibilidad con el nombre anterior
    @api.model
    def _amunet_lotes_por_retirar(self):
        return self._amunet_lotes_por_mover()

    def _amunet_piezas_en_anaquel(self):
        self.ensure_one()
        destino = self._amunet_destino_esperado()
        return sum(self._amunet_quants_movibles(destino).mapped('quantity'))

    def _amunet_resumen_movimiento(self):
        """El texto del aviso: a donde va este lote y por que."""
        self.ensure_one()
        destino = self._amunet_destino_esperado()
        estado = dict(self._fields['amunet_condicion_caducidad'].selection).get(
            self.amunet_condicion_caducidad, self.amunet_condicion_caducidad)
        caduca = fields.Date.to_string(self.expiration_date) if self.expiration_date else '-'
        return _(
            'Mover de anaquel: %(producto)s lote %(lote)s -> %(destino)s (%(estado)s, caduca %(fecha)s)',
            producto=self.product_id.default_code or self.product_id.display_name,
            lote=self.name,
            destino=destino.display_name if destino else _('sin anaquel destino'),
            estado=estado, fecha=caduca), destino, estado, caduca

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
        pendientes = self._amunet_lotes_por_mover()

        # Primero se limpian los avisos que ya no dicen la verdad: los de lotes
        # que ya se movieron, y los que quedaron con el texto de otra condicion.
        # Los lotes a los que se les borro un aviso y siguen pendientes se
        # vuelven a avisar AHORA aunque no toque por calendario: si no, se
        # quedarian sin ningun aviso hasta que venza el intervalo, que es peor
        # que el aviso viejo.
        reavisar = self._amunet_limpiar_avisos(pendientes)

        lotes = pendientes.filtered(
            lambda l: not l.amunet_aviso_retiro_fecha or l.amunet_aviso_retiro_fecha <= limite)
        lotes |= reavisar
        if not lotes:
            return lotes

        filas = []
        for lote in lotes:
            resumen, destino, estado, caduca = lote._amunet_resumen_movimiento()
            piezas = lote._amunet_piezas_en_anaquel()
            nota = _(
                'Hay %(piezas)s piezas de este lote fuera de su anaquel (%(estado)s). '
                'Muevelas a "%(destino)s" y confirmalo en Inventario > Lotes > filtro '
                '"Debe moverse" > Confirmar movimiento de anaquel: Odoo genera el traslado '
                'con folio, fecha y usuario.',
                piezas=int(piezas) if piezas == int(piezas) else piezas,
                estado=estado,
                destino=destino.display_name if destino else _('el anaquel que corresponde'))
            for usuario in usuarios:
                abierta = lote.activity_ids.filtered(
                    lambda a: a.user_id == usuario and a.summary == resumen)
                if abierta:
                    continue
                lote.activity_schedule(
                    act_type_xmlid='mail.mail_activity_data_todo',
                    date_deadline=fields.Date.context_today(self),
                    summary=resumen, note=nota, user_id=usuario.id)
            filas.append((lote, piezas, estado, caduca,
                          destino.display_name if destino else _('sin anaquel destino')))

        self._amunet_correo_retiro(usuarios, filas)
        lotes.sudo().write({'amunet_aviso_retiro_fecha': ahora})
        return lotes

    @api.model
    def _amunet_limpiar_avisos(self, pendientes):
        """Borra las actividades de este sistema que ya no corresponden.

        Dos casos: el lote ya se movio (ya no esta pendiente) o su condicion
        cambio y el texto quedo viejo. Un aviso que dice algo que ya no es
        cierto es peor que no avisar: enseña a ignorar los avisos.

        Devuelve los lotes que siguen pendientes y se quedaron sin aviso, para
        que se les vuelva a avisar de inmediato.
        """
        Activity = self.env['mail.activity'].sudo()
        modelo = self.env['ir.model']._get_id('stock.lot')
        abiertas = Activity.search([('res_model_id', '=', modelo)])
        vigentes = {}
        for lote in pendientes:
            vigentes[lote.id] = lote._amunet_resumen_movimiento()[0]
        borrar = Activity.browse()
        reavisar_ids = set()
        for act in abiertas:
            if not act.summary or not act.summary.startswith(PREFIJOS_AVISO):
                continue
            if vigentes.get(act.res_id) != act.summary:
                borrar |= act
                if act.res_id in vigentes:
                    reavisar_ids.add(act.res_id)   # sigue pendiente: hay que re-avisar
        if borrar:
            borrar.unlink()
        # y el sello de "ya avise" de los lotes que dejaron de estar pendientes
        movidos = self.search([
            ('amunet_aviso_retiro_fecha', '!=', False),
            ('id', 'not in', pendientes.ids),
        ])
        if movidos:
            movidos.sudo().write({'amunet_aviso_retiro_fecha': False})
        return pendientes.filtered(lambda l: l.id in reavisar_ids)

    @api.model
    def _amunet_correo_retiro(self, usuarios, filas):
        correos = [u.email or u.partner_id.email for u in usuarios]
        correos = [c for c in correos if c]
        if not correos or not filas:
            return False
        base = self.env['ir.config_parameter'].sudo().get_param('web.base.url') or ''
        cuerpo = [
            '<p>Hola,</p>',
            '<p>Este material <b>ya no esta en el anaquel que le toca</b> segun su caducidad. '
            'Muevelo y confirmalo en Odoo (Inventario &gt; Lotes &gt; filtro "Debe moverse" &gt; '
            'Confirmar movimiento de anaquel), para que quede el traslado con folio.</p>',
            '<table border="1" cellpadding="4" cellspacing="0" style="border-collapse:collapse">',
            '<tr><th>Producto</th><th>Lote</th><th>Piezas</th><th>Condicion</th>'
            '<th>Caduca</th><th>Mover a</th></tr>',
        ]
        for lote, piezas, estado, caduca, destino in filas:
            url = '%s/odoo/action-stock.action_production_lot_form/%s' % (base, lote.id)
            cuerpo.append(
                '<tr><td>%s</td><td><a href="%s">%s</a></td><td align="right">%s</td>'
                '<td>%s</td><td>%s</td><td>%s</td></tr>' % (
                    html_escape(lote.product_id.display_name), html_escape(url),
                    html_escape(lote.name),
                    html_escape(str(int(piezas) if piezas == int(piezas) else piezas)),
                    html_escape(estado), html_escape(caduca), html_escape(destino)))
        cuerpo.append('</table>')
        cuerpo.append('<p>Este aviso se repite mientras el material siga fuera de su anaquel. '
                      'Se apaga solo cuando confirmas el movimiento.</p>')
        self.env['mail.mail'].sudo().create({
            'subject': _('Almacen PT: %s lote(s) por mover de anaquel') % len(filas),
            'email_to': ','.join(correos),
            'body_html': ''.join(cuerpo),
            'auto_delete': True,
        }).send()
        return True

    # ------------------------------------------------------------------
    @api.model
    def _cron_amunet_semaforo_caducidad(self):
        res = super()._cron_amunet_semaforo_caducidad()
        # despues de recalcular, se avisa lo que quedo pendiente de mover
        self._amunet_avisar_retiro()
        return res
