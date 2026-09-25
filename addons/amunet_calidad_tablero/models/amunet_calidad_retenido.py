# -*- coding: utf-8 -*-

from datetime import date

from odoo import api, fields, models, _
from odoo.exceptions import UserError

# Ubicaciones internas donde un material se considera inmovilizado por Calidad.
# Se busca por nombre completo porque las ubicaciones no tienen una marca
# propia y los almacenes (AMP, APT, AMPB, ADT) las nombran igual.
FRAGMENTOS_UBICACION = ('Control de calidad', '/Entrada')

# Estados del analisis que se consideran abiertos
CHECK_ABIERTOS = ('draft', 'in_progress', 'pending', 'awaiting_reception')

# Estados del retenido que siguen vivos
ESTADOS_ABIERTOS = ('pendiente', 'asignado', 'con_analisis')


class AmunetCalidadRetenido(models.Model):
    """Material que esta fisicamente detenido en una ubicacion de Calidad.

    No sustituye al analisis (amunet.quality.check): es la foto de lo que hay
    parado en el piso, para que nada se quede olvidado meses en Entrada sin
    que nadie lo mire. Lo llena un cron diario; no se captura a mano.
    """

    _name = 'amunet.calidad.retenido'
    _description = 'Material inmovilizado en Calidad'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'dias desc, id desc'

    name = fields.Char(
        string='Referencia',
        compute='_compute_name',
        store=True,
    )
    lot_id = fields.Many2one(
        'stock.lot',
        string='Lote',
        required=True,
        ondelete='cascade',
        index=True,
        tracking=True,
    )
    product_id = fields.Many2one(
        'product.product',
        string='Producto',
        index=True,
        tracking=True,
    )
    location_id = fields.Many2one(
        'stock.location',
        string='Ubicacion',
        required=True,
        ondelete='cascade',
        index=True,
        tracking=True,
    )
    cantidad = fields.Float(
        string='Cantidad detenida',
        digits='Product Unit',
    )
    fecha_ingreso = fields.Datetime(
        string='Detenido desde',
        help='Fecha en que la existencia mas antigua entro a esta ubicacion.',
    )
    # Almacenado a proposito: la lista se ordena por este campo y el orden de
    # un campo no almacenado no se puede usar en SQL. El cron lo recalcula.
    dias = fields.Integer(
        string='Dias detenido',
        compute='_compute_dias',
        store=True,
    )
    analista_id = fields.Many2one(
        'res.users',
        string='Analista asignado',
        index=True,
        tracking=True,
        domain=lambda self: self.env['amunet.quality.check']._tablero_dominio_analistas(),
    )
    quality_check_id = fields.Many2one(
        'amunet.quality.check',
        string='Analisis relacionado',
        ondelete='set null',
        index=True,
        tracking=True,
        help='Analisis abierto del mismo lote, si ya existe.',
    )
    estado = fields.Selection(
        [
            ('pendiente',    'Pendiente'),
            ('asignado',     'Asignado'),
            ('con_analisis', 'Con analisis'),
            ('resuelto',     'Resuelto'),
        ],
        string='Estado',
        default='pendiente',
        required=True,
        index=True,
        tracking=True,
    )
    notas = fields.Text(string='Notas')
    active = fields.Boolean(
        string='Activo',
        default=True,
        help='Se archiva solo cuando el material ya no tiene existencia en la '
             'ubicacion. No se borra: queda el historial.',
    )

    # Odoo 19 ignora _sql_constraints (solo avisa en el log y NO crea la
    # restriccion); con models.Constraint si se crea el UNIQUE en la tabla.
    # Es lo que hace idempotente al cron: un lote en una ubicacion, un registro.
    _lote_ubicacion_uniq = models.Constraint(
        'unique(lot_id, location_id)',
        'Ya existe un registro de material inmovilizado para ese lote en esa ubicacion.',
    )

    # ---------------------------------------------------------------
    # Computos
    # ---------------------------------------------------------------
    @api.depends('lot_id', 'product_id', 'location_id')
    def _compute_name(self):
        for rec in self:
            partes = [
                rec.product_id.display_name or '',
                rec.lot_id.name or '',
                rec.location_id.complete_name or '',
            ]
            rec.name = ' / '.join(p for p in partes if p)

    @api.depends('fecha_ingreso')
    def _compute_dias(self):
        hoy = date.today()
        for rec in self:
            if rec.fecha_ingreso:
                rec.dias = (hoy - rec.fecha_ingreso.date()).days
            else:
                rec.dias = 0

    # ---------------------------------------------------------------
    # Cron diario: detectar, repartir y escalar
    # ---------------------------------------------------------------
    @api.model
    def _cron_detectar_retenidos(self):
        """Una pasada al dia sobre lo que hay parado en Calidad."""
        self._detectar()
        self._repartir()
        self._escalar()
        return True

    @api.model
    def _ubicaciones_calidad(self):
        dominio = ['|'] * (len(FRAGMENTOS_UBICACION) - 1)
        for frag in FRAGMENTOS_UBICACION:
            dominio.append(('complete_name', 'ilike', frag))
        return self.env['stock.location'].search(
            [('usage', '=', 'internal')] + dominio)

    @api.model
    def _detectar(self):
        """Crea, actualiza y archiva segun las existencias reales."""
        ubicaciones = self._ubicaciones_calidad()
        if not ubicaciones:
            return
        quants = self.env['stock.quant'].sudo().search([
            ('location_id', 'in', ubicaciones.ids),
            ('quantity', '>', 0),
            ('lot_id', '!=', False),
        ])

        # Un renglon por lote y ubicacion
        agrupado = {}
        for quant in quants:
            clave = (quant.lot_id.id, quant.location_id.id)
            datos = agrupado.setdefault(clave, {
                'product_id': quant.product_id.id,
                'cantidad': 0.0,
                'fecha_ingreso': quant.in_date,
            })
            datos['cantidad'] += quant.quantity
            if quant.in_date and (not datos['fecha_ingreso']
                                  or quant.in_date < datos['fecha_ingreso']):
                datos['fecha_ingreso'] = quant.in_date

        # Se mira tambien lo archivado: si el material regresa, se reabre el
        # mismo registro en vez de crear uno nuevo (la restriccion unica no
        # distingue activos de archivados).
        existentes = self.with_context(active_test=False).search([])
        por_clave = {(r.lot_id.id, r.location_id.id): r for r in existentes}

        creados = self.browse()
        for clave, datos in agrupado.items():
            rec = por_clave.get(clave)
            if rec:
                vals = {
                    'product_id': datos['product_id'],
                    'cantidad': datos['cantidad'],
                    'fecha_ingreso': datos['fecha_ingreso'],
                }
                if not rec.active:
                    vals.update({'active': True, 'estado': 'pendiente'})
                rec.write(vals)
                if vals.get('active'):
                    rec.message_post(body=_(
                        'El material volvio a tener existencia en esta '
                        'ubicacion. Se reabre el seguimiento.'))
            else:
                rec = self.create({
                    'lot_id': clave[0],
                    'location_id': clave[1],
                    'product_id': datos['product_id'],
                    'cantidad': datos['cantidad'],
                    'fecha_ingreso': datos['fecha_ingreso'],
                })
                creados |= rec
                por_clave[clave] = rec

        # Lo que ya no tiene existencia se da por resuelto y se archiva.
        # No se borra nunca: el historial de calidad se conserva.
        sobrantes = existentes.filtered(
            lambda r: r.active and (r.lot_id.id, r.location_id.id) not in agrupado)
        for rec in sobrantes:
            rec.message_post(body=_(
                'Ya no hay existencia de este lote en la ubicacion. '
                'Se cierra el seguimiento.'))
            rec.write({'estado': 'resuelto', 'active': False})

        # Dias al dia (el campo esta almacenado y la fecha de hoy cambia)
        vivos = self.search([])
        if vivos:
            vivos._compute_dias()

        # Enlace con el analisis abierto del mismo lote, si existe
        vivos._enlazar_analisis()

    def _enlazar_analisis(self):
        """Si el lote ya tiene un analisis abierto, se enlaza y se marca."""
        Check = self.env['amunet.quality.check']
        for rec in self.filtered(lambda r: r.estado != 'resuelto'):
            check = rec.quality_check_id
            if not check or check.state == 'done' or not check.active:
                check = Check.search([
                    ('lot_id', '=', rec.lot_id.id),
                    ('state', 'in', CHECK_ABIERTOS),
                ], order='id desc', limit=1)
            if check:
                vals = {}
                if rec.quality_check_id != check:
                    vals['quality_check_id'] = check.id
                if rec.estado in ('pendiente', 'asignado'):
                    vals['estado'] = 'con_analisis'
                # Si el analisis ya trae analista, el material es de esa misma
                # persona: no tiene sentido repartirselo a otro.
                if not rec.analista_id and check.tablero_analista_id:
                    vals['analista_id'] = check.tablero_analista_id.id
                if vals:
                    rec.write(vals)

    # ---------------------------------------------------------------
    # Reparto entre analistas
    # ---------------------------------------------------------------
    @api.model
    def _analistas_disponibles(self):
        """Analistas de Calidad a los que se les puede repartir carga.

        Se usa el mismo criterio del tablero (grupo Analista QC, sin cuentas
        tecnicas y sin managers), asi el reparto automatico y el desplegable
        de la pantalla ofrecen la misma gente.
        """
        grupo = self.env.ref('amunet_quality.group_quality_user',
                             raise_if_not_found=False)
        if not grupo:
            return self.env['res.users'].browse()
        dominio = [
            ('group_ids', 'in', grupo.ids),
            ('share', '=', False),
            ('login', 'not in', ['__system__', 'default']),
            ('login', 'not like', 'verif-odoo%'),
        ]
        manager = self.env.ref('amunet_quality.group_quality_manager',
                               raise_if_not_found=False)
        if manager:
            dominio.append(('group_ids', 'not in', manager.ids))
        return self.env['res.users'].sudo().search(dominio, order='id')

    @api.model
    def _repartir(self):
        """Reparto balanceado por carga: al que menos trae abiertos.

        No es un turno ciego: si alguien ya arrastra diez lotes no se le
        cargan mas. Empate por id, para que el resultado sea estable y se
        pueda repetir la corrida sin sorpresas.
        """
        activo = self.env['ir.config_parameter'].sudo().get_param(
            'amunet_calidad_tablero.reparto_automatico', '1')
        if activo not in ('1', 'True', 'true'):
            return
        analistas = self._analistas_disponibles()
        if not analistas:
            return
        carga = {}
        for usuario in analistas:
            carga[usuario.id] = self.search_count([
                ('analista_id', '=', usuario.id),
                ('estado', 'in', ESTADOS_ABIERTOS),
            ])
        # Se reparte TODO lo abierto sin dueño, no solo lo 'pendiente'. Un
        # material con analisis abierto pero sin analista tambien necesita a
        # alguien que lo empuje; si se dejaran fuera, dos tercios del material
        # detenido se quedarian sin aparecer en el "Mi dia" de nadie.
        pendientes = self.search([
            ('estado', 'in', ('pendiente', 'con_analisis')),
            ('analista_id', '=', False),
        ], order='dias desc, id asc')
        for rec in pendientes:
            uid = min(carga, key=lambda k: (carga[k], k))
            vals = {'analista_id': uid}
            if rec.estado == 'pendiente':
                vals['estado'] = 'asignado'
            rec.write(vals)
            carga[uid] += 1
            rec.activity_schedule(
                'mail.mail_activity_data_todo',
                date_deadline=fields.Date.context_today(rec),
                user_id=uid,
                summary=_('Material detenido en Calidad: %s') % (
                    rec.lot_id.name or ''),
                note=_('Revisa el lote %(lote)s de %(producto)s detenido en '
                       '%(ubicacion)s.') % {
                    'lote': rec.lot_id.name or '',
                    'producto': rec.product_id.display_name or '',
                    'ubicacion': rec.location_id.complete_name or ''},
            )

    # ---------------------------------------------------------------
    # Escalamiento al supervisor
    # ---------------------------------------------------------------
    @api.model
    def _supervisor_calidad(self):
        grupo = self.env.ref('amunet_quality.group_quality_supervisor',
                             raise_if_not_found=False)
        if not grupo:
            return self.env['res.users'].browse()
        manager = self.env.ref('amunet_quality.group_quality_manager',
                               raise_if_not_found=False)
        dominio = [
            ('group_ids', 'in', grupo.ids),
            ('share', '=', False),
            ('login', 'not in', ['__system__', 'default']),
            ('login', 'not like', 'verif-odoo%'),
        ]
        if manager:
            dominio.append(('group_ids', 'not in', manager.ids))
        # Una sola actividad, a un solo supervisor: escalar a todos convierte
        # el aviso en ruido y nadie lo atiende.
        return self.env['res.users'].sudo().search(dominio, order='id', limit=1)

    @api.model
    def _escalar(self):
        dias_alerta = int(self.env['ir.config_parameter'].sudo().get_param(
            'amunet_calidad_tablero.dias_alerta_retenido', '7'))
        supervisor = self._supervisor_calidad()
        if not supervisor:
            return
        tipo = self.env.ref('mail.mail_activity_data_todo',
                            raise_if_not_found=False)
        if not tipo:
            return
        atrasados = self.search([
            ('estado', 'in', ESTADOS_ABIERTOS),
            ('dias', '>', dias_alerta),
        ])
        for rec in atrasados:
            ya = self.env['mail.activity'].sudo().search_count([
                ('res_model', '=', self._name),
                ('res_id', '=', rec.id),
                ('activity_type_id', '=', tipo.id),
                ('user_id', '=', supervisor.id),
            ])
            if ya:
                continue
            rec.activity_schedule(
                'mail.mail_activity_data_todo',
                date_deadline=fields.Date.context_today(rec),
                user_id=supervisor.id,
                summary=_('Material detenido %s dias en Calidad') % rec.dias,
                note=_('El lote %(lote)s lleva %(dias)s dias detenido en '
                       '%(ubicacion)s sin resolverse.') % {
                    'lote': rec.lot_id.name or '',
                    'dias': rec.dias,
                    'ubicacion': rec.location_id.complete_name or ''},
            )
            rec.message_post(body=_(
                'Lleva %(dias)s dias detenido (limite %(limite)s). '
                'Se escalo a %(sup)s.') % {
                'dias': rec.dias,
                'limite': dias_alerta,
                'sup': supervisor.display_name})

    # ---------------------------------------------------------------
    # Acciones de pantalla
    # ---------------------------------------------------------------
    def action_tomar(self):
        """El analista se hace cargo del material."""
        es_supervisor = self.env.user.has_group(
            'amunet_quality.group_quality_supervisor')
        for rec in self:
            if (rec.analista_id and rec.analista_id != self.env.user
                    and not es_supervisor):
                raise UserError(_(
                    'Este material ya esta asignado a %s. Pide al supervisor '
                    'de Calidad que lo reasigne.') % rec.analista_id.display_name)
            vals = {'analista_id': self.env.user.id}
            if rec.estado == 'pendiente':
                vals['estado'] = 'asignado'
            rec.write(vals)
        return True

    def action_resolver(self):
        """Se marca como resuelto sin archivar: el cron archiva cuando ya no
        hay existencia. Asi no se pierde de vista un material que sigue ahi."""
        for rec in self:
            rec.write({'estado': 'resuelto'})
            rec.message_post(body=_('Marcado como resuelto por %s.')
                             % self.env.user.display_name)
        return True

    def action_ver_analisis(self):
        self.ensure_one()
        if not self.quality_check_id:
            raise UserError(_('Este material no tiene un analisis enlazado.'))
        return {
            'type': 'ir.actions.act_window',
            'name': _('Analisis'),
            'res_model': 'amunet.quality.check',
            'res_id': self.quality_check_id.id,
            'view_mode': 'form',
        }
