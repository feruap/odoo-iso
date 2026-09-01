# -*- coding: utf-8 -*-
from odoo import api, fields, models, _


class AmunetAuditoriaProveedor(models.Model):
    _name = 'amunet.auditoria.proveedor'
    _description = 'Informe de Auditoría de Proveedor'
    _order = 'fecha_emision desc, name'
    _inherit = ['mail.thread', 'mail.activity.mixin']

    name = fields.Char(string='No. Auditoría', readonly=True, copy=False, default='Nuevo')
    fecha_emision = fields.Date(string='Fecha de emisión', default=fields.Date.today, tracking=True)
    norma = fields.Char(string='Norma por aplicar')
    tipo = fields.Selection([
        ('interna', 'Interna'),
        ('externa', 'Externa'),
        ('seguimiento', 'De seguimiento'),
        ('especial', 'Especial'),
    ], string='Tipo de auditoría', required=True, default='externa', tracking=True)
    proveedor_id = fields.Many2one(
        'res.partner', string='Empresa por auditar',
        domain=[('supplier_rank', '>', 0)], required=True, tracking=True)
    fecha_auditoria = fields.Date(string='Fecha de la auditoría')
    auditor_lider_id = fields.Many2one('res.users', string='Auditor Líder')
    auditores_internos_ids = fields.Many2many(
        'res.users', 'rel_auditoria_auditores_int', 'auditoria_id', 'user_id',
        string='Auditor(es) Interno(s)')
    nombre_atiende = fields.Char(string='Nombre de quien atiende la visita')
    cargo_representante = fields.Char(string='Cargo del representante')
    departamento_auditado = fields.Char(string='Departamento / Área auditada')

    state = fields.Selection([
        ('borrador', 'Borrador'),
        ('en_revision', 'En revisión'),
        ('aprobado', 'Aprobado'),
        ('cerrado', 'Cerrado'),
    ], string='Estado', default='borrador', tracking=True)

    # Sección 2 — Objetivo
    objetivo = fields.Text(string='Objetivo de la auditoría')

    # Sección 3 — Alcance
    alcance = fields.Text(string='Alcance de la auditoría')

    # Sección 4 — Criterios
    criterio_iso9001 = fields.Boolean(string='ISO 9001:2015 (SGC)')
    criterio_iso14001 = fields.Boolean(string='ISO 14001:2015 (SGA)')
    criterio_iso45001 = fields.Boolean(string='ISO 45001:2018 (SST)')
    criterio_contractual = fields.Boolean(string='Requisitos contractuales del cliente')
    criterio_legislacion = fields.Char(string='Legislación aplicable (especificar)')
    criterio_politicas = fields.Char(string='Políticas internas (especificar)')
    criterio_otros = fields.Char(string='Otros criterios (especificar)')

    # Sección 5 — Metodología
    met_documentacion = fields.Text(string='Documentación revisada')
    met_entrevistas = fields.Text(string='Entrevistas realizadas')
    met_areas = fields.Text(string='Áreas / Procesos inspeccionados')
    met_muestras = fields.Text(string='Muestras tomadas')
    met_herramientas = fields.Text(string='Herramientas utilizadas')

    # Sección 6 — Resumen ejecutivo
    hallazgo_ids = fields.One2many('amunet.auditoria.prov.hallazgo', 'auditoria_id', string='Hallazgos')
    ncm_count = fields.Integer(string='NCM', compute='_compute_contadores', store=True)
    ncme_count = fields.Integer(string='NCMe', compute='_compute_contadores', store=True)
    op_count = fields.Integer(string='Observaciones (OP)', compute='_compute_contadores', store=True)
    om_count = fields.Integer(string='OM', compute='_compute_contadores', store=True)
    fortalezas_count = fields.Integer(string='Fortalezas', compute='_compute_contadores', store=True)
    total_hallazgos = fields.Integer(string='Total hallazgos', compute='_compute_contadores', store=True)
    fortalezas_resumen = fields.Text(string='Fortalezas identificadas (resumen)')
    calificacion_final = fields.Selection([
        ('aprobado', 'Aprobado'),
        ('condiciones', 'Aprobado con condiciones'),
        ('no_aprobado', 'No aprobado'),
    ], string='Calificación final', tracking=True)

    # Sección 7 — Observaciones generales
    observaciones_generales = fields.Text(string='Observaciones generales')

    # Sección 9 — Análisis por proceso (opcional)
    analisis_ids = fields.One2many(
        'amunet.auditoria.prov.analisis', 'auditoria_id', string='Análisis por proceso / área')

    # Sección 10 — Conclusiones
    conclusion_general = fields.Text(string='Conclusión general')
    recomendaciones = fields.Text(string='Recomendaciones')
    riesgos_identificados = fields.Text(string='Riesgos identificados')

    # Sección 11 — Plan de acción correctiva
    accion_ids = fields.One2many(
        'amunet.auditoria.prov.accion', 'auditoria_id', string='Acciones correctivas')

    # Sección 12 — Seguimiento y cierre
    fecha_seguimiento_1 = fields.Date(string='Fecha de seguimiento 1')
    resultado_seguimiento_1 = fields.Text(string='Resultados seguimiento 1')
    fecha_seguimiento_2 = fields.Date(string='Fecha de seguimiento 2')
    resultado_seguimiento_2 = fields.Text(string='Resultados seguimiento 2')
    fecha_cierre = fields.Date(string='Fecha de cierre')
    auditoria_cerrada = fields.Boolean(string='Auditoría cerrada')

    # Sección 13 — Firmas
    firma_nombre_lider = fields.Char(string='Nombre')
    firma_fecha_lider = fields.Date(string='Fecha')
    firma_nombre_auditores = fields.Char(string='Nombre')
    firma_fecha_auditores = fields.Date(string='Fecha')
    firma_nombre_representante = fields.Char(string='Nombre')
    firma_fecha_representante = fields.Date(string='Fecha')
    firma_nombre_gerente = fields.Char(string='Nombre')
    firma_fecha_gerente = fields.Date(string='Fecha')

    # Sección 14 — Anexos
    anexo_checklist = fields.Boolean(string='Lista de verificación (checklist) utilizada')
    anexo_fotos = fields.Boolean(string='Evidencias fotográficas')
    anexo_entrevistas = fields.Boolean(string='Registros de entrevistas')
    anexo_documentacion = fields.Boolean(string='Documentación de respaldo')
    anexo_otros = fields.Char(string='Otros anexos (especificar)')

    @api.depends('hallazgo_ids.tipo')
    def _compute_contadores(self):
        for r in self:
            tipos = r.hallazgo_ids.mapped('tipo')
            r.ncm_count = tipos.count('ncm')
            r.ncme_count = tipos.count('ncme')
            r.op_count = tipos.count('op')
            r.om_count = tipos.count('om')
            r.fortalezas_count = tipos.count('fortaleza')
            r.total_hallazgos = len(r.hallazgo_ids)

    def action_enviar_revision(self):
        self.write({'state': 'en_revision'})

    def action_aprobar(self):
        for r in self:
            r.write({'state': 'aprobado'})
            if r.proveedor_id and r.fecha_auditoria and hasattr(r.proveedor_id, 'last_audit_date'):
                r.proveedor_id.write({'last_audit_date': r.fecha_auditoria})

    def action_cerrar(self):
        self.write({
            'state': 'cerrado',
            'auditoria_cerrada': True,
            'fecha_cierre': fields.Date.today(),
        })

    def action_volver_borrador(self):
        self.write({'state': 'borrador'})

    def action_report_auditoria_proveedor(self):
        return self.env.ref(
            'amunet_proveedores.action_report_auditoria_proveedor'
        ).report_action(self)

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if vals.get('name', 'Nuevo') == 'Nuevo':
                vals['name'] = (
                    self.env['ir.sequence'].next_by_code('amunet.auditoria.proveedor') or 'Nuevo'
                )
        return super().create(vals_list)


class AmunetAuditoriaProvHallazgo(models.Model):
    _name = 'amunet.auditoria.prov.hallazgo'
    _description = 'Hallazgo de Auditoría de Proveedor'
    _order = 'tipo, id'

    auditoria_id = fields.Many2one(
        'amunet.auditoria.proveedor', string='Auditoría',
        ondelete='cascade', required=True, index=True)
    tipo = fields.Selection([
        ('ncm', 'No Conformidad Mayor (NCM)'),
        ('ncme', 'No Conformidad Menor (NCMe)'),
        ('op', 'Observación (OP)'),
        ('om', 'Oportunidad de Mejora (OM)'),
        ('fortaleza', 'Fortaleza'),
    ], string='Tipo', required=True, default='ncme')
    proceso_area = fields.Char(string='Proceso / Área')
    requisito_incumplido = fields.Char(string='Requisito incumplido')
    evidencia = fields.Text(string='Evidencia')
    impacto = fields.Text(string='Impacto')
    plazo_dias = fields.Integer(string='Plazo (días)')
    descripcion = fields.Text(string='Descripción')
    beneficio_esperado = fields.Text(string='Beneficio esperado')


class AmunetAuditoriaProvAccion(models.Model):
    _name = 'amunet.auditoria.prov.accion'
    _description = 'Acción Correctiva de Auditoría de Proveedor'
    _order = 'id'

    auditoria_id = fields.Many2one(
        'amunet.auditoria.proveedor', string='Auditoría',
        ondelete='cascade', required=True)
    hallazgo_ref = fields.Char(string='N° Hallazgo')
    accion_propuesta = fields.Text(string='Acción Correctiva Propuesta')
    responsable = fields.Char(string='Responsable')
    fecha_inicio = fields.Date(string='Fecha inicio')
    fecha_fin = fields.Date(string='Fecha fin')
    estado = fields.Selection([
        ('pendiente', 'Pendiente'),
        ('en_proceso', 'En proceso'),
        ('completado', 'Completado'),
    ], string='Estado', default='pendiente')


class AmunetAuditoriaProvAnalisis(models.Model):
    _name = 'amunet.auditoria.prov.analisis'
    _description = 'Análisis por Proceso — Auditoría de Proveedor'
    _order = 'id'

    auditoria_id = fields.Many2one(
        'amunet.auditoria.proveedor', string='Auditoría',
        ondelete='cascade', required=True)
    proceso_area = fields.Char(string='Proceso / Área')
    cumplimiento = fields.Float(string='Cumplimiento (%)', digits=(5, 1))
    observaciones = fields.Text(string='Observaciones')
