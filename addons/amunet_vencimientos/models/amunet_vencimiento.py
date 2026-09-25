# -*- coding: utf-8 -*-
from datetime import date, timedelta
from dateutil.relativedelta import relativedelta
from odoo.exceptions import UserError
from odoo import _, api, fields, models

DESTINATARIOS = [
    'desarrollo@amunet.com.mx',
    'r.sanitario@amunet.com.mx',
    's.controldecalidad@amunet.com.mx',
    'documentacion@amunet.com.mx',
    'fernando.ruiz@amunet.com.mx',
    'pm@amunet.com.mx',
]

# (días_antes, etiqueta, color_hex)
RECORDATORIOS = [
    (240, '📋 CHECKLIST — Documentos a preparar',   '#8e44ad'),
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
    ('cert_libre_venta',   'Certificado de libre venta de dispositivos médicos'),
    ('otro',                'Otro'),
]

AVISO_PRORROGA = [
    ('checklist', 'Preparar documentos'),
    ('iniciar',   'Iniciar preparación'),
    ('enviar',    'Enviar a COFEPRIS'),
    ('urgente',   'Prórroga urgente'),
    ('vencido',   'Vencido'),
    ('vigente',   ''),
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

    # ── Candado: los datos que mueven la frontera de uso no se cambian a pelo ──
    # Hay que pasar por el wizard de firma, que exige razon y PIN. El candado
    # vive aqui y no en la vista porque la vista no es candado: un write por
    # shell, por importacion o por otro modulo se la salta entera.
    CAMPOS_FIRMADOS = ('fecha_vencimiento', 'numero', 'fecha_emision')

    def write(self, vals):
        tocados = [c for c in self.CAMPOS_FIRMADOS if c in vals]
        if tocados and not self.env.context.get('amunet_venc_firmado'):
            # el alta y las semillas del modulo no pasan por aqui: solo se
            # revisa cuando el registro ya existe y alguien lo modifica
            etiquetas = {
                'fecha_vencimiento': _('la fecha de vencimiento'),
                'numero': _('el número de registro'),
                'fecha_emision': _('la fecha de emisión'),
            }
            raise UserError(_(
                'Para cambiar %(campos)s hay que usar el botón '
                '«Modificar con firma»: se necesita la razón del cambio y tu '
                'PIN.\n\nEsta ficha dice hasta cuándo se puede usar el '
                'producto; un cambio sin razón asentada no se sostiene en una '
                'auditoría.'
            ) % {'campos': ', '.join(etiquetas[c] for c in tocados)})
        return super().write(vals)

    def action_abrir_firma(self):
        """Abre el wizard de modificacion con razon y firma."""
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': _('Modificar vigencia con firma'),
            'res_model': 'amunet.vencimiento.firma.wizard',
            'view_mode': 'form',
            'target': 'new',
            'context': {
                'default_vencimiento_id': self.id,
                'default_actual_numero': self.numero,
                'default_actual_fecha_vencimiento': self.fecha_vencimiento,
                'default_actual_fecha_emision': self.fecha_emision,
                'default_numero': self.numero,
                'default_fecha_vencimiento': self.fecha_vencimiento,
                'default_fecha_emision': self.fecha_emision,
            },
        }

    @api.depends('fecha_vencimiento')
    def _compute_dias_restantes(self):
        hoy = date.today()
        for rec in self:
            if rec.fecha_vencimiento:
                rec.dias_restantes = (rec.fecha_vencimiento - hoy).days
            else:
                rec.dias_restantes = 0

    @api.depends('dias_restantes', 'tipo')
    def _compute_estado(self):
        for rec in self:
            d = rec.dias_restantes
            if d < 0:
                rec.estado = 'vencido'
            elif rec.tipo in ('permiso_importacion', 'cert_libre_venta'):
                rec.estado = 'por_vencer' if d <= 70 else 'vigente'
            elif rec.tipo == 'certificado_bpf':
                rec.estado = 'por_vencer' if d <= 200 else 'vigente'
            else:
                rec.estado = 'por_vencer' if d <= 180 else 'vigente'

    @api.depends('dias_restantes', 'tipo')
    def _compute_aviso_prorroga(self):
        for rec in self:
            d = rec.dias_restantes
            if d < 0:
                rec.aviso_prorroga = 'vencido'
            elif rec.tipo in ('permiso_importacion', 'cert_libre_venta'):
                if d <= 60:
                    rec.aviso_prorroga = 'urgente'
                elif d <= 70:
                    rec.aviso_prorroga = 'iniciar'
                else:
                    rec.aviso_prorroga = 'vigente'
            elif rec.tipo == 'certificado_bpf':
                if d <= 180:
                    rec.aviso_prorroga = 'urgente'
                elif d <= 200:
                    rec.aviso_prorroga = 'iniciar'
                else:
                    rec.aviso_prorroga = 'vigente'
            else:
                if d <= 150:
                    rec.aviso_prorroga = 'urgente'
                elif d <= 180:
                    rec.aviso_prorroga = 'enviar'
                elif d <= 200:
                    rec.aviso_prorroga = 'iniciar'
                elif d <= 240:
                    rec.aviso_prorroga = 'checklist'
                else:
                    rec.aviso_prorroga = 'vigente'

    def _bloque_checklist(self):
        return """
        <h3 style="color:#8e44ad;">📋 Documentos a preparar para la prórroga</h3>

        <h4 style="margin-bottom:4px;">1) Documentos básicos obligatorios</h4>
        <ul>
          <li>Formato de solicitud de prórroga completado</li>
          <li>Comprobante de pago de derechos gubernamentales (original)</li>
          <li>Documento de identidad del representante legal (RUPA o carta poder)</li>
          <li>Copia simple del registro sanitario vigente y sus modificaciones</li>
        </ul>

        <h4 style="margin-bottom:4px;">2) Documentos técnicos esenciales</h4>
        <ul>
          <li>Informe de tecnovigilancia (últimos 5 años)</li>
          <li>Certificado de Análisis del fabricante (con membrete y firma del responsable sanitario)</li>
          <li>Certificado de Buenas Prácticas de Fabricación (GMP / BPF)</li>
        </ul>

        <h4 style="margin-bottom:4px;">3) Si el dispositivo es importado</h4>
        <ul>
          <li>Certificado de Libre Venta (emitido en el último año)</li>
          <li>Carta de representación (si aplica)</li>
          <li>Proyecto de etiquetado e instructivos de uso</li>
        </ul>

        <div style="background:#fef9e7;padding:12px;border-left:4px solid #f1c40f;margin-top:8px;">
          <b>⚠️ Importante:</b>
          <ul style="margin:6px 0;">
            <li>Documentos en otro idioma requieren traducción al español.</li>
            <li>Documentos del extranjero requieren apostilla o legalización.</li>
            <li>Verifica la clasificación del dispositivo (Clase I / II / III) para confirmar requisitos específicos.</li>
          </ul>
        </div>
        """

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
        checklist_html = self._bloque_checklist() if disparar == 240 else ''

        asunto = '%s — %s (vence %s)' % (
            etiqueta.split(' — ')[0],
            self.name,
            self.fecha_vencimiento.strftime('%d/%m/%Y'),
        )
        cuerpo = ('''
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

          %(checklist_html)s

          <h3>Acciones requeridas</h3>
          <ul style="font-size:13px;">
            <li><b>240 días antes:</b> Revisar checklist e iniciar recopilación de documentos.</li>
            <li><b>200 días antes:</b> Confirmar que todos los documentos estén listos y vigentes.</li>
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
            'checklist_html': checklist_html,
        })

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
