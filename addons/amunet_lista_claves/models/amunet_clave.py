from odoo import models, fields

CLASIFICACIONES = [
    ('mp', 'Materia Prima'),
    ('sp', 'Semiprocesado'),
    ('st', 'Semiterminado'),
    ('mi', 'Material de Impresión'),
    ('pt', 'Producto Terminado'),
    ('ptr', 'Producto Terminado Reactivos'),
    ('eq', 'Equipo'),
    ('co', 'Consumible'),
]


class AmunetClave(models.Model):
    _name = 'amunet.clave'
    _description = 'Lista maestra de claves'
    _order = 'clasificacion, subcategoria, clave'
    _rec_name = 'clave'

    clave = fields.Char(string='Clave', required=True, index=True)
    nombre = fields.Char(string='Nombre', required=True)
    clasificacion = fields.Selection(CLASIFICACIONES, string='Clasificación', required=True)
    subcategoria = fields.Char(string='Subcategoría')
    estado = fields.Selection([
        ('activa', 'Activa'),
        ('archivada', 'Archivada'),
    ], string='Estado', default='activa', required=True)
    fecha_alta = fields.Date(string='Fecha de alta', default=fields.Date.today)
    asignado_por = fields.Many2one('res.users', string='Asignado por',
                                   default=lambda self: self.env.user)
    notas = fields.Text(string='Notas')

    _sql_constraints = [
        ('clave_unique', 'UNIQUE(clave)', 'Esta clave ya existe en el catálogo.'),
    ]
