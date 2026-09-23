# -*- coding: utf-8 -*-
from datetime import date, timedelta
from dateutil.relativedelta import relativedelta
from odoo import api, fields, models

DESTINATARIOS = [
    'desarrollo@amunet.com.mx',
    'r.sanitario@amunet.com.mx',
    's.controldecalidad@amunet.com.mx',
    'documentacion@amunet.com.mx',
    'fernando.ruiz@amunet.com.mx',
]

# (días_antes, etiqueta, color_hex)
RECORDATORIOS = [
    (200, '🟢 PRIMER AVISO — Iniciar preparación',  '#27ae60'),
    (180, '🟠 ENVIAR DOCUMENTOS — Fecha ideal',     '#e67e22'),
    (150, '🔴 FECHA LÍMITE LEGAL — Plazo COFEPRIS', '#c0392b'),
    (120, '⚠️ Vencimiento en 120 días',             '#b45309'),
    ( 90, '⚠️ Vencimiento en 90 días',              '#b45309'),
    ( 60, '⚠️ Vencimiento en 60 días',              '#b45309'),
    ( 30, '🔴 Vencimiento en 30 días',              '#dc2626'),
    ( 15, '🔴 Vencimiento en 15 días',              '#dc2626'),
    (  5, '🔴 Vencimiento en 5 días',               '#dc2626'),
]

TIPO_SELECTION = [
    ('registro_sanitario',  'Registro sanitario'),
    ('certificado_bpf',     'Certificado BPF'),
    ('permiso_importacion', 'Permiso de importación'),
    ('aviso_funcionamiento','Aviso de funcionamiento'),
    ('otro',                'Otro'),
]

AVISO_PRORROGA = [
    ('iniciar',  'Iniciar preparación'),
    ('enviar',   'Enviar a COFEPRIS'),
    ('urgente',  'Prórroga urgente'),
    ('vencido',  'Vencido'),
    ('vigente',  ''),
]


class AmunetVencimiento(models.Model):
    _name = 'amunet.vencimiento'
    _description = 'Control de vigencias — registros, certificados y permisos'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'fecha_vencimiento asc'

    name = fields.Char(string='Nombre del documento', required=True, tracking=True)
    numero = fields.Char(string='Número / Folio', tracking=True)
    tipo = fields.Selection(TIPO_SELECTION, string='Tipo', required=True,
                            default='registro_sanitario', tracking=True)
    titular = fields.Char(string='Titular / Empresa')
    fecha_emision = fields.Date(string='Fecha de emisión')
    fecha_vencimiento = fields.Date(string='Fecha de vencimiento', required=True, tracking=True)
    archivo = fields.Binary(string='Documento (PDF)')
    archivo_filename = fields.Char()
    notas = fields.Text(string='Notas')

    dias_restantes = fields.Integer(
        string='Días restantes',
        compute='_compute_dias_restantes',
        store=True,
    )
    estado = fields.Selection([
        ('vigente',    'Vigente'),
        ('por_vencer', 'Por vencer'),
        ('vencido',    'Vencido'),
    ], string='Estado', compute='_compute_estado', store=True)

    aviso_prorroga = fields.Selection(
        AVISO_PRORROGA,
        string='Aviso prórroga',
        compute='_compute_aviso_prorroga',
        store=True,
    )

    alerta_ids = fields.One2many('amunet.vencimiento.alerta', 'vencimiento_id',
                                 string='Alertas enviadas')

    @api.depends('fecha_vencimiento')
    def _compute_dias_restantes(self):
        hoy = date.today()
        for rec in self:
            if rec.fecha_vencimiento:
                rec.dias_restantes = (rec.fecha_vencimiento - hoy).days
            else:
                rec.dias_restantes = 0

    @api.depends('dias_restantes')
    def _compute_estado(self):
        for rec in self:
            d = rec.dias_restantes
            if d < 0:
                rec.estado = 'vencido'
            elif d <= 180:
                rec.estado = 'por_vencer'
            else:
                rec.estado = 'vigente'

    @api.depends('dias_restantes')
    def _compute_aviso_prorroga(self):
        for rec in self:
            d = rec.dias_restantes
            if d < 0:
                rec.aviso_prorroga = 'vencido'
            elif d <= 150:
                rec.aviso_prorroga = 'urgente'
            elif d <= 180:
                rec.aviso_prorroga = 'enviar'
            elif d <= 200:
                rec.aviso_prorroga = 'iniciar'
            else:
                rec.aviso_prorroga = 'vigente'

    def action_enviar_alerta_manual(self):
        self.ensure_one()
        self._enviar_correo_alerta(forzar=True)
        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'title': 'Alerta enviada',
                'message': 'Se envió el correo de alerta al comité.',
                'type': 'success',
            },
        }

    def _ya_enviado(self, dias):
        self.ensure_one()
        return self.env['amunet.vencimiento.alerta'].search_count([
            ('vencimiento_id', '=', self.id),
            ('dias_antes', '=', dias),
        ]) > 0

    def _enviar_correo_alerta(self, forzar=False):
        self.ensure_one()
        hoy = date.today()
        dias = self.dias_restantes

        disparar = None
        etiqueta = '⚠️ Recordatorio de vencimiento'
        color = '#b45309'

        if not forzar:
            for d, lbl, clr in RECORDATORIOS:
                disparo = self.fecha_vencimiento - timedelta(days=d)
                if hoy >= disparo and not self._ya_enviado(d):
                    disparar = d
                    etiqueta = lbl
                    color = clr
                    break
            if disparar is None:
                return
        else:
            disparar = dias
            for d, lbl, clr in RECORDATORIOS:
                if dias <= d:
                    etiqueta = lbl
                    color = clr
                    break

        fecha_ideal = self.fecha_vencimiento - timedelta(days=180)
        fecha_limite = self.fecha_vencimiento - timedelta(days=150)

        asunto = '%s — %s (vence %s)' % (
            etiqueta.split(' — ')[0],
            self.name,
            self.fecha_vencimiento.strftime('%d/%m/%Y'),
        )
        cuerpo = '''
        <html><body style="font-family:Arial;color:#2c3e50;">
          <div style="border-left:6px solid %(color)s;padding:12px 20px;margin-bottom:16px;">
            <h2 style="color:%(color)s;margin:0;">%(etiqueta)s</h2>
            <p style="margin-top:6px;"><b>Faltan %(dias)d días para el vencimiento</b></p>
          </div>

          <h3>Datos del registro</h3>
          <table cellpadding="6" style="font-size:13px;">
            <tr><td><b>Documento:</b></td><td>%(nombre)s</td></tr>
            <tr><td><b>Número:</b></td><td>%(numero)s</td></tr>
            <tr><td><b>Tipo:</b></td><td>%(tipo)s</td></tr>
            <tr><td><b>Titular:</b></td><td>%(titular)s</td></tr>
          </table>

          <h3>Fechas clave para la prórroga</h3>
          <table cellpadding="6" style="font-size:13px;">
            <tr><td>📅 Fecha ideal — someter en DIGIPRiS (180 días antes):</td>
                <td><b>%(fecha_ideal)s</b></td></tr>
            <tr><td>⚠️ Fecha límite legal — plazo COFEPRIS (150 días antes):</td>
                <td><b>%(fecha_limite)s</b></td></tr>
            <tr><td>⛔ Vencimiento del registro:</td>
                <td><b style="color:#dc2626;">%(fecha_vencimiento)s</b></td></tr>
          </table>

          <h3>Acciones requeridas</h3>
          <ul style="font-size:13px;">
            <li><b>200 días antes:</b> Iniciar preparación y recopilación de documentos.</li>
            <li><b>180 días antes:</b> Someter la solicitud de prórroga en DIGIPRiS (COFEPRIS).</li>
            <li><b>150 días antes:</b> Último día legal para presentar. Si no se ha hecho, es urgente.</li>
          </ul>

          <p style="font-size:11px;color:#7f8c8d;">
            Mensaje automático del sistema de alertas de vigencias — Amunet.
          </p>
        </body></html>
        ''' % {
            'color': color,
            'etiqueta': etiqueta,
            'dias': dias,
            'nombre': self.name,
            'numero': self.numero or '—',
            'tipo': dict(TIPO_SELECTION).get(self.tipo, self.tipo),
            'titular': self.titular or '—',
            'fecha_ideal': fecha_ideal.strftime('%d/%m/%Y'),
            'fecha_limite': fecha_limite.strftime('%d/%m/%Y'),
            'fecha_vencimiento': self.fecha_vencimiento.strftime('%d/%m/%Y'),
        }

        partners = self.env['res.partner'].search([('email', 'in', DESTINATARIOS)])
        if partners:
            self.env['mail.mail'].sudo().create({
                'subject': asunto,
                'body_html': cuerpo,
                'email_from': self.env.company.email or 'odoobot@amunet.com.mx',
                'recipient_ids': [(4, p.id) for p in partners],
                'auto_delete': True,
            }).send()

        if not forzar:
            self.env['amunet.vencimiento.alerta'].create({
                'vencimiento_id': self.id,
                'dias_antes': disparar,
                'fecha_envio': hoy,
            })

    @api.model
    def cron_revisar_vencimientos(self):
        for rec in self.search([('fecha_vencimiento', '>=', date.today())]):
            rec._enviar_correo_alerta()


class AmunetVencimientoAlerta(models.Model):
    _name = 'amunet.vencimiento.alerta'
    _description = 'Historial de alertas de vencimiento enviadas'

    vencimiento_id = fields.Many2one('amunet.vencimiento', required=True, ondelete='cascade')
    dias_antes = fields.Integer(string='Días antes del vencimiento')
    fecha_envio = fields.Date(string='Fecha de envío', default=fields.Date.today)
