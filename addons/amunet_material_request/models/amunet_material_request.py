from odoo import models, fields, api, _
from odoo.exceptions import UserError


class AmunetMaterialRequest(models.Model):
    _name = 'amunet.material.request'
    _description = 'Solicitud de Material'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'request_date desc, id desc'

    name = fields.Char(
        string='Folio',
        required=True, readonly=True, copy=False, default='Nuevo',
        tracking=True,
    )
    state = fields.Selection(
        selection=[
            ('draft', 'Borrador'),
            ('submitted', 'Enviada'),
            ('in_picking', 'En surtido'),
            ('pending_reception', 'Pte. recepcion'),
            ('closed', 'Cerrada'),
            ('cancelled', 'Cancelada'),
        ],
        string='Estado', default='draft', required=True, tracking=True, copy=False,
    )

    requester_id = fields.Many2one(
        'res.users', string='Solicitante',
        default=lambda self: self.env.user, required=True, tracking=True,
    )
    department_id = fields.Many2one(
        'hr.department', string='Area',
        compute='_compute_department_id', store=True, readonly=False, tracking=True,
    )

    request_date = fields.Datetime(
        string='Fecha solicitud', default=fields.Datetime.now,
        required=True, readonly=True, tracking=True,
    )
    required_date = fields.Datetime(string='Fecha requerida', tracking=True)

    warehouse_id = fields.Many2one(
        'stock.warehouse', string='Almacen origen',
        required=True, tracking=True,
        # Las solicitudes de material siempre salen del Almacen de
        # Materia Prima (AMP). Forzamos el default con sudo() para que
        # sea independiente del usuario que crea la solicitud (incluso
        # si esta restringido a otro almacen via amunet_warehouse_access).
        # Si no existe el AMP, cae al primer warehouse de la compania.
        default=lambda self: self._default_warehouse_id(),
    )

    @api.model
    def _default_warehouse_id(self):
        wh_su = self.env['stock.warehouse'].sudo()
        amp = wh_su.search([('code', '=', 'AMP')], limit=1)
        if amp:
            return amp.id
        fallback = wh_su.search(
            [('company_id', '=', self.env.company.id)], limit=1)
        return fallback.id if fallback else False

    picking_id = fields.Many2one(
        'stock.picking', string='Transferencia', readonly=True, copy=False,
    )
    picking_state = fields.Selection(related='picking_id.state', string='Estado transferencia')

    note = fields.Text(string='Notas')

    line_ids = fields.One2many(
        'amunet.material.request.line', 'request_id', string='Lineas',
        copy=True,
    )

    # Firmas digitales (no editables, las setea la accion)
    user_requested_id = fields.Many2one('res.users', string='Firmo solicitud',
                                        readonly=True, copy=False)
    requested_signature_date = fields.Datetime(string='Fecha firma solicitud',
                                               readonly=True, copy=False)
    user_dispatched_id = fields.Many2one('res.users', string='Firmo entrega',
                                         readonly=True, copy=False)
    dispatched_signature_date = fields.Datetime(string='Fecha firma entrega',
                                                readonly=True, copy=False)
    # Tercera firma: el solicitante o su jefe de area valida la recepcion.
    user_validator_id = fields.Many2one('res.users', string='Firmo recepcion',
                                        readonly=True, copy=False)
    validation_signature_date = fields.Datetime(string='Fecha firma recepcion',
                                                readonly=True, copy=False)

    # Campos asociados a la validacion de recepcion.
    reception_notes = fields.Text(string='Observaciones de recepcion',
                                  help='Observaciones generales sobre la recepcion del material.')
    reception_complete = fields.Boolean(
        string='Recibido completo',
        compute='_compute_reception_complete', store=True,
        help='True si todas las cantidades recibidas igualan o superan las surtidas.',
    )
    can_validate_reception = fields.Boolean(
        compute='_compute_can_validate_reception',
        help='Indica si el usuario actual puede validar la recepcion de esta solicitud.',
    )

    line_count = fields.Integer(compute='_compute_line_count', string='No. lineas')

    # Helper para vistas: True solo para usuarios autorizados a editar la
    # cabecera (requester_id / department_id / warehouse_id) de una
    # solicitud. Por requerimiento operativo (trazabilidad ISO), solo el
    # usuario "desarrollo@amunet.com.mx" (Mery, super-admin de respaldo)
    # puede modificarla. Cualquier otro usuario, incluso almacen o admin
    # del modulo, ve los campos en solo lectura.
    is_material_manager_for_user = fields.Boolean(
        compute='_compute_is_material_manager_for_user',
        help='True solo para el super-admin autorizado a editar la cabecera '
             'de una solicitud (campos requester_id, department_id, '
             'warehouse_id). Se usa solo para condiciones de UI.',
    )

    _CABECERA_EDITORES = ('desarrollo@amunet.com.mx',)

    @api.depends_context('uid')
    def _compute_is_material_manager_for_user(self):
        is_editor = self.env.user.login in self._CABECERA_EDITORES
        for rec in self:
            rec.is_material_manager_for_user = is_editor

    _PROTECTED_FIELDS = {
        'name',
        'state',
        'picking_id',
        'picking_state',
        'user_requested_id',
        'requested_signature_date',
        'user_dispatched_id',
        'dispatched_signature_date',
        'user_validator_id',
        'validation_signature_date',
    }

    def _is_material_manager(self):
        return self.env.user.has_group(
            'amunet_material_request.group_material_manager')

    def _is_material_warehouse(self):
        return self.env.user.has_group(
            'amunet_material_request.group_material_warehouse')

    def _check_warehouse_role(self):
        if not (self._is_material_warehouse() or self._is_material_manager()):
            raise UserError(_(
                'Solo usuarios del grupo Solicitudes de Material / Almacen '
                'pueden ejecutar esta accion.'))

    def _check_manager_role(self):
        if not self._is_material_manager():
            raise UserError(_(
                'Solo el administrador de Solicitudes de Material puede '
                'ejecutar esta accion.'))

    def _check_can_write_manual(self, vals):
        if self.env.context.get('material_request_internal_write'):
            return
        if self._is_material_manager():
            return

        protected = self._PROTECTED_FIELDS.intersection(vals)
        if protected:
            raise UserError(_(
                'No puedes modificar campos de estado, transferencia o firmas '
                'directamente. Usa las acciones del flujo.'))

        allowed_warehouse_fields = {'line_ids', 'note'}
        # En 'pending_reception' el solicitante (o jefe de area que
        # puede validar) puede capturar cantidades recibidas y notas
        # antes de firmar. Solo se permite tocar line_ids (donde estan
        # qty_received y line_reception_note) y reception_notes.
        allowed_reception_fields = {'line_ids', 'reception_notes'}
        user = self.env.user
        for rec in self:
            if rec.state == 'draft' and rec.requester_id == user:
                continue
            if (
                self._is_material_warehouse()
                and rec.state == 'in_picking'
                and set(vals).issubset(allowed_warehouse_fields)
            ):
                continue
            if (
                rec.state == 'pending_reception'
                and rec.can_validate_reception
                and set(vals).issubset(allowed_reception_fields)
            ):
                continue
            raise UserError(_(
                'La solicitud %s ya esta firmada o no te pertenece. '
                'No puede editarse manualmente en este estado.') % rec.name)

    @api.depends('line_ids')
    def _compute_line_count(self):
        for rec in self:
            rec.line_count = len(rec.line_ids)

    @api.depends('line_ids.qty_supplied', 'line_ids.qty_received', 'state')
    def _compute_reception_complete(self):
        for rec in self:
            if rec.state not in ('pending_reception', 'closed'):
                rec.reception_complete = False
                continue
            if not rec.line_ids:
                rec.reception_complete = False
                continue
            rec.reception_complete = all(
                line.qty_received >= line.qty_supplied
                for line in rec.line_ids
            )

    @api.depends('requester_id', 'department_id', 'department_id.manager_id',
                 'department_id.manager_id.user_id')
    def _compute_can_validate_reception(self):
        user = self.env.user
        is_manager = self._is_material_manager()
        for rec in self:
            if is_manager:
                rec.can_validate_reception = True
                continue
            if rec.requester_id.id == user.id:
                rec.can_validate_reception = True
                continue
            dept_manager_user = (
                rec.department_id.manager_id.user_id
                if rec.department_id and rec.department_id.manager_id
                else None
            )
            if dept_manager_user and dept_manager_user.id == user.id:
                rec.can_validate_reception = True
                continue
            rec.can_validate_reception = False

    @api.depends('requester_id')
    def _compute_department_id(self):
        for rec in self:
            if rec.department_id:
                continue
            if rec.requester_id:
                emp = self.env['hr.employee'].search(
                    [('user_id', '=', rec.requester_id.id)], limit=1)
                rec.department_id = emp.department_id.id if emp else False
            else:
                rec.department_id = False

    @api.model_create_multi
    def create(self, vals_list):
        if not self._is_material_manager():
            # Forzar requester_id = usuario actual.
            # Limpiar department_id y warehouse_id que un solicitante
            # malicioso podria mandar en los vals desde un cliente
            # custom; los valores reales se computan automaticamente
            # desde el empleado del solicitante y el warehouse por
            # defecto de la compania.
            for vals in vals_list:
                requester_id = vals.get('requester_id')
                if requester_id and requester_id != self.env.user.id:
                    raise UserError(_(
                        'Solo el administrador puede crear solicitudes a '
                        'nombre de otro usuario.'))
                vals['requester_id'] = self.env.user.id
                vals.pop('department_id', None)
                vals.pop('warehouse_id', None)
        for vals in vals_list:
            if vals.get('name', 'Nuevo') == 'Nuevo':
                vals['name'] = self.env['ir.sequence'].next_by_code(
                    'amunet.material.request') or 'Nuevo'
        return super().create(vals_list)

    def _get_consumption_location(self):
        loc = self.env.ref(
            'amunet_material_request.location_consumption_requests',
            raise_if_not_found=False,
        )
        if not loc:
            raise UserError(_(
                'No se encontro la ubicacion de consumo. '
                'Reinstala el modulo "Solicitudes de Material".'))
        return loc

    def _get_internal_picking_type(self):
        self.ensure_one()
        # Preferimos el tipo "Traslados internos" del warehouse (int_type_id),
        # no cualquier picking_type con code='internal' (que tambien incluye QC,
        # Empaquetar, etc.).
        ptype = self.warehouse_id.int_type_id
        if not ptype:
            ptype = self.env['stock.picking.type'].search([
                ('warehouse_id', '=', self.warehouse_id.id),
                ('code', '=', 'internal'),
                ('sequence_code', 'in', ('INT', 'Traslado_ubicación')),
            ], limit=1)
        if not ptype:
            raise UserError(_(
                'No hay un tipo de operacion "Traslados internos" en el almacen %s.'
            ) % self.warehouse_id.name)
        return ptype

    def _get_transfer_sequence(self):
        """Devuelve (creando si hace falta) la secuencia de transferencias
        para este warehouse. Hay una por warehouse, sin reset anual por defecto."""
        self.ensure_one()
        wh_code = self.warehouse_id.code or 'XXX'
        seq_code = f'amunet.material.transfer.{wh_code}'
        seq = self.env['ir.sequence'].sudo().search(
            [('code', '=', seq_code)], limit=1)
        if not seq:
            seq = self.env['ir.sequence'].sudo().create({
                'name': f'Transferencia {wh_code} - Solicitudes de Material',
                'code': seq_code,
                'prefix': '',
                'padding': 5,
                'number_next': 1,
                'number_increment': 1,
                'implementation': 'standard',
                'company_id': False,
            })
        return seq

    def _build_transfer_name(self):
        """Construye el nombre custom 'T/<WH>/<DEPT>/<NNNNN>' validando
        que el departamento tenga su codigo de 3 letras."""
        self.ensure_one()
        if not self.department_id:
            raise UserError(_(
                'La solicitud %s no tiene Area definida. '
                'Asigna un departamento antes de iniciar surtido.'
            ) % self.name)
        dept_code = self.department_id.material_request_code
        if not dept_code:
            raise UserError(_(
                'El departamento "%(dept)s" no tiene codigo de 3 letras '
                'configurado. Ir a Empleados > Departamentos > "%(dept)s" '
                'y configurar "Codigo Solicitudes Material" (ej: PRO, CAL).'
            ) % {'dept': self.department_id.name})
        if not self.warehouse_id.code:
            raise UserError(_(
                'El almacen %s no tiene codigo configurado.'
            ) % self.warehouse_id.name)
        seq = self._get_transfer_sequence()
        next_num = seq.next_by_id()
        return f'T/{self.warehouse_id.code}/{dept_code}/{next_num}'

    def _notify_warehouse_pending(self):
        """Crea actividades para los almacenistas avisando que hay una
        solicitud pendiente de surtir.

        Una actividad por cada usuario del grupo Almacen que tenga
        acceso al almacen origen de la solicitud (segun el modulo
        amunet_warehouse_access cuando esta instalado). Cualquiera de
        ellos puede tomar la solicitud; cuando lo hace, las actividades
        de los demas se eliminan en _close_warehouse_activities.
        """
        self.ensure_one()
        wh_group = self.env.ref(
            'amunet_material_request.group_material_warehouse',
            raise_if_not_found=False,
        )
        todo_act = self.env.ref(
            'mail.mail_activity_data_todo', raise_if_not_found=False)
        if not wh_group or not todo_act:
            return
        # En Odoo 19 el campo es user_ids (era users en versiones previas).
        users = wh_group.sudo().all_user_ids.filtered(
            lambda u: u.active and u.id != 1)
        # Filtrar por acceso a almacen si el modulo lo trae
        if 'warehouse_ids' in users._fields:
            users = users.filtered(
                lambda u: not u.warehouse_ids or self.warehouse_id in u.warehouse_ids
            )
        body = _(
            'Solicitante: %(s)s\nArea: %(d)s\nLineas: %(n)s\nAlmacen: %(w)s'
        ) % {
            's': self.requester_id.name,
            'd': self.department_id.name or '-',
            'n': len(self.line_ids),
            'w': self.warehouse_id.name,
        }
        for u in users:
            self.sudo().activity_schedule(
                'mail.mail_activity_data_todo',
                summary=_('Surtir solicitud %s') % self.name,
                note=body.replace('\n', '<br/>'),
                user_id=u.id,
            )

    def _close_warehouse_activities(self):
        """Elimina las actividades de surtido pendientes (cuando alguien
        ya tomo la solicitud o la cancelo). Identifica solo las que
        creamos nosotros por el 'summary'."""
        self.ensure_one()
        summary_prefix = _('Surtir solicitud ')
        actividades = self.sudo().activity_ids.filtered(
            lambda a: a.summary and a.summary.startswith(summary_prefix)
        )
        actividades.unlink()

    def _notify_requester_ready(self):
        """Crea una actividad para el solicitante avisandole que su
        material ya esta surtido y listo para recoger. Se invoca al
        confirmar la entrega (estado pasa de in_picking a pending_reception).
        La actividad aparece en la bandeja superior del solicitante en
        cualquier app de Odoo.
        """
        self.ensure_one()
        if not self.requester_id:
            return
        todo_act = self.env.ref(
            'mail.mail_activity_data_todo', raise_if_not_found=False)
        if not todo_act:
            return
        body = _(
            'Tu material ya esta surtido y puedes pasar por el.\n'
            'Solicitud: %(s)s\n'
            'Almacen: %(w)s\n'
            'Surtido por: %(u)s'
        ) % {
            's': self.name,
            'w': self.warehouse_id.name,
            'u': self.env.user.display_name,
        }
        self.sudo().activity_schedule(
            'mail.mail_activity_data_todo',
            summary=_('Recoger material - %s') % self.name,
            note=body.replace('\n', '<br/>'),
            user_id=self.requester_id.id,
        )

    def _close_requester_activities(self):
        """Elimina la actividad de 'Recoger material' del solicitante.
        Se invoca cuando el solicitante valida la recepcion (cierra el
        ciclo) o cuando la solicitud se cancela. Identifica solo las
        actividades creadas por _notify_requester_ready via el summary."""
        self.ensure_one()
        summary_prefix = _('Recoger material - ')
        actividades = self.sudo().activity_ids.filtered(
            lambda a: a.summary and a.summary.startswith(summary_prefix)
        )
        actividades.unlink()

    def action_submit(self):
        for rec in self:
            if rec.state != 'draft':
                raise UserError(_('Solo se puede enviar una solicitud en Borrador.'))
            if rec.requester_id != self.env.user and not self._is_material_manager():
                raise UserError(_(
                    'Solo el solicitante puede firmar y enviar su propia solicitud.'))
            if not rec.line_ids:
                raise UserError(_('No puedes enviar una solicitud sin lineas.'))
            for line in rec.line_ids:
                if line.qty_requested <= 0:
                    raise UserError(_(
                        'La cantidad solicitada de %s debe ser mayor a 0.'
                    ) % line.product_id.display_name)
                if line.qty_requested > line.stock_available:
                    raise UserError(_(
                        'No hay stock suficiente de %(prod)s en %(wh)s. '
                        'Solicitado: %(req)s, disponible: %(avail)s.'
                    ) % {
                        'prod': line.product_id.display_name,
                        'wh': rec.warehouse_id.name,
                        'req': line.qty_requested,
                        'avail': line.stock_available,
                    })
            rec.with_context(material_request_internal_write=True).write({
                'state': 'submitted',
                'user_requested_id': self.env.user.id,
                'requested_signature_date': fields.Datetime.now(),
            })
            rec.message_post(body=_(
                'Solicitud enviada y firmada por %s.'
            ) % self.env.user.display_name)
            # Notificar a los almacenistas: aparece como actividad
            # pendiente en su bandeja superior de Odoo.
            rec._notify_warehouse_pending()
        return True

    def action_start_picking(self):
        self._check_warehouse_role()
        for rec in self:
            if rec.state != 'submitted':
                raise UserError(_('Solo se puede iniciar surtido desde Enviada.'))
            consumption_loc = rec._get_consumption_location()
            ptype = rec._get_internal_picking_type()
            src_loc = ptype.default_location_src_id or rec.warehouse_id.lot_stock_id
            transfer_name = rec._build_transfer_name()
            picking_vals = {
                'name': transfer_name,
                'picking_type_id': ptype.id,
                'location_id': src_loc.id,
                'location_dest_id': consumption_loc.id,
                'origin': rec.name,
                'company_id': rec.warehouse_id.company_id.id,
                'move_ids': [(0, 0, {
                    'product_id': line.product_id.id,
                    'product_uom_qty': line.qty_requested,
                    'product_uom': line.uom_id.id,
                    'location_id': src_loc.id,
                    'location_dest_id': consumption_loc.id,
                }) for line in rec.line_ids],
            }
            picking = self.env['stock.picking'].create(picking_vals)
            picking.action_confirm()
            picking.action_assign()
            rec.with_context(material_request_internal_write=True).write({
                'picking_id': picking.id,
                'state': 'in_picking',
            })
            # Pre-cargar qty_supplied = qty_requested para acelerar al almacenista
            for line in rec.line_ids:
                if not line.qty_supplied:
                    line.qty_supplied = line.qty_requested
            rec.message_post(body=_(
                'Surtido iniciado. Transferencia %s creada.'
            ) % picking.name)
            # Alguien tomo la solicitud: cerrar las actividades
            # pendientes de los demas almacenistas.
            rec._close_warehouse_activities()
        return True

    def action_confirm_delivery(self):
        self._check_warehouse_role()
        for rec in self:
            if rec.state != 'in_picking':
                raise UserError(_('Solo se puede confirmar entrega desde En surtido.'))
            if not rec.picking_id:
                raise UserError(_('La solicitud no tiene transferencia asociada.'))
            # Validar lotes y cantidades surtidas
            for line in rec.line_ids:
                if line.qty_supplied <= 0:
                    raise UserError(_(
                        'La cantidad surtida de %s debe ser mayor a 0.'
                    ) % line.product_id.display_name)
                if line.tracking in ('lot', 'serial') and not line.lot_id:
                    raise UserError(_(
                        'Falta asignar lote para %s.'
                    ) % line.product_id.display_name)
                if line.lot_id and line.qty_supplied > line.lot_available_qty:
                    raise UserError(_(
                        'Stock insuficiente en el lote %(lot)s de %(prod)s. '
                        'Solicitado: %(req)s, disponible en lote: %(avail)s.'
                    ) % {
                        'lot': line.lot_id.name,
                        'prod': line.product_id.display_name,
                        'req': line.qty_supplied,
                        'avail': line.lot_available_qty,
                    })
            # Sincronizar stock.move.lines con los lotes y cantidades elegidas
            # Si la linea fue agregada por el almacenista despues de
            # 'Iniciar Surtido' (no tiene move correspondiente), creamos
            # el stock.move sobre el mismo picking y lo confirmamos/reservamos.
            consumption_loc = rec._get_consumption_location()
            ptype = rec._get_internal_picking_type()
            src_loc = ptype.default_location_src_id or rec.warehouse_id.lot_stock_id
            for line in rec.line_ids:
                moves = rec.picking_id.move_ids.filtered(
                    lambda m, prod=line.product_id: m.product_id.id == prod.id
                )
                if not moves:
                    # Linea agregada por el almacenista durante surtido:
                    # creamos su stock.move asociado al picking actual.
                    new_move = self.env['stock.move'].sudo().create({
                        'picking_id': rec.picking_id.id,
                        'name': line.product_id.display_name,
                        'product_id': line.product_id.id,
                        'product_uom_qty': line.qty_requested,
                        'product_uom': line.uom_id.id,
                        'location_id': src_loc.id,
                        'location_dest_id': consumption_loc.id,
                        'company_id': rec.warehouse_id.company_id.id,
                    })
                    new_move._action_confirm()
                    new_move._action_assign()
                    moves = new_move
                move = moves[0]
                # Limpiar move_lines actuales y crear una sola con lote
                move.move_line_ids.unlink()
                self.env['stock.move.line'].create({
                    'move_id': move.id,
                    'product_id': line.product_id.id,
                    'product_uom_id': line.uom_id.id,
                    'location_id': move.location_id.id,
                    'location_dest_id': move.location_dest_id.id,
                    'lot_id': line.lot_id.id or False,
                    'quantity': line.qty_supplied,
                    'picking_id': rec.picking_id.id,
                })
            # Validar el picking (descuenta stock real)
            res = rec.picking_id.with_context(
                skip_backorder=True,
                picking_ids_not_to_backorder=rec.picking_id.ids,
            ).button_validate()
            # Si Odoo devuelve un wizard de backorder, lo procesamos cancelando
            if isinstance(res, dict) and res.get('res_model') == 'stock.backorder.confirmation':
                ctx = res.get('context') or {}
                wiz = self.env[res['res_model']].with_context(**ctx).create({})
                if hasattr(wiz, 'process_cancel_backorder'):
                    wiz.process_cancel_backorder()
            rec.with_context(material_request_internal_write=True).write({
                'state': 'pending_reception',
                'user_dispatched_id': self.env.user.id,
                'dispatched_signature_date': fields.Datetime.now(),
            })
            rec.message_post(body=_(
                'Entrega confirmada y firmada por %s. '
                'Queda pendiente la validacion de recepcion por el solicitante.'
            ) % self.env.user.display_name)
            # Notificar al solicitante: aparece como actividad pendiente
            # en su bandeja superior de Odoo ("Recoger material - SMP/...").
            rec._notify_requester_ready()
        return True

    def action_validate_reception(self):
        for rec in self:
            if rec.state != 'pending_reception':
                raise UserError(_(
                    'Solo se puede validar recepcion desde "Pte. recepcion".'))
            if not rec.can_validate_reception:
                raise UserError(_(
                    'No tienes permiso para validar la recepcion de %s. '
                    'Solo el solicitante, el jefe del area o el administrador '
                    'del modulo pueden validar.') % rec.name)
            # Validacion de cantidades recibidas
            for line in rec.line_ids:
                if line.qty_received < 0:
                    raise UserError(_(
                        'La cantidad recibida de %s no puede ser negativa.'
                    ) % line.product_id.display_name)
                if line.qty_received > line.qty_supplied:
                    raise UserError(_(
                        'La cantidad recibida de %(prod)s (%(recv)s) no puede '
                        'ser mayor a la surtida (%(supp)s).'
                    ) % {
                        'prod': line.product_id.display_name,
                        'recv': line.qty_received,
                        'supp': line.qty_supplied,
                    })
            rec.with_context(material_request_internal_write=True).write({
                'state': 'closed',
                'user_validator_id': self.env.user.id,
                'validation_signature_date': fields.Datetime.now(),
            })
            body = _('Recepcion validada y firmada por %s.') % self.env.user.display_name
            if not rec.reception_complete:
                body += _(
                    ' <b>Recepcion PARCIAL</b>: hay diferencias entre lo '
                    'surtido y lo recibido. Revisar observaciones por linea.')
            rec.message_post(body=body)
            # Cerrar la actividad "Recoger material" del solicitante
            rec._close_requester_activities()
        return True

    def action_cancel(self):
        for rec in self:
            if rec.state == 'closed':
                raise UserError(_('No se puede cancelar una solicitud ya cerrada.'))
            if not self._is_material_manager():
                if rec.requester_id == self.env.user and rec.state in ('draft', 'submitted'):
                    pass
                elif self._is_material_warehouse() and rec.state == 'in_picking':
                    pass
                else:
                    raise UserError(_(
                        'No tienes permiso para cancelar la solicitud %s en '
                        'este estado.') % rec.name)
            if rec.picking_id and rec.picking_id.state not in ('done', 'cancel'):
                rec.picking_id.action_cancel()
            rec.with_context(material_request_internal_write=True).write({
                'state': 'cancelled',
            })
            # Limpiar las actividades de surtido pendientes y la del
            # solicitante (si la solicitud ya estaba surtida y aun no
            # validada al cancelar).
            rec._close_warehouse_activities()
            rec._close_requester_activities()
        return True

    def action_draft(self):
        self._check_manager_role()
        for rec in self:
            if rec.state != 'cancelled':
                raise UserError(_('Solo desde Cancelada se regresa a Borrador.'))
            rec.with_context(material_request_internal_write=True).write({
                'state': 'draft',
                'user_requested_id': False,
                'requested_signature_date': False,
                'user_dispatched_id': False,
                'dispatched_signature_date': False,
                'user_validator_id': False,
                'validation_signature_date': False,
                'picking_id': False,
            })
            for line in rec.line_ids:
                line.with_context(material_request_internal_write=True).write({
                    'qty_received': 0.0,
                    'line_reception_note': False,
                })
        return True

    def action_view_picking(self):
        self.ensure_one()
        if not self.picking_id:
            return False
        return {
            'type': 'ir.actions.act_window',
            'res_model': 'stock.picking',
            'view_mode': 'form',
            'res_id': self.picking_id.id,
        }

    def write(self, vals):
        self._check_can_write_manual(vals)
        return super().write(vals)

    def unlink(self):
        if not self._is_material_manager():
            raise UserError(_(
                'Las solicitudes de material no se eliminan. Cancela la '
                'solicitud para conservar trazabilidad.'))
        if any(rec.state not in ('draft', 'cancelled') for rec in self):
            raise UserError(_(
                'Solo se pueden eliminar solicitudes en Borrador o Cancelada.'))
        return super().unlink()
