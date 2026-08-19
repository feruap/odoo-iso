from odoo import api, fields, models, _
from odoo.exceptions import ValidationError


class AmunetInformeAuditoria(models.Model):
    _name = 'amunet.informe.auditoria'
    _description = 'Informe de Auditoría Interna'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _rec_name = 'clave'
    _order = 'fecha desc, id'

    clave = fields.Char(string='Clave', readonly=True, copy=False,
        default=lambda self: _('Nuevo'))
    state = fields.Selection([
        ('borrador', 'Borrador'),
        ('firmado', 'Firmado'),
    ], default='borrador', string='Estado', tracking=True)

    # ── Vinculación al plan ────────────────────────────────────────────────
    plan_id = fields.Many2one('amunet.plan.auditoria', string='Plan de auditoría',
        required=True, domain=[('state', '=', 'emitido')])

    # Datos heredados del plan
    no_auditoria = fields.Char(related='plan_id.clave', string='No. Auditoría', store=True)
    tipo = fields.Selection(related='plan_id.tipo', string='Tipo de auditoría')
    fecha = fields.Date(related='plan_id.fecha_inicio', string='Fecha de la auditoría', store=True)
    lider_id = fields.Many2one(related='plan_id.lider_id', string='Auditor Líder', store=True)
    auditor_ids = fields.Many2many(related='plan_id.auditor_ids', string='Auditores internos')
    objetivos = fields.Text(related='plan_id.objetivos', string='Objetivo de la auditoría')
    alcance = fields.Text(related='plan_id.alcance', string='Alcance de la auditoría')

    # Datos propios de identificación
    norma = fields.Char(string='Norma por aplicar', default='ISO 13485:2016')
    area_proceso = fields.Char(string='Área / Proceso auditado')
    quien_atiende_id = fields.Many2one('res.users', string='Nombre de quien atiende la visita',
        domain=[('share', '=', False)])
    cargo_quien_atiende = fields.Char(string='Cargo')

    # ── Criterios (resumen desde el plan) ─────────────────────────────────
    criterios_descripcion = fields.Text(string='Criterios de la auditoría')

    # ── Cuerpo del informe ────────────────────────────────────────────────
    observaciones = fields.Text(string='Observaciones')
    hallazgos = fields.Text(string='Descripción de los Hallazgos de la Auditoría')
    conclusiones = fields.Text(string='Conclusiones de la Auditoría')

    # ── Firma ─────────────────────────────────────────────────────────────
    firma_lider_id = fields.Many2one('res.users', string='Firmado por', readonly=True)
    fecha_firma_lider = fields.Date(string='Fecha de firma', readonly=True)

    # ── Secuencia ─────────────────────────────────────────────────────────

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if vals.get('clave', _('Nuevo')) == _('Nuevo'):
                hoy = fields.Date.context_today(self)
                mm = hoy.strftime('%m')
                yy = hoy.strftime('%y')
                num = self.env['ir.sequence'].next_by_code('amunet.informe.auditoria') or '001'
                vals['clave'] = f'IA{mm}{yy}-{num}'
        return super().create(vals_list)

    @api.onchange('plan_id')
    def _onchange_plan_id(self):
        if self.plan_id and self.plan_id.criterio_ids:
            self.criterios_descripcion = '\n'.join(
                f'• {c.nombre}' + (f': {c.descripcion}' if c.descripcion else '')
                for c in self.plan_id.criterio_ids
            )

    # ── Cargar hallazgos desde Lista de Verificación ──────────────────────

    def action_cargar_hallazgos(self):
        self.ensure_one()
        listas = self.env['amunet.lista.verificacion'].search(
            [('plan_id', '=', self.plan_id.id)], order='id asc')
        if not listas:
            return

        _ETIQUETA_RESP = {'0': '0 — No cumple', '1': '1 — Parcial'}
        _ETIQUETA_SEC = {
            'cumplimiento_legal': 'Cumplimiento Legal',
            'capacidad_area': 'Capacidad del Área',
            'desempeno_area': 'Desempeño del Área',
            'personal': 'Personal',
        }

        bloques = []
        for lista in listas:
            items_hallazgo = lista.env['amunet.lista.verificacion.item'].search([
                ('lista_id', '=', lista.id),
                ('respuesta', 'in', ['0', '1']),
            ], order='seccion, sequence, id')

            if not items_hallazgo:
                continue

            encabezado = f'Lista: {lista.clave}'
            if lista.area_proceso:
                encabezado += f' — {lista.area_proceso}'
            bloques.append(encabezado)

            seccion_actual = None
            for item in items_hallazgo:
                if item.seccion != seccion_actual:
                    seccion_actual = item.seccion
                    bloques.append(f'\n{_ETIQUETA_SEC.get(seccion_actual, seccion_actual)}:')
                linea = f'  • {item.punto}: {_ETIQUETA_RESP.get(item.respuesta, item.respuesta)}'
                if item.observaciones:
                    linea += f' — Observaciones: {item.observaciones}'
                bloques.append(linea)

        self.hallazgos = '\n'.join(bloques) if bloques else self.hallazgos

    # ── Firma electrónica ─────────────────────────────────────────────────

    def _amunet_signature_allowed_methods(self):
        return {
            '_signature_lider': _('Firma del Auditor Líder — Informe de Auditoría'),
        }

    def action_firmar_lider(self):
        self.ensure_one()
        return self.env['amunet.generic.signature.wizard'].open_for(
            self, '_signature_lider',
            _('Auditor Líder'),
            _('Firma del informe de auditoría %s.') % self.clave,
        )

    def _signature_lider(self):
        self.ensure_one()
        self.write({
            'firma_lider_id': self.env.user.id,
            'fecha_firma_lider': fields.Date.today(),
            'state': 'firmado',
        })
        return {'type': 'ir.actions.act_window_close'}

    def action_borrador(self):
        self.write({
            'state': 'borrador',
            'firma_lider_id': False,
            'fecha_firma_lider': False,
        })
