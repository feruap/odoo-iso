from odoo import api, fields, models, _
from odoo.exceptions import ValidationError

_TIPO = [
    ('P',  'P — Programada'),
    ('NP', 'NP — No Programada'),
    ('AR', 'AR — Reprogramada'),
]


class AmunetProgramaAuditoriaProveedor(models.Model):
    _name = 'amunet.programa.auditoria.proveedor'
    _description = 'Programa de Auditoría a Técnicas de Proveedores'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'anio desc'
    _rec_name = 'name'

    name = fields.Char(compute='_compute_name', store=True)
    anio = fields.Integer(
        string='Año', required=True,
        default=lambda self: fields.Date.today().year)
    state = fields.Selection([
        ('borrador', 'Borrador'),
        ('vigente',  'Vigente'),
        ('cerrado',  'Cerrado'),
    ], default='borrador', string='Estado', required=True, tracking=True)

    linea_ids = fields.One2many(
        'amunet.programa.auditoria.proveedor.linea', 'programa_id',
        string='Proveedores / Contratistas')
    proveedor_count = fields.Integer(
        compute='_compute_proveedor_count', string='Núm. proveedores')

    observaciones = fields.Text()

    elaboro_id    = fields.Many2one('res.users', string='Elaboró',   readonly=True)
    fecha_elaboracion = fields.Date(string='Fecha elaboración',      readonly=True)
    autorizo_id   = fields.Many2one('res.users', string='Autorizó',  readonly=True)
    fecha_autorizacion = fields.Date(string='Fecha autorización',    readonly=True)

    @api.depends('anio')
    def _compute_name(self):
        for r in self:
            r.name = 'Programa Auditoría Proveedores %s' % (r.anio or '')

    def _compute_proveedor_count(self):
        for r in self:
            r.proveedor_count = len(r.linea_ids)

    # ── Firma electrónica ──────────────────────────────────────────────────

    def _amunet_signature_allowed_methods(self):
        return {
            '_signature_elaborar':  _('Elaboración del programa de auditoría a proveedores'),
            '_signature_autorizar': _('Autorización del programa de auditoría a proveedores'),
        }

    def action_firmar_elaboracion(self):
        self.ensure_one()
        if self.state != 'borrador':
            raise ValidationError(_('Solo se puede firmar la elaboración en estado Borrador.'))
        return self.env['amunet.generic.signature.wizard'].open_for(
            self, '_signature_elaborar',
            _('Elaboró'),
            _('Firma de elaboración del %s.') % self.name,
        )

    def _signature_elaborar(self):
        self.ensure_one()
        self.write({
            'elaboro_id': self.env.user.id,
            'fecha_elaboracion': fields.Date.today(),
        })
        return {'type': 'ir.actions.act_window_close'}

    def action_firmar_autorizacion(self):
        self.ensure_one()
        if not self.elaboro_id:
            raise ValidationError(_('Firma primero la elaboración antes de autorizar.'))
        if self.state == 'cerrado':
            raise ValidationError(_('El programa ya está cerrado.'))
        return self.env['amunet.generic.signature.wizard'].open_for(
            self, '_signature_autorizar',
            _('Autorizó'),
            _('Firma de autorización del %s.') % self.name,
        )

    def _signature_autorizar(self):
        self.ensure_one()
        self.write({
            'autorizo_id': self.env.user.id,
            'fecha_autorizacion': fields.Date.today(),
            'state': 'vigente',
        })
        return {'type': 'ir.actions.act_window_close'}

    def action_cerrar(self):
        self.write({'state': 'cerrado'})

    def action_borrador(self):
        self.write({
            'state': 'borrador',
            'autorizo_id': False,
            'fecha_autorizacion': False,
        })

    def unlink(self):
        if not self.env.user.has_group('amunet_documentos.group_documentos_manager'):
            raise ValidationError(_('Solo el gestor de documentos puede eliminar este programa.'))
        return super().unlink()


class AmunetProgramaAuditoriaProveedorLinea(models.Model):
    _name = 'amunet.programa.auditoria.proveedor.linea'
    _description = 'Línea del programa de auditoría a proveedores'
    _order = 'programa_id, secuencia, id'

    programa_id = fields.Many2one(
        'amunet.programa.auditoria.proveedor', required=True, ondelete='cascade')
    secuencia   = fields.Integer(default=10)
    proveedor   = fields.Char(string='Proveedor / Contratista', required=True)

    ene = fields.Selection(_TIPO, string='ENE')
    feb = fields.Selection(_TIPO, string='FEB')
    mar = fields.Selection(_TIPO, string='MAR')
    abr = fields.Selection(_TIPO, string='ABR')
    may = fields.Selection(_TIPO, string='MAY')
    jun = fields.Selection(_TIPO, string='JUN')
    jul = fields.Selection(_TIPO, string='JUL')
    ago = fields.Selection(_TIPO, string='AGO')
    sep = fields.Selection(_TIPO, string='SEP')
    oct = fields.Selection(_TIPO, string='OCT')
    nov = fields.Selection(_TIPO, string='NOV')
    dic = fields.Selection(_TIPO, string='DIC')
