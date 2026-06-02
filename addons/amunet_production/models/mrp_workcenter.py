# -*- coding: utf-8 -*-
from odoo import _, api, fields, models
from odoo.exceptions import UserError


class MrpWorkcenter(models.Model):
    _inherit = 'mrp.workcenter'

    amunet_parent_workcenter_id = fields.Many2one(
        'mrp.workcenter',
        string='Área padre',
        ondelete='set null',
        help='Si este centro de trabajo es un sub-área de otro (ej. LAM es '
             'sub-área de PROD), indica aquí el padre. La validación de '
             'calibración de equipos se hereda del padre cuando este WC no '
             'tiene equipos propios vinculados.',
    )
    amunet_child_workcenter_ids = fields.One2many(
        'mrp.workcenter',
        'amunet_parent_workcenter_id',
        string='Sub-áreas',
    )

    amunet_workcenter_type = fields.Selection(
        selection=[
            ('area', 'Área principal'),
            ('subarea', 'Sub-área'),
        ],
        string='Tipo',
        compute='_compute_amunet_workcenter_type',
        store=True,
    )

    amunet_complete_name = fields.Char(
        string='Área / Sub-área',
        compute='_compute_amunet_complete_name',
        store=True,
    )

    amunet_area_name = fields.Char(
        string='Área',
        compute='_compute_amunet_area_name',
        store=True,
        help='Nombre del área principal a la que pertenece este workcenter. '
             'Usado para agrupar la lista.',
    )

    @api.depends('amunet_parent_workcenter_id')
    def _compute_amunet_workcenter_type(self):
        for wc in self:
            wc.amunet_workcenter_type = 'subarea' if wc.amunet_parent_workcenter_id else 'area'

    @api.depends('name', 'amunet_parent_workcenter_id', 'amunet_parent_workcenter_id.name')
    def _compute_amunet_complete_name(self):
        for wc in self:
            if wc.amunet_parent_workcenter_id:
                wc.amunet_complete_name = f"{wc.amunet_parent_workcenter_id.name} / {wc.name}"
            else:
                wc.amunet_complete_name = wc.name

    @api.depends('name', 'amunet_parent_workcenter_id', 'amunet_parent_workcenter_id.name')
    def _compute_amunet_area_name(self):
        for wc in self:
            if wc.amunet_parent_workcenter_id:
                wc.amunet_area_name = wc.amunet_parent_workcenter_id.name
            else:
                wc.amunet_area_name = wc.name

    amunet_equipment_ids = fields.Many2many(
        comodel_name='amunet.equipment',
        relation='amunet_workcenter_equipment_rel',
        column1='workcenter_id',
        column2='equipment_id',
        string='Equipos vinculados',
        help=(
            'Equipos fisicos del catalogo Amunet que pertenecen a este centro '
            'de trabajo. Cuando se inicia una orden de trabajo (button_start) '
            'el sistema valida que TODOS los equipos vinculados:\n'
            ' (a) tengan certificado de calibracion vigente '
            '(state=done y expiration_date >= hoy), y\n'
            ' (b) esten en estado operativo (state=active).\n'
            'Si la lista esta vacia y no se marca explicitamente la excepcion '
            'amunet_no_equipment_required, button_start tambien se bloquea '
            'para evitar fail-open silencioso.'
        ),
    )

    amunet_equipment_count = fields.Integer(
        compute='_compute_amunet_equipment_count',
        string='# Equipos',
    )

    amunet_no_equipment_required = fields.Boolean(
        string='No requiere equipo calibrado',
        default=False,
        help=(
            'Marca explicita para workcenters que legitimamente no necesitan '
            'equipos con calibracion vigente, ej. mesas de trabajo manual sin '
            'instrumento. ISO 13485 requiere justificacion documentada en '
            'la nota del workcenter o en CAPA antes de marcar esta excepcion. '
            'Cuando es True, button_start permite arrancar sin chequeos de '
            'equipo y registra una nota en el chatter de la WO.'
        ),
    )
    amunet_equipment_exception_reason = fields.Text(
        string='Justificacion ISO 13485',
        help='Motivo documentado para permitir este centro de trabajo sin '
             'equipos calibrados vinculados.')
    amunet_equipment_exception_signed_by_id = fields.Many2one(
        'res.users', string='Excepcion firmada por', readonly=True, copy=False)
    amunet_equipment_exception_signed_date = fields.Datetime(
        string='Fecha firma excepcion', readonly=True, copy=False)

    @api.depends('amunet_equipment_ids')
    def _compute_amunet_equipment_count(self):
        for wc in self:
            wc.amunet_equipment_count = len(wc.amunet_equipment_ids)

    def _amunet_check_equipment_calibration(self):
        """Valida que el WC pueda iniciar trabajo segun reglas Amunet:

        1. Si amunet_equipment_ids esta vacio Y amunet_no_equipment_required
           es False -> bloquea (fail-closed, evita default permisivo).
        2. Si amunet_no_equipment_required es True -> permite y devuelve
           {'no_equipment_required': True} para que el caller registre log.
        3. Para cada equipo vinculado:
           a) state debe ser 'active' (no maintenance ni out_of_service).
           b) Debe existir al menos una calibracion done con expiration_date
              >= hoy.

        Devuelve dict {'no_equipment_required': bool} si todo OK.
        Levanta UserError consolidando todos los problemas detectados.
        """
        today = fields.Date.context_today(self)
        problemas = []
        any_skipped = False

        for wc in self:
            wc_label = wc.code or wc.name

            if not wc.amunet_equipment_ids:
                if wc.amunet_no_equipment_required:
                    if not (
                        wc.amunet_equipment_exception_reason
                        and wc.amunet_equipment_exception_signed_by_id
                        and wc.amunet_equipment_exception_signed_date
                    ):
                        problemas.append(
                            ' - Workcenter %s: excepcion "No requiere equipo '
                            'calibrado" sin justificacion y firma electronica.'
                            % wc_label
                        )
                        continue
                    any_skipped = True
                    continue
                # Sin equipos propios: si tiene padre, delegar al padre
                if wc.amunet_parent_workcenter_id:
                    parent = wc.amunet_parent_workcenter_id
                    try:
                        parent._amunet_check_equipment_calibration()
                    except UserError as e:
                        problemas.append(
                            ' - Workcenter %s (sub-area de %s): %s'
                            % (wc_label, parent.code or parent.name, str(e.args[0]))
                        )
                    continue
                problemas.append(
                    ' - Workcenter %s: no tiene equipos vinculados ni esta '
                    'marcado como "No requiere equipo calibrado". Vincula '
                    'los equipos en la pestana "Equipos Amunet" o marca la '
                    'excepcion explicitamente con justificacion ISO 13485.'
                    % wc_label
                )
                continue

            for eq in wc.amunet_equipment_ids:
                # (a) estado del equipo
                eq_state = eq.state if hasattr(eq, 'state') else 'active'
                if eq_state != 'active':
                    state_label = dict(
                        eq._fields['state'].selection
                    ).get(eq_state, eq_state)
                    problemas.append(
                        ' - %s (%s) en %s: estado "%s" (no operativo)'
                        % (eq.serial_number, eq.name, wc_label, state_label)
                    )
                    # No haga continue: tambien reporta cert si aplica
                # (b) calibracion vigente
                cal = self.env['amunet.equipment.calibration'].search([
                    ('equipment_id', '=', eq.id),
                    ('state', '=', 'done'),
                    ('expiration_date', '>=', today),
                ], limit=1)
                if not cal:
                    last = self.env['amunet.equipment.calibration'].search([
                        ('equipment_id', '=', eq.id),
                    ], order='expiration_date desc', limit=1)
                    if last:
                        problemas.append(
                            ' - %s (%s) en %s: ultima calibracion vence %s '
                            '(state=%s)' % (
                                eq.serial_number, eq.name, wc_label,
                                last.expiration_date, last.state,
                            )
                        )
                    else:
                        problemas.append(
                            ' - %s (%s) en %s: sin calibracion registrada'
                            % (eq.serial_number, eq.name, wc_label)
                        )

        if problemas:
            raise UserError(_(
                'No se puede iniciar la orden de trabajo. Problemas en el '
                'centro de trabajo:\n%s\n\n'
                'Soluciona la causa antes de arrancar produccion (subir '
                'certificados de calibracion vigentes, reactivar equipos, '
                'vincular equipos al workcenter, o marcar la excepcion '
                'amunet_no_equipment_required con justificacion ISO 13485).'
            ) % '\n'.join(problemas))
        return {'no_equipment_required': any_skipped}

    def _check_can_approve_equipment_exception(self):
        for wc in self:
            if not (
                self.env.user.has_group('amunet_equipment_calibration.group_equipment_manager')
                or self.env.user.has_group('amunet_quality.group_quality_manager')
                or self.env.user.has_group('mrp.group_mrp_manager')
            ):
                raise UserError(_(
                    'Solo Metrologia, Manager QC o Responsable MRP puede '
                    'aprobar esta excepcion ISO 13485.'))
            if wc.amunet_equipment_ids:
                raise UserError(_(
                    'Este centro ya tiene equipos vinculados; no requiere excepcion.'))
            if not wc.amunet_equipment_exception_reason:
                raise UserError(_(
                    'Captura la justificacion ISO 13485 antes de firmar la excepcion.'))

    def _amunet_signature_allowed_methods(self):
        return {
            '_signature_action_approve_equipment_exception': _(
                'Aprobar excepcion de equipo calibrado'),
        }

    def action_approve_equipment_exception(self):
        self.ensure_one()
        self._check_can_approve_equipment_exception()
        return self.env['amunet.generic.signature.wizard'].open_for(
            self,
            '_signature_action_approve_equipment_exception',
            _('Aprobar excepcion de equipo calibrado'),
            _('Firma de excepcion ISO 13485 para %s.') % (self.code or self.name),
        )

    def _signature_action_approve_equipment_exception(self):
        self.ensure_one()
        self._check_can_approve_equipment_exception()
        self.with_context(amunet_workcenter_exception_signature_write=True).write({
            'amunet_no_equipment_required': True,
            'amunet_equipment_exception_signed_by_id': self.env.user.id,
            'amunet_equipment_exception_signed_date': fields.Datetime.now(),
        })
        return True

    def _has_equipment_exception_signature_values(self, vals):
        signature_fields = {
            'amunet_equipment_exception_signed_by_id',
            'amunet_equipment_exception_signed_date',
        }
        return (
            vals.get('amunet_no_equipment_required') is True
            or signature_fields.intersection(vals)
        )

    @api.model_create_multi
    def create(self, vals_list):
        if (
            not self.env.context.get('amunet_workcenter_exception_signature_write')
            and not self.env.su
        ):
            for vals in vals_list:
                if self._has_equipment_exception_signature_values(vals):
                    raise UserError(_(
                        'La excepcion "No requiere equipo calibrado" y sus '
                        'campos de firma deben aprobarse con firma electronica '
                        'desde el boton correspondiente.'))
        return super().create(vals_list)

    def write(self, vals):
        if (
            self._has_equipment_exception_signature_values(vals)
            and not self.env.context.get('amunet_workcenter_exception_signature_write')
            and not self.env.su
        ):
            raise UserError(_(
                'La excepcion "No requiere equipo calibrado" y sus campos '
                'de firma deben aprobarse con firma electronica desde el '
                'boton correspondiente.'))
        if vals.get('amunet_no_equipment_required') is False:
            vals = dict(vals)
            vals.update({
                'amunet_equipment_exception_signed_by_id': False,
                'amunet_equipment_exception_signed_date': False,
            })
        return super().write(vals)
