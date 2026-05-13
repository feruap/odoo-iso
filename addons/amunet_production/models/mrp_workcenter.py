# -*- coding: utf-8 -*-
from odoo import _, api, fields, models
from odoo.exceptions import UserError


class MrpWorkcenter(models.Model):
    _inherit = 'mrp.workcenter'

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
                    any_skipped = True
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
