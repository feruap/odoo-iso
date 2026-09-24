# -*- coding: utf-8 -*-
"""Modificar una vigencia exige razon y firma electronica.

Una vigencia dice hasta cuando se puede vender un producto. Cambiar una fecha
mueve esa frontera, y hasta hoy se hacia editando el campo y guardando: quedaba
el rastro del tracking, pero sin decir POR QUE ni quien lo respaldaba con su
firma.

Mery, 24-sep-2026: quien modifique tiene que poner la razon y firmar con su PIN.

Se sigue el patron que ya usan los demas modulos de la casa (rechazo de control
de cambios, firma de AMEF, captura de temperatura): el PIN se valida contra
amunet.quality.signature.pin y, si el usuario no tiene PIN dado de alta, se
acepta su contrasena de Odoo. La razon queda en el chatter del registro y en la
bitacora de auditoria, que es la que vale para ISO 13485.
"""

from markupsafe import Markup

from odoo import _, fields, models
from odoo.exceptions import ValidationError

# Los campos que no se pueden mover sin razon y firma. El resto de la ficha
# -- notas, titular, el PDF -- no cambia la frontera de uso del producto.
CAMPOS_CONTROLADOS = ('fecha_vencimiento', 'numero', 'fecha_emision', 'name', 'tipo')


class AmunetVencimientoFirmaWizard(models.TransientModel):
    _name = 'amunet.vencimiento.firma.wizard'
    _description = 'Modificar una vigencia con razón y firma'

    vencimiento_id = fields.Many2one(
        'amunet.vencimiento', string='Vigencia', required=True, readonly=True)

    # lo que hay hoy, para que se vea contra que se compara
    actual_numero = fields.Char(string='Número actual', readonly=True)
    actual_fecha_vencimiento = fields.Date(string='Vence actualmente', readonly=True)
    actual_fecha_emision = fields.Date(string='Emitido actualmente', readonly=True)

    # lo nuevo
    numero = fields.Char(string='Número / Folio')
    fecha_emision = fields.Date(string='Fecha de emisión')
    fecha_vencimiento = fields.Date(string='Fecha de vencimiento')

    motivo = fields.Text(
        string='Razón del cambio', required=True,
        help='Por qué se modifica. Queda en el expediente del registro y en la '
             'bitácora de auditoría; es lo que se muestra en una revisión.')
    password = fields.Char(string='Contraseña / PIN', required=True)

    def _validate_credentials(self, password):
        """PIN de firmas, y si no tiene PIN dado de alta, su contrasena."""
        user = self.env.user
        pin_record = self.env['amunet.quality.signature.pin'].sudo().search(
            [('user_id', '=', user.id)], limit=1)
        if pin_record and pin_record.check_pin(password):
            return True
        try:
            uid = self.env['res.users'].authenticate(
                {'type': 'password', 'db': self.env.cr.dbname,
                 'login': user.login, 'password': password},
                {'interactive': True})
            return bool(uid)
        except Exception:
            return False

    def action_confirmar(self):
        self.ensure_one()
        if not self._validate_credentials(self.password):
            raise ValidationError(_('La contraseña o PIN es incorrecto.'))

        venc = self.vencimiento_id
        cambios, vals = [], {}
        for campo in ('numero', 'fecha_emision', 'fecha_vencimiento'):
            nuevo = self[campo]
            viejo = venc[campo]
            if nuevo and nuevo != viejo:
                vals[campo] = nuevo
                cambios.append((campo, viejo, nuevo))
        if not cambios:
            raise ValidationError(_('No cambiaste ningún dato.'))

        # el write del modelo solo pasa con esta llave en el contexto
        venc.with_context(amunet_venc_firmado=True).sudo().write(vals)

        etiquetas = dict(
            numero=_('Número'), fecha_emision=_('Fecha de emisión'),
            fecha_vencimiento=_('Fecha de vencimiento'))
        # El cuerpo va como Markup: message_post escapa un str normal y en el
        # chatter se leeria el HTML crudo, etiquetas incluidas.
        detalle = Markup('<br/>').join(
            Markup('%s: <b>%s</b> &#8594; <b>%s</b>') % (etiquetas[c], v or '—', n)
            for c, v, n in cambios)
        venc.message_post(body=Markup(
            '<p><b>%(quien)s</b> modificó esta vigencia y lo firmó '
            'electrónicamente.</p><p>%(detalle)s</p><p>Razón: %(motivo)s</p>'
        ) % {'quien': self.env.user.name, 'detalle': detalle,
             'motivo': self.motivo})

        Log = self.env['amunet.quality.audit.log'].sudo()
        for campo, viejo, nuevo in cambios:
            Log.create({
                'model_name': venc._name,
                'res_id': venc.id,
                'res_name': venc.display_name,
                'user_id': self.env.user.id,
                'field_name': campo,
                'field_description': etiquetas[campo],
                'old_value': str(viejo or ''),
                'new_value': str(nuevo),
                'justification': self.motivo,
            })
        return {'type': 'ir.actions.act_window_close'}
