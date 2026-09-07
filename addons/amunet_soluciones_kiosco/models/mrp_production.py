# -*- coding: utf-8 -*-

from odoo import api, fields, models, _
from odoo.exceptions import UserError


class MrpProduction(models.Model):
    _inherit = 'mrp.production'

    kiosco_sesion_ids = fields.One2many(
        'amunet.kiosco.sesion', 'production_id', string='Sesiones de kiosco')
    kiosco_operador_id = fields.Many2one(
        'res.users', string='Elaborando ahora',
        compute='_compute_kiosco_operador', store=False,
        help='Persona que tiene abierta esta elaboracion en la tablet.')
    kiosco_es_dispositivo = fields.Boolean(
        string='Estoy en una tablet de kiosco',
        compute='_compute_kiosco_es_dispositivo', store=False)

    # ------------------------------------------------------------------
    @api.depends('kiosco_sesion_ids.state', 'kiosco_sesion_ids.operador_id')
    def _compute_kiosco_operador(self):
        for mo in self:
            activa = mo.kiosco_sesion_ids.filtered(lambda s: s.state == 'activa')[:1]
            mo.kiosco_operador_id = activa.operador_id if activa else False

    def _compute_kiosco_es_dispositivo(self):
        """La tablet se marca en el usuario, no en el registro: asi el mismo
        flujo sirve desde el telefono de cada quien SIN pedir PIN de apertura
        (ahi la sesion ya identifica a la persona)."""
        es_kiosco = self.env.user.has_group(
            'amunet_soluciones_kiosco.group_kiosco_soluciones')
        for mo in self:
            mo.kiosco_es_dispositivo = es_kiosco

    def _kiosco_sesion_activa(self):
        self.ensure_one()
        Sesion = self.env['amunet.kiosco.sesion']
        Sesion._cerrar_vencidas()
        return Sesion.sudo().search([
            ('production_id', '=', self.id),
            ('state', '=', 'activa'),
        ], limit=1)

    # ------------------------------------------------------------------
    # Botones del kiosco
    # ------------------------------------------------------------------
    def action_kiosco_iniciar(self):
        self.ensure_one()
        if self._kiosco_sesion_activa():
            raise UserError(_(
                'Esta elaboracion ya esta abierta por %s.'
            ) % self.kiosco_operador_id.name)
        return self.env['amunet.kiosco.pin.wizard'].abrir_para(self, 'abrir')

    def action_kiosco_supervision(self):
        self.ensure_one()
        return self.env['amunet.kiosco.pin.wizard'].abrir_para(self, 'supervision')

    def action_kiosco_analisis(self):
        self.ensure_one()
        return self.env['amunet.kiosco.pin.wizard'].abrir_para(self, 'analisis')

    def action_kiosco_producir(self):
        self.ensure_one()
        return self.env['amunet.kiosco.pin.wizard'].abrir_para(self, 'producir')

    # ------------------------------------------------------------------
    def _kiosco_ejecutar(self, accion, operador):
        """Ejecuta la accion del flujo normal, pero DEJANDO CONSTANCIA de que
        la hizo la persona del PIN y no el usuario de la tablet.

        No se reimplementa nada del flujo: se llama al metodo que ya existe.
        Asi el kiosco no puede desviarse de lo que hace el sistema normal.
        """
        self.ensure_one()
        etiquetas = {
            'supervision': _('envio a supervision'),
            'analisis':    _('solicito el analisis'),
            'producir':    _('produjo la solucion'),
        }
        if accion not in etiquetas:
            raise UserError(_('Accion no valida: %s') % accion)

        # La accion corre CON el usuario identificado por PIN, no con el de la
        # tablet: asi create_uid/write_uid y las firmas del flujo quedan a su
        # nombre, que es lo que exige la trazabilidad.
        registro = self.with_user(operador.id)

        if accion == 'supervision':
            registro.action_amunet_request_supervision()
        elif accion == 'analisis':
            registro.action_request_analysis()
        elif accion == 'producir':
            registro.button_mark_done()

        self.sudo().message_post(body=_(
            '<b>%(quien)s</b> %(que)s desde la tablet (%(tablet)s), '
            'identificada con su PIN.',
            quien=operador.name, que=etiquetas[accion],
            tablet=self.env.user.name,
        ))
        return True
