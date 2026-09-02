# -*- coding: utf-8 -*-

from datetime import date

from odoo import api, fields, models, _
from odoo.exceptions import UserError

# Estados de orden de manufactura que se consideran "esperando material"
MO_ABIERTAS = ('confirmed', 'progress', 'to_close')

# Estados de capacitacion que cuentan como vigente
CAPACITACION_OK = ('vigente', 'proxima')


class AmunetQualityCheck(models.Model):
    _inherit = 'amunet.quality.check'

    # ---------------------------------------------------------------
    # Capa de planeacion
    # ---------------------------------------------------------------
    tablero_analista_id = fields.Many2one(
        'res.users',
        string='Analista asignado',
        tracking=True,
        index=True,
        domain=lambda self: self._tablero_dominio_analistas(),
        help='Quien va a realizar este analisis. Lo asigna el supervisor de Calidad.',
    )
    tablero_fecha_planeada = fields.Date(
        string='Fecha planeada',
        tracking=True,
        help='Cuando se planea realizar el analisis.',
    )

    @api.depends('tablero_prioridad', 'tablero_mo_count', 'tablero_dias_caducidad')
    def _compute_tablero_orden(self):
        """El orden sale de la prioridad EFECTIVA, sea deducida o forzada.

        Va en su propio compute a proposito: tablero_prioridad se puede escribir
        a mano, y cuando Odoo recibe un valor manual para un campo calculado ya
        no ejecuta su metodo de calculo. Si el orden compartiera ese metodo, se
        quedaria con el valor viejo y el analisis forzado a rojo no subiria al
        principio de la lista. Paso el 2026-09-01.
        """
        for check in self:
            if check.tablero_prioridad == 'bloqueo':
                check.tablero_orden = max(0, 100 - (check.tablero_mo_count or 0))
            elif check.tablero_prioridad == 'caducidad':
                check.tablero_orden = 1000 + max(0, check.tablero_dias_caducidad or 0)
            else:
                check.tablero_orden = 9000

    def _compute_tablero_es_supervisor(self):
        es = self.env.user.has_group('amunet_quality.group_quality_supervisor')
        for check in self:
            check.tablero_es_supervisor = es

    def _inverse_tablero_prioridad(self):
        """Escribir la prioridad a mano guarda el override.

        Si el valor elegido coincide con el que dedujo el sistema, se entiende
        que la persona quiere volver a lo automatico y se limpia el override:
        asi no queda un 'forzado' fantasma que despues nadie sabe si sigue
        vigente.
        """
        for check in self:
            if check.tablero_prioridad == check.tablero_prioridad_auto:
                if check.tablero_prioridad_manual:
                    check.tablero_prioridad_manual = False
                    check.tablero_prioridad_motivo = False
            else:
                check.tablero_prioridad_manual = check.tablero_prioridad
                etiquetas = dict(
                    self._fields['tablero_prioridad'].selection)
                check.message_post(body=_(
                    'Prioridad cambiada a mano a <b>%(nueva)s</b>. '
                    'El sistema habia deducido <b>%(auto)s</b>.',
                    nueva=etiquetas.get(check.tablero_prioridad, '?'),
                    auto=etiquetas.get(check.tablero_prioridad_auto, '?'),
                ))

    # Campos que solo el supervisor de Calidad reparte
    TABLERO_CAMPOS_SUPERVISOR = (
        'tablero_analista_id',
        'tablero_prioridad',
        'tablero_prioridad_manual',
        'tablero_prioridad_motivo',
    )

    @api.model
    def _tablero_cron_refrescar(self):
        """Red de seguridad del tablero.

        El aviso desde la orden de produccion cubre el caso principal, pero el
        bloqueo tambien cambia por cosas que pasan fuera de la orden: un lote
        que se libera, una caducidad que se acerca. En vez de perseguir cada
        camino uno por uno, se recalcula lo abierto cada tanto.
        """
        abiertos = self.search([('state', 'not in', ('done', 'cancel'))])
        if not abiertos:
            return True
        abiertos._compute_tablero_bloqueo()
        abiertos._compute_tablero_caducidad()
        abiertos._compute_tablero_prioridad()
        abiertos._compute_tablero_orden()
        return True

    @api.model
    def _tablero_dominio_analistas(self):
        """Solo se puede asignar el analisis a un Analista de Calidad.

        Antes el campo ofrecia CUALQUIER usuario del sistema, asi que se podia
        asignar un analisis a alguien de almacen o de compras. Se restringe al
        grupo 'Calidad / Analista QC'.

        Se excluyen los usuarios tecnicos (OdooBot, cuentas VERIF-ODOO de
        verificacion): no son personas y no pueden realizar un analisis. Los
        inactivos ya los descarta Odoo solo.

        Tambien se excluyen los MANAGERS de Calidad (hoy Mery y Fernando). Estan
        en el grupo de analistas porque los dueños del sistema pertenecen a todos
        los grupos restringidos, pero no hacen analisis en el laboratorio y
        ensuciaban el desplegable. Se filtra por ROL y no por nombre, para que
        siga funcionando cuando cambien las personas. Los supervisores SI
        aparecen: Diana supervisa y ademas analiza.
        """
        grupo = self.env.ref('amunet_quality.group_quality_user',
                             raise_if_not_found=False)
        if not grupo:
            return []
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
        return dominio

    tablero_prioridad = fields.Selection(
        [
            ('bloqueo',   'Bloquea produccion o venta'),
            ('caducidad', 'Proximo a caducar o usar'),
            ('normal',    'Normal'),
        ],
        string='Prioridad',
        compute='_compute_tablero_prioridad',
        inverse='_inverse_tablero_prioridad',
        readonly=False,
        store=True,
        index=True,
        tracking=True,
        help='La calcula el sistema a partir de lo que esta pasando (ordenes '
             'detenidas, caducidad). Se puede cambiar a mano: al hacerlo, tu '
             'eleccion manda. Si la regresas al valor que calcula el sistema, '
             'vuelve a ser automatica.',
    )
    # Lo que DEDUCE el sistema, siempre calculado. Se conserva aunque alguien
    # fuerce la prioridad a mano: asi nunca se pierde el dato objetivo y se ve
    # de un vistazo cuando lo forzado difiere de la realidad.
    tablero_prioridad_auto = fields.Selection(
        [
            ('bloqueo',   'Bloquea produccion o venta'),
            ('caducidad', 'Proximo a caducar o usar'),
            ('normal',    'Normal'),
        ],
        string='Prioridad deducida',
        compute='_compute_tablero_prioridad',
        store=True,
        readonly=True,
    )
    # El override manual. Vacio = manda la deducida.
    tablero_prioridad_manual = fields.Selection(
        [
            ('bloqueo',   'Bloquea produccion o venta'),
            ('caducidad', 'Proximo a caducar o usar'),
            ('normal',    'Normal'),
        ],
        string='Prioridad forzada',
        tracking=True,
        help='Solo para cuando sabes algo que el sistema no ve. Si la dejas '
             'vacia, manda la prioridad que deduce el sistema.',
    )
    tablero_prioridad_motivo = fields.Char(
        string='Motivo del cambio de prioridad',
        tracking=True,
        help='Por que se forzo la prioridad. Queda en el expediente.',
    )
    # Entero para poder ordenar: 0 = lo mas urgente
    tablero_orden = fields.Integer(
        string='Orden de atencion',
        compute='_compute_tablero_orden',
        store=True,
    )

    tablero_mo_ids = fields.Many2many(
        'mrp.production',
        compute='_compute_tablero_bloqueo',
        string='Ordenes que esperan este material',
    )
    tablero_mo_count = fields.Integer(
        string='Ordenes detenidas',
        compute='_compute_tablero_bloqueo',
        store=True,
    )
    tablero_bloquea_venta = fields.Boolean(
        string='Bloquea venta',
        compute='_compute_tablero_bloqueo',
        store=True,
        help='Producto terminado con lote no liberado: no se puede publicar en la tienda.',
    )

    tablero_dias_caducidad = fields.Integer(
        string='Dias para caducar',
        compute='_compute_tablero_caducidad',
        store=True,
    )

    tablero_es_supervisor = fields.Boolean(
        string='Soy supervisor de Calidad',
        compute='_compute_tablero_es_supervisor',
        help='Uso interno de la vista: decide que campos puede editar quien mira.',
    )

    tablero_aviso_capacitacion = fields.Char(
        string='Aviso de capacitacion',
        compute='_compute_tablero_aviso_capacitacion',
    )

    # ---------------------------------------------------------------
    # Computos
    # ---------------------------------------------------------------
    @api.depends('product_id', 'lot_id', 'state')
    def _compute_tablero_bloqueo(self):
        MO = self.env['mrp.production']
        for check in self:
            mos = MO.browse()
            bloquea_venta = False
            if check.product_id and check.state not in ('done', 'cancel'):
                # Bloquea PRODUCCION: hay ordenes abiertas que consumen este producto
                mos = MO.search([
                    ('state', 'in', MO_ABIERTAS),
                    ('move_raw_ids.product_id', '=', check.product_id.id),
                ])
                # Bloquea VENTA: producto terminado cuyo lote no esta liberado
                categ = check.product_id.categ_id.complete_name or ''
                if categ.startswith('Producto terminado'):
                    lot = check.lot_id
                    estado = getattr(lot, 'amunet_lot_release_state', False)
                    bloquea_venta = bool(lot) and estado != 'released'
            check.tablero_mo_ids = mos
            check.tablero_mo_count = len(mos)
            check.tablero_bloquea_venta = bloquea_venta

    @api.depends('lot_id', 'lot_id.expiration_date')
    def _compute_tablero_caducidad(self):
        hoy = date.today()
        for check in self:
            dias = 0
            exp = check.lot_id.expiration_date if check.lot_id else False
            if exp:
                exp_date = exp.date() if hasattr(exp, 'date') else exp
                dias = (exp_date - hoy).days
            check.tablero_dias_caducidad = dias

    @api.depends('tablero_mo_count', 'tablero_bloquea_venta',
                 'tablero_dias_caducidad', 'state',
                 'tablero_prioridad_manual')
    def _compute_tablero_prioridad(self):
        """La prioridad la deduce el sistema, salvo que alguien la haya forzado.

        La deduccion refleja lo que de verdad esta pasando (ordenes detenidas,
        lote por caducar). La manual existe para el caso contrario: cuando una
        persona sabe algo que el sistema no puede ver. Si hay manual, MANDA; la
        deducida se sigue calculando y queda visible en tablero_prioridad_auto,
        para no perder el dato objetivo.
        """
        limite = int(self.env['ir.config_parameter'].sudo().get_param(
            'amunet_calidad_tablero.dias_caducidad_prioritaria', '365'))
        for check in self:
            # 1) Lo que deduce el sistema (siempre se calcula)
            if check.tablero_mo_count or check.tablero_bloquea_venta:
                auto = 'bloqueo'
                orden = max(0, 100 - check.tablero_mo_count)
            elif check.tablero_dias_caducidad and check.tablero_dias_caducidad <= limite:
                auto = 'caducidad'
                orden = 1000 + max(0, check.tablero_dias_caducidad)
            else:
                auto = 'normal'
                orden = 9000
            check.tablero_prioridad_auto = auto

            # 2) La manual manda si existe
            if check.tablero_prioridad_manual:
                check.tablero_prioridad = check.tablero_prioridad_manual
            else:
                check.tablero_prioridad = auto

    # ---------------------------------------------------------------
    # Capacitacion: aviso hoy, bloqueo despues de la fecha del parametro
    # ---------------------------------------------------------------
    def _tablero_procedimientos_faltantes(self, usuario):
        """Procedimientos de este analisis para los que el usuario NO tiene
        capacitacion vigente. Reusa el mismo criterio del gate de liberacion."""
        self.ensure_one()
        if not usuario:
            return []
        if 'amunet.registro.capacitacion' not in self.env.registry:
            return []
        if 'procedure_ids' not in self._fields:
            return []
        procedimientos = self.procedure_ids.filtered('active')
        if not procedimientos:
            return []
        Training = self.env['amunet.registro.capacitacion'].sudo()
        faltantes = []
        for proc in procedimientos:
            existe = Training.search_count([
                ('user_id', '=', usuario.id),
                ('procedure_id', '=', proc.id),
                ('state', 'in', CAPACITACION_OK),
            ])
            if not existe:
                faltantes.append(proc.code or proc.display_name)
        return faltantes

    @api.depends('tablero_analista_id')
    def _compute_tablero_aviso_capacitacion(self):
        for check in self:
            faltantes = check._tablero_procedimientos_faltantes(check.tablero_analista_id)
            if faltantes:
                check.tablero_aviso_capacitacion = _(
                    'Sin capacitacion vigente para: %s'
                ) % ', '.join(faltantes)
            else:
                check.tablero_aviso_capacitacion = False

    def _tablero_bloqueo_capacitacion_activo(self):
        """Antes de la fecha del parametro: solo aviso. Desde esa fecha: bloqueo."""
        valor = self.env['ir.config_parameter'].sudo().get_param(
            'amunet_calidad_tablero.capacitacion_bloqueo_desde')
        if not valor:
            return False
        try:
            desde = fields.Date.to_date(valor)
        except (ValueError, TypeError):
            return False
        return bool(desde) and date.today() >= desde

    def write(self, vals):
        """Reparto y prioridad: solo el supervisor de Calidad.

        El analista ve su carga y puede mover su fecha planeada, pero no puede
        reasignarse analisis ni subirse la prioridad. Se valida aqui y no solo
        en la vista: un readonly de pantalla no impide escribir por otras vias.

        OJO: este es el UNICO write del modulo. Hubo un momento con dos
        definiciones y la segunda anulaba a la primera en silencio, dejando el
        candado inservible. Si hace falta mas logica, va aqui dentro.
        """
        tocados = set(vals) & set(self.TABLERO_CAMPOS_SUPERVISOR)
        if (tocados and not self.env.su
                and not self.env.context.get('amunet_tablero_interno')
                and not self.env.user.has_group(
                    'amunet_quality.group_quality_supervisor')):
            etiquetas = ', '.join(
                sorted(self._fields[f].string for f in tocados))
            raise UserError(_(
                'Solo el supervisor de Calidad puede cambiar: %s.\n\n'
                'Tu puedes ajustar la fecha en que planeas hacer el analisis, '
                'pero el reparto y la prioridad los define Calidad.'
            ) % etiquetas)
        res = super().write(vals)
        if 'tablero_analista_id' in vals and vals.get('tablero_analista_id'):
            self._tablero_validar_capacitacion()
        return res

    @api.model_create_multi
    def create(self, vals_list):
        records = super().create(vals_list)
        con_analista = records.filtered('tablero_analista_id')
        if con_analista:
            con_analista._tablero_validar_capacitacion()
        return records

    def _tablero_validar_capacitacion(self):
        if not self._tablero_bloqueo_capacitacion_activo():
            # Periodo de aviso: no se bloquea. El aviso se ve en el campo
            # tablero_aviso_capacitacion y en el chatter.
            for check in self:
                faltantes = check._tablero_procedimientos_faltantes(check.tablero_analista_id)
                if faltantes:
                    check.message_post(body=_(
                        'Aviso: %(analista)s no tiene capacitacion vigente para: %(procs)s. '
                        'Se permite la asignacion, pero la firma puede quedar detenida.',
                        analista=check.tablero_analista_id.display_name,
                        procs=', '.join(faltantes),
                    ))
            return
        # Periodo de bloqueo
        for check in self:
            faltantes = check._tablero_procedimientos_faltantes(check.tablero_analista_id)
            if faltantes:
                raise UserError(_(
                    'No se puede asignar a %(analista)s: no tiene capacitacion vigente '
                    'para %(procs)s.',
                    analista=check.tablero_analista_id.display_name,
                    procs=', '.join(faltantes),
                ))

    # ---------------------------------------------------------------
    # Acciones del tablero
    # ---------------------------------------------------------------
    def action_tablero_tomar(self):
        """El analista se asigna a si mismo."""
        self.write({'tablero_analista_id': self.env.user.id})

    def action_tablero_ver_ordenes(self):
        """Abre las ordenes de manufactura detenidas por este analisis."""
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': _('Ordenes que esperan este material'),
            'res_model': 'mrp.production',
            'view_mode': 'list,form',
            'domain': [('id', 'in', self.tablero_mo_ids.ids)],
        }
