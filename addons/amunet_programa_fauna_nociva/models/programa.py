from odoo import api, fields, models, _
from odoo.exceptions import ValidationError

_ESTADO = [
    ('P',         'P — Programada'),
    ('R',         'R — Reprogramada'),
    ('realizada', 'Realizada'),
    ('cancelada', 'Cancelada'),
]

_AREAS = [
    ('almacen_mp',    'Almacén de materia prima'),
    ('produccion',    'Producción'),
    ('control_cal',   'Control de calidad'),
    ('oficinas',      'Oficina y vestidores'),
    ('comedor',       'Comedor'),
    ('almacen_pt',    'Almacén producto terminado'),
    ('servicios',     'Servicios auxiliares, pasillos y sanitarios'),
]


class AmunetProgramaFaunaNociva(models.Model):
    _name = 'amunet.programa.fauna.nociva'
    _description = 'Programa Anual Prevención de Fauna Nociva'
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
        'amunet.programa.fauna.nociva.linea', 'programa_id', string='Áreas')

    observaciones = fields.Text()

    elaboro_id        = fields.Many2one('res.users', string='Elaboró',  readonly=True)
    fecha_elaboracion = fields.Date(string='Fecha elaboración',          readonly=True)
    reviso_id         = fields.Many2one('res.users', string='Revisó',   readonly=True)
    fecha_revision    = fields.Date(string='Fecha revisión',             readonly=True)

    @api.depends('anio')
    def _compute_name(self):
        for r in self:
            r.name = 'Programa Fauna Nociva %s' % (r.anio or '')

    @api.model_create_multi
    def create(self, vals_list):
        records = super().create(vals_list)
        for rec in records:
            if not rec.linea_ids:
                self.env['amunet.programa.fauna.nociva.linea'].create([
                    {'programa_id': rec.id, 'area': area, 'secuencia': i * 10}
                    for i, (area, _) in enumerate(_AREAS, start=1)
                ])
        return records

    # ── Firma electrónica ──────────────────────────────────────────────────

    def _amunet_signature_allowed_methods(self):
        return {
            '_signature_elaborar': _('Elaboración del programa de prevención de fauna nociva'),
            '_signature_revisar':  _('Revisión del programa de prevención de fauna nociva'),
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

    def action_firmar_revision(self):
        self.ensure_one()
        if not self.elaboro_id:
            raise ValidationError(_('Firma primero la elaboración antes de revisar.'))
        if self.state == 'cerrado':
            raise ValidationError(_('El programa ya está cerrado.'))
        return self.env['amunet.generic.signature.wizard'].open_for(
            self, '_signature_revisar',
            _('Revisó'),
            _('Firma de revisión del %s.') % self.name,
        )

    def _signature_revisar(self):
        self.ensure_one()
        self.write({
            'reviso_id': self.env.user.id,
            'fecha_revision': fields.Date.today(),
            'state': 'vigente',
        })
        return {'type': 'ir.actions.act_window_close'}

    def action_cerrar(self):
        self.write({'state': 'cerrado'})

    def action_borrador(self):
        self.write({
            'state': 'borrador',
            'reviso_id': False,
            'fecha_revision': False,
        })

    def unlink(self):
        if not self.env.user.has_group('amunet_documentos.group_documentos_manager'):
            raise ValidationError(_('Solo el gestor de documentos puede eliminar este programa.'))
        return super().unlink()


class AmunetProgramaFaunaNocivaLinea(models.Model):
    _name = 'amunet.programa.fauna.nociva.linea'
    _description = 'Línea del programa de prevención de fauna nociva'
    _order = 'programa_id, secuencia, id'

    programa_id = fields.Many2one(
        'amunet.programa.fauna.nociva', required=True, ondelete='cascade')
    secuencia   = fields.Integer(default=10)
    area        = fields.Selection(_AREAS, string='Área', required=True)

    ene = fields.Selection(_ESTADO, string='ENE')
    feb = fields.Selection(_ESTADO, string='FEB')
    mar = fields.Selection(_ESTADO, string='MAR')
    abr = fields.Selection(_ESTADO, string='ABR')
    may = fields.Selection(_ESTADO, string='MAY')
    jun = fields.Selection(_ESTADO, string='JUN')
    jul = fields.Selection(_ESTADO, string='JUL')
    ago = fields.Selection(_ESTADO, string='AGO')
    sep = fields.Selection(_ESTADO, string='SEP')
    oct = fields.Selection(_ESTADO, string='OCT')
    nov = fields.Selection(_ESTADO, string='NOV')
    dic = fields.Selection(_ESTADO, string='DIC')
