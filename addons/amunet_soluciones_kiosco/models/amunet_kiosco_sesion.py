# -*- coding: utf-8 -*-

from datetime import timedelta

from odoo import api, fields, models, _
from odoo.exceptions import UserError

# Grupo de fabricantes de soluciones: solo ellos pueden identificarse por PIN.
GRUPO_FABRICANTE = 'amunet_production.group_solution_maker'


class AmunetKioscoSesion(models.Model):
    """Sesion de trabajo en una tablet compartida del area de soluciones.

    En la tablet la sesion de Odoo es de un usuario OPERATIVO del area, no de
    una persona. Esta sesion de trabajo es la que dice QUIEN esta elaborando,
    resuelto a partir de su PIN individual. Lo que queda en el expediente es la
    persona del PIN, no el usuario de la tablet.
    """
    _name = 'amunet.kiosco.sesion'
    _description = 'Sesion de trabajo en kiosco de soluciones'
    _order = 'inicio desc'

    production_id = fields.Many2one(
        'mrp.production', string='Orden de solucion',
        required=True, ondelete='cascade', index=True)
    operador_id = fields.Many2one(
        'res.users', string='Quien elabora', required=True, index=True,
        help='Persona resuelta a partir del PIN, no el usuario de la tablet.')
    dispositivo_uid = fields.Many2one(
        'res.users', string='Usuario de la tablet', required=True,
        help='La sesion de Odoo con la que esta abierta la tablet.')

    inicio = fields.Datetime(string='Inicio', required=True,
                             default=fields.Datetime.now)
    ultima_actividad = fields.Datetime(string='Ultima actividad', required=True,
                                       default=fields.Datetime.now)
    fin = fields.Datetime(string='Fin')
    motivo_cierre = fields.Selection([
        ('enviada',     'Enviada a supervision'),
        ('inactividad', 'Cerrada por inactividad'),
        ('relevo',      'Otra persona tomo la tablet'),
        ('manual',      'Cerrada a mano'),
    ], string='Motivo de cierre')

    state = fields.Selection([
        ('activa',  'Activa'),
        ('cerrada', 'Cerrada'),
    ], string='Estado', default='activa', required=True, index=True)

    # ------------------------------------------------------------------
    # Parametros
    # ------------------------------------------------------------------
    @api.model
    def _minutos_inactividad(self):
        """Minutos sin actividad antes de cerrar la sesion. Acordado: 10."""
        valor = self.env['ir.config_parameter'].sudo().get_param(
            'amunet_soluciones_kiosco.minutos_inactividad', '10')
        try:
            return max(1, int(valor))
        except (TypeError, ValueError):
            return 10

    # ------------------------------------------------------------------
    # Identificacion por PIN
    # ------------------------------------------------------------------
    @api.model
    def _resolver_por_pin(self, pin_plano):
        """Devuelve el usuario cuyo PIN coincide, entre los fabricantes
        autorizados. Es lo que distingue al kiosco: aqui el PIN IDENTIFICA,
        no solo verifica.

        Reglas duras:
          - Solo se busca entre miembros del grupo de fabricantes.
          - Si el PIN coincide con MAS DE UNA persona se rechaza: un expediente
            no puede quedar con firma ambigua.
        """
        pin_plano = (pin_plano or '').strip()
        if not pin_plano:
            raise UserError(_('Escribe tu PIN.'))

        grupo = self.env.ref(GRUPO_FABRICANTE, raise_if_not_found=False)
        if not grupo:
            raise UserError(_('No esta configurado el grupo de fabricantes de soluciones.'))

        Pin = self.env['amunet.quality.signature.pin'].sudo()
        coincidencias = self.env['res.users'].sudo().browse()
        for usuario in grupo.sudo().user_ids.filtered('active'):
            registro = Pin.search([('user_id', '=', usuario.id)], limit=1)
            if registro and registro.check_pin(pin_plano):
                coincidencias |= usuario

        if not coincidencias:
            raise UserError(_(
                'Ese PIN no corresponde a ninguna persona autorizada para '
                'elaborar soluciones.\n\n'
                'Si eres nueva o nuevo en el area, pide que te den de alta tu '
                'PIN antes de empezar.'))
        if len(coincidencias) > 1:
            # No se dice quienes son: seria filtrar credenciales.
            raise UserError(_(
                'Ese PIN corresponde a mas de una persona, asi que no se puede '
                'saber quien esta elaborando.\n\n'
                'Avisa a tu supervisor para que se asignen PIN distintos antes '
                'de continuar. El expediente no puede quedar con una firma '
                'ambigua.'))
        return coincidencias

    # ------------------------------------------------------------------
    # Ciclo de vida
    # ------------------------------------------------------------------
    @api.model
    def _cerrar_vencidas(self):
        """Cierra las sesiones que pasaron el limite de inactividad."""
        limite = fields.Datetime.now() - timedelta(minutes=self._minutos_inactividad())
        vencidas = self.sudo().search([
            ('state', '=', 'activa'),
            ('ultima_actividad', '<', limite),
        ])
        if vencidas:
            vencidas.write({
                'state': 'cerrada',
                'fin': fields.Datetime.now(),
                'motivo_cierre': 'inactividad',
            })
        return len(vencidas)

    @api.model
    def abrir(self, production, pin_plano):
        """Abre la sesion de trabajo de una elaboracion, identificando por PIN."""
        self._cerrar_vencidas()
        operador = self._resolver_por_pin(pin_plano)

        # Relevo: si esta tablet tenia otra sesion activa, se cierra.
        previas = self.sudo().search([
            ('state', '=', 'activa'),
            ('dispositivo_uid', '=', self.env.uid),
        ])
        if previas:
            previas.write({
                'state': 'cerrada',
                'fin': fields.Datetime.now(),
                'motivo_cierre': 'relevo',
            })

        sesion = self.sudo().create([{
            'production_id': production.id,
            'operador_id': operador.id,
            'dispositivo_uid': self.env.uid,
        }])
        production.sudo().message_post(body=_(
            'Elaboracion iniciada por <b>%(quien)s</b> desde la tablet '
            '(%(tablet)s).',
            quien=operador.name, tablet=self.env.user.name,
        ))
        return sesion

    def latir(self):
        """Registra actividad para que la sesion no expire."""
        activas = self.filtered(lambda s: s.state == 'activa')
        if activas:
            activas.sudo().write({'ultima_actividad': fields.Datetime.now()})
        return True

    def cerrar(self, motivo='manual'):
        abiertas = self.filtered(lambda s: s.state == 'activa')
        if abiertas:
            abiertas.sudo().write({
                'state': 'cerrada',
                'fin': fields.Datetime.now(),
                'motivo_cierre': motivo,
            })
        return True

    @api.model
    def _cron_cerrar_inactivas(self):
        """Cron de respaldo: cierra sesiones olvidadas aunque nadie toque la
        tablet (fin de turno, tablet apagada, etc.)."""
        n = self._cerrar_vencidas()
        if n:
            self.env['ir.logging'].sudo().create({
                'name': 'amunet_soluciones_kiosco',
                'type': 'server',
                'level': 'INFO',
                'dbname': self.env.cr.dbname,
                'message': 'Cerradas %s sesiones de kiosco por inactividad' % n,
                'path': 'amunet.kiosco.sesion',
                'func': '_cron_cerrar_inactivas',
                'line': '0',
            })
        return True
