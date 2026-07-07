from odoo import models, fields, api

CATEGORIAS = [
    ('lfia', 'LFIA'),
    ('nalf', 'NALF'),
    ('equipos', 'EQUIPOS'),
]

SUBCAT_LFIA = [
    ('sangre', 'Sangre total-capilar'),
    ('suero', 'Suero o plasma'),
    ('nasofaringea', 'Nasofaríngea'),
    ('heces', 'Heces'),
    ('orofaringea', 'Orofaríngea'),
    ('saliva', 'Saliva'),
]

ESTADOS = [
    ('borrador', 'Borrador'),
    ('en_revision', 'En revisión'),
    ('aprobado', 'Aprobado'),
]


class DocCompartida(models.Model):
    _name = 'amunet.doc.compartida'
    _description = 'Documentación Compartida'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'fecha desc, name'

    name = fields.Char(string='Título', required=True, tracking=True)
    carpeta_id = fields.Many2one('amunet.doc.carpeta', string='Carpeta', tracking=True)
    categoria = fields.Selection(CATEGORIAS, string='Apartado', required=True, tracking=True)
    subcategoria_lfia = fields.Selection(SUBCAT_LFIA, string='Matriz / Muestra', tracking=True)
    state = fields.Selection(ESTADOS, string='Estado', default='borrador',
                             required=True, tracking=True)
    version = fields.Char(string='Versión', default='1.0')
    fecha = fields.Date(string='Fecha', default=fields.Date.today)
    responsable_validacion_id = fields.Many2one(
        'res.users', string='Responsable Validación', tracking=True)
    responsable_calidad_id = fields.Many2one(
        'res.users', string='Responsable Calidad', tracking=True)
    descripcion = fields.Html(string='Descripción / Contenido')
    notas = fields.Text(string='Notas internas')

    def action_en_revision(self):
        self.write({'state': 'en_revision'})

    def action_aprobar(self):
        self.write({'state': 'aprobado'})

    def action_borrador(self):
        self.write({'state': 'borrador'})
