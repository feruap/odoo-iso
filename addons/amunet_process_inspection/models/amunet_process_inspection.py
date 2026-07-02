# -*- coding: utf-8 -*-
from odoo import models, fields, api, _
from odoo.exceptions import UserError, ValidationError


class AmunetProcessInspection(models.Model):
    """Inspeccion DE PROCESO realizada por estacion durante la
    produccion. NO es liberacion de lote (eso vive en amunet_quality).
    Cubre ISO 13485 clausula 8.2.5 (seguimiento del proceso).
    """
    _name = 'amunet.process.inspection'
    _description = 'Inspeccion de proceso'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'inspection_date desc, id desc'

    # ============================
    # Identificacion
    # ============================
    name = fields.Char(
        string='Folio',
        default='Nuevo',
        copy=False, readonly=True, required=True, tracking=True,
        help='INP/MMAA/NNN, consecutivo por mes.',
    )
    inspection_type = fields.Selection(
        selection=[
            ('qc_formal', 'Inspeccion en proceso'),
            ('production_supervision', 'Supervision'),
        ],
        string='Tipo de control', required=True, tracking=True,
        help='Inspeccion en proceso: control de calidad en proceso, la '
             'firma un Analista o Supervisor de Calidad. '
             'Supervision: la firma el supervisor de produccion; NO es '
             'una inspeccion. Ninguna de las dos libera el lote.',
    )
    production_id = fields.Many2one(
        'mrp.production', string='Orden de produccion',
        required=True, ondelete='restrict', tracking=True,
        index=True,
    )
    workcenter_id = fields.Many2one(
        'mrp.workcenter', string='Estacion',
        required=True, ondelete='restrict', tracking=True,
    )
    workorder_id = fields.Many2one(
        'mrp.workorder', string='Operacion',
        ondelete='set null', tracking=True,
        help='Operacion (workorder) del routing a la que pertenece. '
             'Opcional - puede haber inspecciones sin workorder asociada.',
    )

    # ============================
    # Lote / trazabilidad
    # ============================
    product_id = fields.Many2one(
        related='production_id.product_id', store=True, readonly=True,
        string='Producto',
    )
    lot_id = fields.Many2one(
        'stock.lot', string='Lote',
        domain="[('product_id', '=', product_id)]",
        ondelete='restrict', tracking=True,
    )
    lot_name = fields.Char(
        string='Numero de lote (texto)',
        help='Si el lote aun no existe en sistema, se puede capturar '
             'como texto y vincularlo despues.',
    )

    # ============================
    # Quien inspecciona y cuando
    # ============================
    inspector_id = fields.Many2one(
        'res.users', string='Inspector',
        default=lambda self: self.env.user,
        required=True, tracking=True,
    )
    inspection_date = fields.Datetime(
        string='Fecha y hora de inspeccion',
        default=fields.Datetime.now, required=True, tracking=True,
    )

    # ============================
    # Datos de la inspeccion
    # ============================
    qty_inspected = fields.Float(
        string='Piezas inspeccionadas',
        digits='Product Unit of Measure', tracking=True,
    )
    qty_removed = fields.Float(
        string='Piezas retiradas',
        digits='Product Unit of Measure', tracking=True,
        help='Cantidad de piezas que el inspector retiro del lote por '
             'no conformidad detectada.',
    )
    removal_reason = fields.Selection(
        selection=[
            ('mal_corte', 'Mal corte'),
            ('sello_defectuoso', 'Sello defectuoso'),
            ('etiqueta_ilegible', 'Etiqueta ilegible / mal impresa'),
            ('empaque_danado', 'Empaque danado'),
            ('contaminacion', 'Contaminacion visible'),
            ('faltante', 'Faltante de componente'),
            ('dimensional', 'Fuera de medidas'),
            ('apariencia', 'Defecto de apariencia'),
            ('otro', 'Otro (especificar en observaciones)'),
        ],
        string='Motivo del retiro',
        help='Aplica solo si qty_removed > 0.',
    )
    notes = fields.Text(string='Observaciones')

    # ============================
    # Resultado
    # ============================
    result = fields.Selection(
        selection=[
            ('conforme', 'Conforme'),
            ('conforme_con_retiros', 'Conforme con retiros'),
            ('detener', 'Detener proceso (escalar)'),
        ],
        string='Resultado',
        compute='_compute_result', store=True, readonly=False,
        tracking=True,
    )

    # ============================
    # Firma / estado
    # ============================
    state = fields.Selection(
        selection=[
            ('draft', 'Borrador'),
            ('signed', 'Firmada'),
        ],
        string='Estado', default='draft', required=True, tracking=True,
        copy=False,
    )
    signed_by_id = fields.Many2one(
        'res.users', string='Firmada por', readonly=True, copy=False)
    signed_date = fields.Datetime(
        string='Fecha de firma', readonly=True, copy=False)
    company_id = fields.Many2one(
        'res.company', string='Compania',
        default=lambda self: self.env.company, required=True,
    )

    # ============================
    # Constraints
    # ============================
    @api.constrains('qty_inspected', 'qty_removed')
    def _check_qty(self):
        for rec in self:
            if rec.qty_inspected < 0 or rec.qty_removed < 0:
                raise ValidationError(_(
                    'Las cantidades no pueden ser negativas.'))
            if rec.qty_removed > rec.qty_inspected:
                raise ValidationError(_(
                    'Las piezas retiradas (%(r)s) no pueden ser mayores '
                    'que las inspeccionadas (%(i)s).'
                ) % {'r': rec.qty_removed, 'i': rec.qty_inspected})

    @api.constrains('qty_removed', 'removal_reason')
    def _check_removal_reason(self):
        for rec in self:
            if rec.qty_removed and not rec.removal_reason:
                raise ValidationError(_(
                    'Captura el motivo del retiro de piezas.'))

    # ============================
    # Compute resultado
    # ============================
    @api.depends('qty_inspected', 'qty_removed')
    def _compute_result(self):
        for rec in self:
            if rec.qty_inspected and rec.qty_removed == 0:
                rec.result = 'conforme'
            elif rec.qty_removed and rec.qty_inspected:
                rec.result = 'conforme_con_retiros'
            elif not rec.result:
                rec.result = False

    # ============================
    # Folio (secuencia mensual)
    # ============================
    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if not vals.get('name') or vals.get('name') == 'Nuevo':
                vals['name'] = self.env['ir.sequence'].next_by_code(
                    'amunet.process.inspection'
                ) or 'INP/Nuevo'
        return super().create(vals_list)

    # ============================
    # Acciones
    # ============================
    def _amunet_signature_allowed_methods(self):
        return {'_signature_action_sign': _('Firmar inspeccion de proceso')}

    def action_sign(self):
        """Firma la inspeccion. A partir de aqui es inmutable."""
        self.ensure_one()
        self._check_can_sign()
        return self.env['amunet.generic.signature.wizard'].open_for(
            self,
            '_signature_action_sign',
            _('Firmar inspeccion de proceso'),
            _('Firma de inspeccion %s.') % self.name,
        )

    def _check_can_sign(self):
        for rec in self:
            if rec.state == 'signed':
                continue
            # Validar grupos y requisitos por tipo
            if rec.inspection_type == 'qc_formal':
                # La inspeccion de QC solo exige piezas analizadas. El
                # detalle va en Observaciones; la liberacion formal de lote
                # (conforme/rechazo) vive aparte en Calidad.
                if not rec.qty_inspected:
                    raise UserError(_(
                        'Captura cuantas piezas analizaste.'))
                if not (
                    self.env.user.has_group('amunet_quality.group_quality_user')
                    or self.env.user.has_group('amunet_quality.group_quality_supervisor')
                    or self.env.user.has_group('amunet_quality.group_quality_manager')
                ):
                    raise UserError(_(
                        'Solo personal de Calidad puede firmar '
                        'inspecciones formales de QC.'))
            elif rec.inspection_type == 'production_supervision':
                # La supervision de produccion solo requiere PIN (y una
                # observacion opcional); NO exige resultado ni piezas
                # inspeccionadas.
                if not (
                    self.env.user.has_group('amunet_production.group_production_supervisor')
                    or self.env.user.has_group('amunet_quality.group_quality_supervisor')
                ):
                    raise UserError(_(
                        'Solo el supervisor de produccion (o un '
                        'supervisor de QC) puede firmar la supervision.'))

    def _signature_action_sign(self):
        self.ensure_one()
        self._check_can_sign()
        for rec in self:
            if rec.state == 'signed':
                continue
            rec.with_context(amunet_process_signature_write=True).write({
                'state': 'signed',
                'signed_by_id': self.env.user.id,
                'signed_date': fields.Datetime.now(),
            })
            if rec.inspection_type == 'production_supervision':
                rec.message_post(body=_(
                    'Supervision firmada por %(u)s.'
                ) % {'u': self.env.user.display_name})
            else:
                rec.message_post(body=_(
                    'Inspeccion firmada por %(u)s.'
                ) % {'u': self.env.user.display_name})
        return True

    def write(self, vals):
        signature_fields = {'state', 'signed_by_id', 'signed_date'}
        if (
            set(vals).intersection(signature_fields)
            and not self.env.context.get('amunet_process_signature_write')
            and not self.env.su
        ):
            raise UserError(_(
                'La firma de inspeccion solo puede registrarse desde el '
                'wizard de firma electronica.'
            ))
        # Una vez firmada, no se permite editar campos relevantes.
        protected = {
            'inspection_type', 'production_id', 'workcenter_id',
            'workorder_id', 'lot_id', 'lot_name', 'inspector_id',
            'inspection_date', 'qty_inspected', 'qty_removed',
            'removal_reason', 'notes', 'result',
        }
        for rec in self:
            if (
                rec.state == 'signed'
                and set(vals).intersection(protected)
                and not self.env.user.has_group('amunet_quality.group_quality_manager')
            ):
                raise UserError(_(
                    'La inspeccion %s ya esta firmada y es inmutable '
                    '(ISO 13485 4.2.5). Solo un Manager de Calidad '
                    'puede modificarla.') % rec.name)
        return super().write(vals)

    def unlink(self):
        for rec in self:
            if rec.state == 'signed' and not self.env.user.has_group(
                    'amunet_quality.group_quality_manager'):
                raise UserError(_(
                    'No se puede borrar una inspeccion firmada. '
                    'Cancelar a traves de CAPA si fue erronea.'))
        return super().unlink()
