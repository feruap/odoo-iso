import logging
from odoo import api, fields, models, _

_logger = logging.getLogger(__name__)

_DICTAMEN = [
    ('pass', 'Aprobado'),
    ('fail', 'Rechazado'),
    ('pending', 'Pendiente'),
    ('not_applicable', 'N/A'),
]


class AmunetCopiaControlada(models.Model):
    _name = 'amunet.copia.controlada'
    _description = 'Lista Maestra de Copias Controladas — Certificados de Calidad'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _rec_name = 'clave'
    _order = 'fecha_generacion desc, id desc'

    # ── Identificación ─────────────────────────────────────────────────────
    clave = fields.Char(string='Clave', readonly=True, copy=False,
        default=lambda self: _('Nuevo'))
    state = fields.Selection([
        ('pendiente', 'Pendiente de recepción'),
        ('recibida', 'Recibida'),
    ], default='pendiente', string='Estado', tracking=True)

    # ── Vínculo al control de calidad ──────────────────────────────────────
    check_id = fields.Many2one('amunet.quality.check',
        string='Control de Calidad', required=True, readonly=True,
        ondelete='restrict')

    # Datos heredados del QC
    no_analisis = fields.Char(
        related='check_id.analysis_number', string='No. de Análisis', store=True)
    producto_id = fields.Many2one(
        related='check_id.product_id', string='Producto', store=True)
    lote = fields.Char(
        related='check_id.lot_id.name', string='Lote', store=True)
    dictamen = fields.Selection(
        _DICTAMEN, related='check_id.global_result', string='Dictamen', store=True)
    fecha_autorizacion = fields.Datetime(
        related='check_id.authorized_date', string='Fecha de autorización', store=True)

    # ── Datos propios ──────────────────────────────────────────────────────
    fecha_generacion = fields.Date(
        string='Fecha de emisión', default=fields.Date.today, readonly=True)
    receptor_id = fields.Many2one('res.users',
        string='Responsable de recepción',
        domain=[('share', '=', False)],
        tracking=True)
    observaciones = fields.Text(string='Observaciones')

    # ── Firma de recepción ────────────────────────────────────────────────
    firma_receptor_id = fields.Many2one(
        'res.users', string='Firmado por', readonly=True)
    fecha_firma_recepcion = fields.Date(
        string='Fecha de firma', readonly=True)
    puede_firmar = fields.Boolean(
        compute='_compute_puede_firmar', store=False)

    # ── Cómputos ──────────────────────────────────────────────────────────

    @api.depends('state', 'receptor_id', 'firma_receptor_id')
    def _compute_puede_firmar(self):
        uid = self.env.user.id
        for r in self:
            r.puede_firmar = (
                r.state == 'pendiente'
                and not r.firma_receptor_id
                and (not r.receptor_id or r.receptor_id.id == uid)
            )

    # ── Secuencia ─────────────────────────────────────────────────────────

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if vals.get('clave', _('Nuevo')) == _('Nuevo'):
                hoy = fields.Date.context_today(self)
                mm = hoy.strftime('%m')
                yy = hoy.strftime('%y')
                num = self.env['ir.sequence'].next_by_code(
                    'amunet.copia.controlada') or '001'
                vals['clave'] = f'CC{mm}{yy}-{num}'
        return super().create(vals_list)

    # ── Creación automática desde QC ──────────────────────────────────────

    @api.model
    def _crear_desde_qc(self, check):
        """Crea la copia controlada cuando calidad finaliza un análisis."""
        receptor = self.env['res.users'].search(
            [('login', '=', 'documentacion@amunet.com.mx')], limit=1)

        copia = self.create({
            'check_id': check.id,
            'receptor_id': receptor.id if receptor else False,
        })

        # Aviso interno al receptor en el chatter
        if receptor and receptor.partner_id:
            copia.message_post(
                body=(
                    f'Se generó automáticamente esta copia controlada del análisis '
                    f'<b>{check.analysis_number}</b> — '
                    f'Producto: {check.product_id.display_name if check.product_id else "—"}, '
                    f'Lote: {check.lot_id.name if check.lot_id else "—"}. '
                    f'<br/>Pendiente de tu firma de recepción.'
                ),
                partner_ids=[receptor.partner_id.id],
                message_type='comment',
                subtype_xmlid='mail.mt_comment',
            )
        return copia

    # ── Descarga de certificado ───────────────────────────────────────────

    def action_descargar_certificado_interno(self):
        self.ensure_one()
        return {
            'type': 'ir.actions.act_url',
            'url': f'/amunet_quality/download_certificado_interno/{self.check_id.id}',
            'target': 'new',
        }

    # ── Firma electrónica ─────────────────────────────────────────────────

    def _amunet_signature_allowed_methods(self):
        return {
            '_signature_recepcion': _('Acuse de Recepción — Copia Controlada'),
        }

    def action_firmar_recepcion(self):
        self.ensure_one()
        return self.env['amunet.generic.signature.wizard'].open_for(
            self, '_signature_recepcion',
            _('Responsable de Documentación'),
            _('Acuse de recepción de copia controlada %s.') % self.clave,
        )

    def _signature_recepcion(self):
        self.ensure_one()
        self.write({
            'firma_receptor_id': self.env.user.id,
            'fecha_firma_recepcion': fields.Date.today(),
            'state': 'recibida',
        })
        return {'type': 'ir.actions.act_window_close'}
