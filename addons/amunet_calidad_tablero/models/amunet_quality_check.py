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
        help='Quien va a realizar este analisis. Lo asigna el supervisor de Calidad.',
    )
    tablero_fecha_planeada = fields.Date(
        string='Fecha planeada',
        tracking=True,
        help='Cuando se planea realizar el analisis.',
    )

    tablero_prioridad = fields.Selection(
        [
            ('bloqueo',   'Bloquea produccion o venta'),
            ('caducidad', 'Proximo a caducar o usar'),
            ('normal',    'Normal'),
        ],
        string='Prioridad',
        compute='_compute_tablero_prioridad',
        store=True,
        index=True,
    )
    # Entero para poder ordenar: 0 = lo mas urgente
    tablero_orden = fields.Integer(
        string='Orden de atencion',
        compute='_compute_tablero_prioridad',
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
                 'tablero_dias_caducidad', 'state')
    def _compute_tablero_prioridad(self):
        limite = int(self.env['ir.config_parameter'].sudo().get_param(
            'amunet_calidad_tablero.dias_caducidad_prioritaria', '365'))
        for check in self:
            if check.tablero_mo_count or check.tablero_bloquea_venta:
                check.tablero_prioridad = 'bloqueo'
                # Entre los que bloquean, primero los que detienen mas ordenes
                check.tablero_orden = max(0, 100 - check.tablero_mo_count)
            elif check.tablero_dias_caducidad and check.tablero_dias_caducidad <= limite:
                check.tablero_prioridad = 'caducidad'
                # Entre los proximos a caducar, primero el que vence antes
                check.tablero_orden = 1000 + max(0, check.tablero_dias_caducidad)
            else:
                check.tablero_prioridad = 'normal'
                check.tablero_orden = 9000

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
