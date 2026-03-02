# -*- coding: utf-8 -*-
import logging
from odoo import models, fields, api
from odoo.exceptions import UserError

_logger = logging.getLogger(__name__)


class AmunetAuditoriaHallazgo(models.Model):
    """
    Hallazgo / No Conformidad levantado durante una auditoría.
    Contiene el botón 'Crear CAPA' para generar automáticamente
    una Acción Correctiva/Preventiva en amunet_quality.

    ISO 13485:2016 §8.5.2 (CAPA) / §8.2.4 (Auditoría)
    """
    _name = 'amunet.auditoria.hallazgo'
    _description = 'Hallazgo / No Conformidad de Auditoría'
    _inherit = ['mail.thread']
    _order = 'severidad desc, id asc'

    # =========================================================================
    # IDENTIFICACIÓN
    # =========================================================================

    name = fields.Char(
        string='Referencia',
        readonly=True,
        copy=False,
        default='Nuevo',
        help='Número de serie (HALL-XXXX)'
    )

    auditoria_id = fields.Many2one(
        'amunet.auditoria',
        string='Auditoría',
        required=True,
        ondelete='cascade',
        index=True
    )

    # =========================================================================
    # DESCRIPCIÓN DEL HALLAZGO
    # =========================================================================

    titulo = fields.Char(
        string='Descripción del Hallazgo',
        required=True,
        tracking=True
    )

    severidad = fields.Selection([
        ('observacion', '💬 Observación'),
        ('nc_menor', '⚠️ NC Menor'),
        ('nc_mayor', '🔴 NC Mayor'),
        ('critica', '☠️ Crítica (Seguridad del Paciente)'),
    ], string='Severidad', required=True, default='nc_menor', tracking=True)

    clausula_incumplida = fields.Char(
        string='Cláusula Incumplida',
        help='Ej: ISO 13485:2016 §7.4.3'
    )

    evidencia_objetiva = fields.Text(
        string='Evidencia Objetiva',
        help='Descripción de la evidencia que soporta el hallazgo'
    )

    accion_inmediata = fields.Text(
        string='Acción Inmediata Tomada',
        help='Contención o acción correctiva inmediata realizada durante la auditoría'
    )

    fecha_limite = fields.Date(
        string='Fecha Límite de Corrección',
        tracking=True
    )

    responsable_id = fields.Many2one(
        'res.users',
        string='Responsable de Corrección',
        tracking=True
    )

    # =========================================================================
    # VÍNCULO CON CAPA (el "cruce de auditoría")
    # =========================================================================

    capa_id = fields.Many2one(
        'amunet.quality.capa',
        string='CAPA Generada',
        readonly=True,
        tracking=True,
        help='CAPA generada automáticamente desde este hallazgo'
    )

    capa_state = fields.Selection(
        related='capa_id.state',
        string='Estado CAPA',
        store=True,
        help='Estado actual de la CAPA (se actualiza en tiempo real)'
    )

    estado_hallazgo = fields.Selection([
        ('abierto', '🔴 Abierto'),
        ('capa_creada', '🟡 CAPA Creada'),
        ('cerrado', '✅ Cerrado'),
    ], string='Estado del Hallazgo', default='abierto', tracking=True)

    # =========================================================================
    # MÉTODO CRÍTICO: Crear CAPA
    # =========================================================================

    def action_crear_capa(self):
        """
        Genera automáticamente un amunet.quality.capa vinculado a este hallazgo.

        - Bloquea si ya existe un CAPA para este hallazgo.
        - Mapea la severidad del hallazgo a la del CAPA.
        - Añade trazabilidad completa: source_audit_id, source_hallazgo_id, audit_partner_id.
        - Registra el evento en el Audit Log (21 CFR Part 11).
        - Redirige al form del CAPA recién creado.
        """
        self.ensure_one()

        if self.capa_id:
            raise UserError(
                f"Este hallazgo ya tiene un CAPA asociado: {self.capa_id.name}.\n"
                "No se permite crear un segundo CAPA para el mismo hallazgo."
            )

        auditoria = self.auditoria_id

        # Obtener producto de referencia (se puede dejar vacío y completar en CAPA)
        # Para auditorías a proveedor, intentamos buscar el primer producto del proveedor
        product_id = self._get_default_product(auditoria)

        capa_vals = {
            'title': f"[{auditoria.name}] {self.titulo}",
            'severity': self._mapear_severidad(),
            'product_id': product_id,
            # Trazabilidad de auditoría (campos añadidos por _inherit en amunet_quality_capa_ext)
            'source_audit_id': auditoria.id,
            'source_hallazgo_id': self.id,
            'audit_partner_id': auditoria.partner_id.id if auditoria.partner_id else False,
        }

        new_capa = self.env['amunet.quality.capa'].create(capa_vals)

        # Actualizar el hallazgo
        self.write({
            'capa_id': new_capa.id,
            'estado_hallazgo': 'capa_creada',
        })

        # Registrar en Audit Log (21 CFR Part 11 / ISO 13485)
        self.env['amunet.quality.audit.log'].sudo().create({
            'model_name': 'amunet.auditoria.hallazgo',
            'res_id': self.id,
            'res_name': self.name,
            'field_name': 'capa_id',
            'old_value': 'Sin CAPA',
            'new_value': new_capa.name,
            'justification': (
                f"CAPA generada desde hallazgo de auditoría {auditoria.name}. "
                f"Proveedor: {auditoria.partner_id.name if auditoria.partner_id else 'N/A'}. "
                f"Severidad: {dict(self._fields['severidad'].selection).get(self.severidad, self.severidad)}"
            ),
            'user_id': self.env.user.id,
        })

        _logger.info(
            "CAPA '%s' creada desde hallazgo '%s' de auditoría '%s' por usuario '%s'.",
            new_capa.name, self.name, auditoria.name, self.env.user.name
        )

        # Abrir el CAPA recién creado para completar la investigación 8D
        return {
            'type': 'ir.actions.act_window',
            'res_model': 'amunet.quality.capa',
            'res_id': new_capa.id,
            'view_mode': 'form',
            'target': 'current',
        }

    def action_cerrar_hallazgo(self):
        """Permite cerrar un hallazgo manualmente una vez atendido."""
        for rec in self:
            if rec.severidad in ('nc_mayor', 'critica') and not rec.capa_id:
                raise UserError(
                    f"El hallazgo '{rec.name}' es de severidad Mayor/Crítica y "
                    "requiere un CAPA antes de cerrar."
                )
            rec.estado_hallazgo = 'cerrado'

    # =========================================================================
    # HELPERS PRIVADOS
    # =========================================================================

    def _mapear_severidad(self):
        """Mapea la severidad del hallazgo a la del modelo amunet.quality.capa."""
        mapa = {
            'observacion': 'low',
            'nc_menor': 'low',
            'nc_mayor': 'medium',
            'critica': 'critical',
        }
        return mapa.get(self.severidad, 'medium')

    def _get_default_product(self, auditoria):
        """
        Intenta obtener un producto de referencia para el CAPA.
        Si no hay proveedor o no tiene productos, retorna False
        (el usuario podrá seleccionarlo en el form del CAPA).
        """
        if auditoria.partner_id:
            # Buscar el primer producto de compra asociado a este proveedor
            seller = self.env['product.supplierinfo'].search(
                [('partner_id', '=', auditoria.partner_id.id)], limit=1
            )
            if seller and seller.product_id:
                return seller.product_id.id
            if seller and seller.product_tmpl_id:
                product = seller.product_tmpl_id.product_variant_ids[:1]
                if product:
                    return product.id
        return False

    # =========================================================================
    # CRUD
    # =========================================================================

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if vals.get('name', 'Nuevo') == 'Nuevo':
                vals['name'] = (
                    self.env['ir.sequence'].next_by_code('amunet.auditoria.hallazgo')
                    or 'HALL-000'
                )
        return super().create(vals_list)
