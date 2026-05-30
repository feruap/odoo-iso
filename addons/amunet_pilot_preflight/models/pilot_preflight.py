# -*- coding: utf-8 -*-

from odoo import api, fields, models, _
from odoo.exceptions import UserError


class AmunetPilotPreflight(models.Model):
    _name = 'amunet.pilot.preflight'
    _description = 'Preflight del piloto de fabricacion'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'write_date desc, id desc'

    name = fields.Char(
        string='Folio',
        default='Nuevo',
        required=True,
        readonly=True,
        copy=False,
        tracking=True,
    )
    production_id = fields.Many2one(
        'mrp.production',
        string='Orden de fabricacion',
        tracking=True,
    )
    product_id = fields.Many2one(
        'product.product',
        string='Producto',
        required=True,
        tracking=True,
    )
    product_tmpl_id = fields.Many2one(
        'product.template',
        string='Producto maestro',
        related='product_id.product_tmpl_id',
        store=True,
        readonly=True,
    )
    product_qty = fields.Float(
        string='Cantidad piloto',
        digits='Product Unit of Measure',
        default=70.0,
        required=True,
        tracking=True,
    )
    product_uom_id = fields.Many2one(
        'uom.uom',
        string='UdM',
        related='product_id.uom_id',
        readonly=True,
    )
    company_id = fields.Many2one(
        'res.company',
        string='Compania',
        default=lambda self: self.env.company,
        required=True,
    )
    route_type = fields.Selection([
        ('short', 'Fabricacion corta'),
        ('long', 'Fabricacion larga / hoja'),
        ('solution', 'Soluciones'),
        ('resale', 'Compra y reventa'),
    ], string='Ruta esperada', default='short', required=True, tracking=True)
    bom_id = fields.Many2one('mrp.bom', string='BOM usada')

    production_user_id = fields.Many2one('res.users', string='Produccion')
    quality_user_id = fields.Many2one('res.users', string='Analista QC')
    quality_supervisor_id = fields.Many2one('res.users', string='Supervisor QC')
    warehouse_user_id = fields.Many2one('res.users', string='Almacen')
    packaging_user_id = fields.Many2one('res.users', string='Empaque / envios')

    state = fields.Selection([
        ('draft', 'Borrador'),
        ('blocked', 'Bloqueado'),
        ('warning', 'Con advertencias'),
        ('ready', 'Listo para piloto'),
        ('accepted', 'Aceptado para piloto'),
        ('cancel', 'Cancelado'),
    ], string='Estado', default='draft', required=True, tracking=True)
    last_check_date = fields.Datetime(string='Ultima validacion', readonly=True)
    checked_by_id = fields.Many2one('res.users', string='Validado por', readonly=True)
    accepted_by_id = fields.Many2one('res.users', string='Aceptado por', readonly=True)
    accepted_date = fields.Datetime(string='Fecha aceptacion', readonly=True)

    line_ids = fields.One2many(
        'amunet.pilot.preflight.line',
        'preflight_id',
        string='Checklist',
        copy=False,
    )
    block_count = fields.Integer(compute='_compute_counts', string='Bloqueos')
    warning_count = fields.Integer(compute='_compute_counts', string='Advertencias')
    pass_count = fields.Integer(compute='_compute_counts', string='Correctos')
    readiness_score = fields.Float(compute='_compute_counts', string='Avance')
    next_step = fields.Char(compute='_compute_next_step', string='Siguiente paso')

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if vals.get('name', 'Nuevo') == 'Nuevo':
                vals['name'] = self.env['ir.sequence'].next_by_code(
                    'amunet.pilot.preflight'
                ) or 'PREF/Nuevo'
            if vals.get('production_id') and not vals.get('product_id'):
                mo = self.env['mrp.production'].browse(vals['production_id'])
                vals['product_id'] = mo.product_id.id
                vals['product_qty'] = vals.get('product_qty') or mo.product_qty
                vals['bom_id'] = vals.get('bom_id') or mo.bom_id.id
                vals['company_id'] = vals.get('company_id') or mo.company_id.id
        records = super().create(vals_list)
        records._set_default_participants()
        return records

    @api.onchange('production_id')
    def _onchange_production_id(self):
        for rec in self:
            if not rec.production_id:
                continue
            rec.product_id = rec.production_id.product_id
            rec.product_qty = rec.production_id.product_qty
            rec.bom_id = rec.production_id.bom_id
            rec.company_id = rec.production_id.company_id

    @api.onchange('product_id', 'company_id')
    def _onchange_product_id(self):
        for rec in self:
            if rec.product_id and not rec.bom_id:
                rec.bom_id = rec._find_bom()

    @api.depends('line_ids.status')
    def _compute_counts(self):
        for rec in self:
            lines = rec.line_ids
            rec.block_count = len(lines.filtered(lambda line: line.status == 'block'))
            rec.warning_count = len(lines.filtered(lambda line: line.status == 'warn'))
            rec.pass_count = len(lines.filtered(lambda line: line.status == 'pass'))
            counted = lines.filtered(lambda line: line.status in ('pass', 'warn', 'block'))
            rec.readiness_score = (
                round(100.0 * rec.pass_count / len(counted), 1) if counted else 0.0
            )

    @api.depends('state', 'line_ids.status', 'line_ids.action_hint')
    def _compute_next_step(self):
        for rec in self:
            blocker = rec.line_ids.filtered(lambda line: line.status == 'block')[:1]
            warning = rec.line_ids.filtered(lambda line: line.status == 'warn')[:1]
            if rec.state == 'draft':
                rec.next_step = 'Dar clic en Validar preflight'
            elif blocker:
                rec.next_step = blocker.action_hint or blocker.name
            elif warning:
                rec.next_step = 'Puede iniciar con advertencias si el responsable las acepta'
            elif rec.state == 'accepted':
                rec.next_step = 'Crear/confirmar orden y seguir flujo normal'
            else:
                rec.next_step = 'Listo para piloto'

    def _set_default_participants(self):
        for rec in self:
            vals = {}
            if not rec.production_user_id:
                vals['production_user_id'] = rec._first_user('amunet_production.group_production_supervisor').id
            if not rec.quality_user_id:
                vals['quality_user_id'] = rec._first_user('amunet_quality.group_quality_user').id
            if not rec.quality_supervisor_id:
                vals['quality_supervisor_id'] = rec._first_user('amunet_quality.group_quality_supervisor').id
            if not rec.warehouse_user_id:
                vals['warehouse_user_id'] = rec._first_user('amunet_material_request.group_material_warehouse').id
            if not rec.packaging_user_id:
                vals['packaging_user_id'] = rec._first_user('amunet_packaging_planning.group_packaging_manager').id
            if vals:
                rec.write(vals)

    def _first_user(self, group_xmlid):
        group = self.env.ref(group_xmlid, raise_if_not_found=False)
        if not group:
            return self.env['res.users']
        return self.env['res.users'].search([
            ('active', '=', True),
            ('group_ids', 'in', group.id),
            ('share', '=', False),
            ('login', '!=', 'fernando.ruiz@amunet.com.mx'),
        ], limit=1)

    def _find_bom(self):
        self.ensure_one()
        if not self.product_id:
            return self.env['mrp.bom']
        if self.bom_id:
            return self.bom_id
        bom = self.env['mrp.bom']
        try:
            found = self.env['mrp.bom']._bom_find(
                self.product_id,
                company_id=self.company_id.id,
                bom_type='normal',
            )
            bom = found.get(self.product_id) if isinstance(found, dict) else found
        except Exception:
            bom = self.env['mrp.bom']
        if not bom:
            bom = self.env['mrp.bom'].search([
                '|',
                ('product_id', '=', self.product_id.id),
                ('product_tmpl_id', '=', self.product_tmpl_id.id),
                '|',
                ('company_id', '=', False),
                ('company_id', '=', self.company_id.id),
            ], limit=1)
        return bom

    def _add_line(self, section, name, status, detail='', action_hint='', related=None, sequence=10):
        self.ensure_one()
        model = self.env['ir.model']
        related_model = False
        related_res_id = 0
        if related:
            related_model = model._get(related._name)
            related_res_id = related.id
        return self.env['amunet.pilot.preflight.line'].create({
            'preflight_id': self.id,
            'section': section,
            'name': name,
            'status': status,
            'detail': detail or '',
            'action_hint': action_hint or '',
            'related_model_id': related_model.id if related_model else False,
            'related_res_id': related_res_id,
            'sequence': sequence,
        })

    def action_run_checks(self):
        for rec in self:
            rec._set_default_participants()
            rec.line_ids.unlink()
            rec.bom_id = rec._find_bom()
            rec._check_master_data()
            rec._check_bom_and_inventory()
            rec._check_quality()
            rec._check_packaging()
            rec._check_people_and_training()
            rec._check_open_changes()
            rec._compute_state_after_checks()
            rec.write({
                'last_check_date': fields.Datetime.now(),
                'checked_by_id': self.env.user.id,
            })
            rec.message_post(body=_('Preflight validado. Estado: %s') % rec.state)
        return True

    def _compute_state_after_checks(self):
        for rec in self:
            if rec.line_ids.filtered(lambda line: line.status == 'block'):
                rec.state = 'blocked'
            elif rec.line_ids.filtered(lambda line: line.status == 'warn'):
                rec.state = 'warning'
            else:
                rec.state = 'ready'

    def action_accept_for_pilot(self):
        for rec in self:
            if rec.block_count:
                raise UserError(_('No se puede aceptar el piloto con bloqueos abiertos.'))
            if not rec.line_ids:
                raise UserError(_('Primero ejecute Validar preflight.'))
            rec.write({
                'state': 'accepted',
                'accepted_by_id': self.env.user.id,
                'accepted_date': fields.Datetime.now(),
            })
            rec.message_post(body=_('Preflight aceptado para iniciar piloto.'))
        return True

    def action_cancel(self):
        self.write({'state': 'cancel'})

    def _check_master_data(self):
        for rec in self:
            if rec.product_id:
                rec._add_line(
                    'master',
                    'Producto seleccionado',
                    'pass',
                    rec.product_id.display_name,
                    related=rec.product_id,
                    sequence=10,
                )
            if rec.product_qty > 0:
                rec._add_line(
                    'master',
                    'Cantidad de piloto',
                    'pass',
                    '%s %s' % (rec.product_qty, rec.product_uom_id.name or ''),
                    sequence=20,
                )
            else:
                rec._add_line(
                    'master',
                    'Cantidad de piloto',
                    'block',
                    'La cantidad debe ser mayor a cero.',
                    'Definir cantidad antes de crear la MO.',
                    sequence=20,
                )
            if rec.route_type == 'long':
                rec._add_line(
                    'master',
                    'Ruta larga',
                    'warn',
                    'Ruta larga detectada. Para este piloto conviene fabricar o comprar la hoja primero y usarla como insumo de ruta corta.',
                    'Confirmar si la hoja impregnada ya existe como insumo disponible.',
                    sequence=30,
                )
            elif rec.route_type == 'solution':
                rec._add_line(
                    'master',
                    'Ruta soluciones',
                    'warn',
                    'El area de Soluciones participa solo si el producto/BOM requiere fabricar buffer o solucion.',
                    'Confirmar receta y solicitud de analisis de la solucion.',
                    sequence=30,
                )
            else:
                rec._add_line(
                    'master',
                    'Ruta esperada',
                    'pass',
                    dict(rec._fields['route_type'].selection).get(rec.route_type),
                    sequence=30,
                )

    def _check_bom_and_inventory(self):
        StockQuant = self.env['stock.quant']
        today = fields.Date.context_today(self)
        for rec in self:
            bom = rec.bom_id
            if not bom:
                rec._add_line(
                    'bom',
                    'BOM de fabricacion',
                    'block',
                    'No se encontro BOM para este producto.',
                    'Crear BOM corta con hoja impregnada, cassette, buffer/accesorios y empaque.',
                    sequence=100,
                )
                continue
            rec._add_line(
                'bom',
                'BOM de fabricacion',
                'pass',
                bom.display_name,
                related=bom,
                sequence=100,
            )
            if not bom.bom_line_ids:
                rec._add_line(
                    'bom',
                    'Componentes BOM',
                    'block',
                    'La BOM no tiene componentes.',
                    'Agregar insumos antes del piloto.',
                    related=bom,
                    sequence=110,
                )
            else:
                rec._add_line(
                    'bom',
                    'Componentes BOM',
                    'pass',
                    '%s componentes configurados.' % len(bom.bom_line_ids),
                    related=bom,
                    sequence=110,
                )
            if not bom.operation_ids:
                rec._add_line(
                    'bom',
                    'Operaciones / routing',
                    'warn',
                    'La BOM no tiene operaciones. El operador podria no ver trabajo claro en su pantalla.',
                    'Agregar operaciones por area: encartuchado, acondicionado, QC/empaque segun aplique.',
                    related=bom,
                    sequence=120,
                )
            else:
                rec._add_line(
                    'bom',
                    'Operaciones / routing',
                    'pass',
                    '%s operaciones configuradas.' % len(bom.operation_ids),
                    related=bom,
                    sequence=120,
                )
            for operation in bom.operation_ids:
                wc = operation.workcenter_id
                if not wc:
                    rec._add_line(
                        'equipment',
                        'Workcenter en operacion',
                        'block',
                        'La operacion %s no tiene area/workcenter.' % operation.name,
                        'Asignar workcenter real.',
                        related=operation,
                        sequence=130,
                    )
                    continue
                try:
                    wc._amunet_check_equipment_calibration()
                    rec._add_line(
                        'equipment',
                        'Equipo/metrologia: %s' % (wc.code or wc.name),
                        'pass',
                        'Workcenter listo: equipos calibrados o excepcion documentada.',
                        related=wc,
                        sequence=140,
                    )
                except UserError as exc:
                    rec._add_line(
                        'equipment',
                        'Equipo/metrologia: %s' % (wc.code or wc.name),
                        'block',
                        str(exc),
                        'Corregir equipos/calibracion antes de iniciar work orders.',
                        related=wc,
                        sequence=140,
                    )
            factor = 1.0
            if bom.product_qty:
                factor = rec.product_qty / bom.product_qty
            missing = []
            lot_warnings = []
            for line in bom.bom_line_ids:
                product = line.product_id
                required = line.product_qty * factor
                available = product.qty_available
                if product.uom_id and line.product_uom_id and product.uom_id != line.product_uom_id:
                    try:
                        available = product.uom_id._compute_quantity(available, line.product_uom_id)
                    except Exception:
                        available = product.qty_available
                if available + 0.000001 < required:
                    missing.append('%s: requiere %.3f %s, disponible %.3f' % (
                        product.display_name,
                        required,
                        line.product_uom_id.name,
                        available,
                    ))
                if product.tracking != 'none':
                    lot_qty = StockQuant.search_count([
                        ('product_id', '=', product.id),
                        ('lot_id', '!=', False),
                        ('location_id.usage', '=', 'internal'),
                        ('quantity', '>', 0),
                    ])
                    if not lot_qty and available > 0:
                        lot_warnings.append(product.display_name)
            if missing:
                rec._add_line(
                    'inventory',
                    'Inventario de componentes',
                    'block',
                    '\n'.join(missing[:12]),
                    'Comprar, fabricar o ajustar BOM antes de confirmar la MO.',
                    related=bom,
                    sequence=200,
                )
            else:
                rec._add_line(
                    'inventory',
                    'Inventario de componentes',
                    'pass',
                    'Stock suficiente para la cantidad piloto al corte %s.' % today,
                    sequence=200,
                )
            if lot_warnings:
                rec._add_line(
                    'inventory',
                    'Lotes de componentes',
                    'warn',
                    'Productos con stock pero sin lote interno visible: %s' % ', '.join(lot_warnings[:10]),
                    'Confirmar lotes antes de surtir material a produccion.',
                    sequence=210,
                )

    def _check_quality(self):
        SamplingPlan = self.env['amunet.quality.sampling.plan']
        for rec in self:
            tmpl = rec.product_tmpl_id
            qc_required = bool(tmpl.qc_required or getattr(tmpl, 'amunet_req_quality_control', False))
            if qc_required:
                rec._add_line(
                    'quality',
                    'Control de calidad requerido',
                    'pass',
                    'El producto esta marcado como requiere QC.',
                    related=tmpl,
                    sequence=300,
                )
            else:
                rec._add_line(
                    'quality',
                    'Control de calidad requerido',
                    'block',
                    'El producto no esta marcado como requiere QC.',
                    'Activar QC en el producto o documentar por que no aplica.',
                    related=tmpl,
                    sequence=300,
                )
            if tmpl.qc_parameter_count:
                rec._add_line(
                    'quality',
                    'Parametros MAVI/VIMA',
                    'pass',
                    '%s parametros configurados para el producto.' % tmpl.qc_parameter_count,
                    related=tmpl,
                    sequence=310,
                )
            else:
                rec._add_line(
                    'quality',
                    'Parametros MAVI/VIMA',
                    'block' if qc_required else 'warn',
                    'No hay parametros de calidad configurados para este producto.',
                    'Asociar parametros MAVI/VIMA antes del piloto.',
                    related=tmpl,
                    sequence=310,
                )
            plan = SamplingPlan.find_applicable_plan(rec.product_id, rec.product_qty, stage='final_release')
            if plan:
                sample_qty = plan.compute_sample_qty(rec.product_qty)
                rec._add_line(
                    'quality',
                    'Plan de muestreo liberacion final',
                    'pass',
                    '%s: muestra sugerida %.0f de %.0f piezas.' % (
                        plan.display_name,
                        sample_qty,
                        rec.product_qty,
                    ),
                    related=plan,
                    sequence=320,
                )
            else:
                rec._add_line(
                    'quality',
                    'Plan de muestreo liberacion final',
                    'block',
                    'No se encontro plan de muestreo aplicable.',
                    'Crear o ajustar plan de muestreo para familia/producto y cantidad.',
                    sequence=320,
                )

    def _check_packaging(self):
        Presentation = self.env['amunet.packaging.presentation']
        Trend = self.env['amunet.woo.sales.trend']
        for rec in self:
            presentations = Presentation.search([
                ('product_tmpl_id', '=', rec.product_tmpl_id.id),
                ('is_authorized', '=', True),
                ('active', '=', True),
            ], order='package_qty')
            if not presentations:
                rec._add_line(
                    'packaging',
                    'Presentaciones autorizadas',
                    'block',
                    'No hay cajas/presentaciones autorizadas para este producto.',
                    'Crear presentaciones publicadas/autorizadas antes de fabricar.',
                    sequence=400,
                )
                continue
            rec._add_line(
                'packaging',
                'Presentaciones autorizadas',
                'pass',
                ', '.join('%s (%s pzas)' % (p.name, p.package_qty) for p in presentations),
                sequence=400,
            )
            possible = self._can_pack_exact(int(round(rec.product_qty or 0)), [p.package_qty for p in presentations])
            rec._add_line(
                'packaging',
                'Mezcla exacta de empaque',
                'pass' if possible else 'block',
                'La cantidad %s %s empaquetarse con presentaciones autorizadas.' % (
                    int(round(rec.product_qty or 0)),
                    'puede' if possible else 'no puede',
                ),
                'Ajustar cantidad o crear presentacion autorizada.' if not possible else '',
                sequence=410,
            )
            missing_packaging = []
            for p in presentations:
                if p.label_required and not p.label_component_id:
                    missing_packaging.append('%s sin producto etiqueta' % p.name)
                if p.manual_required and not p.manual_component_id:
                    missing_packaging.append('%s sin producto manual/instructivo' % p.name)
            if missing_packaging:
                rec._add_line(
                    'packaging',
                    'Etiquetas y manuales',
                    'warn',
                    '; '.join(missing_packaging[:8]),
                    'Configurar componentes de etiqueta/manual o documentar impresion controlada.',
                    sequence=430,
                )
            else:
                rec._add_line(
                    'packaging',
                    'Etiquetas y manuales',
                    'pass',
                    'Presentaciones con componentes de etiqueta/manual configurados o no requeridos.',
                    sequence=430,
                )

    def _can_pack_exact(self, qty, sizes):
        if qty <= 0:
            return False
        sizes = sorted({int(s) for s in sizes if s and int(s) > 0})
        reachable = {0}
        for used in range(qty + 1):
            if used not in reachable:
                continue
            for size in sizes:
                if used + size <= qty:
                    reachable.add(used + size)
        return qty in reachable

    def _check_people_and_training(self):
        for rec in self:
            role_specs = [
                ('people', 'Supervisor Produccion', rec.production_user_id, 'amunet_production.group_production_supervisor'),
                ('people', 'Analista QC', rec.quality_user_id, 'amunet_quality.group_quality_user'),
                ('people', 'Supervisor QC', rec.quality_supervisor_id, 'amunet_quality.group_quality_supervisor'),
                ('people', 'Almacen', rec.warehouse_user_id, 'amunet_material_request.group_material_warehouse'),
                ('people', 'Empaque / envios', rec.packaging_user_id, 'amunet_packaging_planning.group_packaging_manager'),
            ]
            for section, label, user, group_xmlid in role_specs:
                group = self.env.ref(group_xmlid, raise_if_not_found=False)
                if not user:
                    rec._add_line(
                        section,
                        label,
                        'block',
                        'No hay usuario asignado para este rol.',
                        'Asignar responsable antes del piloto.',
                        sequence=500,
                    )
                    continue
                if group and group not in user.group_ids:
                    rec._add_line(
                        section,
                        label,
                        'block',
                        '%s no pertenece al grupo %s.' % (user.display_name, group.display_name),
                        'Corregir permisos antes del piloto.',
                        related=user,
                        sequence=500,
                    )
                else:
                    rec._add_line(
                        section,
                        label,
                        'pass',
                        '%s tiene permisos para su rol.' % user.display_name,
                        related=user,
                        sequence=500,
                    )
                self._check_training_for_user(rec, label, user)

    def _check_training_for_user(self, rec, label, user):
        if not user:
            return
        records = self.env['amunet.registro.capacitacion'].search([
            ('user_id', '=', user.id),
            ('state', 'in', ('vigente', 'proxima')),
        ], limit=5)
        if records:
            rec._add_line(
                'training',
                'Capacitacion: %s' % label,
                'pass',
                '%s registros vigentes/proximos.' % len(records),
                related=records[0],
                sequence=600,
            )
        else:
            expired = self.env['amunet.registro.capacitacion'].search([
                ('user_id', '=', user.id),
            ], limit=1)
            rec._add_line(
                'training',
                'Capacitacion: %s' % label,
                'warn',
                '%s no tiene capacitacion vigente visible%s.' % (
                    user.display_name,
                    ' (existen registros vencidos/cancelados)' if expired else '',
                ),
                'RRHH/Calidad debe registrar capacitacion o dejar brecha demo documentada.',
                related=user,
                sequence=600,
            )

    def _check_open_changes(self):
        Change = self.env['amunet.change.control']
        for rec in self:
            open_changes = Change.search([
                ('product_id', '=', rec.product_id.id),
                ('state', 'not in', ('closed', 'cancel', 'rejected')),
            ], limit=5)
            if open_changes:
                rec._add_line(
                    'documentation',
                    'Desviaciones/cambios abiertos',
                    'warn',
                    'Hay %s cambio(s) abierto(s) para este producto.' % len(open_changes),
                    'Revisar si afectan manual, gotas, buffer, materiales o empaque del piloto.',
                    related=open_changes[0],
                    sequence=700,
                )
            else:
                rec._add_line(
                    'documentation',
                    'Desviaciones/cambios abiertos',
                    'pass',
                    'No se detectaron cambios abiertos para este producto.',
                    sequence=700,
                )
            tmpl = rec.product_tmpl_id
            if tmpl.report_document_code or tmpl.certificate_document_code:
                rec._add_line(
                    'documentation',
                    'Documentos QC del producto',
                    'pass',
                    'Hay codigo documental de reporte/certificado en el producto.',
                    related=tmpl,
                    sequence=710,
                )
            else:
                rec._add_line(
                    'documentation',
                    'Documentos QC del producto',
                    'warn',
                    'No se detecto codigo documental de reporte/certificado en el producto.',
                    'Documentacion debe confirmar manual/IFU y formatos vigentes antes del piloto.',
                    related=tmpl,
                    sequence=710,
                )


class AmunetPilotPreflightLine(models.Model):
    _name = 'amunet.pilot.preflight.line'
    _description = 'Linea de preflight piloto'
    _order = 'sequence, id'

    preflight_id = fields.Many2one(
        'amunet.pilot.preflight',
        string='Preflight',
        required=True,
        ondelete='cascade',
    )
    sequence = fields.Integer(default=10)
    section = fields.Selection([
        ('master', 'Datos maestros'),
        ('bom', 'BOM / routing'),
        ('inventory', 'Inventario'),
        ('equipment', 'Equipos / metrologia'),
        ('quality', 'Calidad'),
        ('packaging', 'Empaque'),
        ('people', 'Usuarios / permisos'),
        ('training', 'Capacitacion'),
        ('documentation', 'Documentacion'),
    ], string='Area', required=True, default='master')
    name = fields.Char(string='Chequeo', required=True)
    status = fields.Selection([
        ('pass', 'OK'),
        ('warn', 'Advertencia'),
        ('block', 'Bloqueo'),
        ('na', 'No aplica'),
    ], string='Resultado', required=True, default='na')
    detail = fields.Text(string='Detalle')
    action_hint = fields.Text(string='Que hacer')
    related_model_id = fields.Many2one('ir.model', string='Modelo relacionado')
    related_res_id = fields.Integer(string='ID relacionado')

    def action_open_related(self):
        self.ensure_one()
        if not self.related_model_id or not self.related_res_id:
            return False
        return {
            'type': 'ir.actions.act_window',
            'name': self.related_model_id.name,
            'res_model': self.related_model_id.model,
            'view_mode': 'form',
            'res_id': self.related_res_id,
            'target': 'current',
        }
