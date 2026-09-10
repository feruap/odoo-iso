# -*- coding: utf-8 -*-
from odoo import models, fields, api, _
from odoo.exceptions import UserError


class MrpProduction(models.Model):
    _inherit = 'mrp.production'

    # ============================
    # Relacion con inspecciones
    # ============================
    process_inspection_ids = fields.One2many(
        'amunet.process.inspection', 'production_id',
        string='Controles en proceso',
    )
    # Listas separadas (separacion ligera): una Supervision NO es una
    # inspeccion, se muestran en bloques distintos.
    inspection_qc_ids = fields.One2many(
        'amunet.process.inspection', 'production_id',
        string='Inspecciones en proceso',
        domain=[('inspection_type', '=', 'qc_formal')],
    )
    inspection_sup_ids = fields.One2many(
        'amunet.process.inspection', 'production_id',
        string='Supervisiones',
        domain=[('inspection_type', '=', 'production_supervision')],
    )
    process_inspection_count = fields.Integer(
        string='Controles en proceso',
        compute='_compute_process_inspection_count',
    )

    @api.depends('process_inspection_ids')
    def _compute_process_inspection_count(self):
        for rec in self:
            rec.process_inspection_count = len(rec.process_inspection_ids)

    # ============================
    # Linea (corta / larga)
    # ============================
    route_type = fields.Selection(
        selection=[
            ('short', 'Linea Corta'),
            ('long', 'Linea Larga / hoja'),
            ('solution', 'Soluciones'),
            ('resale', 'Compra y reventa'),
        ],
        string='Linea de produccion', default='short',
        tracking=True,
        help='Define el flujo SGC aplicable a esta orden. Por defecto '
             'Linea Corta.',
    )

    # ============================
    # Etapas de LINEA LARGA (L1 - L4)
    # ============================
    # Antes se le decia "linea larga" a todo el proceso de fabricar la hoja.
    # Desde sep-2026 se divide en cuatro lineas encadenadas. Las cuatro
    # siguen siendo linea larga, y por lo tanto produccion:
    #
    #   Soluciones   ya opera (hoy con su propio flujo, route_type='solution')
    #   Conjugados
    #   Inyeccion
    #   Laminado
    #
    # El orden de la lista es el orden real del proceso. NO se numeran: la
    # numeracion L1-L4 fue solo la forma de nombrarlas al describirlas, no
    # como deben aparecerle al usuario (Mery, 08-sep-2026).
    #
    # Va APARTE de route_type a proposito. route_type define el FLUJO de la
    # orden -- que gates aplican, que inspecciones nacen, que botones se ven --
    # y hoy gobierna las 96 ordenes que ya corrieron. Este campo dice en que
    # ETAPA de la linea larga esta la orden. Meter L1-L4 dentro de route_type
    # habria cambiado el flujo de ordenes vivas, que es justo lo que no se
    # debe mover.
    amunet_sublinea = fields.Selection(
        selection=[
            ('soluciones', 'Soluciones'),
            ('conjugados', 'Conjugados'),
            ('inyeccion', 'Inyección'),
            ('laminado', 'Laminado'),
        ],
        string='Etapa de linea larga',
        tracking=True,
        help='Etapa de la linea larga a la que pertenece esta orden. Las '
             'cuatro son linea larga y son produccion. Se deja vacio en las '
             'ordenes de linea corta y de compra-reventa.',
    )

    @api.onchange('route_type')
    def _amunet_onchange_route_type_sublinea(self):
        """Soluciones ES la L1: se rellena sola, y se limpia si no aplica."""
        for rec in self:
            if rec.route_type == 'solution':
                if not rec.amunet_sublinea:
                    rec.amunet_sublinea = 'soluciones'
            elif rec.route_type in ('short', 'resale'):
                rec.amunet_sublinea = False

    # ============================
    # Gating Linea Corta (solo ordenes nuevas)
    # ============================
    amunet_lc_gating = fields.Boolean(
        string='Aplica reglas de secuencia Linea Corta',
        default=False, copy=False,
        help='Si esta activo, la orden aplica el gating de Linea Corta: '
             '(A) el Surtido debe estar entregado antes de iniciar la '
             'produccion; (B) cada paso solo inicia si el anterior ya '
             'inicio; (C) la orden solo cierra con todas las actividades '
             'terminadas y todas las supervisiones e inspecciones firmadas. '
             'Se activa automaticamente solo en ordenes NUEVAS de ruta '
             'corta; las ordenes existentes quedan exentas.',
    )

    # ============================
    # Vinculacion con preflight
    # ============================
    preflight_ids = fields.One2many(
        'amunet.pilot.preflight', 'production_id',
        string='Preflights asociados',
    )
    preflight_approved = fields.Boolean(
        string='Preflight aprobado',
        compute='_compute_preflight_approved', store=False,
        help='True si existe al menos un preflight en estado '
             '"Aceptado para piloto" para esta orden.',
    )

    @api.depends('preflight_ids.state')
    def _compute_preflight_approved(self):
        for rec in self:
            rec.preflight_approved = any(
                p.state == 'accepted' for p in rec.preflight_ids
            )

    # ============================
    # Acciones
    # ============================
    def action_view_process_inspections(self):
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': _('Inspecciones de proceso'),
            'res_model': 'amunet.process.inspection',
            'view_mode': 'list,form',
            'domain': [('production_id', '=', self.id)],
            'context': {
                'default_production_id': self.id,
                'search_default_production_id': self.id,
            },
        }

    # ============================
    # Marcar ordenes NUEVAS de ruta corta para el gating
    # ============================
    @api.model_create_multi
    def create(self, vals_list):
        records = super().create(vals_list)
        for rec in records:
            if rec.route_type == 'short' and not rec.amunet_lc_gating:
                rec.amunet_lc_gating = True
        # Antes habia un segundo `create` mas abajo en esta misma clase que
        # pisaba a este: el gating de Linea Corta nunca se activaba.
        records._amunet_check_solution_maker()
        return records

    # ============================
    # Responsable de una SOLUCION = quien la elabora
    # ============================
    # En linea corta el responsable es quien planea la orden. En Soluciones no:
    # el responsable es la persona que fisicamente prepara la solucion, porque
    # es quien responde por ella (Mery, 08-sep-2026).
    #
    # Hay dos formas de llegar aqui y las dos quedan cubiertas:
    #   - Desde la tableta del area: la persona se identifica con su PIN y el
    #     kiosco llama a este metodo con ese operador. El usuario conectado es
    #     la tableta, que NO sirve como responsable.
    #   - Desde la sesion de cada quien: al confirmar la orden, el responsable
    #     pasa a ser quien confirma, si es del grupo de Soluciones.
    def _amunet_set_responsable_solucion(self, persona):
        """Deja a `persona` como responsable de las ordenes de solucion."""
        if not persona:
            return
        for mo in self:
            if mo.route_type != 'solution' and not mo.amunet_is_solution_product:
                continue
            if mo.user_id == persona:
                continue
            anterior = mo.user_id
            mo.sudo().write({'user_id': persona.id})
            mo.sudo().message_post(body=_(
                'Responsable de la elaboracion: <b>%(nuevo)s</b>%(antes)s'
            ) % {
                'nuevo': persona.name,
                'antes': (' (antes %s)' % anterior.name) if anterior else '',
            })

    # ============================
    # Gate de CIERRE (C): no cerrar sin actividades terminadas y
    # sin todas las supervisiones e inspecciones firmadas.
    # ============================
    def _amunet_lc_check_close_gate(self):
        for mo in self:
            if not mo.amunet_lc_gating:
                continue
            pendientes = mo.workorder_ids.filtered(
                lambda w: w.state not in ('done', 'cancel'))
            sin_firmar = mo.process_inspection_ids.filtered(
                lambda i: i.state not in ('signed', 'cancel'))
            if not pendientes and not sin_firmar:
                continue
            msg = _('No se puede cerrar la orden %s todavia:') % mo.name
            if pendientes:
                msg += _('\n\nFaltan actividades por TERMINAR:\n- %s') % (
                    '\n- '.join(pendientes.mapped('display_name')))
            if sin_firmar:
                tipos = {
                    'production_supervision': 'Supervision',
                    'qc_formal': 'Inspeccion en proceso',
                }
                faltan = []
                for i in sin_firmar:
                    etq = i.workorder_id.display_name or (
                        i.workcenter_id.name or '')
                    faltan.append('%s - %s' % (
                        tipos.get(i.inspection_type, i.inspection_type), etq))
                msg += _('\n\nFaltan FIRMAS (supervisiones / inspecciones):'
                         '\n- %s') % '\n- '.join(faltan)
            raise UserError(msg)

    # ============================
    # Candado: solo el personal autorizado de Soluciones (grupo
    # group_solution_maker) puede FABRICAR ordenes de solucion, es decir
    # crearlas, confirmarlas o producirlas. Mery y Fernando (superuser /
    # miembros del grupo) pasan. Un supervisor de Linea Corta que no sea
    # fabricante puede VER la orden pero no actuar sobre ella.
    # ============================
    def _amunet_check_solution_maker(self):
        if self.env.su or self.env.user.has_group(
                'amunet_production.group_solution_maker'):
            return
        sols = self.filtered(
            lambda m: m.route_type == 'solution' or m.amunet_is_solution_product)
        if sols:
            raise UserError(_(
                'Solo el personal autorizado de Soluciones puede fabricar '
                'esta orden (%s).\n\n'
                'Actualmente fabrican soluciones: Julissa y Alondra. Si '
                'necesitas acceso, pideselo a Fernando o Mery.'
            ) % ', '.join(sols.mapped('name')))

    def _amunet_check_solution_equipment(self):
        """Al PRODUCIR una solucion, valida que los equipos que usan sus
        actividades (Balanza=pesado, Agitador=disolucion, Analizador=pH) esten
        operativos y con calibracion vigente. Las soluciones NO usan operaciones
        de ruta, por eso el candado es a nivel orden (no por workorder).
        Configurable por parametro de sistema amunet.solution.equipment.serials
        (por defecto PRO/BAL/01,PRO/AGI/01,PRO/AMO/01). Respeta el periodo de
        gracia global de calibracion (via _amunet_calibration_problems_for)."""
        if self.env.su:
            return
        sols = self.filtered(
            lambda m: m.route_type == 'solution' or m.amunet_is_solution_product)
        if not sols:
            return
        serials = self.env['ir.config_parameter'].sudo().get_param(
            'amunet.solution.equipment.serials',
            'PRO/BAL/01,PRO/AGI/01,PRO/AMO/01')
        serials = [s.strip() for s in (serials or '').split(',') if s.strip()]
        if not serials:
            return
        equipos = self.env['amunet.equipment'].sudo().search(
            [('serial_number', 'in', serials)])
        problemas = self.env['mrp.workcenter']._amunet_calibration_problems_for(
            equipos, 'Soluciones')
        for f in sorted(set(serials) - set(equipos.mapped('serial_number'))):
            problemas.append(' - Equipo %s no existe en el catalogo' % f)
        if problemas:
            raise UserError(_(
                'No se puede producir la solucion. Equipos de Soluciones sin '
                'calibracion vigente o no operativos:\n%s\n\n'
                'Sube certificados de calibracion vigentes o reactiva los '
                'equipos antes de producir.'
            ) % '\n'.join(problemas))

    def button_mark_done(self):
        self._amunet_check_solution_maker()
        self._amunet_check_solution_equipment()
        self._amunet_lc_check_close_gate()
        return super().button_mark_done()

    # ============================
    # Override action_confirm: gate preflight
    # (las inspecciones YA NO se generan al confirmar; ver button_plan)
    # ============================
    def _amunet_solution_moves_from_aru(self):
        """Para ordenes de SOLUCION, los componentes cuya categoria enruta al
        Almacen de reactivos en uso (ARU) se consumen desde ARU/Stock, no desde
        el almacen general. El agua y las sub-soluciones (que no son reactivos)
        siguen desde su ubicacion normal. Se corre tras confirmar."""
        wh = self.env['stock.warehouse'].sudo().search(
            [('code', '=', 'ARU')], limit=1)
        if not wh:
            return
        aru_loc = wh.lot_stock_id
        for mo in self.filtered(
                lambda m: m.route_type == 'solution' or m.amunet_is_solution_product):
            moves = mo.move_raw_ids.filtered(
                lambda mv: mv.state not in ('done', 'cancel')
                and mv.product_id.categ_id
                and hasattr(mv.product_id.categ_id, '_amunet_routes_to_aru')
                and mv.product_id.categ_id._amunet_routes_to_aru()
                # Excepcion por producto: hay reactivos que el area NO resguarda
                # y se piden a Materia Prima en cada orden. Sin esto el sistema
                # los buscaria en ARU y la orden se quedaria sin material aunque
                # haya existencia en MP.
                and not mv.product_id.product_tmpl_id.amunet_surtir_desde_mp)
            if not moves:
                continue
            moves._do_unreserve()
            moves.write({'location_id': aru_loc.id})
            moves._action_assign()

    def action_confirm(self):
        self._amunet_check_solution_maker()
        for rec in self:
            if rec.route_type in ('short', 'long', 'solution'):
                if not rec.preflight_approved:
                    raise UserError(_(
                        'No se puede confirmar la orden %s sin un '
                        'Preflight piloto aprobado.\n\n'
                        'Crea o ejecuta un preflight ANTES de confirmar '
                        'esta orden (Manufactura > Preflight piloto).'
                    ) % rec.name)
        res = super().action_confirm()
        self._amunet_solution_moves_from_aru()
        # El responsable de una solucion es quien la elabora. Solo se toma a
        # quien confirma si pertenece a Soluciones: una tableta de kiosco NO
        # esta en ese grupo, asi que no pisa al operador que entro con PIN.
        if not self.env.su and self.env.user.has_group(
                'amunet_production.group_solution_maker'):
            self._amunet_set_responsable_solucion(self.env.user)
        return res

    # ============================
    # Override button_plan: generar inspecciones al PLANIFICAR.
    # Planificar es el candado que declara "esta orden si se va a
    # producir". Una orden solo confirmada NO genera controles.
    # ============================
    def button_plan(self):
        res = super().button_plan()
        for rec in self:
            rec._generate_process_inspections()
        return res

    # ============================
    # Override action_cancel: cancelar en cascada los controles NO
    # firmados. Al cancelar la orden, sus inspecciones/supervisiones que
    # aun estan en borrador pasan a 'Cancelada'; las firmadas se conservan.
    # ============================
    def action_cancel(self):
        res = super().action_cancel()
        for rec in self:
            if rec.process_inspection_ids:
                rec.process_inspection_ids.sudo().action_amunet_cancel_unsigned()
        return res

    def _generate_process_inspections(self):
        """Crea los controles en proceso para esta MO segun lo configurado
        en cada ACTIVIDAD (operacion del routing):

        - amunet_requires_supervision -> genera una Supervision
          (inspection_type = production_supervision)
        - amunet_requires_inspection  -> genera una Inspeccion en proceso
          (inspection_type = qc_formal)

        Idempotente por (orden, workorder, tipo): no duplica.
        """
        self.ensure_one()
        if self.route_type not in ('short', 'long'):
            return
        Inspection = self.env['amunet.process.inspection'].sudo()
        for wo in self.workorder_ids:
            op = wo.operation_id
            if not op:
                continue
            wanted = []
            if op.amunet_requires_supervision:
                wanted.append('production_supervision')
            if op.amunet_requires_inspection:
                wanted.append('qc_formal')
            for itype in wanted:
                existing = Inspection.search([
                    ('production_id', '=', self.id),
                    ('workorder_id', '=', wo.id),
                    ('inspection_type', '=', itype),
                ], limit=1)
                if existing:
                    continue
                Inspection.create({
                    'production_id': self.id,
                    'workcenter_id': wo.workcenter_id.id,
                    'workorder_id': wo.id,
                    'inspection_type': itype,
                    'inspector_id': self.env.user.id,
                })
