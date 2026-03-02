# -*- coding: utf-8 -*-
from odoo import models, fields


class AmunetAuditoriaChecklist(models.Model):
    """
    Ítem de Checklist dinámico para una Auditoría.
    Cada ítem evalúa una cláusula específica de la norma.

    ISO 13485:2016 §8.2.4
    """
    _name = 'amunet.auditoria.checklist'
    _description = 'Ítem de Checklist de Auditoría'
    _order = 'sequence asc, id asc'

    auditoria_id = fields.Many2one(
        'amunet.auditoria',
        string='Auditoría',
        required=True,
        ondelete='cascade',
        index=True
    )

    sequence = fields.Integer(string='Secuencia', default=10)

    clausula = fields.Char(
        string='Cláusula / Requisito',
        help='Ej: ISO 13485:2016 §7.4.1 o NOM-241 §5.3'
    )

    requisito = fields.Text(
        string='Requisito Evaluado',
        required=True,
        help='Descripción del requisito que se está evaluando'
    )

    evidencia = fields.Text(
        string='Evidencia Encontrada',
        help='Evidencia objetiva observada durante la auditoría'
    )

    resultado = fields.Selection([
        ('conforme', '✅ Conforme'),
        ('nc_menor', '⚠️ NC Menor'),
        ('nc_mayor', '🔴 NC Mayor'),
        ('observacion', '💬 Observación'),
        ('na', '⚪ N/A'),
    ], string='Resultado', default='conforme', required=True)

    notas = fields.Text(string='Notas del Auditor')

    hallazgo_id = fields.Many2one(
        'amunet.auditoria.hallazgo',
        string='Hallazgo Relacionado',
        help='Si este ítem generó un hallazgo, se puede vincular aquí'
    )
