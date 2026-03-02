# -*- coding: utf-8 -*-
import logging
from odoo import models, fields, api
from odoo.exceptions import ValidationError

_logger = logging.getLogger(__name__)


class AmunetAuditoria(models.Model):
    """
    Programa de Auditorías — Encabezado.
    Soporta auditorías internas (a departamentos) y externas (a proveedores).

    ISO 13485:2016 §8.2.4 (Auditoría Interna) y §7.4 (Control de Proveedores).
    """
    _name = 'amunet.auditoria'
    _description = 'Auditoría (Interna / Proveedores)'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'fecha_planeada desc'

    # =========================================================================
    # IDENTIFICACIÓN
    # =========================================================================

    name = fields.Char(
        string='Referencia',
        readonly=True,
        copy=False,
        default='Nuevo',
        help='Número de serie (AUD-XXXX)'
    )

    tipo = fields.Selection([
        ('interna', '🏢 Interna (Departamento)'),
        ('proveedores', '🏭 Externa (Proveedor)'),
    ], string='Tipo de Auditoría', required=True, tracking=True)

    state = fields.Selection([
        ('planificada', 'Planificada'),
        ('en_ejecucion', 'En Ejecución'),
        ('con_hallazgos', 'Con Hallazgos Pendientes'),
        ('cerrada', 'Cerrada'),
        ('cancelada', 'Cancelada'),
    ], string='Estado', default='planificada', required=True, tracking=True)

    # =========================================================================
    # FECHAS Y EQUIPO AUDITOR
    # =========================================================================

    fecha_planeada = fields.Date(
        string='Fecha Planeada',
        required=True,
        tracking=True
    )

    fecha_ejecucion = fields.Date(
        string='Fecha de Ejecución Real',
        tracking=True
    )

    auditor_lider_id = fields.Many2one(
        'res.users',
        string='Auditor Líder',
        required=True,
        default=lambda self: self.env.user,
        tracking=True
    )

    co_auditores_ids = fields.Many2many(
        'res.users',
        'amunet_auditoria_coauditores_rel',
        'auditoria_id', 'user_id',
        string='Co-Auditores'
    )

    # =========================================================================
    # ALCANCE (varía según tipo)
    # =========================================================================

    norma_referencia = fields.Char(
        string='Norma / Cláusula',
        help='Ej: ISO 13485:2016 §8.2.4',
        tracking=True
    )

    alcance = fields.Text(
        string='Alcance de la Auditoría',
        help='Descripción de los procesos, áreas o requisitos evaluados'
    )

    # Auditorías Internas
    department_id = fields.Many2one(
        'hr.department',
        string='Departamento Auditado',
        help='Solo para auditorías internas'
    )

    # Auditorías a Proveedores (ISO 13485 §7.4)
    partner_id = fields.Many2one(
        'res.partner',
        string='Proveedor Auditado',
        domain=[('supplier_rank', '>', 0)],
        tracking=True,
        help='Solo para auditorías a proveedores'
    )

    # =========================================================================
    # RESULTADO
    # =========================================================================

    resultado_global = fields.Selection([
        ('conforme', '✅ Conforme'),
        ('conforme_con_obs', '⚠️ Conforme con Observaciones'),
        ('no_conforme', '🔴 No Conforme'),
        ('pendiente', '⏳ Pendiente'),
    ], string='Resultado Global', default='pendiente', tracking=True)

    conclusion = fields.Html(
        string='Conclusión / Informe Narrativo',
        help='Resumen ejecutivo de la auditoría'
    )

    report_file = fields.Binary(string='Informe de Auditoría (PDF)', attachment=True)
    report_filename = fields.Char(string='Nombre archivo informe')

    # =========================================================================
    # RELACIONES
    # =========================================================================

    checklist_ids = fields.One2many(
        'amunet.auditoria.checklist',
        'auditoria_id',
        string='Checklist de Evaluación'
    )

    hallazgo_ids = fields.One2many(
        'amunet.auditoria.hallazgo',
        'auditoria_id',
        string='Hallazgos / No Conformidades'
    )

    # =========================================================================
    # CONTADORES (para smart buttons)
    # =========================================================================

    hallazgo_count = fields.Integer(
        string='Hallazgos',
        compute='_compute_hallazgo_count',
        store=True
    )

    capa_count = fields.Integer(
        string='CAPAs Generadas',
        compute='_compute_capa_count'
    )

    checklist_count = fields.Integer(
        string='Ítems Checklist',
        compute='_compute_checklist_count',
        store=True
    )

    @api.depends('hallazgo_ids')
    def _compute_hallazgo_count(self):
        for rec in self:
            rec.hallazgo_count = len(rec.hallazgo_ids)

    @api.depends('hallazgo_ids.capa_id')
    def _compute_capa_count(self):
        for rec in self:
            rec.capa_count = len(rec.hallazgo_ids.filtered('capa_id').mapped('capa_id'))

    @api.depends('checklist_ids')
    def _compute_checklist_count(self):
        for rec in self:
            rec.checklist_count = len(rec.checklist_ids)

    # =========================================================================
    # ACCIONES DE ESTADO
    # =========================================================================

    def action_iniciar(self):
        self.ensure_one()
        self.write({
            'state': 'en_ejecucion',
            'fecha_ejecucion': fields.Date.today(),
        })

    def action_con_hallazgos(self):
        self.write({'state': 'con_hallazgos'})

    def action_cerrar(self):
        for rec in self:
            # Verificar que todos los hallazgos tengan CAPA si son NC mayor o crítica
            hallazgos_sin_capa = rec.hallazgo_ids.filtered(
                lambda h: h.severidad in ('nc_mayor', 'critica') and not h.capa_id
            )
            if hallazgos_sin_capa:
                nombres = ', '.join(hallazgos_sin_capa.mapped('name'))
                raise ValidationError(
                    f"No se puede cerrar la auditoría. Los siguientes hallazgos de severidad "
                    f"Mayor/Crítica aún no tienen una CAPA generada:\n\n{nombres}\n\n"
                    "Genere los CAPAs correspondientes antes de cerrar."
                )
            rec._actualizar_estatus_proveedor()
            rec.state = 'cerrada'

    def action_cancelar(self):
        self.write({'state': 'cancelada'})

    def _actualizar_estatus_proveedor(self):
        """Actualiza el campo quality_status en res.partner según el resultado de la auditoría."""
        if self.tipo != 'proveedores' or not self.partner_id:
            return

        mapa = {
            'conforme': 'approved',
            'conforme_con_obs': 'conditional',
            'no_conforme': 'rejected',
        }
        nuevo_estatus = mapa.get(self.resultado_global)
        if nuevo_estatus and hasattr(self.partner_id, 'quality_status'):
            self.partner_id.write({
                'quality_status': nuevo_estatus,
                'last_audit_date': self.fecha_ejecucion or fields.Date.today(),
            })

    # =========================================================================
    # ACCIONES DE VISTA (smart buttons)
    # =========================================================================

    def action_ver_hallazgos(self):
        self.ensure_one()
        return {
            'name': 'Hallazgos',
            'type': 'ir.actions.act_window',
            'res_model': 'amunet.auditoria.hallazgo',
            'view_mode': 'list,form',
            'domain': [('auditoria_id', '=', self.id)],
            'context': {'default_auditoria_id': self.id},
        }

    def action_ver_capas(self):
        self.ensure_one()
        capa_ids = self.hallazgo_ids.filtered('capa_id').mapped('capa_id').ids
        return {
            'name': 'CAPAs Generadas',
            'type': 'ir.actions.act_window',
            'res_model': 'amunet.quality.capa',
            'view_mode': 'list,form',
            'domain': [('id', 'in', capa_ids)],
        }

    # =========================================================================
    # CRUD
    # =========================================================================

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if vals.get('name', 'Nuevo') == 'Nuevo':
                vals['name'] = (
                    self.env['ir.sequence'].next_by_code('amunet.auditoria')
                    or 'AUD-000'
                )
        return super().create(vals_list)

    @api.constrains('tipo', 'partner_id', 'department_id')
    def _check_scope(self):
        for rec in self:
            if rec.tipo == 'proveedores' and not rec.partner_id:
                raise ValidationError(
                    "Las auditorías a Proveedores requieren seleccionar un Proveedor."
                )
            if rec.tipo == 'interna' and not rec.department_id:
                raise ValidationError(
                    "Las auditorías Internas requieren seleccionar un Departamento."
                )
