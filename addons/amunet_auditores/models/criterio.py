from odoo import fields, models


class AmunetAuditorCriterio(models.Model):
    _name = 'amunet.auditor.criterio'
    _description = 'Criterio de evaluación para auditores internos'
    _order = 'categoria, secuencia, name'

    name = fields.Char(string='Criterio', required=True)
    secuencia = fields.Integer(default=10)
    categoria = fields.Selection([
        ('conocimiento', 'Conocimiento técnico'),
        ('habilidad', 'Habilidades'),
        ('experiencia', 'Experiencia'),
        ('disponibilidad', 'Disponibilidad'),
    ], string='Categoría', required=True, default='conocimiento')
    descripcion = fields.Text(string='Descripción')
    tipo = fields.Selection([
        ('numerica', 'Calificación 1-5'),
        ('abierta', 'Respuesta abierta'),
    ], string='Tipo de evaluación', default='numerica', required=True)
    active = fields.Boolean(default=True)
