# -*- coding: utf-8 -*-
from odoo import models, fields, api, _
from odoo.exceptions import UserError


class AmunetEquipmentRequest(models.Model):
    _name = 'amunet.equipment.request'
    _description = 'Solicitud de ingreso de equipo (Validación)'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'create_date desc'

    name = fields.Char(string='Folio', default='Nueva', copy=False, readonly=True)
    state = fields.Selection([
        ('por_validar', 'Por validar'),
        ('validada', 'Validada'),
    ], string='Estado', default='por_validar', tracking=True, readonly=True)

    # ── Datos de recepción (los llena Almacén automáticamente al validar) ──
    picking_id = fields.Many2one('stock.picking', string='Recepción', readonly=True)
    product_id = fields.Many2one('product.product', string='Producto genérico', readonly=True)
    lot_id = fields.Many2one('stock.lot', string='Serie/Lote recibido', readonly=True)
    serie_recibida = fields.Char(string='Serie/Lote', readonly=True)
    fecha_recepcion = fields.Datetime(string='Fecha de recepción', readonly=True)
    partner_id = fields.Many2one('res.partner', string='Proveedor', readonly=True)
    location_id = fields.Many2one('stock.location', string='Ubicación actual', readonly=True)

    # ── Datos que captura Validación ──
    equipo_nombre = fields.Char(string='Nombre del equipo', tracking=True)
    codigo_equipo = fields.Char(string='Código de equipo', tracking=True)
    department = fields.Selection(
        selection='_department_selection', string='Área', tracking=True)
    funcion = fields.Text(string='Función')
    brand = fields.Char(string='Marca')
    model_name = fields.Char(string='Modelo')

    # Tipo de control (lo determina Ensayo/Calibración, no Almacén):
    #  - independiente: tiene su propia calibración y/o calificación.
    #  - complemento: cuelga de otro equipo ya registrado (equipo padre).
    #  - no_aplica: sin control formal.
    tipo_control = fields.Selection([
        ('independiente', 'Independiente'),
        ('complemento', 'Complemento'),
        ('no_aplica', 'No aplica'),
    ], string='Tipo de control', default='independiente', tracking=True)
    requiere_calibracion = fields.Boolean(string='Requiere calibración')
    requiere_calificacion = fields.Boolean(string='Requiere calificación')
    equipo_padre_id = fields.Many2one(
        'amunet.equipment', string='Equipo padre',
        help='Equipo ya registrado del que depende este complemento.')
    responsable_id = fields.Many2one('res.users', string='Responsable del área')

    equipment_id = fields.Many2one(
        'amunet.equipment', string='Equipo dado de alta', readonly=True, copy=False)

    # Solo Ensayo/Calibración (Gestor de Equipos) edita tipo de control, código,
    # área y responsable. El resto los ve pero no los modifica.
    puede_editar_validacion = fields.Boolean(
        compute='_compute_puede_editar_validacion')

    def _compute_puede_editar_validacion(self):
        es_gestor = self.env.user.has_group(
            'amunet_equipment_calibration.group_equipment_manager')
        for rec in self:
            rec.puede_editar_validacion = es_gestor

    def _department_selection(self):
        # Reusa la lista de áreas/departamentos del propio equipo.
        return self.env['amunet.equipment']._fields['department'].selection

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if not vals.get('name') or vals['name'] == 'Nueva':
                vals['name'] = self.env['ir.sequence'].next_by_code(
                    'amunet.equipment.request') or 'Nueva'
        return super().create(vals_list)

    def action_validar_datos(self):
        self.ensure_one()
        if self.state != 'por_validar':
            raise UserError(_('Esta solicitud ya fue validada.'))
        faltan = []
        if not self.equipo_nombre:
            faltan.append(_('Nombre del equipo'))
        if not self.codigo_equipo:
            faltan.append(_('Código de equipo'))
        if not self.department:
            faltan.append(_('Área'))
        if faltan:
            raise UserError(_('Captura antes de validar:\n- %s') % '\n- '.join(faltan))

        # 1. Dar de alta el equipo en la lista de validación. Nace INACTIVO
        # (registrado, pendiente de calificación): Metrología lo activa cuando
        # complete su expediente de calificación y calibración.
        eq_vals = {
            'name': self.equipo_nombre,
            'serial_number': self.codigo_equipo,
            'brand': self.brand or False,
            'model_name': self.model_name or False,
            'department': self.department,
            'state': 'out_of_service',
        }
        # Mapear el tipo de control al equipo
        if self.tipo_control == 'independiente':
            eq_vals['calibration_required'] = self.requiere_calibracion
            eq_vals['qualification_required'] = self.requiere_calificacion
        elif self.tipo_control == 'complemento':
            eq_vals['parent_equipment_id'] = self.equipo_padre_id.id or False
            eq_vals['calibration_required'] = False
            eq_vals['qualification_required'] = False
        else:  # no_aplica
            eq_vals['calibration_required'] = False
            eq_vals['qualification_required'] = False
        eq = self.env['amunet.equipment'].sudo().create(eq_vals)

        # 2. Sacar la serie del inventario (deja de ser material de almacén)
        self._amunet_salida_inventario()

        # 3. Cerrar la solicitud
        self.write({'state': 'validada', 'equipment_id': eq.id})
        self.message_post(body=_(
            'Datos validados. Equipo dado de alta: <b>%s</b> (código %s). '
            'Salió del inventario de almacén.'
        ) % (eq.name, eq.serial_number or '-'))
        return True

    def _amunet_salida_inventario(self):
        """Saca la unidad del equipo del inventario de almacén (a la ubicación
        virtual de equipos ingresados), para que deje de contar como stock."""
        self.ensure_one()
        if not self.product_id:
            return
        dest = self.env.ref(
            'amunet_equipment_calibration.stock_location_equipos_ingresados',
            raise_if_not_found=False)
        if not dest:
            return
        Quant = self.env['stock.quant'].sudo()
        # Prefiere la ubicación de la solicitud si ahí hay existencia; si no,
        # cualquier ubicación interna con existencia del producto.
        src = False
        if self.location_id and Quant.search_count([
                ('product_id', '=', self.product_id.id),
                ('location_id', '=', self.location_id.id),
                ('quantity', '>', 0)]):
            src = self.location_id
        else:
            q = Quant.search([
                ('product_id', '=', self.product_id.id),
                ('location_id.usage', '=', 'internal'),
                ('quantity', '>', 0)], limit=1)
            src = q.location_id if q else self.location_id
        if not src:
            return
        Move = self.env['stock.move'].sudo()
        move = Move.create({
            'product_id': self.product_id.id,
            'product_uom_qty': 1.0,
            'product_uom': self.product_id.uom_id.id,
            'location_id': src.id,
            'location_dest_id': dest.id,
            'company_id': (self.picking_id.company_id.id if self.picking_id
                           else False) or self.env.company.id,
        })
        move._action_confirm()
        move._action_assign()
        if move.move_line_ids:
            for ml in move.move_line_ids:
                ml.quantity = 1.0
        else:
            self.env['stock.move.line'].sudo().create({
                'move_id': move.id,
                'product_id': self.product_id.id,
                'product_uom_id': self.product_id.uom_id.id,
                'location_id': src.id,
                'location_dest_id': dest.id,
                'quantity': 1.0,
            })
        move.picked = True
        move._action_done()
