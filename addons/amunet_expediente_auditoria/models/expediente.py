# -*- coding: utf-8 -*-
from odoo import fields, models
from odoo.tools import drop_view_if_exists


class AmunetExpedienteAuditoria(models.Model):
    _name = 'amunet.expediente.auditoria'
    _description = 'Expediente de Auditoría'
    _auto = False
    _rec_name = 'plan_clave'
    _order = 'fecha_inicio desc'

    plan_id = fields.Many2one('amunet.plan.auditoria', string='Plan', readonly=True)
    plan_clave = fields.Char(string='No. Auditoría', readonly=True)
    convocatoria = fields.Char(string='Convocatoria', readonly=True)
    fecha_inicio = fields.Date(string='Fecha', readonly=True)
    lider_id = fields.Many2one('res.users', string='Auditor Líder', readonly=True)
    plan_state = fields.Selection([
        ('borrador', 'Borrador'),
        ('emitido', 'Emitido'),
        ('cerrado', 'Cerrado'),
    ], string='Estado del plan', readonly=True)

    acta_id = fields.Many2one('amunet.acta.auditoria', string='Acta', readonly=True)
    acta_clave = fields.Char(string='Acta', readonly=True)
    acta_state = fields.Selection([
        ('borrador', 'Borrador'),
        ('firmado', 'Firmado'),
    ], string='Estado acta', readonly=True)

    lista_id = fields.Many2one('amunet.lista.verificacion', string='Lista', readonly=True)
    lista_clave = fields.Char(string='Lista de verificación', readonly=True)
    lista_state = fields.Selection([
        ('borrador', 'Borrador'),
        ('firmado', 'Firmado'),
    ], string='Estado lista', readonly=True)

    informe_id = fields.Many2one('amunet.informe.auditoria', string='Informe', readonly=True)
    informe_clave = fields.Char(string='Informe', readonly=True)
    informe_state = fields.Selection([
        ('borrador', 'Borrador'),
        ('firmado', 'Firmado'),
    ], string='Estado informe', readonly=True)

    def init(self):
        drop_view_if_exists(self.env.cr, self._table)
        self.env.cr.execute("""
            CREATE OR REPLACE VIEW amunet_expediente_auditoria AS (
                SELECT
                    p.id                                                        AS id,
                    p.id                                                        AS plan_id,
                    p.clave                                                     AS plan_clave,
                    c.name                                                      AS convocatoria,
                    p.fecha_inicio                                              AS fecha_inicio,
                    p.lider_id                                                  AS lider_id,
                    p.state                                                     AS plan_state,
                    (SELECT id    FROM amunet_acta_auditoria
                     WHERE plan_id = p.id ORDER BY id LIMIT 1)                 AS acta_id,
                    (SELECT clave FROM amunet_acta_auditoria
                     WHERE plan_id = p.id ORDER BY id LIMIT 1)                 AS acta_clave,
                    (SELECT state FROM amunet_acta_auditoria
                     WHERE plan_id = p.id ORDER BY id LIMIT 1)                 AS acta_state,
                    (SELECT id    FROM amunet_lista_verificacion
                     WHERE plan_id = p.id ORDER BY id LIMIT 1)                 AS lista_id,
                    (SELECT clave FROM amunet_lista_verificacion
                     WHERE plan_id = p.id ORDER BY id LIMIT 1)                 AS lista_clave,
                    (SELECT state FROM amunet_lista_verificacion
                     WHERE plan_id = p.id ORDER BY id LIMIT 1)                 AS lista_state,
                    (SELECT id    FROM amunet_informe_auditoria
                     WHERE plan_id = p.id ORDER BY id LIMIT 1)                 AS informe_id,
                    (SELECT clave FROM amunet_informe_auditoria
                     WHERE plan_id = p.id ORDER BY id LIMIT 1)                 AS informe_clave,
                    (SELECT state FROM amunet_informe_auditoria
                     WHERE plan_id = p.id ORDER BY id LIMIT 1)                 AS informe_state
                FROM amunet_plan_auditoria p
                LEFT JOIN amunet_auditor_convocatoria c ON c.id = p.convocatoria_id
            )
        """)
