# -*- coding: utf-8 -*-
from odoo import api, fields, models
from odoo.exceptions import UserError


class AmunetDocumento(models.Model):
    _name = 'amunet.documento'
    _description = 'Documento Controlado (ISO 13485 4.2)'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'codigo'

    codigo = fields.Char(string='Codigo', required=True, copy=False,
                         default='Nuevo', tracking=True)
    name = fields.Char(string='Titulo', required=True, tracking=True)
    tipo = fields.Selection([
        ('pno', 'PNO'), ('formato', 'Formato'), ('manual', 'Manual'),
        ('instructivo', 'Instructivo'), ('politica', 'Politica'), ('otro', 'Otro'),
    ], string='Tipo', default='pno', required=True, tracking=True)
    version_actual = fields.Char(string='Version actual', default='1.0', tracking=True)
    state = fields.Selection([
        ('borrador', 'Borrador'), ('en_revision', 'En revision'),
        ('vigente', 'Vigente'), ('obsoleto', 'Obsoleto'),
    ], string='Estado', default='borrador', tracking=True)
    responsable_id = fields.Many2one('res.users', string='Responsable',
                                     default=lambda self: self.env.user, tracking=True)
    fecha_vigencia = fields.Date(string='Vigente hasta', tracking=True)
    fecha_publicacion = fields.Date(string='Fecha de publicacion', readonly=True)
    archivo = fields.Binary(string='Archivo (version actual)', attachment=True)
    archivo_filename = fields.Char(string='Nombre de archivo')
    version_ids = fields.One2many('amunet.documento.version', 'documento_id',
                                  string='Historial de versiones')
    distribucion_ids = fields.One2many('amunet.documento.distribucion', 'documento_id',
                                       string='Distribucion')
    firma_revisa_id = fields.Many2one('res.users', string='Revisado por', readonly=True)
    fecha_revisa = fields.Date(string='Fecha de revision', readonly=True)
    firma_aprueba_id = fields.Many2one('res.users', string='Aprobado por', readonly=True)
    fecha_aprueba = fields.Date(string='Fecha de aprobacion', readonly=True)
    company_id = fields.Many2one('res.company', string='Compania',
                                 default=lambda self: self.env.company)

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if not vals.get('codigo') or vals.get('codigo') == 'Nuevo':
                vals['codigo'] = self.env['ir.sequence'].next_by_code('amunet.documento') or 'Nuevo'
        return super().create(vals_list)

    def action_en_revision(self):
        for r in self:
            r.write({'state': 'en_revision',
                     'firma_revisa_id': self.env.user.id,
                     'fecha_revisa': fields.Date.today()})

    def action_aprobar(self):
        for r in self:
            if not r.archivo:
                raise UserError('Adjunta el archivo de la version antes de aprobar y publicar.')
            r.write({'state': 'vigente',
                     'firma_aprueba_id': self.env.user.id,
                     'fecha_aprueba': fields.Date.today(),
                     'fecha_publicacion': fields.Date.today()})

    def action_obsoleto(self):
        self.write({'state': 'obsoleto'})

    def action_volver_borrador(self):
        self.write({'state': 'borrador'})

    def action_nueva_version(self):
        for r in self:
            self.env['amunet.documento.version'].create({
                'documento_id': r.id,
                'version': r.version_actual,
                'fecha': r.fecha_publicacion or fields.Date.today(),
                'archivo': r.archivo,
                'archivo_filename': r.archivo_filename,
                'aprobado_por_id': r.firma_aprueba_id.id or False,
            })
            try:
                nv = str(round(float(r.version_actual) + 1.0, 1))
            except (ValueError, TypeError):
                nv = (r.version_actual or '1') + '.1'
            r.write({
                'version_actual': nv, 'state': 'borrador',
                'archivo': False, 'archivo_filename': False,
                'firma_revisa_id': False, 'fecha_revisa': False,
                'firma_aprueba_id': False, 'fecha_aprueba': False,
                'fecha_publicacion': False,
            })


class AmunetDocumentoVersion(models.Model):
    _name = 'amunet.documento.version'
    _description = 'Version historica de documento controlado'
    _order = 'fecha desc, id desc'

    documento_id = fields.Many2one('amunet.documento', required=True, ondelete='cascade')
    version = fields.Char(string='Version')
    fecha = fields.Date(string='Fecha')
    archivo = fields.Binary(string='Archivo', attachment=True)
    archivo_filename = fields.Char(string='Nombre de archivo')
    cambios = fields.Text(string='Resumen de cambios')
    aprobado_por_id = fields.Many2one('res.users', string='Aprobado por')


class AmunetDocumentoDistribucion(models.Model):
    _name = 'amunet.documento.distribucion'
    _description = 'Distribucion de documento controlado'

    documento_id = fields.Many2one('amunet.documento', required=True, ondelete='cascade')
    usuario_id = fields.Many2one('res.users', string='Destinatario', required=True)
    acuse = fields.Boolean(string='Acuse de recibido')
    fecha_acuse = fields.Date(string='Fecha de acuse', readonly=True)

    def action_acusar(self):
        for r in self:
            r.write({'acuse': True, 'fecha_acuse': fields.Date.today()})
