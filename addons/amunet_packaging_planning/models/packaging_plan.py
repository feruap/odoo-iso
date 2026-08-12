# -*- coding: utf-8 -*-

import re
import base64

from odoo import api, fields, models, _
from odoo.exceptions import UserError, ValidationError


class AmunetPackagingPlan(models.Model):
    _name = 'amunet.packaging.plan'
    _description = 'Plan de empaque por orden de fabricacion'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'create_date desc, id desc'

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
        required=True,
        tracking=True,
    )
    product_id = fields.Many2one(
        'product.product',
        string='Producto',
        related='production_id.product_id',
        store=True,
        readonly=True,
    )
    product_tmpl_id = fields.Many2one(
        'product.template',
        string='Producto maestro',
        related='product_id.product_tmpl_id',
        store=True,
        readonly=True,
    )
    product_qty = fields.Float(
        string='Piezas teóricas a empacar',
        related='production_id.product_qty',
        readonly=True,
    )
    lot_name = fields.Char(
        string='Lote',
        compute='_compute_lot_name',
        store=True,
        readonly=False,
        tracking=True,
    )
    expiration_text = fields.Char(
        string='Caducidad',
        compute='_compute_lot_name',
        store=True,
        readonly=True,
    )

    trend_months = fields.Integer(string='Meses de tendencia', default=6, required=True)
    trend_date_from = fields.Date(string='Desde (fecha)', compute='_compute_trend_dates', store=True)
    trend_date_to = fields.Date(string='Hasta (fecha)', compute='_compute_trend_dates', store=True)
    trend_date_from_display = fields.Char(
        string='Desde',
        compute='_compute_trend_dates_display',
        store=True,
    )
    trend_date_to_display = fields.Char(
        string='Hasta',
        compute='_compute_trend_dates_display',
        store=True,
    )
    trend_source_note = fields.Text(string='Fuente / criterio de tendencia')

    state = fields.Selection([
        ('draft', 'Borrador'),
        ('suggested', 'Sugerido'),
        ('approved', 'Aprobado'),
        ('done', 'Cerrado'),
        ('cancel', 'Cancelado'),
    ], string='Estado', default='draft', required=True, tracking=True)

    line_ids = fields.One2many(
        'amunet.packaging.plan.line',
        'plan_id',
        string='Mezcla de empaque',
        copy=True,
    )
    total_approved_pieces = fields.Float(
        string='Piezas planeadas',
        compute='_compute_totals',
    )
    total_approved_boxes = fields.Float(
        string='Cajas planeadas',
        compute='_compute_totals',
    )
    total_suggested_pieces = fields.Float(
        string='Piezas sugeridas',
        compute='_compute_totals',
    )
    has_exact_mix = fields.Boolean(
        string='Mezcla exacta',
        compute='_compute_totals',
    )
    allow_mix_exception = fields.Boolean(
        string='Autorizar mezcla distinta a la orden',
        help='Excepcion: permite aprobar aunque la mezcla no sume exactamente '
             'la cantidad de la orden (ej. empacar mas de lo que produce la '
             'orden para un pedido especial). Requiere capturar el motivo. '
             'Queda registrado en el historial al aprobar.')
    mix_exception_reason = fields.Text(string='Motivo de la excepcion de mezcla')
    approved_by_id = fields.Many2one('res.users', string='Aprobado por', readonly=True)
    approved_date = fields.Datetime(string='Fecha aprobacion', readonly=True)
    closed_by_id = fields.Many2one('res.users', string='Cerrado por', readonly=True)
    closed_date = fields.Datetime(string='Fecha cierre', readonly=True)
    notes = fields.Html(string='Notas')

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if vals.get('name', 'Nuevo') == 'Nuevo':
                vals['name'] = self._amunet_next_pe_folio()
        return super().create(vals_list)

    @api.model
    def _amunet_next_pe_folio(self):
        """Folio PE con reinicio mensual y a prueba de -u: PE/MMYY/##### donde
        ##### = (maximo existente para ese mes) + 1. NO usa ir.sequence (que se
        reiniciaba a 1 con cada actualizacion del modulo -> folios duplicados).
        Como el prefijo lleva el mes+anio (%m%y), el consecutivo reinicia solo a
        00001 al empezar un mes nuevo. Patron identico al numerador de lotes."""
        today = fields.Date.context_today(self)
        prefix = 'PE/%s%s/' % (today.strftime('%m'), today.strftime('%y'))
        plen = len(prefix)
        maxn = 0
        for nm in self.sudo().search([('name', '=like', prefix + '%')]).mapped('name'):
            core = (nm or '')[plen:]
            if core.isdigit():
                maxn = max(maxn, int(core))
        return '%s%05d' % (prefix, maxn + 1)

    @api.depends('production_id.solution_lot_id', 'production_id.lot_producing_ids', 'production_id.amunet_expiration_text')
    def _compute_lot_name(self):
        for rec in self:
            lots = rec.production_id.lot_producing_ids.mapped('name')
            rec.lot_name = ', '.join(lots) or rec.production_id.solution_lot_id or ''
            rec.expiration_text = rec.production_id.amunet_expiration_text or ''

    @api.depends('trend_months')
    def _compute_trend_dates(self):
        from dateutil.relativedelta import relativedelta
        today = fields.Date.context_today(self)
        for rec in self:
            months = rec.trend_months or 6
            rec.trend_date_to = today
            rec.trend_date_from = today - relativedelta(months=months)

    @api.depends('trend_date_from', 'trend_date_to')
    def _compute_trend_dates_display(self):
        for rec in self:
            rec.trend_date_from_display = rec.trend_date_from.strftime('%d.%m.%y') if rec.trend_date_from else ''
            rec.trend_date_to_display = rec.trend_date_to.strftime('%d.%m.%y') if rec.trend_date_to else ''

    @api.depends('line_ids.suggested_box_qty', 'line_ids.suggested_piece_qty', 'line_ids.approved_box_qty', 'line_ids.approved_piece_qty', 'product_qty')
    def _compute_totals(self):
        for rec in self:
            rec.total_suggested_pieces = sum(rec.line_ids.mapped('suggested_piece_qty'))
            rec.total_approved_pieces = sum(rec.line_ids.mapped('approved_piece_qty'))
            rec.total_approved_boxes = sum(rec.line_ids.mapped('approved_box_qty'))
            rec.has_exact_mix = abs((rec.total_approved_pieces or 0.0) - (rec.product_qty or 0.0)) < 0.0001

    def _require_manager(self):
        if not (
            self.env.user.has_group('amunet_packaging_planning.group_packaging_manager')
            or self.env.user.has_group('amunet_production.group_production_supervisor')
            or self.env.user.has_group('amunet_quality.group_quality_supervisor')
            or self.env.user.has_group('amunet_quality.group_quality_manager')
        ):
            raise UserError(_('No tiene permisos para aprobar o cerrar planes de empaque.'))

    def _amunet_signature_allowed_methods(self):
        return {
            '_signature_action_approve': _('Aprobar plan de empaque'),
            '_signature_action_close': _('Cerrar plan de empaque'),
        }

    def _authorized_presentations(self):
        self.ensure_one()
        presentations = self.env['amunet.packaging.presentation'].search([
            ('product_tmpl_id', '=', self.product_tmpl_id.id),
            ('is_authorized', '=', True),
            ('active', '=', True),
        ], order='package_qty desc, id')
        if not presentations:
            raise UserError(_(
                'No hay presentaciones autorizadas para %s. Configure caja c/5, c/20 u otras presentaciones antes de planear.'
            ) % self.product_id.display_name)
        return presentations

    def _trend_by_presentation(self, presentations):
        self.ensure_one()
        trends = self.env['amunet.woo.sales.trend'].read_group(
            [
                ('presentation_id', 'in', presentations.ids),
                ('sale_date', '>=', self.trend_date_from),
                ('sale_date', '<=', self.trend_date_to),
            ],
            ['piece_qty:sum', 'box_qty:sum'],
            ['presentation_id'],
        )
        by_id = {
            row['presentation_id'][0]: {
                'piece_qty': row.get('piece_qty') or 0.0,
                'box_qty': row.get('box_qty') or 0.0,
            }
            for row in trends
            if row.get('presentation_id')
        }
        return by_id

    def _solve_mix(self, target_qty, presentations, trend_by_id):
        """Integer exact mix nearest to Woo piece-ratio targets."""
        target_qty = int(round(target_qty or 0))
        if target_qty <= 0:
            raise UserError(_('La orden no tiene cantidad a empacar.'))

        trend_total = sum((trend_by_id.get(p.id, {}).get('piece_qty') or 0.0) for p in presentations)
        if trend_total <= 0:
            targets = {p.id: target_qty / float(len(presentations)) for p in presentations}
        else:
            targets = {
                p.id: target_qty * (trend_by_id.get(p.id, {}).get('piece_qty') or 0.0) / trend_total
                for p in presentations
            }

        dp = {0: (0.0, {})}
        for presentation in presentations:
            size = presentation.package_qty
            next_dp = {}
            for used, (cost, counts) in dp.items():
                remaining = target_qty - used
                for boxes in range(0, (remaining // size) + 1):
                    pieces = boxes * size
                    new_used = used + pieces
                    new_cost = cost + abs(pieces - targets[presentation.id])
                    new_counts = dict(counts)
                    new_counts[presentation.id] = boxes
                    previous = next_dp.get(new_used)
                    if previous is None or new_cost < previous[0]:
                        next_dp[new_used] = (new_cost, new_counts)
            dp = next_dp

        if target_qty not in dp:
            sizes = ', '.join(str(p.package_qty) for p in presentations)
            raise UserError(_(
                'No existe combinacion exacta para %s piezas con presentaciones: %s. Ajuste cantidad o agregue una presentacion autorizada.'
            ) % (target_qty, sizes))
        return dp[target_qty][1], targets, trend_total

    def action_generate_suggestion(self):
        for rec in self:
            presentations = rec._authorized_presentations()
            trend_by_id = rec._trend_by_presentation(presentations)
            counts, targets, trend_total = rec._solve_mix(rec.product_qty, presentations, trend_by_id)
            rec.line_ids.unlink()
            line_commands = []
            for presentation in presentations:
                boxes = counts.get(presentation.id, 0)
                if boxes <= 0 and not trend_by_id.get(presentation.id, {}).get('piece_qty'):
                    continue
                trend_piece_qty = trend_by_id.get(presentation.id, {}).get('piece_qty') or 0.0
                ratio = trend_piece_qty / trend_total if trend_total else 0.0
                line_commands.append((0, 0, {
                    'presentation_id': presentation.id,
                    'trend_piece_qty': trend_piece_qty,
                    'trend_ratio': ratio,
                    'target_piece_qty': targets[presentation.id],
                    'suggested_box_qty': boxes,
                    'approved_box_qty': boxes,
                }))
            rec.write({
                'line_ids': line_commands,
                'state': 'suggested',
                'trend_source_note': _(
                    'Sugerencia calculada con ventas WooCommerce de los ultimos %s meses. Woo sugiere demanda; Odoo valida presentaciones autorizadas.'
                ) % rec.trend_months,
            })
            rec.message_post(body=_('Mezcla sugerida a partir de tendencia WooCommerce.'))

    def action_approve(self):
        self.ensure_one()
        self._check_can_approve()
        return self.env['amunet.generic.signature.wizard'].open_for(
            self,
            '_signature_action_approve',
            _('Aprobar plan de empaque'),
            _('Firma de aprobacion del plan %s.') % self.name,
        )

    def _check_can_approve(self):
        for rec in self:
            rec._require_manager()
            if not rec.line_ids:
                raise UserError(_('Genere o capture una mezcla antes de aprobar.'))
            if not rec.has_exact_mix:
                if not rec.allow_mix_exception:
                    raise UserError(_(
                        'La mezcla aprobada debe sumar exactamente %s piezas. Actualmente suma %s.'
                    ) % (rec.product_qty, rec.total_approved_pieces))
                if not (rec.mix_exception_reason or '').strip():
                    raise UserError(_(
                        'Para aprobar con una mezcla distinta a la orden '
                        '(%s vs %s piezas) debes capturar el motivo de la excepcion.'
                    ) % (rec.total_approved_pieces, rec.product_qty))
            # 3B: solo se puede aprobar/modificar el plan si la MO esta en draft o confirmed
            if rec.production_id.state not in ('draft', 'confirmed'):
                raise UserError(_(
                    'No se puede aprobar el plan: la orden de fabricacion %(mo)s '
                    'esta en estado "%(state)s". Solo se puede aprobar cuando la '
                    'orden esta en Borrador o Confirmada.'
                ) % {'mo': rec.production_id.name, 'state': rec.production_id.state})
            # 2B: cada linea con aprobada > 0 debe tener componentes secundarios configurados
            for line in rec.line_ids.filtered(lambda l: l.approved_box_qty > 0):
                if not line.presentation_id.component_ids:
                    raise UserError(_(
                        'La presentacion "%(pres)s" no tiene componentes secundarios '
                        'configurados (caja, instructivo, vial, etc.). Configurarlos '
                        'antes de aprobar el plan.\n\nIr a Configuracion > Presentaciones '
                        'y editar la presentacion para agregarle componentes.'
                    ) % {'pres': line.presentation_id.name})

    def _signature_action_approve(self):
        self.ensure_one()
        self._check_can_approve()
        for rec in self:
            rec._sync_secondary_components_to_production()
            rec.with_context(amunet_packaging_signature_write=True).write({
                'state': 'approved',
                'approved_by_id': self.env.user.id,
                'approved_date': fields.Datetime.now(),
            })
            if not rec.has_exact_mix and rec.allow_mix_exception:
                rec.message_post(body=_(
                    'EXCEPCION DE MEZCLA autorizada por %(u)s: la orden produce '
                    '%(p)s piezas pero la mezcla empaca %(m)s. Motivo: %(r)s'
                ) % {'u': self.env.user.name, 'p': rec.product_qty,
                     'm': rec.total_approved_pieces,
                     'r': rec.mix_exception_reason or ''})
            rec.message_post(body=_('Plan de empaque aprobado. Componentes secundarios sincronizados con la orden.'))

    def _sync_secondary_components_to_production(self):
        """Por cada linea aprobada del plan, sumar componentes secundarios de
        la presentacion (qty = approved_box_qty * qty_per_box) y aplicarlos
        a los move_raw_ids de la MO: si el producto ya existe como move, se
        actualiza product_uom_qty; si no, se crea un move nuevo.
        Incluye box_component_id, label_component_id y manual_component_id
        (1 unidad por caja) ademas de los component_ids secundarios.
        """
        self.ensure_one()
        needed = {}  # product_id -> qty total
        for line in self.line_ids.filtered(lambda l: l.approved_box_qty > 0):
            pres = line.presentation_id
            # Componentes principales: caja, funda, instructivo (1 por caja)
            for prod in filter(None, [pres.box_component_id, pres.label_component_id, pres.manual_component_id]):
                needed[prod.id] = needed.get(prod.id, 0.0) + line.approved_box_qty
            # Componentes secundarios con su qty_per_box
            for comp in pres.component_ids:
                qty = line.approved_box_qty * (comp.qty_per_box or 1.0)
                needed[comp.product_id.id] = needed.get(comp.product_id.id, 0.0) + qty

        production = self.production_id
        existing_by_product = {m.product_id.id: m for m in production.move_raw_ids}
        for product_id, qty in needed.items():
            move = existing_by_product.get(product_id)
            if move:
                move.product_uom_qty = qty
            else:
                product = self.env['product.product'].browse(product_id)
                production.move_raw_ids = [(0, 0, {
                    'product_id': product.id,
                    'product_uom_qty': qty,
                    'product_uom': product.uom_id.id,
                    'location_id': production.location_src_id.id,
                    'location_dest_id': production.production_location_id.id,
                    'raw_material_production_id': production.id,
                    'origin': production.name,
                    'company_id': production.company_id.id,
                })]

    def action_close(self):
        self.ensure_one()
        self._check_can_close()
        return self.env['amunet.generic.signature.wizard'].open_for(
            self,
            '_signature_action_close',
            _('Cerrar plan de empaque'),
            _('Firma de cierre del plan %s.') % self.name,
        )

    def _check_can_close(self):
        for rec in self:
            rec._require_manager()
            if rec.state != 'approved':
                raise UserError(_('Solo puede cerrar un plan aprobado.'))

    def _signature_action_close(self):
        self.ensure_one()
        self._check_can_close()
        for rec in self:
            rec.with_context(amunet_packaging_signature_write=True).write({
                'state': 'done',
                'closed_by_id': self.env.user.id,
                'closed_date': fields.Datetime.now(),
            })
            rec.message_post(body=_('Plan de empaque cerrado.'))

    def action_cancel(self):
        self.write({'state': 'cancel'})

    def write(self, vals):
        signature_fields = {'approved_by_id', 'approved_date', 'closed_by_id', 'closed_date'}
        signature_state = vals.get('state') in ('approved', 'done')
        if (
            (signature_state or set(vals).intersection(signature_fields))
            and not self.env.context.get('amunet_packaging_signature_write')
            and not self.env.su
        ):
            raise UserError(_(
                'Las aprobaciones y cierres de empaque solo pueden registrarse '
                'desde el wizard de firma electronica.'
            ))
        return super().write(vals)

    # Cajas genericas: llevan la etiqueta GRANDE (S/H/P/M). Cualquier otra caja
    # caple (especifica de un producto) ya viene pre-impresa -> etiqueta chica
    # (Plantilla A). MICAJ15 es generica pero pendiente de su etiqueta chica
    # propia; por ahora se trata como grande.
    _CAJAS_GENERICAS = ('MICAJ01', 'MICAJ15')

    def _caja_micaj_de_presentacion(self, pres):
        """Devuelve el default_code de la caja MICAJ de la presentacion (de sus
        componentes o box_component_id), o '' si no tiene."""
        for comp in pres.component_ids:
            code = comp.product_id.default_code or ''
            if code.startswith('MICAJ'):
                return code
        bc = pres.box_component_id
        if bc and (bc.default_code or '').startswith('MICAJ'):
            return bc.default_code
        return ''

    def action_generar_etiquetas_caja(self):
        """Genera UN PPTX con las etiquetas de CAJA de ESTE plan y lo descarga.
        Por cada linea decide la etiqueta segun la caja de la presentacion:
        caja generica -> etiqueta grande S/H/P/M; caja especifica (pre-impresa)
        -> etiqueta chica (Plantilla A). Usa el motor de amunet_label."""
        self.ensure_one()
        mo = self.production_id
        if not mo:
            raise UserError(_('El plan no tiene orden de fabricacion.'))
        plan_lineas = self.line_ids.filtered(lambda l: l.approved_box_qty > 0)
        if not plan_lineas:
            raise UserError(_('El plan no tiene cajas aprobadas para etiquetar.'))

        bloques = []
        for ln in plan_lineas:
            caja = self._caja_micaj_de_presentacion(ln.presentation_id)
            tipo = 'A' if (caja and caja not in self._CAJAS_GENERICAS) else 'grande'
            bloques.append({
                'tipo': tipo,
                'n': ln.package_qty,
                'cajas': ln.approved_box_qty,
            })

        subtipo, lot_name, datos = mo._etiqueta_datos()
        contenido = mo._etiqueta_construir_pptx(subtipo, datos, bloques)

        total = sum(b['cajas'] for b in bloques)
        safe = re.sub(r'[/\\:*?"<>|]', '-', lot_name or self.name)
        ref = mo.product_id.default_code or 'SREF'
        Attachment = self.env['ir.attachment']
        # Reemplaza el archivo previo de este plan para no acumular.
        Attachment.search([
            ('res_model', '=', 'amunet.packaging.plan'),
            ('res_id', '=', self.id),
            ('name', '=like', 'Etiquetas_%.pptx'),
        ]).unlink()
        nombre = 'Etiquetas_%s_%s_%setiq.pptx' % (ref, safe, total)
        att = Attachment.create({
            'name': nombre,
            'type': 'binary',
            'datas': base64.b64encode(contenido),
            'mimetype': ('application/vnd.openxmlformats-officedocument'
                         '.presentationml.presentation'),
            'res_model': 'amunet.packaging.plan',
            'res_id': self.id,
        })
        # --- Etiquetas de BUFFER: se anexan al MISMO plan (misma lista) ---
        Attachment.search([
            ('res_model', '=', 'amunet.packaging.plan'),
            ('res_id', '=', self.id),
            ('name', '=like', 'Etiquetas_Buffer_%.pptx'),
        ]).unlink()
        buffer_msgs = []
        for plantilla, valores in mo._etiqueta_buffers_de_orden(num_cajas=total).items():
            if not valores:
                continue
            contenido_b = mo._etiqueta_construir_buffer_pptx(plantilla, valores)
            nombre_b = 'Etiquetas_Buffer_%s_%s_%setiq.pptx' % (
                plantilla, safe, len(valores))
            Attachment.create({
                'name': nombre_b,
                'type': 'binary',
                'datas': base64.b64encode(contenido_b),
                'mimetype': ('application/vnd.openxmlformats-officedocument'
                             '.presentationml.presentation'),
                'res_model': 'amunet.packaging.plan',
                'res_id': self.id,
            })
            buffer_msgs.append('%s (%s etiq)' % (plantilla, len(valores)))

        resumen = ', '.join(
            '%s cajas de %s pzas (%s)' % (
                b['cajas'], b['n'],
                'chica' if b['tipo'] == 'A' else 'grande')
            for b in bloques)
        cuerpo = _(
            'Etiquetas de caja generadas: %(cant)s en un archivo (%(resumen)s).',
            cant=total, resumen=resumen)
        if buffer_msgs:
            cuerpo += _(' Etiquetas de buffer anexas: %s.') % ', '.join(buffer_msgs)
        self.message_post(body=cuerpo)
        return {
            'type': 'ir.actions.act_url',
            'url': '/web/content/%s?download=true' % att.id,
            'target': 'self',
        }

    def action_open_label_wizard(self):
        self.ensure_one()
        first_line = self.line_ids.filtered(lambda line: line.approved_box_qty > 0)[:1]
        if not first_line:
            raise UserError(_('No hay cajas aprobadas para imprimir etiquetas.'))
        product = first_line.presentation_id.product_id or self.product_id
        return {
            'type': 'ir.actions.act_window',
            'name': _('Generar etiquetas'),
            'res_model': 'amunet.label.print.wizard',
            'view_mode': 'form',
            'target': 'new',
            'context': {
                'default_product_id': product.id,
                'default_lot_name': self.lot_name,
                'default_expiration_date_text': self.expiration_text,
                'default_quantity': int(first_line.approved_box_qty),
            },
        }


class AmunetPackagingPlanLine(models.Model):
    _name = 'amunet.packaging.plan.line'
    _description = 'Linea de plan de empaque'
    _order = 'package_qty desc, id'

    plan_id = fields.Many2one(
        'amunet.packaging.plan',
        string='Plan',
        required=True,
        ondelete='cascade',
    )
    presentation_id = fields.Many2one(
        'amunet.packaging.presentation',
        string='Presentacion',
        required=True,
    )
    package_qty = fields.Integer(
        related='presentation_id.package_qty',
        string='Pruebas por caja',
        store=True,
        readonly=True,
    )
    trend_piece_qty = fields.Float(string='Piezas vendidas Woo')
    trend_ratio = fields.Float(string='% tendencia')
    target_piece_qty = fields.Float(string='Objetivo por tendencia')

    suggested_box_qty = fields.Integer(string='Cajas sugeridas')
    suggested_piece_qty = fields.Integer(
        string='Piezas sugeridas',
        compute='_compute_pieces',
        store=True,
    )
    approved_box_qty = fields.Integer(string='Cajas planeadas')
    approved_piece_qty = fields.Integer(
        string='Piezas planeadas',
        compute='_compute_pieces',
        store=True,
    )
    label_qty = fields.Integer(
        string='Etiquetas a imprimir',
        compute='_compute_pieces',
        store=True,
    )
    manual_qty = fields.Integer(
        string='Manuales a surtir/imprimir',
        compute='_compute_pieces',
        store=True,
    )

    @api.depends('suggested_box_qty', 'approved_box_qty', 'package_qty')
    def _compute_pieces(self):
        for line in self:
            line.suggested_piece_qty = (line.suggested_box_qty or 0) * (line.package_qty or 0)
            line.approved_piece_qty = (line.approved_box_qty or 0) * (line.package_qty or 0)
            line.label_qty = line.approved_box_qty or 0
            line.manual_qty = line.approved_box_qty or 0

    @api.constrains('suggested_box_qty', 'approved_box_qty')
    def _check_box_qty(self):
        for line in self:
            if line.suggested_box_qty < 0 or line.approved_box_qty < 0:
                raise ValidationError(_('Las cajas no pueden ser negativas.'))
