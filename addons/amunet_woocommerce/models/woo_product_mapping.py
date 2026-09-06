# -*- coding: utf-8 -*-

import base64
import json
import logging
import re
from urllib.parse import unquote, quote

import requests

from odoo import api, fields, models, _
from odoo.exceptions import AccessError, UserError, ValidationError
from odoo.tools.float_utils import float_round

_logger = logging.getLogger(__name__)

# Campos que el grupo Revisor puede editar manualmente (relación/confirmación).
# Todo lo demás del mapeo solo lo escribe el Administrador (importación/sistema).
REVIEWER_ALLOWED_FIELDS = {
    'product_id', 'relation_state', 'confidence', 'match_method',
    'review_notes', 'supply_classification', 'woo_name', 'woo_image',
    'odoo_name_edit',
}

# Captura de INVENTARIO INICIAL: la hace el almacen, no el administrador
# de la integracion. Son campos de captura, no del vinculo Woo-Odoo, asi
# que no llevan sello de revision.
INICIAL_CAPTURE_FIELDS = {
    'inicial_qty', 'inicial_lot_id', 'inicial_lot_name',
    'inicial_expiration_date', 'inicial_nota',
}

SNAPSHOT_MAX_AGE_PARAM = 'amunet_woocommerce.snapshot_max_age_days'
SNAPSHOT_MAX_AGE_DEFAULT = 7


class AmunetWooProductMapping(models.Model):
    """Mapeo auditable entre un artículo WooCommerce y un producto Odoo.

    Modelo central de la pantalla de consulta y validación. Todos los cálculos
    son de solo lectura y cada resultado trae su bandera ``*_calculable`` con
    la razón cuando no puede obtenerse ("dato ausente" nunca se convierte en
    cero).
    """

    _name = 'amunet.woo.product.mapping'
    _description = 'Mapeo y consulta producto Odoo - WooCommerce'
    _inherit = ['mail.thread']
    _order = 'woo_sku, id'
    _rec_name = 'woo_sku'

    active = fields.Boolean(default=True)
    company_id = fields.Many2one(
        'res.company', string='Compañía', required=True,
        default=lambda self: self.env.company, index=True)
    backend_id = fields.Many2one(
        'amunet.woo.backend', string='Tienda', required=True,
        ondelete='restrict', index=True)

    # --------------------------------------------------------------
    # Producto Woo
    # --------------------------------------------------------------
    woo_product_id = fields.Integer(string='ID Woo', required=True, index=True)
    woo_parent_id = fields.Integer(
        string='ID padre Woo', default=0,
        help='0 para producto simple; ID del producto variable para variaciones.')
    woo_sku = fields.Char(string='SKU Woo', index=True)
    woo_name = fields.Char(string='Nombre en Woo')
    woo_type = fields.Char(string='Tipo Woo')
    woo_status = fields.Char(string='Estado Woo', default='unknown')
    woo_image_url = fields.Char(string='URL fotografía Woo')
    woo_image = fields.Image(
        string='Fotografía Woo / fotografía propuesta',
        help='Descárgala desde Woo o súbela aquí para transferirla a Odoo o Woo.')
    snapshot_ids = fields.One2many(
        'amunet.woo.stock.snapshot', 'mapping_id', string='Snapshots Woo')

    # --------------------------------------------------------------
    # Producto Odoo
    # --------------------------------------------------------------
    product_id = fields.Many2one(
        'product.product', string='Producto Odoo', index=True,
        help='Puede quedar vacío mientras una persona revisa el vínculo.')
    default_code = fields.Char(
        string='SKU Odoo', related='product_id.default_code', store=True)
    product_name = fields.Char(
        string='Nombre Odoo (consulta)', related='product_id.name', store=False)
    product_image_128 = fields.Image(
        string='Fotografía Odoo', related='product_id.image_128')
    odoo_name_edit = fields.Char(
        string='Nombre Odoo', compute='_compute_odoo_name_edit',
        inverse='_inverse_odoo_name_edit',
        help='Editar aquí cambia el nombre del producto Odoo vinculado y deja '
             'registro en la bitácora del mapeo.')

    # --------------------------------------------------------------
    # Estado de la relación (auditable, editable por Revisor)
    # --------------------------------------------------------------
    relation_state = fields.Selection([
        ('pending', 'Pendiente'),
        ('confirmed', 'Confirmada'),
        ('rejected', 'Rechazada'),
    ], string='Estado de relación', default='pending', required=True,
        tracking=True, index=True)
    confidence = fields.Selection([
        ('high', 'Alta'),
        ('medium', 'Media'),
        ('low', 'Baja'),
        ('unknown', 'Desconocida'),
    ], string='Confianza', default='unknown', required=True, tracking=True)
    match_method = fields.Char(string='Método de emparejamiento', tracking=True)
    review_notes = fields.Text(string='Notas / justificación')
    reviewer_id = fields.Many2one(
        'res.users', string='Revisor', readonly=True, tracking=True)
    review_date = fields.Datetime(string='Fecha de revisión', readonly=True)

    # --------------------------------------------------------------
    # Tipo de Fabricación (antes "Clasificación de abastecimiento")
    # Se calcula solo: marcador de línea larga / BoM / compra-venta.
    # --------------------------------------------------------------
    supply_classification = fields.Selection([
        ('short_manufacturing', 'Fabricación corta'),
        ('long_manufacturing', 'Fabricación larga'),
        ('purchased_qc', 'Compra-venta'),
        ('other', 'Otro / no definido'),
    ], string='Tipo de Fabricación',
        compute='_compute_supply_classification', store=True, index=True)
    linea_larga = fields.Boolean(
        string='Línea larga',
        related='product_id.product_tmpl_id.amunet_linea_larga',
        readonly=False, store=True,
        groups='amunet_woocommerce.group_linea_larga_editor',
        help='Marcador manual de línea larga en el producto. Editable '
             'aquí para clasificar el Tipo de Fabricación mientras se '
             'ajustan las rutas de BoM de línea larga. Visible/editable '
             'solo para el grupo restringido (Mery).')

    # --------------------------------------------------------------
    # Inventario Woo (solo desde snapshot conocido)
    # --------------------------------------------------------------
    latest_snapshot_id = fields.Many2one(
        'amunet.woo.stock.snapshot', string='Último snapshot',
        compute='_compute_woo_inventory')
    last_snapshot_date = fields.Datetime(
        string='Fecha último snapshot', compute='_compute_woo_inventory')
    woo_qty_available = fields.Float(
        string='Woo disponible (valor)', compute='_compute_woo_inventory')
    woo_qty_reserved = fields.Float(
        string='Woo reservado (valor)', compute='_compute_woo_inventory')
    woo_qty_expired = fields.Float(
        string='Woo caducado (valor)', compute='_compute_woo_inventory')
    woo_qty_damaged = fields.Float(
        string='Woo dañado (valor)', compute='_compute_woo_inventory')
    woo_available_known = fields.Boolean(
        string='Woo disponible conocido', compute='_compute_woo_inventory')
    woo_reserved_known = fields.Boolean(
        string='Woo reservado conocido', compute='_compute_woo_inventory')
    woo_expired_known = fields.Boolean(
        string='Woo caducado conocido', compute='_compute_woo_inventory')
    woo_damaged_known = fields.Boolean(
        string='Woo dañado conocido', compute='_compute_woo_inventory')
    woo_available_display = fields.Char(
        string='Woo disponible', compute='_compute_woo_inventory')
    woo_reserved_display = fields.Char(
        string='Woo reservado', compute='_compute_woo_inventory')
    woo_expired_display = fields.Char(
        string='Woo caducado', compute='_compute_woo_inventory')
    woo_damaged_display = fields.Char(
        string='Woo dañado', compute='_compute_woo_inventory')
    woo_inventory_calculable = fields.Boolean(
        string='Inventario Woo calculable', compute='_compute_woo_inventory')
    woo_inventory_reason = fields.Char(
        string='Razón inventario Woo', compute='_compute_woo_inventory')
    snapshot_stale = fields.Boolean(
        string='Snapshot vencido', compute='_compute_woo_inventory',
        search='_search_snapshot_stale')

    # --------------------------------------------------------------
    # Inventario físico Odoo
    # --------------------------------------------------------------
    odoo_qty_onhand = fields.Float(
        string='Odoo físico interno (valor)',
        compute='_compute_odoo_inventory')
    odoo_qty_free = fields.Float(
        string='Odoo libre (valor)', compute='_compute_odoo_inventory')
    odoo_lot_released_qty = fields.Float(
        string='Odoo en lotes liberados (valor)',
        compute='_compute_odoo_inventory')
    odoo_lot_pending_qty = fields.Float(
        string='Odoo en lotes pendientes (valor)',
        compute='_compute_odoo_inventory')
    odoo_physical_calculable = fields.Boolean(
        string='Inventario físico Odoo calculable',
        compute='_compute_odoo_inventory')
    odoo_physical_reason = fields.Char(
        string='Razón inventario físico Odoo',
        compute='_compute_odoo_inventory')
    odoo_onhand_display = fields.Char(
        string='Odoo físico interno', compute='_compute_odoo_inventory')
    odoo_free_display = fields.Char(
        string='Odoo libre', compute='_compute_odoo_inventory')
    odoo_lot_released_display = fields.Char(
        string='Odoo en lotes liberados', compute='_compute_odoo_inventory')
    odoo_lot_pending_display = fields.Char(
        string='Odoo en lotes pendientes', compute='_compute_odoo_inventory')
    has_released_lots = fields.Boolean(
        string='Tiene lotes liberados', compute='_compute_odoo_inventory')
    lot_release_calculable = fields.Boolean(
        string='Liberación calculable', compute='_compute_odoo_inventory')
    lot_release_reason = fields.Char(
        string='Razón liberación', compute='_compute_odoo_inventory')

    # --------------------------------------------------------------
    # Existencias por etapa de producción (suma en todas las ubicaciones
    # internas cuyo nombre corresponde a esa etapa: APT, AMP, AMPB, ARU...)
    # --------------------------------------------------------------
    # Pipeline de produccion (piezas de producto terminado):
    # Preproduccion = capacidad ("para cuanto me alcanza") por cuello de
    #   botella del BoM, con stock LIBRE de insumos (incluye Entrada/Calidad).
    # En produccion = fabricado sin liberar (lote pendiente en APT/Temporal PT)
    #   + WIP de MO surtidas en proceso. Posproduccion = terminado LIBERADO en APT.
    stock_preproduccion = fields.Float(
        string='Preproducción (capacidad)', compute='_compute_produccion_pipeline')
    stock_en_produccion = fields.Float(
        string='En producción', compute='_compute_produccion_pipeline')
    stock_posproduccion = fields.Float(
        string='Posproducción', compute='_compute_produccion_pipeline')
    stock_control_calidad = fields.Float(
        string='Control de calidad', compute='_compute_produccion_pipeline')
    stock_existencias = fields.Float(
        string='Existencia total', compute='_compute_produccion_pipeline',
        help='Total del pipeline = Preproducción + En producción + '
             'Posproducción + Control de calidad.')
    stock_entrada = fields.Float(
        string='Entrada', compute='_compute_stage_stock')
    stock_salida = fields.Float(
        string='Salida', compute='_compute_stage_stock')
    stock_empaquetado = fields.Float(
        string='Zona de empaquetado', compute='_compute_stage_stock')

    # --------------------------------------------------------------
    # Configuración de calidad
    # --------------------------------------------------------------
    has_quality_manual = fields.Boolean(
        string='Tiene manual',
        compute='_compute_has_quality_manual',
        help='El producto tiene un manual APROBADO publicado en la carpeta '
             'de Nextcloud de Documentación (archivo CLAVE_Nombre.pdf cuya '
             'clave coincide con la clave del producto). Usa el botón '
             '"Actualizar manuales" para refrescar la lista desde Nextcloud.')
    manual_pdf_url = fields.Char(
        string='Manual (PDF)',
        compute='_compute_has_quality_manual',
        help='Enlace directo al PDF del manual en Nextcloud, si existe.')
    qc_required = fields.Boolean(
        string='Requiere QC', compute='_compute_quality')
    qc_parameter_count = fields.Integer(
        string='Parámetros de calidad', compute='_compute_quality')
    qc_check_count = fields.Integer(
        string='Controles de calidad', compute='_compute_quality')
    quality_calculable = fields.Boolean(
        string='Calidad calculable', compute='_compute_quality')
    quality_reason = fields.Char(
        string='Razón calidad', compute='_compute_quality')
    quality_status_display = fields.Char(
        string='Parámetros de calidad', compute='_compute_quality',
        help='"No requiere" = el producto no se analiza por calidad. '
             '"Falta configurar" = requiere QC pero no tiene parámetros. '
             'Un número = parámetros de calidad ya configurados.')

    # --------------------------------------------------------------
    # Órdenes MRP abiertas
    # --------------------------------------------------------------
    open_mo_count = fields.Integer(
        string='MO abiertas', compute='_compute_mrp')
    open_mo_qty = fields.Float(
        string='Cantidad en MO abiertas (valor)', compute='_compute_mrp')
    open_mo_summary = fields.Char(
        string='Detalle MO abiertas', compute='_compute_mrp')
    mrp_calculable = fields.Boolean(
        string='Órdenes MRP calculables', compute='_compute_mrp')
    mrp_reason = fields.Char(
        string='Razón órdenes MRP', compute='_compute_mrp')
    open_mo_qty_display = fields.Char(
        string='Cantidad en MO abiertas', compute='_compute_mrp')

    # --------------------------------------------------------------
    # BOM activa y fase de empaque
    # --------------------------------------------------------------
    active_bom_count = fields.Integer(
        string='BOM activas', compute='_compute_bom_info')
    has_active_bom = fields.Boolean(
        string='Tiene BOM activa', compute='_compute_bom_info',
        search='_search_has_active_bom')
    bom_status_display = fields.Char(
        string='Estado de BOM', compute='_compute_bom_info')
    bom_summary = fields.Text(
        string='Detalle de BOM activas', compute='_compute_bom_info')
    bom_required = fields.Boolean(
        string='Requiere BOM', compute='_compute_bom_info',
        search='_search_bom_required',
        help='Solo los productos que se manufacturan (categoria "Producto '
             'terminado") requieren BOM. Consumibles, equipos y semiterminados '
             'son de compra-venta y no llevan BOM.')
    packaging_plan_count = fields.Integer(
        string='Planes de empaque activos', compute='_compute_packaging_phase')
    packaging_planned_qty = fields.Float(
        string='Piezas planificadas en empaque (valor)',
        compute='_compute_packaging_phase')
    packaging_calculable = fields.Boolean(
        string='Fase de empaque calculable',
        compute='_compute_packaging_phase')
    packaging_reason = fields.Char(
        string='Razón fase de empaque', compute='_compute_packaging_phase')
    packaging_display = fields.Char(
        string='Piezas planificadas en empaque',
        compute='_compute_packaging_phase')
    packaging_summary = fields.Text(
        string='Detalle de empaque', compute='_compute_packaging_phase')

    # --------------------------------------------------------------
    # Presentaciones / cajas
    # --------------------------------------------------------------
    presentation_name = fields.Char(
        string='Presentación autorizada', compute='_compute_presentation')
    presentation_count = fields.Integer(
        string='Presentaciones autorizadas', compute='_compute_presentation')
    presentation_summary = fields.Text(
        string='Equivalencias autorizadas', compute='_compute_presentation')
    pieces_per_box = fields.Integer(
        string='Piezas por caja', compute='_compute_presentation')
    pieces_per_box_source = fields.Char(
        string='Fuente piezas por caja', compute='_compute_presentation')
    pieces_per_box_calculable = fields.Boolean(
        string='Piezas por caja calculable', compute='_compute_presentation')
    pieces_per_box_reason = fields.Char(
        string='Razón piezas por caja', compute='_compute_presentation')

    # --------------------------------------------------------------
    # Capacidad de fabricación corta
    # --------------------------------------------------------------
    short_capacity_qty = fields.Float(
        string='Capacidad fabricación corta (valor)',
        compute='_compute_short_capacity')
    short_capacity_calculable = fields.Boolean(
        string='Capacidad corta calculable', compute='_compute_short_capacity')
    short_capacity_reason = fields.Char(
        string='Razón capacidad corta', compute='_compute_short_capacity')
    short_capacity_display = fields.Char(
        string='Capacidad fabricación corta',
        compute='_compute_short_capacity')

    # --------------------------------------------------------------
    # Perfil y capacidad de fabricación larga
    # --------------------------------------------------------------
    long_process_id = fields.Many2one(
        'amunet.woo.long.process', string='Perfil de fabricación larga',
        compute='_compute_long_process')
    long_capacity_calculable = fields.Boolean(
        string='Capacidad larga calculable', compute='_compute_long_process')
    long_capacity_reason = fields.Char(
        string='Razón capacidad larga', compute='_compute_long_process')
    long_capacity_display = fields.Char(
        string='Capacidad fabricación larga', compute='_compute_long_process')

    # --------------------------------------------------------------
    # Alertas
    # --------------------------------------------------------------
    alert_text = fields.Text(string='Alertas', compute='_compute_alerts')
    has_alerts = fields.Boolean(
        string='Con alertas', compute='_compute_alerts',
        search='_search_has_alerts')
    any_not_calculable = fields.Boolean(
        string='Con datos no calculables', compute='_compute_alerts',
        search='_search_any_not_calculable')

    _uniq_backend_woo_item = models.Constraint(
        'unique(backend_id, woo_product_id, woo_parent_id)',
        'Este artículo de WooCommerce ya está mapeado en esta tienda.',
    )

    # --------------------------------------------------------------
    # Restricciones y guardas de escritura
    # --------------------------------------------------------------

    @api.constrains('backend_id', 'company_id', 'product_id')
    def _check_backend_company(self):
        for rec in self:
            if rec.backend_id and rec.backend_id.company_id != rec.company_id:
                raise UserError(_(
                    'La compañía del mapeo debe coincidir con la de la tienda %s.'
                ) % rec.backend_id.name)
            if rec.product_id.company_id \
                    and rec.product_id.company_id != rec.company_id:
                raise UserError(_(
                    'El producto Odoo pertenece a otra compañía.'))

    def write(self, vals):
        incoming = set(vals)
        if not self.env.su and not self.env.user.has_group(
                'amunet_woocommerce.group_woo_admin'):
            forbidden = incoming - REVIEWER_ALLOWED_FIELDS \
                - INICIAL_CAPTURE_FIELDS
            if forbidden:
                raise AccessError(_(
                    'Solo el grupo Administrador puede modificar estos campos '
                    'del mapeo: %s') % ', '.join(sorted(forbidden)))
        if not self.env.context.get('skip_review_stamp') \
                and incoming.intersection(REVIEWER_ALLOWED_FIELDS):
            vals = dict(vals)
            if 'product_id' in incoming and 'relation_state' not in incoming:
                vals['relation_state'] = 'pending'
            vals['reviewer_id'] = self.env.user.id
            vals['review_date'] = fields.Datetime.now()
        result = super().write(vals)
        if not self.env.context.get('skip_review_stamp') \
                and incoming.intersection(REVIEWER_ALLOWED_FIELDS):
            for rec in self:
                rec.message_post(body=_(
                    'Revisión del vínculo actualizada por %(user)s. '
                    'Estado: %(state)s. Producto Odoo: %(product)s.',
                    user=self.env.user.display_name,
                    state=dict(
                        rec._fields['relation_state'].selection
                    ).get(rec.relation_state, rec.relation_state),
                    product=rec.product_id.display_name
                    if rec.product_id else _('Sin vincular'),
                ))
        return result

    @api.depends('product_id.name')
    def _compute_odoo_name_edit(self):
        for rec in self:
            rec.odoo_name_edit = rec.product_id.name if rec.product_id else False

    def _inverse_odoo_name_edit(self):
        for rec in self:
            if not rec.odoo_name_edit:
                raise UserError(_('El nombre Odoo no puede quedar vacío.'))
            if not rec.product_id:
                raise UserError(_('Primero selecciona un producto Odoo para editar su nombre.'))
            previous_name = rec.product_id.name
            if previous_name != rec.odoo_name_edit:
                rec.product_id.sudo().write({'name': rec.odoo_name_edit})
                rec.message_post(body=_(
                    'Nombre del producto Odoo actualizado por %(user)s: '
                    '"%(old)s" → "%(new)s".',
                    user=self.env.user.display_name,
                    old=previous_name, new=rec.odoo_name_edit))

    def _require_reviewer(self):
        if not self.env.user.has_group('amunet_woocommerce.group_woo_revisor') \
                and not self.env.user.has_group('amunet_woocommerce.group_woo_admin'):
            raise AccessError(_('Solo un revisor o administrador puede transferir datos.'))

    def _woo_endpoint(self):
        self.ensure_one()
        if self.woo_parent_id:
            return 'products/%s/variations/%s' % (self.woo_parent_id, self.woo_product_id)
        return 'products/%s' % self.woo_product_id

    def action_download_woo_image(self):
        """Descarga la foto registrada en Woo sin escribir fuera de Odoo."""
        self.ensure_one()
        self._require_reviewer()
        if not self.woo_image_url:
            raise UserError(_('Este producto Woo no tiene una URL de fotografía.'))
        try:
            response = requests.get(self.woo_image_url, timeout=30, verify=True)
            response.raise_for_status()
        except requests.RequestException as exc:
            raise UserError(_('No se pudo descargar la fotografía Woo: %s') % exc)
        content_type = response.headers.get('Content-Type', '')
        if not content_type.startswith('image/'):
            raise UserError(_('La URL Woo no devolvió una imagen válida.'))
        if len(response.content) > 10 * 1024 * 1024:
            raise UserError(_('La fotografía Woo excede el límite de 10 MB.'))
        self.write({'woo_image': base64.b64encode(response.content)})
        self.message_post(body=_(
            'Fotografía descargada desde Woo por %(user)s; queda lista para revisión o transferencia.',
            user=self.env.user.display_name))
        return True

    def action_copy_woo_image_to_odoo(self):
        self.ensure_one()
        self._require_reviewer()
        if not self.product_id:
            raise UserError(_('Primero selecciona el producto Odoo destino.'))
        if not self.woo_image:
            self.action_download_woo_image()
        self.product_id.sudo().write({'image_1920': self.woo_image})
        self.message_post(body=_(
            'Fotografía Woo transferida al producto Odoo por %(user)s.',
            user=self.env.user.display_name))
        return True

    def action_push_woo_name(self):
        self.ensure_one()
        self._require_reviewer()
        if not self.woo_name:
            raise UserError(_('El nombre Woo no puede quedar vacío.'))
        self.backend_id._bridge_request(
            'POST', 'product/%s/name' % self.woo_product_id,
            {'name': self.woo_name})
        self.message_post(body=_(
            'Nombre publicado en WooCommerce por %(user)s: "%(name)s".',
            user=self.env.user.display_name, name=self.woo_name))
        return True

    def action_push_odoo_image_to_woo(self):
        self.ensure_one()
        self._require_reviewer()
        image = self.woo_image or (self.product_id and self.product_id.image_1920)
        if not image:
            raise UserError(_('No hay fotografía cargada en el mapeo ni en el producto Odoo.'))
        try:
            image_bytes = base64.b64decode(image)
        except (TypeError, ValueError) as exc:
            raise UserError(_('La fotografía Odoo no es válida: %s') % exc)
        filename = '%s-odoo.png' % (self.woo_sku or self.woo_product_id)
        result = self.backend_id._bridge_request(
            'POST', 'product/%s/image' % self.woo_product_id, {
                'filename': filename,
                'image_base64': base64.b64encode(image_bytes).decode('ascii'),
            })
        image_url = result.get('image_url')
        if not image_url:
            raise UserError(_('El puente Woo no devolvió la URL de la fotografía.'))
        self.sudo().with_context(skip_review_stamp=True).write({
            'woo_image_url': image_url,
            'woo_image': image,
        })
        self.message_post(body=_(
            'Fotografía Odoo publicada en WooCommerce por %(user)s.',
            user=self.env.user.display_name))
        return True

    def action_delete_woo_image(self):
        self.ensure_one()
        self._require_reviewer()
        self.backend_id._bridge_request(
            'DELETE', 'product/%s/image' % self.woo_product_id)
        self.sudo().with_context(skip_review_stamp=True).write({
            'woo_image_url': False,
            'woo_image': False,
        })
        self.message_post(body=_(
            'Fotografía eliminada de WooCommerce por %(user)s.',
            user=self.env.user.display_name))
        return True

    def action_delete_odoo_image(self):
        self.ensure_one()
        self._require_reviewer()
        if not self.product_id:
            raise UserError(_('Este mapeo no tiene un producto Odoo vinculado.'))
        self.product_id.sudo().write({'image_1920': False})
        self.message_post(body=_(
            'Fotografía eliminada del producto Odoo por %(user)s.',
            user=self.env.user.display_name))
        return True

    # --------------------------------------------------------------
    # Acciones de revisión (auditables)
    # --------------------------------------------------------------

    def _set_review_state(self, state):
        if state == 'confirmed' and any(not rec.product_id for rec in self):
            raise UserError(_(
                'No se puede confirmar una relación sin producto Odoo.'))
        self.write({'relation_state': state})

    def action_confirm(self):
        self._set_review_state('confirmed')
        return True

    def action_confirm_selected_product(self):
        """Confirma explícitamente el producto elegido por el revisor."""
        self.ensure_one()
        self._require_reviewer()
        if not self.product_id:
            raise UserError(_('Selecciona primero el producto Odoo correcto.'))
        self._set_review_state('confirmed')
        return True

    def action_reject(self):
        self._set_review_state('rejected')
        return True

    def action_reset_pending(self):
        self._set_review_state('pending')
        return True

    # --------------------------------------------------------------
    # Cálculos de solo lectura
    # --------------------------------------------------------------

    def _snapshot_max_age_days(self):
        value = self.env['ir.config_parameter'].sudo().get_param(
            SNAPSHOT_MAX_AGE_PARAM, SNAPSHOT_MAX_AGE_DEFAULT)
        try:
            return max(int(value), 1)
        except (TypeError, ValueError):
            return SNAPSHOT_MAX_AGE_DEFAULT

    def _compute_woo_inventory(self):
        max_age = self._snapshot_max_age_days()
        now = fields.Datetime.now()
        for rec in self:
            snapshot = rec.snapshot_ids.sorted('date', reverse=True)[:1]
            rec.latest_snapshot_id = snapshot
            rec.last_snapshot_date = snapshot.date if snapshot else False
            rec.woo_available_known = bool(
                snapshot and snapshot.available_known)
            rec.woo_reserved_known = bool(
                snapshot and snapshot.reserved_known)
            rec.woo_expired_known = bool(
                snapshot and snapshot.expired_known)
            rec.woo_damaged_known = bool(
                snapshot and snapshot.damaged_known)
            if not snapshot:
                rec.woo_qty_available = 0.0
                rec.woo_qty_reserved = 0.0
                rec.woo_qty_expired = 0.0
                rec.woo_qty_damaged = 0.0
                rec.woo_available_display = _('No calculable')
                rec.woo_reserved_display = _('No calculable')
                rec.woo_expired_display = _('No calculable')
                rec.woo_damaged_display = _('No calculable')
                rec.woo_inventory_calculable = False
                rec.woo_inventory_reason = _(
                    'No existe snapshot de inventario Woo conocido.')
                rec.snapshot_stale = False
                continue
            rec.woo_qty_available = snapshot.qty_available
            rec.woo_qty_reserved = snapshot.qty_reserved
            rec.woo_qty_expired = snapshot.qty_expired
            rec.woo_qty_damaged = snapshot.qty_damaged
            rec.woo_available_display = snapshot.available_display
            rec.woo_reserved_display = snapshot.reserved_display
            rec.woo_expired_display = snapshot.expired_display
            rec.woo_damaged_display = snapshot.damaged_display
            known = {
                _('disponible'): snapshot.available_known,
                _('reservado'): snapshot.reserved_known,
                _('caducado'): snapshot.expired_known,
                _('dañado'): snapshot.damaged_known,
            }
            missing = [label for label, is_known in known.items() if not is_known]
            rec.woo_inventory_calculable = not missing
            rec.woo_inventory_reason = (
                _('Categorías sin dato: %s.') % ', '.join(missing)
                if missing else False)
            rec.snapshot_stale = bool(
                snapshot.date and (now - snapshot.date).days > max_age)

    _STAGE_PATTERNS = [
        ('stock_entrada', ('Entrada',)),
        ('stock_salida', ('Salida',)),
        ('stock_empaquetado', ('Zona de empaquetado',)),
    ]

    def _compute_stage_stock(self):
        """Columnas informativas de existencia por ubicacion (Existencias,
        Control de calidad, Entrada, Salida, Zona de empaquetado): suma la
        existencia del producto agrupada por el nombre de la ubicacion."""
        Quant = self.env['stock.quant']
        for rec in self:
            for fname, _pats in self._STAGE_PATTERNS:
                rec[fname] = 0.0
            if not rec.product_id:
                continue
            try:
                quants = Quant.search([
                    ('product_id', '=', rec.product_id.id),
                    ('location_id.usage', '=', 'internal'),
                    ('company_id', '=', rec.company_id.id),
                ])
            except AccessError:
                continue
            for quant in quants:
                cname = quant.location_id.complete_name or ''
                for fname, pats in self._STAGE_PATTERNS:
                    if any(p in cname for p in pats):
                        rec[fname] += quant.quantity
                        break

    def _amunet_capacidad_preproduccion(self, product, company, apt_path):
        """Piezas fabricables ('para cuanto me alcanza') por cuello de botella
        del BoM, con stock LIBRE de cada insumo en el almacen ANTES de producto
        terminado (todo lo interno que NO es APT: AMP/AMPB/ARU, INCLUYENDO
        Entrada y Control de calidad; excluye Rechazo). Libre = onhand -
        reservado (lo ya surtido/reservado no cuenta). Teorico por producto."""
        bom = self._find_bom(product, company)
        if not bom or bom.type != 'normal' or not bom.bom_line_ids:
            return 0.0
        base = bom.product_qty or 1.0
        Quant = self.env['stock.quant']
        cap = None
        for line in bom.bom_line_ids:
            comp = line.product_id
            if not comp or line.product_qty <= 0:
                continue
            try:
                req = line.product_uom_id._compute_quantity(
                    line.product_qty, comp.uom_id, round=False) / base
            except UserError:
                return 0.0
            if req <= 0:
                continue
            try:
                cquants = Quant.search([
                    ('product_id', '=', comp.id),
                    ('location_id.usage', '=', 'internal'),
                    ('company_id', '=', company.id),
                ])
            except AccessError:
                return 0.0
            free = 0.0
            for q in cquants:
                cn = q.location_id.complete_name or ''
                if 'Rechazo' in cn:
                    continue
                is_apt = bool(apt_path and q.location_id.parent_path
                              and q.location_id.parent_path.startswith(apt_path))
                if is_apt:
                    continue
                free += max(q.quantity - q.reserved_quantity, 0.0)
            possible = free / req
            cap = possible if cap is None else min(cap, possible)
        return float(int(cap)) if cap is not None else 0.0

    def _compute_produccion_pipeline(self):
        """Pipeline en piezas de producto terminado:
        - Preproduccion = CAPACIDAD (cuello de botella del BoM, stock libre de
          insumos incl. Entrada/Calidad).
        - En produccion = producto FABRICADO sin liberar (en APT/Temporal PT
          con lote NO liberado) + WIP de MO surtidas en proceso (lo que falta
          producir). Sin rechazados.
        - Posproduccion = producto terminado LIBERADO por Calidad en APT.
        """
        Quant = self.env['stock.quant']
        MO = self.env['mrp.production'].sudo()
        has_release = 'amunet_lot_release_state' in self.env['stock.lot']._fields
        apt_wh = self.env['stock.warehouse'].sudo().search(
            [('code', '=', 'APT')], limit=1)
        apt_path = apt_wh.view_location_id.parent_path if apt_wh else False
        for rec in self:
            rec.stock_preproduccion = 0.0
            rec.stock_control_calidad = 0.0
            rec.stock_en_produccion = 0.0
            rec.stock_posproduccion = 0.0
            rec.stock_existencias = 0.0
            product = rec.product_id
            if not product:
                continue
            rec.stock_preproduccion = self._amunet_capacidad_preproduccion(
                product, rec.company_id, apt_path)
            # Producto terminado en APT: liberado (pos) vs sin liberar (en prod)
            try:
                pquants = Quant.search([
                    ('product_id', '=', product.id),
                    ('location_id.usage', '=', 'internal'),
                    ('company_id', '=', rec.company_id.id),
                ])
            except AccessError:
                pquants = Quant.browse()
            en_cc = 0.0           # Control de calidad: Almacen Temporal PT
            fabricado_pend = 0.0  # fabricado sin liberar fuera de Temporal PT
            liberado = 0.0
            for q in pquants:
                cname = q.location_id.complete_name or ''
                if 'Rechazo' in cname:
                    continue
                is_apt = bool(apt_path and q.location_id.parent_path
                              and q.location_id.parent_path.startswith(apt_path))
                if not is_apt:
                    continue
                if 'Temporal' in cname:
                    en_cc += q.quantity
                elif (has_release and q.lot_id
                        and q.lot_id.amunet_lot_release_state == 'released'):
                    liberado += q.quantity
                else:
                    fabricado_pend += q.quantity
            # WIP: MO surtidas en proceso, no rechazadas -> lo que falta producir
            wip = 0.0
            try:
                mos = MO.search([
                    ('product_id', '=', product.id),
                    ('state', 'in', ('confirmed', 'progress', 'to_close')),
                    ('company_id', '=', rec.company_id.id),
                ])
            except AccessError:
                mos = MO.browse()
            for mo in mos:
                if ('quality_analysis_status' in mo._fields
                        and mo.quality_analysis_status == 'rejected'):
                    continue
                # "surtido" = ya se surtio material (has_supplied_moves), NO
                # el flag has_surtido_components que significa "le FALTA surtir".
                if ('amunet_has_supplied_moves' in mo._fields
                        and not mo.amunet_has_supplied_moves):
                    continue
                wip += max((mo.product_qty or 0.0) - (mo.qty_produced or 0.0), 0.0)
            rec.stock_control_calidad = en_cc
            rec.stock_en_produccion = fabricado_pend + wip
            rec.stock_posproduccion = liberado
            # Existencia total = suma del pipeline (pre + en + pos + calidad).
            rec.stock_existencias = (rec.stock_preproduccion
                                     + rec.stock_en_produccion
                                     + rec.stock_posproduccion
                                     + rec.stock_control_calidad)

    # ------------------------------------------------------------------
    # Manual de calidad = PDF aprobado en la carpeta Nextcloud de Documentación
    # ------------------------------------------------------------------
    MANUAL_WEBDAV_URL_DEFAULT = 'https://next.amunet.com.mx/public.php/webdav/'
    MANUAL_TOKEN_DEFAULT = '2dB7KWadAnPKZjz'
    MANUAL_SHARE_URL_DEFAULT = 'https://next.amunet.com.mx/s/2dB7KWadAnPKZjz'

    def _manual_config(self):
        ICP = self.env['ir.config_parameter'].sudo()
        return (
            ICP.get_param('amunet_woocommerce.manual_webdav_url',
                          self.MANUAL_WEBDAV_URL_DEFAULT),
            ICP.get_param('amunet_woocommerce.manual_webdav_token',
                          self.MANUAL_TOKEN_DEFAULT),
            ICP.get_param('amunet_woocommerce.manual_share_url',
                          self.MANUAL_SHARE_URL_DEFAULT),
        )

    def _manual_codes_map(self):
        """Dict {CLAVE_MAYUS: nombre_archivo.pdf} cacheado en config."""
        raw = self.env['ir.config_parameter'].sudo().get_param(
            'amunet_woocommerce.manual_codes_json', '{}')
        try:
            return json.loads(raw) or {}
        except (ValueError, TypeError):
            return {}

    def action_refresh_manuals(self):
        """Baja la lista de manuales de la carpeta Nextcloud (WebDAV) y la
        cachea en config. Actualiza la columna 'Tiene manual'."""
        url, token, share = self._manual_config()
        try:
            resp = requests.request(
                'PROPFIND', url, auth=(token, ''),
                headers={'Depth': '1'}, timeout=30)
            resp.raise_for_status()
        except Exception as exc:  # noqa: BLE001
            raise UserError(
                _('No se pudo conectar con la carpeta de manuales en '
                  'Nextcloud:\n%s') % exc)
        codes = {}
        for m in re.finditer(r'<d:href>(.*?)</d:href>', resp.text):
            href = m.group(1)
            if href.lower().endswith('.pdf'):
                fname = unquote(href.split('/webdav/')[-1])
                code = fname.split('_')[0].strip().upper()
                if code:
                    codes[code] = fname
        ICP = self.env['ir.config_parameter'].sudo()
        ICP.set_param('amunet_woocommerce.manual_codes_json',
                      json.dumps(codes))
        ICP.set_param('amunet_woocommerce.manual_codes_updated',
                      fields.Datetime.to_string(fields.Datetime.now()))
        self.env['amunet.woo.product.mapping'].search([]).invalidate_recordset(
            ['has_quality_manual', 'manual_pdf_url'])
        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'title': _('Manuales actualizados'),
                'message': _('%d manuales encontrados en Nextcloud.')
                % len(codes),
                'type': 'success',
                'sticky': False,
                'next': {'type': 'ir.actions.act_window_close'},
            },
        }

    @api.depends('product_id')
    def _compute_has_quality_manual(self):
        codes = self._manual_codes_map()
        _, _token, share = self._manual_config()
        for rec in self:
            code = (rec.product_id.default_code or '').strip().upper()
            fname = codes.get(code)
            rec.has_quality_manual = bool(fname)
            rec.manual_pdf_url = (
                '%s/download?path=%%2F&files=%s' % (share, quote(fname))
                if fname else False)

    def _compute_odoo_inventory(self):
        Quant = self.env['stock.quant']
        Lot = self.env['stock.lot']
        release_field = 'amunet_lot_release_state' in Lot._fields
        for rec in self:
            rec.odoo_qty_onhand = 0.0
            rec.odoo_qty_free = 0.0
            rec.odoo_lot_released_qty = 0.0
            rec.odoo_lot_pending_qty = 0.0
            rec.has_released_lots = False
            rec.odoo_physical_calculable = False
            rec.odoo_physical_reason = False
            rec.odoo_onhand_display = _('No calculable')
            rec.odoo_free_display = _('No calculable')
            rec.odoo_lot_released_display = _('No calculable')
            rec.odoo_lot_pending_display = _('No calculable')
            rec.lot_release_calculable = False
            rec.lot_release_reason = False
            if not rec.product_id:
                reason = _('No hay producto Odoo mapeado.')
                rec.odoo_physical_reason = reason
                rec.lot_release_reason = reason
                continue
            try:
                quants = Quant.search([
                    ('product_id', '=', rec.product_id.id),
                    ('location_id.usage', '=', 'internal'),
                    ('company_id', '=', rec.company_id.id),
                ])
            except AccessError:
                reason = _(
                    'Sin permiso de lectura sobre existencias (stock.quant).')
                rec.odoo_physical_reason = reason
                rec.lot_release_reason = reason
                continue
            for quant in quants:
                reserved = getattr(quant, 'reserved_quantity', 0.0)
                rec.odoo_qty_onhand += quant.quantity
                rec.odoo_qty_free += quant.quantity - reserved
                if not release_field or not quant.lot_id:
                    continue
                state = quant.lot_id.amunet_lot_release_state
                if state == 'released':
                    rec.odoo_lot_released_qty += quant.quantity
                elif state == 'pending':
                    rec.odoo_lot_pending_qty += quant.quantity
            rec.has_released_lots = rec.odoo_lot_released_qty > 0
            rec.odoo_physical_calculable = True
            rec.odoo_onhand_display = '%g' % rec.odoo_qty_onhand
            rec.odoo_free_display = '%g' % rec.odoo_qty_free
            if release_field:
                rec.lot_release_calculable = True
                rec.odoo_lot_released_display = (
                    '%g' % rec.odoo_lot_released_qty)
                rec.odoo_lot_pending_display = (
                    '%g' % rec.odoo_lot_pending_qty)
            else:
                rec.lot_release_reason = _(
                    'El campo regulatorio amunet_lot_release_state no existe '
                    'en stock.lot (módulo de calidad no instalado).')

    def _compute_quality(self):
        tmpl_fields = self.env['product.template']._fields
        has_qc = 'qc_required' in tmpl_fields
        has_param_count = 'qc_parameter_count' in tmpl_fields
        try:
            Check = self.env['amunet.quality.check']
        except KeyError:
            Check = None
        for rec in self:
            rec.qc_required = False
            rec.qc_parameter_count = 0
            rec.qc_check_count = 0
            rec.quality_calculable = False
            rec.quality_reason = False
            rec.quality_status_display = False
            if not rec.product_id:
                rec.quality_reason = _('No hay producto Odoo mapeado.')
                continue
            tmpl = rec.product_id.product_tmpl_id
            if not has_qc:
                rec.quality_reason = _(
                    'La configuración de calidad no existe (módulo '
                    'amunet_quality no instalado).')
                continue
            rec.quality_calculable = True
            rec.qc_required = bool(tmpl.qc_required)
            if has_param_count:
                rec.qc_parameter_count = tmpl.qc_parameter_count
            if Check is not None:
                try:
                    rec.qc_check_count = Check.search_count(
                        [('product_id', '=', rec.product_id.id)])
                except AccessError:
                    rec.qc_check_count = 0
                    rec.quality_calculable = False
                    rec.quality_reason = _(
                        'Sin permiso para consultar controles de calidad.')
            # Texto de estado de calidad para la lista
            if not rec.qc_required:
                rec.quality_status_display = _('No requiere')
            elif rec.qc_parameter_count > 0:
                rec.quality_status_display = str(rec.qc_parameter_count)
            else:
                rec.quality_status_display = _('Falta configurar')

    def _compute_mrp(self):
        Production = self.env['mrp.production']
        for rec in self:
            rec.open_mo_count = 0
            rec.open_mo_qty = 0.0
            rec.open_mo_summary = False
            rec.mrp_calculable = False
            rec.mrp_reason = False
            rec.open_mo_qty_display = _('No calculable')
            if not rec.product_id:
                rec.mrp_reason = _('No hay producto Odoo mapeado.')
                continue
            try:
                mos = Production.search([
                    ('product_id', '=', rec.product_id.id),
                    ('state', 'not in', ('done', 'cancel')),
                    ('company_id', '=', rec.company_id.id),
                ])
            except AccessError:
                rec.mrp_reason = _('Sin acceso a órdenes de fabricación.')
                rec.open_mo_summary = rec.mrp_reason
                continue
            rec.open_mo_count = len(mos)
            rec.open_mo_qty = sum(mos.mapped('product_qty'))
            rec.mrp_calculable = True
            rec.open_mo_qty_display = '%g' % rec.open_mo_qty
            if mos:
                states = dict(mos._fields['state'].selection)
                rec.open_mo_summary = '; '.join(
                    '%s (%s): %s' % (mo.name, states.get(mo.state, mo.state),
                                     mo.product_qty)
                    for mo in mos[:5])

    @api.depends('product_id',
                 'product_id.product_tmpl_id.amunet_linea_larga',
                 'product_id.purchase_ok',
                 'product_id.product_tmpl_id.bom_ids',
                 'product_id.product_tmpl_id.bom_ids.active')
    def _compute_supply_classification(self):
        """Tipo de Fabricación, calculado:
        - Línea larga: marcador amunet_linea_larga (o, a futuro, ruta de BoM
          de línea larga). El marcador manda mientras se ajustan las rutas.
        - Fabricación corta: tiene BoM activa y no es larga.
        - Compra-venta: sin BoM y comprable.
        - Otro: no calculable.
        """
        Bom = self.env['mrp.bom'].sudo()
        for rec in self:
            p = rec.product_id
            if not p:
                rec.supply_classification = 'other'
                continue
            tmpl = p.product_tmpl_id
            if tmpl.amunet_linea_larga:
                rec.supply_classification = 'long_manufacturing'
                continue
            has_bom = bool(Bom.search_count([
                ('active', '=', True),
                ('type', '=', 'normal'),
                '|',
                ('product_id', '=', p.id),
                '&',
                ('product_id', '=', False),
                ('product_tmpl_id', '=', tmpl.id),
            ]))
            if has_bom:
                rec.supply_classification = 'short_manufacturing'
            elif p.purchase_ok:
                rec.supply_classification = 'purchased_qc'
            else:
                rec.supply_classification = 'other'

    def _compute_bom_info(self):
        Bom = self.env['mrp.bom'].sudo()
        for rec in self:
            rec.active_bom_count = 0
            rec.has_active_bom = False
            rec.bom_required = False
            rec.bom_status_display = _('No calculable')
            rec.bom_summary = False
            if not rec.product_id:
                continue
            # Solo los productos que se MANUFACTURAN (pruebas/reactivos
            # terminados) requieren BOM. Consumibles, equipos, instrumentos,
            # soportes, semiterminados = compra-venta y NO llevan BOM, aunque
            # su categoria cuelgue de "Producto terminado".
            categ = rec.product_id.categ_id.complete_name or ''
            _no_bom = ('equipo', 'consumible', 'instrumento', 'soporte',
                       'punta', 'hisopo', 'semiterminado', 'accesorio',
                       'distribuci')
            rec.bom_required = (
                categ.startswith('Producto terminado')
                and not any(k in categ.lower() for k in _no_bom))
            boms = Bom.search([
                ('active', '=', True),
                ('type', '=', 'normal'),
                ('company_id', 'in', [False, rec.company_id.id]),
                '|',
                ('product_id', '=', rec.product_id.id),
                '&',
                ('product_id', '=', False),
                ('product_tmpl_id', '=',
                 rec.product_id.product_tmpl_id.id),
            ], order='sequence, id')
            rec.active_bom_count = len(boms)
            rec.has_active_bom = bool(boms)
            if boms:
                rec.bom_status_display = _('%s BOM activa(s)') % len(boms)
            elif not rec.bom_required:
                rec.bom_status_display = _('No aplica (compra-venta)')
            else:
                rec.bom_status_display = _('Sin BOM activa')
            rec.bom_summary = '\n'.join(
                '%s · %g %s' % (
                    bom.display_name,
                    bom.product_qty,
                    bom.product_uom_id.display_name,
                )
                for bom in boms
            ) or False

    def _compute_packaging_phase(self):
        Plan = self.env['amunet.packaging.plan']
        for rec in self:
            rec.packaging_plan_count = 0
            rec.packaging_planned_qty = 0.0
            rec.packaging_calculable = False
            rec.packaging_reason = False
            rec.packaging_display = _('No calculable')
            rec.packaging_summary = False
            if not rec.product_id:
                rec.packaging_reason = _('No hay producto Odoo mapeado.')
                continue
            try:
                plans = Plan.search([
                    ('product_id', '=', rec.product_id.id),
                    ('production_id.company_id', '=', rec.company_id.id),
                    ('state', 'in', ('draft', 'suggested', 'approved')),
                ])
            except AccessError:
                rec.packaging_reason = _(
                    'Sin permiso para consultar planes de empaque.')
                continue
            states = dict(Plan._fields['state'].selection)
            rec.packaging_plan_count = len(plans)
            quantities = [
                (
                    plan.total_approved_pieces
                    if plan.state == 'approved'
                    else plan.product_qty
                )
                for plan in plans
            ]
            rec.packaging_planned_qty = sum(quantities)
            rec.packaging_calculable = True
            rec.packaging_display = '%g' % rec.packaging_planned_qty
            rec.packaging_summary = '\n'.join(
                '%s (%s): %g piezas planificadas' % (
                    plan.name,
                    states.get(plan.state, plan.state),
                    quantity,
                )
                for plan, quantity in zip(plans, quantities)
            ) or _('Sin planes de empaque activos.')

    def _compute_presentation(self):
        Presentation = self.env['amunet.packaging.presentation'].sudo()
        for rec in self:
            rec.presentation_name = False
            rec.presentation_count = 0
            rec.presentation_summary = False
            rec.pieces_per_box = 0
            rec.pieces_per_box_source = False
            rec.pieces_per_box_calculable = False
            rec.pieces_per_box_reason = False
            if not rec.product_id:
                rec.pieces_per_box_reason = _(
                    'No hay producto Odoo mapeado.')
                continue
            domain = [
                ('product_tmpl_id', '=',
                 rec.product_id.product_tmpl_id.id),
                ('active', '=', True),
                ('is_authorized', '=', True),
            ]
            if 'company_id' in Presentation._fields:
                domain.append(
                    ('company_id', 'in', [False, rec.company_id.id]))
            presentations = Presentation.search(
                domain, order='package_qty, name, id')
            if presentations:
                rows = [
                    _('%(name)s: %(qty)s piezas/caja',
                      name=presentation.name,
                      qty=presentation.package_qty)
                    for presentation in presentations
                ]
                rec.presentation_count = len(presentations)
                rec.presentation_name = presentations[0].display_name
                rec.presentation_summary = '\n'.join(rows)
                if len(presentations) == 1:
                    rec.pieces_per_box = presentations.package_qty
                rec.pieces_per_box_source = _(
                    'Catálogo de presentaciones autorizadas de Odoo.')
                rec.pieces_per_box_calculable = True
            else:
                rec.pieces_per_box_reason = _(
                    'Sin presentaciones autorizadas para el producto Odoo.')

    def _find_bom(self, product, company):
        try:
            boms = self.env['mrp.bom']._bom_find(
                product, company_id=company.id)
        except AccessError:
            return self.env['mrp.bom'].browse()
        if isinstance(boms, dict):
            return boms.get(product) or self.env['mrp.bom'].browse()
        return boms[:1] if boms else self.env['mrp.bom'].browse()

    def _get_bom_source_location(self, bom, company):
        """Ubicación fuente del tipo de operación de la BOM (con fallback al
        tipo de operación de manufactura del almacén de la compañía)."""
        picking_type = bom.picking_type_id
        if not picking_type:
            try:
                warehouse = self.env['stock.warehouse'].search(
                    [('company_id', '=', company.id)], limit=1)
            except AccessError:
                return False
            picking_type = warehouse and warehouse.manu_type_id or False
        return picking_type and picking_type.default_location_src_id or False

    def _capacity_from_bom(self, bom, product, company, location=None):
        """Capacidad fabricable desde una BOM y su ubicación fuente.

        Regresa (qty, calculable, reason). Solo usa lecturas de existencias
        libres y conversiones de UoM; si falta BOM, líneas, ubicación o
        conversión, el resultado es "No calculable". Si todo está configurado
        y el inventario real es insuficiente, cero sí es un resultado válido.
        """
        if not bom:
            return 0.0, False, _('No hay BOM activa para el producto.')
        if bom.type != 'normal':
            return 0.0, False, _('La BOM no es de fabricación normal (kit/subcontrato).')
        if not bom.bom_line_ids:
            return 0.0, False, _('La BOM no tiene líneas de componentes.')
        location = location or self._get_bom_source_location(bom, company)
        if not location:
            return 0.0, False, _(
                'No hay ubicación fuente en el tipo de operación de la BOM.')
        required_by_component = {}
        for line in bom.bom_line_ids:
            component = line.product_id
            if not component:
                return 0.0, False, _('Hay una línea de BOM sin componente.')
            if line.product_qty <= 0:
                continue
            try:
                required = line.product_uom_id._compute_quantity(
                    line.product_qty, component.uom_id, round=False)
            except UserError:
                return 0.0, False, _(
                    'No hay conversión de UoM válida para el componente %s.'
                ) % component.display_name
            item = required_by_component.setdefault(
                component.id, {'product': component, 'required': 0.0})
            item['required'] += required
        if not required_by_component:
            return 0.0, False, _(
                'Todas las líneas de la BOM tienen cantidad cero.')
        capacity_boms = None
        for item in required_by_component.values():
            component = item['product']
            try:
                free_qty = component.with_context(
                    location=location.id).free_qty
            except AccessError:
                return 0.0, False, _(
                    'Sin permiso para consultar existencias del componente %s.'
                ) % component.display_name
            possible = max(free_qty, 0.0) / item['required']
            capacity_boms = possible if capacity_boms is None else min(
                capacity_boms, possible)
        qty = capacity_boms * bom.product_qty
        try:
            qty = bom.product_uom_id._compute_quantity(
                qty, product.uom_id, round=False)
        except UserError:
            return 0.0, False, _(
                'No hay conversión de UoM válida hacia la unidad del producto.')
        rounding = product.uom_id.rounding or 0.01
        return float_round(
            qty,
            precision_rounding=rounding,
            rounding_method='DOWN',
        ), True, False

    def _compute_short_capacity(self):
        for rec in self:
            rec.short_capacity_qty = 0.0
            rec.short_capacity_calculable = False
            rec.short_capacity_reason = False
            rec.short_capacity_display = _('No aplica')
            if rec.supply_classification != 'short_manufacturing':
                rec.short_capacity_reason = _(
                    'No aplica a esta clasificación de abastecimiento.')
                continue
            if not rec.product_id:
                rec.short_capacity_reason = _('No hay producto Odoo mapeado.')
                rec.short_capacity_display = _('No calculable')
                continue
            bom = self._find_bom(rec.product_id, rec.company_id)
            qty, calculable, reason = self._capacity_from_bom(
                bom, rec.product_id, rec.company_id)
            rec.short_capacity_qty = qty
            rec.short_capacity_calculable = calculable
            rec.short_capacity_reason = reason
            rec.short_capacity_display = (
                '%g' % qty if calculable else _('No calculable'))

    def _compute_long_process(self):
        Profile = self.env['amunet.woo.long.process']
        for rec in self:
            rec.long_process_id = False
            rec.long_capacity_calculable = False
            rec.long_capacity_reason = _(
                'No aplica a esta clasificación de abastecimiento.')
            rec.long_capacity_display = _('No aplica')
            if rec.supply_classification != 'long_manufacturing':
                continue
            if not rec.product_id:
                rec.long_capacity_reason = _('No hay producto Odoo mapeado.')
                rec.long_capacity_display = _('No calculable')
                continue
            try:
                profile = Profile.search([
                    ('company_id', '=', rec.company_id.id),
                    ('product_id', '=', rec.product_id.id),
                    ('active', '=', True),
                ], limit=1)
            except AccessError:
                rec.long_capacity_reason = _(
                    'Sin permiso para consultar el perfil de proceso largo.')
                rec.long_capacity_display = _('No calculable')
                continue
            rec.long_process_id = profile
            if not profile:
                rec.long_capacity_reason = _(
                    'No existe perfil de proceso largo para este producto.')
                rec.long_capacity_display = _('No calculable')
                continue
            rec.long_capacity_calculable = profile.pieces_total_calculable
            rec.long_capacity_reason = profile.pieces_total_reason
            rec.long_capacity_display = profile.pieces_total_display

    def _compute_alerts(self):
        max_age = self._snapshot_max_age_days()
        for rec in self:
            alerts = []
            if rec.relation_state == 'pending':
                alerts.append(_('Mapeo pendiente de revisión.'))
            if not rec.product_id:
                alerts.append(_('Artículo Woo sin producto Odoo vinculado.'))
            if not rec.woo_image_url:
                alerts.append(_('Producto Woo sin fotografía.'))
            if rec.product_id and not rec.product_id.image_128:
                alerts.append(_('Producto Odoo sin fotografía.'))
            if not rec.latest_snapshot_id:
                alerts.append(_('Sin snapshot de inventario Woo.'))
            elif rec.snapshot_stale:
                alerts.append(_(
                    'Snapshot de inventario Woo vencido (más de %s días).'
                ) % max_age)
            if rec.quality_calculable and rec.qc_required \
                    and not rec.qc_parameter_count:
                alerts.append(_(
                    'Calidad requerida sin parámetros de calidad configurados.'))
            if rec.supply_classification == 'short_manufacturing' \
                    and not rec.short_capacity_calculable:
                alerts.append(_(
                    'BOM faltante o capacidad no calculable: %s'
                ) % (rec.short_capacity_reason or ''))
            if rec.supply_classification == 'long_manufacturing' \
                    and not rec.long_capacity_calculable:
                alerts.append(_(
                    'Proceso largo no calculable: %s'
                ) % (rec.long_capacity_reason or ''))
            if not rec.odoo_physical_calculable:
                alerts.append(_(
                    'Inventario físico Odoo no calculable: %s'
                ) % (rec.odoo_physical_reason or ''))
            if rec.lot_release_calculable and rec.odoo_lot_pending_qty > 0 \
                    and rec.odoo_lot_released_qty <= 0:
                alerts.append(_(
                    'Existencias en lotes no liberados (pendientes de calidad).'))
            if not rec.pieces_per_box_calculable:
                alerts.append(_(
                    'Piezas por caja no calculables: %s'
                ) % (rec.pieces_per_box_reason or ''))
            rec.alert_text = '\n'.join('• %s' % a for a in alerts) if alerts else False
            rec.has_alerts = bool(alerts)
            required = [
                rec.woo_inventory_calculable,
                rec.odoo_physical_calculable,
                rec.lot_release_calculable,
                rec.quality_calculable,
                rec.pieces_per_box_calculable,
            ]
            if rec.supply_classification == 'short_manufacturing':
                required.append(rec.short_capacity_calculable)
                required.append(rec.mrp_calculable)
            elif rec.supply_classification == 'long_manufacturing':
                required.append(rec.long_capacity_calculable)
                required.append(rec.mrp_calculable)
            rec.any_not_calculable = not all(required)

    # --------------------------------------------------------------
    # Búsquedas de campos computados (filtros)
    # --------------------------------------------------------------

    def _search_ids_by(self, field_name, operator, value):
        if operator not in ('=', '!='):
            raise NotImplementedError
        want = bool(value)
        if operator == '!=':
            want = not want
        matched = self.search([]).filtered(lambda rec: bool(rec[field_name]) == want)
        return [('id', 'in', matched.ids)]

    def _search_has_alerts(self, operator, value):
        return self._search_ids_by('has_alerts', operator, value)

    def _search_any_not_calculable(self, operator, value):
        return self._search_ids_by('any_not_calculable', operator, value)

    def _search_snapshot_stale(self, operator, value):
        return self._search_ids_by('snapshot_stale', operator, value)

    def _search_has_active_bom(self, operator, value):
        return self._search_ids_by('has_active_bom', operator, value)

    def _search_bom_required(self, operator, value):
        return self._search_ids_by('bom_required', operator, value)

    # --------------------------------------------------------------
    # Acciones de navegación
    # --------------------------------------------------------------

    def action_view_mos(self):
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': _('Órdenes de fabricación abiertas'),
            'res_model': 'mrp.production',
            'view_mode': 'list,form',
            'domain': [
                ('product_id', '=', self.product_id.id),
                ('state', 'not in', ('done', 'cancel')),
                ('company_id', '=', self.company_id.id),
            ],
        }

    def action_view_packaging_plans(self):
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': _('Planes de empaque activos'),
            'res_model': 'amunet.packaging.plan',
            'view_mode': 'list,form',
            'domain': [
                ('product_id', '=', self.product_id.id),
                ('production_id.company_id', '=', self.company_id.id),
                ('state', 'in', ('draft', 'suggested', 'approved')),
            ],
        }

    # --------------------------------------------------------------
    # Alta/actualización desde Woo (solo lectura GET)
    # --------------------------------------------------------------

    @api.model
    def _upsert_from_woo(self, backend, woo_item, parent=None):
        """Crea o actualiza el mapeo de un artículo Woo emparejando por SKU.

        Nunca inventa coincidencias: si no hay exactamente un ``default_code``
        igual, crea el renglón pendiente sin producto. El catálogo estándar no
        genera snapshots porque no conoce todos los estados operativos de APT.
        """
        woo_id = woo_item.get('id')
        parent_id = parent and parent.get('id') or 0
        images = woo_item.get('images') or (parent and parent.get('images')) or []
        image_url = images and images[0].get('src') or ''
        values = {
            'backend_id': backend.id,
            'woo_sku': woo_item.get('sku') or '',
            'woo_name': woo_item.get('name') or (parent and parent.get('name')) or '',
            'woo_type': woo_item.get('type') or ('variation' if parent else 'simple'),
            'woo_status': woo_item.get('status') or 'unknown',
            'woo_image_url': image_url,
        }
        existing = self.search([
            ('backend_id', '=', backend.id),
            ('woo_product_id', '=', woo_id),
            ('woo_parent_id', '=', parent_id),
        ], limit=1)
        mapping = existing
        product = existing.product_id
        can_auto_match = (
            not existing
            or (
                not existing.reviewer_id
                and existing.relation_state == 'pending'
            )
        )
        if not product and can_auto_match:
            sku = (woo_item.get('sku') or '').strip()
            products = sku and self.env['product.product'].search(
                [
                    ('default_code', '=', sku),
                    ('company_id', 'in', [False, backend.company_id.id]),
                ],
                limit=2,
            ) or self.env['product.product'].browse()
            product = products if len(products) == 1 else False
            if product:
                values.update({
                    'product_id': product.id,
                    'confidence': 'high',
                    'match_method': _('SKU exacto (sugerencia automática)'),
                    'relation_state': 'pending',
                })
        matched = bool(product)
        result = 'updated' if matched else 'unmatched_updated'
        if not existing:
            mapping = self.create(dict(
                values,
                company_id=backend.company_id.id,
                product_id=product.id if product else False,
                woo_product_id=woo_id,
                woo_parent_id=parent_id))
            result = 'created' if matched else 'unmatched_created'
        else:
            existing.with_context(skip_review_stamp=True).write(values)
        return result

    # ==================================================================
    # INVENTARIO INICIAL (migracion de papel a digital)
    # ==================================================================
    # Hay material que el almacen tiene fisicamente desde antes de que
    # existiera el sistema: se llevaba en papel. Ese material NO tiene orden
    # de fabricacion ni liberacion de Calidad que citar, porque es anterior al
    # proceso; exigirselas seria pedirle un papel que nunca existio. Lo que si
    # se exige es constancia: quien lo capturo, cuando, cuanto, de que lote y
    # con que caducidad, con el motivo escrito en el movimiento.
    #
    # La carga entra por la via normal de Odoo (ajuste de inventario sobre el
    # anaquel de piezas de APT), no por una escritura directa: asi queda el
    # movimiento, el asiento y el historial que pide ISO 13485, y de ahi la
    # publicacion a la tienda sigue el mismo camino que todo lo demas.

    inicial_qty = fields.Float(
        string='Inventario inicial (pz)', copy=False,
        help='Piezas que el almacen ya tiene fisicamente y que nunca pasaron '
             'por el sistema. Se capturan una sola vez y se cargan al anaquel '
             'de piezas de APT como ajuste de inventario.')
    inicial_lot_id = fields.Many2one(
        'stock.lot', string='Lote existente', copy=False,
        domain="[('id', 'in', lote_opcion_ids)]",
        help='Desplegable con los lotes que este producto YA tiene. Elige uno '
             'para ajustarlo, o dejalo vacio para dar de alta uno nuevo.')
    inicial_lot_name = fields.Char(
        string='Lote nuevo', copy=False,
        help='Solo si el material trae un numero de lote que aun no existe en '
             'Odoo. Si el material no trae lote, dejalo vacio: el sistema pone '
             'uno de inventario inicial para poder rastrearlo.')
    inicial_expiration_date = fields.Date(
        string='Caducidad', copy=False,
        help='La tienda clasifica por caducidad (normal / corta / cortesia). '
             'Sin caducidad el material se carga en Odoo pero NO se publica a '
             'la tienda, salvo que el producto no maneje caducidad comercial.')
    inicial_nota = fields.Char(
        string='Observacion de la carga', copy=False,
        help='De donde salio el dato: libreta, formato, conteo fisico, etc.')

    lote_opcion_ids = fields.Many2many(
        'stock.lot', string='Lotes del producto',
        compute='_compute_lotes_producto')
    lote_resumen = fields.Text(
        string='Lotes y piezas en el anaquel', compute='_compute_lotes_producto')
    inicial_cargado_qty = fields.Float(
        string='Inventario inicial ya cargado (pz)',
        compute='_compute_inicial_cargado')

    # --- Inventario inicial por renglones (lote / caducidad / piezas) ---
    inicial_line_ids = fields.One2many(
        'amunet.woo.inicial.line', 'mapping_id',
        string='Lotes de inventario inicial', copy=False)
    inicial_pendientes = fields.Integer(
        string='Lotes por cargar', compute='_compute_inicial_pendientes')
    anaquel_quant_ids = fields.One2many(
        'stock.quant', compute='_compute_anaquel',
        string='Composicion del anaquel (lote / caducidad / piezas)')
    anaquel_total_pz = fields.Float(
        string='Piezas en anaquel', compute='_compute_anaquel')
    anaquel_lotes = fields.Integer(
        string='Lotes en anaquel', compute='_compute_anaquel')
    anaquel_html = fields.Html(
        string='Lotes', compute='_compute_anaquel', sanitize=False,
        help='Los lotes del anaquel con su caducidad y piezas, desplegables '
             'desde la lista sin abrir el producto.')


    @api.depends('product_id')
    def _compute_lotes_producto(self):
        """Los lotes que el producto ya tiene, con sus piezas en el anaquel.

        Es el desplegable que pidio el almacen: en vez de teclear el lote a
        ciegas, el operador ve los que ya existen y ajusta el que corresponde.
        """
        Quant = self.env['stock.quant'].sudo()
        Lot = self.env['stock.lot'].sudo()
        for rec in self:
            if not rec.product_id:
                rec.lote_opcion_ids = [(5, 0, 0)]
                rec.lote_resumen = False
                continue
            lotes = Lot.search(
                [('product_id', '=', rec.product_id.id)],
                order='id desc', limit=200)
            rec.lote_opcion_ids = [(6, 0, lotes.ids)]
            piezas = {}
            ubicacion = rec._ubicacion_piezas()
            if ubicacion:
                for quant in Quant.search([
                        ('product_id', '=', rec.product_id.id),
                        ('location_id', 'child_of', ubicacion.id)]):
                    if quant.lot_id:
                        piezas[quant.lot_id.id] = piezas.get(
                            quant.lot_id.id, 0.0) + quant.quantity
            filas = []
            for lote in lotes[:40]:
                filas.append('%s  |  %s pz en anaquel  |  cad. %s' % (
                    lote.name,
                    int(piezas.get(lote.id, 0.0)),
                    lote.expiration_date.strftime('%m/%Y')
                    if lote.expiration_date else _('sin caducidad')))
            rec.lote_resumen = '\n'.join(filas) or _(
                'Este producto todavia no tiene lotes en Odoo.')

    @api.depends('product_id')
    def _compute_inicial_cargado(self):
        """Cuanto de lo que hay en el anaquel entro como inventario inicial."""
        Lot = self.env['stock.lot'].sudo()
        Quant = self.env['stock.quant'].sudo()
        marca = 'amunet_origen_inicial' in Lot._fields
        for rec in self:
            rec.inicial_cargado_qty = 0.0
            if not rec.product_id or not marca:
                continue
            ubicacion = rec._ubicacion_piezas()
            if not ubicacion:
                continue
            total = 0.0
            for quant in Quant.search([
                    ('product_id', '=', rec.product_id.id),
                    ('location_id', 'child_of', ubicacion.id)]):
                if quant.lot_id and quant.lot_id.amunet_origen_inicial:
                    total += quant.quantity
            rec.inicial_cargado_qty = total

    def _ubicacion_piezas(self):
        """Anaquel de piezas de APT de la tienda de este mapeo."""
        self.ensure_one()
        backend = self.backend_id.sudo()
        if not backend:
            return self.env['stock.location'].browse()
        return backend._apt_pieces_location()

    @api.onchange('inicial_lot_id')
    def _onchange_inicial_lot_id(self):
        """Al elegir un lote del desplegable se traen sus datos.

        Se pregunta la caducidad SIEMPRE, pero si el lote ya la tiene se
        propone la que tiene, para que el operador la confirme en vez de
        teclearla de nuevo (y de paso vea si esta mal).
        """
        for rec in self:
            if not rec.inicial_lot_id:
                continue
            rec.inicial_lot_name = False
            if rec.inicial_lot_id.expiration_date:
                rec.inicial_expiration_date = \
                    rec.inicial_lot_id.expiration_date.date() \
                    if hasattr(rec.inicial_lot_id.expiration_date, 'date') \
                    else rec.inicial_lot_id.expiration_date

    # ------------------------------------------------------------------
    # Inventario inicial: renglones por lote y composicion del anaquel
    # ------------------------------------------------------------------

    def _cargar_inicial_una(self, qty, lote=None, lot_name=None, cad=None, nota=None):
        """Carga UN lote al anaquel de piezas como inventario inicial.

        Devuelve el stock.lot usado. Es el mismo camino de siempre (ajuste de
        inventario con motivo), solo que ahora lo comparten la captura vieja
        (campos sueltos del mapeo) y la nueva (renglones por lote).
        """
        self.ensure_one()
        rec = self
        Lot = self.env['stock.lot'].sudo()
        if not rec.product_id:
            raise UserError(_(
                'El renglon %s no tiene producto Odoo vinculado; no se '
                'puede cargar inventario inicial.') % (rec.woo_sku or ''))
        if not qty or qty <= 0:
            raise UserError(_(
                'El inventario inicial de %s tiene que ser mayor que cero.'
            ) % (rec.woo_sku or rec.product_id.display_name))
        ubicacion = rec._ubicacion_piezas()
        if not ubicacion:
            raise UserError(_(
                'No se encontro el anaquel de piezas de APT para la tienda '
                '%s. Configuralo en la ficha de la tienda antes de cargar '
                'inventario inicial.') % rec.backend_id.display_name)

        if not lote:
            nombre = (lot_name or '').strip()
            if not nombre:
                nombre = 'INI-%s-%s' % (
                    (rec.product_id.default_code or rec.woo_sku or
                     rec.product_id.id),
                    fields.Date.context_today(rec).strftime('%Y%m%d'))
            lote = Lot.search([
                ('product_id', '=', rec.product_id.id),
                ('name', '=', nombre),
            ], limit=1)
            if not lote:
                vals = {
                    'name': nombre,
                    'product_id': rec.product_id.id,
                    'company_id': rec.company_id.id,
                }
                if cad:
                    vals['expiration_date'] = cad
                if 'amunet_origen_inicial' in Lot._fields:
                    vals['amunet_origen_inicial'] = True
                lote = Lot.create(vals)
        escribir = {}
        if cad and not lote.expiration_date:
            escribir['expiration_date'] = cad
        if 'amunet_origen_inicial' in Lot._fields and not lote.amunet_origen_inicial:
            escribir['amunet_origen_inicial'] = True
        if escribir:
            lote.write(escribir)

        motivo = _('Inventario inicial - migracion de papel a digital')
        if nota:
            motivo = '%s (%s)' % (motivo, nota)
        Quant = self.env['stock.quant'].sudo().with_context(
            inventory_mode=True, inventory_name=motivo)
        quant = Quant.search([
            ('product_id', '=', rec.product_id.id),
            ('location_id', '=', ubicacion.id),
            ('lot_id', '=', lote.id),
        ], limit=1)
        if quant:
            quant.write({
                'inventory_quantity': quant.quantity + qty,
                'inventory_quantity_set': True,
            })
        else:
            quant = Quant.create({
                'product_id': rec.product_id.id,
                'location_id': ubicacion.id,
                'lot_id': lote.id,
                'inventory_quantity': qty,
                'inventory_quantity_set': True,
            })
        quant.action_apply_inventory()

        cuerpo = _(
            '<b>INVENTARIO INICIAL cargado.</b> %(qty)s pza(s) al anaquel '
            '%(ubi)s, lote <b>%(lote)s</b>, caducidad %(cad)s.<br/>'
            'Capturado por %(user)s el %(fecha)s.<br/>'
            'Motivo: %(motivo)s.<br/>'
            'Este material es anterior al sistema: no tiene orden de '
            'fabricacion ni liberacion de Calidad que citar. Queda '
            'registrado como ajuste de inventario con su movimiento.',
            qty=qty, ubi=ubicacion.complete_name, lote=lote.name,
            cad=(lote.expiration_date and
                 fields.Date.to_string(lote.expiration_date)) or _('sin capturar'),
            user=self.env.user.display_name,
            fecha=fields.Datetime.now(), motivo=motivo)
        rec.message_post(body=cuerpo)
        try:
            lote.message_post(body=cuerpo)
        except Exception:  # noqa: BLE001 - la bitacora nunca bloquea
            _logger.exception('Aviso de inventario inicial en el lote fallo')
        return lote

    def action_cargar_inventario_inicial(self):
        """Carga al anaquel todo lo que el almacen dejo por cargar.

        Dos fuentes, mismo camino:
        - los renglones por lote (pestana Inventario inicial), que es la
          captura normal: uno por lote fisico, con su caducidad y piezas;
        - los campos sueltos del mapeo (captura vieja de la lista), por
          compatibilidad.
        No se exige orden de fabricacion ni liberacion de Calidad: este
        material es anterior al sistema. Lo que si queda es el movimiento
        con nombre, fecha y motivo.
        """
        # [revision-seguridad] candado de rol en el metodo: corre con sudo().
        if not (self.env.user.has_group('amunet_woocommerce.group_woo_revisor')
                or self.env.user.has_group('amunet_woocommerce.group_woo_admin')):
            raise AccessError(_(
                'Solo un Revisor o Administrador de la tienda puede cargar '
                'inventario inicial.'))
        cargados = 0
        sin_caducidad = []
        for rec in self:
            # 1) Renglones por lote
            for linea in rec.inicial_line_ids.filtered(lambda l: l.state == 'pending'):
                lote = rec._cargar_inicial_una(
                    linea.qty, lot_name=linea.lot_name,
                    cad=linea.expiration_date, nota=linea.nota)
                linea.write({
                    'state': 'done', 'lot_id': lote.id,
                    'cargado_por': self.env.user.id,
                    'cargado_en': fields.Datetime.now(),
                })
                if not lote.expiration_date:
                    sin_caducidad.append('%s (%s)' % (
                        rec.woo_sku or rec.product_id.display_name, lote.name))
                cargados += 1
            # 2) Campos sueltos (captura vieja)
            if rec.inicial_qty:
                lote = rec._cargar_inicial_una(
                    rec.inicial_qty, lote=rec.inicial_lot_id or None,
                    lot_name=rec.inicial_lot_name,
                    cad=rec.inicial_expiration_date, nota=rec.inicial_nota)
                if not lote.expiration_date:
                    sin_caducidad.append('%s (%s)' % (
                        rec.woo_sku or rec.product_id.display_name, lote.name))
                cargados += 1
                rec.with_context(skip_review_stamp=True).write({
                    'inicial_qty': 0.0,
                    'inicial_lot_id': False,
                    'inicial_lot_name': False,
                    'inicial_expiration_date': False,
                    'inicial_nota': False,
                })
        if not cargados:
            raise UserError(_(
                'No hay nada por cargar. Agrega renglones (lote, caducidad, '
                'piezas) en la pestana "Inventario inicial" del producto.'))
        mensaje = _('Se cargaron %s lote(s) de inventario inicial al '
                    'anaquel de piezas.') % cargados
        if sin_caducidad:
            mensaje += _(
                '\n\nSIN CADUCIDAD (quedan en Odoo pero la tienda no los puede '
                'clasificar, asi que no se publican): %s') % ', '.join(
                sin_caducidad[:10])
        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'title': _('Inventario inicial cargado'),
                'message': mensaje,
                'type': 'success' if not sin_caducidad else 'warning',
                'sticky': bool(sin_caducidad),
                'next': {'type': 'ir.actions.client', 'tag': 'reload'},
            },
        }

    def action_abrir_inventario(self):
        """Abre la ficha del producto (pestana de inventario inicial)."""
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': self.woo_name or self.woo_sku,
            'res_model': 'amunet.woo.product.mapping',
            'res_id': self.id,
            'view_mode': 'form',
            'target': 'current',
        }

    @api.depends('product_id', 'backend_id')
    def _compute_anaquel(self):
        """Composicion real del anaquel de piezas: lote, caducidad, piezas.

        Una sola consulta por tienda (no una por renglon): la lista 1109
        trae cientos de productos y se abre todos los dias.
        """
        Quant = self.env['stock.quant'].sudo()
        for rec in self:
            rec.anaquel_quant_ids = Quant.browse()
            rec.anaquel_total_pz = 0.0
            rec.anaquel_lotes = 0
            rec.anaquel_html = '<span class="text-muted">sin lotes</span>'
        por_backend = {}
        for rec in self:
            if rec.product_id and rec.backend_id:
                por_backend.setdefault(rec.backend_id, self.browse()) 
                por_backend[rec.backend_id] |= rec
        for backend, recs in por_backend.items():
            ubicacion = backend.sudo()._apt_pieces_location()
            if not ubicacion:
                continue
            quants = Quant.search([
                ('product_id', 'in', recs.mapped('product_id').ids),
                ('location_id', 'child_of', ubicacion.id),
                ('quantity', '!=', 0),
            ], order='id desc')
            por_producto = {}
            for q in quants:
                por_producto.setdefault(q.product_id.id, Quant.browse())
                por_producto[q.product_id.id] |= q
            for rec in recs:
                qs = por_producto.get(rec.product_id.id, Quant.browse())
                rec.anaquel_quant_ids = qs
                rec.anaquel_total_pz = sum(qs.mapped('quantity'))
                rec.anaquel_lotes = len(qs.filtered('lot_id').mapped('lot_id'))
                rec.anaquel_html = self._html_lotes(qs)

    @api.model
    def _html_lotes(self, quants):
        """Lotes SIEMPRE visibles en la columna de la lista: una linea por
        lote con lote, caducidad y piezas. Sin clic: en la lista editable
        cualquier clic mete el renglon en edicion y Odoo salta a la derecha,
        con lo que el usuario dejaba de ver la columna. El HTML lo arma el
        sistema (sanitize=False) y los textos van escapados.
        """
        from markupsafe import escape
        import datetime
        if not quants:
            return '<span class="text-muted">sin lotes</span>'
        hoy = datetime.date.today()
        lineas = []
        ordenados = quants.sorted(key=lambda x: (x.expiration_date or datetime.datetime.max, x.id))
        for q in ordenados[:8]:
            cad = q.expiration_date
            if cad and hasattr(cad, 'date'):
                cad = cad.date()
            if cad:
                color = 'text-danger' if cad < hoy else ('text-warning' if (cad - hoy).days <= 183 else 'text-success')
                cad_txt = cad.strftime('%d/%m/%Y')
            else:
                color, cad_txt = 'text-muted', 'sin caducidad'
            lineas.append(
                '<div style="white-space:normal;line-height:1.4">'
                '<span style="font-family:monospace">%s</span>'
                ' &middot; <span class="%s">%s</span>'
                ' &middot; <b>%g pz</b></div>' % (
                    escape(q.lot_id.name if q.lot_id else '(sin lote)'),
                    color, cad_txt, q.quantity))
        if len(ordenados) > 8:
            lineas.append('<div class="text-muted">&hellip; y %d lote(s) mas (abrir el producto)</div>' % (len(ordenados) - 8))
        return '<div style="display:block;white-space:normal">%s</div>' % ''.join(lineas)

    @api.depends('inicial_line_ids.state')
    def _compute_inicial_pendientes(self):
        for rec in self:
            rec.inicial_pendientes = len(
                rec.inicial_line_ids.filtered(lambda l: l.state == 'pending'))

    @api.constrains('inicial_qty', 'inicial_lot_id', 'inicial_lot_name',
                    'inicial_expiration_date', 'inicial_nota')
    def _check_inicial_sueltos(self):
        """Captura vieja (campos sueltos): si se llena algo, tiene que traer piezas.

        Evita lo que paso el 1 y 2 de septiembre: renglones con caducidad
        capturada y cero piezas, que nunca se cargaban y nadie avisaba.
        """
        for rec in self:
            algo = rec.inicial_lot_id or rec.inicial_lot_name \
                or rec.inicial_expiration_date or rec.inicial_nota
            if algo and not rec.inicial_qty:
                raise ValidationError(_(
                    '%s: capturaste lote o caducidad de inventario inicial pero '
                    'no las piezas. Pon las piezas, o usa la pestana '
                    '"Inventario inicial" del producto (un renglon por lote).'
                ) % (rec.woo_sku or rec.product_id.display_name))
