# -*- coding: utf-8 -*-

from odoo import api, fields, models, _
from odoo.exceptions import UserError

# Acciones que el kiosco puede firmar. Lista blanca a proposito: el asistente
# NO ejecuta cualquier metodo que le manden por contexto.
ACCIONES_PERMITIDAS = {
    'abrir':      'Iniciar elaboracion',
    'supervision': 'Enviar a supervision',
    'analisis':   'Solicitar analisis',
    'producir':   'Producir',
}


class AmunetKioscoPinWizard(models.TransientModel):
    """Captura de PIN en la tablet del area de soluciones.

    A diferencia del asistente de firma de Calidad (que valida el PIN contra el
    usuario de la SESION), aqui el PIN IDENTIFICA a la persona. Es lo que
    permite que tres personas compartan una tablet sin cerrar sesion y que el
    expediente registre a quien de verdad hizo el trabajo.

    Este asistente es EXCLUSIVO de soluciones. No toca
    amunet.generic.signature.wizard ni el flujo de firmas de Calidad.
    """
    _name = 'amunet.kiosco.pin.wizard'
    _description = 'Identificacion por PIN en kiosco de soluciones'

    production_id = fields.Many2one(
        'mrp.production', string='Orden de solucion', required=True)
    accion = fields.Selection(
        [(k, v) for k, v in ACCIONES_PERMITIDAS.items()],
        string='Accion', required=True)
    pin = fields.Char(string='PIN', password=True)

    titulo = fields.Char(string='Que vas a firmar', readonly=True)
    operador_actual_id = fields.Many2one(
        'res.users', string='Trabajando ahora', readonly=True,
        help='Quien tiene abierta la elaboracion en esta tablet.')

    # ------------------------------------------------------------------
    @api.model
    def abrir_para(self, production, accion):
        if accion not in ACCIONES_PERMITIDAS:
            raise UserError(_('Accion no permitida en el kiosco: %s') % accion)
        sesion = production._kiosco_sesion_activa()
        wizard = self.create([{
            'production_id': production.id,
            'accion': accion,
            'titulo': ACCIONES_PERMITIDAS[accion],
            'operador_actual_id': sesion.operador_id.id if sesion else False,
        }])
        return {
            'type': 'ir.actions.act_window',
            'name': ACCIONES_PERMITIDAS[accion],
            'res_model': self._name,
            'res_id': wizard.id,
            'view_mode': 'form',
            'target': 'new',
        }

    # ------------------------------------------------------------------
    def action_confirmar(self):
        self.ensure_one()
        mo = self.production_id
        Sesion = self.env['amunet.kiosco.sesion']

        if self.accion == 'abrir':
            sesion = Sesion.abrir(mo, self.pin)
            return {
                'type': 'ir.actions.client',
                'tag': 'display_notification',
                'params': {
                    'title': _('Elaboracion iniciada'),
                    'message': _('Trabajando: %s') % sesion.operador_id.name,
                    'type': 'success',
                    'sticky': False,
                    'next': {'type': 'ir.actions.act_window_close'},
                },
            }

        # Para firmar: el PIN identifica, y ademas debe coincidir con quien
        # tiene abierta la elaboracion. Asi nadie firma el trabajo de otro.
        operador = Sesion._resolver_por_pin(self.pin)
        sesion = mo._kiosco_sesion_activa()
        if sesion and sesion.operador_id != operador:
            raise UserError(_(
                'Esta elaboracion la tiene abierta %(abierta)s, pero el PIN es '
                'de %(pin)s.\n\n'
                'Solo puede firmarla quien la elaboro. Si hubo relevo, cierra '
                'la elaboracion y abrela de nuevo con tu PIN.',
                abierta=sesion.operador_id.name, pin=operador.name,
            ))

        mo._kiosco_ejecutar(self.accion, operador)
        if sesion:
            sesion.latir()
            if self.accion == 'supervision':
                sesion.cerrar('enviada')
        return {'type': 'ir.actions.act_window_close'}
