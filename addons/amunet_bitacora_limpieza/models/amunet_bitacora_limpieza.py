from odoo import api, fields, models, _
from odoo.exceptions import UserError

MESES = [
    ('01', 'Enero'), ('02', 'Febrero'), ('03', 'Marzo'), ('04', 'Abril'),
    ('05', 'Mayo'), ('06', 'Junio'), ('07', 'Julio'), ('08', 'Agosto'),
    ('09', 'Septiembre'), ('10', 'Octubre'), ('11', 'Noviembre'), ('12', 'Diciembre'),
]


class AmunetLimpiezaArea(models.Model):
    _name = 'amunet.limpieza.area'
    _description = 'Área de limpieza'
    _inherit = ['mail.thread']
    _order = 'sequence, name'

    name = fields.Char(string='Área / Laboratorio', required=True, tracking=True)
    code = fields.Char(string='Código')
    sequence = fields.Integer(default=10)
    equipo_ids = fields.One2many(
        'amunet.limpieza.equipo', 'area_id', string='Equipos / Zonas predeterminados')


class AmunetLimpiezaEquipo(models.Model):
    _name = 'amunet.limpieza.equipo'
    _description = 'Equipo de limpieza (catálogo)'
    _order = 'sequence, name'

    area_id = fields.Many2one(
        'amunet.limpieza.area', required=True, ondelete='cascade')
    name = fields.Char(string='Equipo / Zona', required=True)
    frecuencia = fields.Selection([
        ('diaria', 'Diaria'),
        ('semanal', 'Semanal'),
        ('mensual', 'Mensual'),
        ('trimestral', 'Trimestral'),
    ], string='Frecuencia', default='mensual', required=True)
    sequence = fields.Integer(default=10)


class AmunetBitacoraLimpieza(models.Model):
    _name = 'amunet.bitacora.limpieza'
    _description = 'Bitácora de Limpieza'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'name desc'

    name = fields.Char(string='Folio', readonly=True, copy=False, default='Nuevo')
    area_id = fields.Many2one(
        'amunet.limpieza.area', string='Área / Laboratorio', required=True,
        ondelete='restrict', tracking=True)
    mes = fields.Selection(MESES, string='Mes', required=True,
                           default=lambda self: '%02d' % fields.Date.today().month)
    anio = fields.Integer(string='Año', required=True,
                          default=lambda self: fields.Date.today().year)
    state = fields.Selection([
        ('borrador',    'Borrador'),
        ('en_revision', 'En revisión'),
        ('cerrado',     'Cerrado'),
    ], string='Estado', default='borrador', required=True, tracking=True)

    n_equipos = fields.Integer(
        string='Equipos', compute='_compute_n_equipos', store=True)

    linea_ids = fields.One2many(
        'amunet.bitacora.limpieza.linea', 'bitacora_id', string='Equipos / Áreas')

    revisor_id = fields.Many2one('res.users', string='Revisado por (QA/Supervisor)')
    firma_revisor_id = fields.Many2one('res.users', string='Firma revisor', readonly=True)
    fecha_firma_revisor = fields.Datetime(string='Fecha firma', readonly=True)
    comentarios = fields.Text(
        string='Comentarios de auditoría / Observaciones adicionales')

    _sql_constraints = [
        ('area_mes_anio_uniq', 'unique(area_id, mes, anio)',
         'Ya existe una bitácora para esta área y período.'),
    ]

    @api.depends('linea_ids')
    def _compute_n_equipos(self):
        for r in self:
            r.n_equipos = len(r.linea_ids)

    @api.onchange('area_id')
    def _onchange_area_id(self):
        if self.area_id and self.area_id.equipo_ids and not self.linea_ids:
            self.linea_ids = [
                (0, 0, {
                    'equipo': eq.name,
                    'frecuencia': eq.frecuencia,
                    'sequence': eq.sequence,
                })
                for eq in self.area_id.equipo_ids
            ]

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if not vals.get('name') or vals['name'] == 'Nuevo':
                today = fields.Date.today()
                mm = '%02d' % today.month
                yy = '%02d' % (today.year % 100)
                seq = self.env['ir.sequence'].next_by_code('amunet.bitacora.limpieza') or '001'
                vals['name'] = 'BL-%s%s-%s' % (mm, yy, seq)
            if vals.get('area_id') and not vals.get('linea_ids'):
                area = self.env['amunet.limpieza.area'].browse(vals['area_id'])
                if area.equipo_ids:
                    vals['linea_ids'] = [
                        (0, 0, {
                            'equipo': eq.name,
                            'frecuencia': eq.frecuencia,
                            'sequence': eq.sequence,
                        })
                        for eq in area.equipo_ids
                    ]
        return super().create(vals_list)

    # ── Firma electrónica ─────────────────────────────────────────────

    def _amunet_signature_allowed_methods(self):
        return {
            '_signature_revisor': 'Firma del revisor',
        }

    def _abrir_firma(self, method_name, label):
        self.ensure_one()
        return self.env['amunet.generic.signature.wizard'].open_for(
            self, method_name, label, _('Bitácora: %s') % (self.name or ''))

    def action_firmar_revisor(self):
        self.ensure_one()
        if self.firma_revisor_id:
            raise UserError(_('Ya se registró esta firma.'))
        if self.revisor_id and self.revisor_id != self.env.user:
            raise UserError(
                _('Solo %s puede firmar en este espacio.') % self.revisor_id.name)
        return self._abrir_firma('_signature_revisor', _('Firma del revisor'))

    def _signature_revisor(self):
        self.ensure_one()
        self.write({
            'firma_revisor_id': self.env.user.id,
            'fecha_firma_revisor': fields.Datetime.now(),
        })
        self._message_log(
            body=_('<p><b>%s</b> firmó como Revisor.</p>') % self.env.user.name)

    # ── Flujo de estados ──────────────────────────────────────────────

    def action_enviar_revision(self):
        for rec in self:
            if rec.state != 'borrador':
                raise UserError(_('Solo puedes enviar a revisión desde Borrador.'))
            rec.state = 'en_revision'

    def action_cerrar(self):
        for rec in self:
            if rec.state != 'en_revision':
                raise UserError(_('Solo puedes cerrar desde "En revisión".'))
            rec.write({'state': 'cerrado'})

    def action_reabrir(self):
        for rec in self:
            if rec.state != 'cerrado':
                raise UserError(_('Solo puedes reabrir un registro cerrado.'))
            rec.state = 'en_revision'

    # ── Generación automática mensual ─────────────────────────────────

    @api.model
    def _cron_generar_mensual(self):
        """Corre el 1° de cada mes: crea la bitácora de cada área activa
        si todavía no existe para el mes y año en curso."""
        today = fields.Date.today()
        mes = '%02d' % today.month
        anio = today.year
        areas = self.env['amunet.limpieza.area'].search([('active', '=', True)])
        creadas = []
        for area in areas:
            existe = self.search([
                ('area_id', '=', area.id),
                ('mes', '=', mes),
                ('anio', '=', anio),
            ], limit=1)
            if not existe:
                nueva = self.create({
                    'area_id': area.id,
                    'mes': mes,
                    'anio': anio,
                })
                creadas.append(nueva.name)
        return creadas


class AmunetBitacoraLimpiezaLinea(models.Model):
    _name = 'amunet.bitacora.limpieza.linea'
    _description = 'Línea de Bitácora de Limpieza'
    _order = 'sequence, id'

    bitacora_id = fields.Many2one(
        'amunet.bitacora.limpieza', string='Bitácora', ondelete='cascade', required=True)
    sequence = fields.Integer(default=10)
    equipo = fields.Char(string='Equipo / Área', required=True)
    frecuencia = fields.Selection([
        ('diaria',      'Diaria'),
        ('semanal',     'Semanal'),
        ('mensual',     'Mensual'),
        ('trimestral',  'Trimestral'),
    ], string='Frecuencia', default='mensual', required=True)

    # ── Días 1–31 ────────────────────────────────────────────────────
    dia_01 = fields.Char(string='1');  dia_02 = fields.Char(string='2')
    dia_03 = fields.Char(string='3');  dia_04 = fields.Char(string='4')
    dia_05 = fields.Char(string='5');  dia_06 = fields.Char(string='6')
    dia_07 = fields.Char(string='7');  dia_08 = fields.Char(string='8')
    dia_09 = fields.Char(string='9');  dia_10 = fields.Char(string='10')
    dia_11 = fields.Char(string='11'); dia_12 = fields.Char(string='12')
    dia_13 = fields.Char(string='13'); dia_14 = fields.Char(string='14')
    dia_15 = fields.Char(string='15'); dia_16 = fields.Char(string='16')
    dia_17 = fields.Char(string='17'); dia_18 = fields.Char(string='18')
    dia_19 = fields.Char(string='19'); dia_20 = fields.Char(string='20')
    dia_21 = fields.Char(string='21'); dia_22 = fields.Char(string='22')
    dia_23 = fields.Char(string='23'); dia_24 = fields.Char(string='24')
    dia_25 = fields.Char(string='25'); dia_26 = fields.Char(string='26')
    dia_27 = fields.Char(string='27'); dia_28 = fields.Char(string='28')
    dia_29 = fields.Char(string='29'); dia_30 = fields.Char(string='30')
    dia_31 = fields.Char(string='31')

    responsable_id = fields.Many2one('res.users', string='Responsable')
    observaciones  = fields.Char(string='Observaciones')
