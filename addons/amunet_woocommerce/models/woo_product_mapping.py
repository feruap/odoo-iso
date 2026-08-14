# -*- coding: utf-8 -*-

import base64

import requests

from odoo import api, fields, models, _
from odoo.exceptions import AccessError, UserError
from odoo.tools.float_utils import float_round

# Campos que el grupo Revisor puede editar manualmente (relación/confirmación).
# Todo lo demás del mapeo solo lo escribe el Administrador (importación/sistema).
REVIEWER_ALLOWED_FIELDS = {
    'product_id', 'relation_state', 'confidence', 'match_method',
    'review_notes', 'supply_classification', 'woo_name', 'woo_image',
    'odoo_name_edit',
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
    stock_preproduccion = fields.Float(
        string='Preproducción', compute='_compute_stage_stock')
    stock_posproduccion = fields.Float(
        string='Posproducción', compute='_compute_stage_stock')
    stock_existencias = fields.Float(
        string='Existencias', compute='_compute_stage_stock')
    stock_control_calidad = fields.Float(
        string='Control de calidad', compute='_compute_stage_stock')
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
        string='Tiene manual de calidad',
        compute='_compute_has_quality_manual',
        help='El producto tiene al menos un parámetro/especificación de '
             'calidad configurado (amunet_quality). Si lo tiene, ya es '
             'evaluable para volverse vendible.')
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
            forbidden = incoming - REVIEWER_ALLOWED_FIELDS
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
        ('stock_preproduccion', ('Preproducción', 'Pre-Production')),
        ('stock_posproduccion', ('Posproducción', 'Post-Production')),
        ('stock_existencias', ('Existencias',)),
        ('stock_control_calidad', ('Control de calidad',)),
        ('stock_entrada', ('Entrada',)),
        ('stock_salida', ('Salida',)),
        ('stock_empaquetado', ('Zona de empaquetado',)),
    ]

    def _compute_stage_stock(self):
        """Existencias del producto por etapa de producción.

        Posproducción = producto terminado LIBERADO del Almacén de Producto
        Terminado (APT/Existencias_*). Preproducción = TODO lo demás: materia
        prima e insumos (AMP/AMPB/ARU) MÁS el 'Almacén Temporal PT' (producto
        fabricado en espera de análisis). El 'Rechazo' NO se contempla en
        ninguna de las dos. Las demás etapas (Existencias, Control de calidad,
        Entrada, Salida, Zona de empaquetado) se agrupan por el nombre de la
        ubicación."""
        Quant = self.env['stock.quant']
        apt_wh = self.env['stock.warehouse'].sudo().search(
            [('code', '=', 'APT')], limit=1)
        apt_path = apt_wh.view_location_id.parent_path if apt_wh else False
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
                loc = quant.location_id
                cname = loc.complete_name or ''
                is_apt = bool(apt_path and loc.parent_path
                              and loc.parent_path.startswith(apt_path))
                # Rechazo no cuenta; APT liberado (no Temporal) = pos;
                # todo lo demás (incl. Almacén Temporal PT) = pre.
                if 'Rechazo' not in cname:
                    if is_apt and 'Temporal' not in cname:
                        rec.stock_posproduccion += quant.quantity
                    else:
                        rec.stock_preproduccion += quant.quantity
                # Demás etapas por nombre de ubicación
                for fname, pats in self._STAGE_PATTERNS:
                    if fname in ('stock_preproduccion', 'stock_posproduccion'):
                        continue
                    if any(p in cname for p in pats):
                        rec[fname] += quant.quantity
                        break

    @api.depends('qc_parameter_count')
    def _compute_has_quality_manual(self):
        for rec in self:
            rec.has_quality_manual = rec.qc_parameter_count > 0

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
