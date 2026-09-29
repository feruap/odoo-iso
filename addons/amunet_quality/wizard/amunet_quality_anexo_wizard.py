# -*- coding: utf-8 -*-
from datetime import timedelta
from odoo import models, fields, api, _
from odoo.exceptions import UserError


class AmunetQualityAnexoWizardLine(models.TransientModel):
    _name = 'amunet.quality.anexo.wizard.line'
    _description = 'Línea temporal de Anexo (Wizard)'
    _order = 'sequence, id'

    wizard_id = fields.Many2one('amunet.quality.anexo.wizard', required=True, ondelete='cascade')
    sequence  = fields.Integer(default=10)
    muestra   = fields.Char(string='# Muestra')
    col1      = fields.Char(string='Col 1')
    col2      = fields.Char(string='Col 2')
    col3      = fields.Char(string='Col 3')
    col4      = fields.Char(string='Col 4')
    col5      = fields.Char(string='Col 5')
    col6      = fields.Char(string='Col 6')
    col7      = fields.Char(string='Col 7')
    col8      = fields.Char(string='Col 8')


class AmunetQualityAnexoWizard(models.TransientModel):
    _name = 'amunet.quality.anexo.wizard'
    _description = 'Captura de Datos del Anexo'
    _transient_max_hours = 48

    def _transient_clean_rows_older_than(self, seconds):
        viejos = self.search([('create_date', '<',
                               fields.Datetime.now() - timedelta(seconds=seconds))])
        if viejos:
            viejos.mapped('line_ids').unlink()
        super()._transient_clean_rows_older_than(seconds)

    check_id = fields.Many2one('amunet.quality.check', required=True, ondelete='cascade')

    # Encabezados (informativos, vienen del QC)
    anexo_titulo = fields.Char(related='check_id.anexo_titulo', readonly=True)
    col1_header  = fields.Char(related='check_id.anexo_col1_header', readonly=True)
    col2_header  = fields.Char(related='check_id.anexo_col2_header', readonly=True)
    col3_header  = fields.Char(related='check_id.anexo_col3_header', readonly=True)
    col4_header  = fields.Char(related='check_id.anexo_col4_header', readonly=True)
    col5_header  = fields.Char(related='check_id.anexo_col5_header', readonly=True)
    col6_header  = fields.Char(related='check_id.anexo_col6_header', readonly=True)
    col7_header  = fields.Char(related='check_id.anexo_col7_header', readonly=True)
    col8_header  = fields.Char(related='check_id.anexo_col8_header', readonly=True)

    # Líneas propias del wizard — no se pierden con onchanges del formulario principal
    line_ids = fields.One2many('amunet.quality.anexo.wizard.line', 'wizard_id', string='Muestras')

    @api.model
    def _load_lines_from_check(self, check):
        """Copia las líneas actuales del QC al wizard para edición."""
        return [(0, 0, {
            'sequence': line.sequence,
            'muestra':  line.muestra,
            'col1': line.col1, 'col2': line.col2, 'col3': line.col3,
            'col4': line.col4, 'col5': line.col5, 'col6': line.col6,
            'col7': line.col7, 'col8': line.col8,
        }) for line in check.anexo_line_ids]

    def _sync_to_check(self):
        """Sincroniza las líneas del wizard al modelo permanente. Devuelve True si era corrección."""
        self.ensure_one()
        check = self.check_id
        # Un analisis firmado es historia y no se toca. El boton que abre la
        # captura ya lo impide, pero AQUI es donde de verdad se escribe: un
        # wizard abierto antes de la firma seguia guardando despues de ella, y
        # ahora los wizard viven 48 horas, asi que es facil que pase.
        motivo = check._amunet_anexo_bloqueado()
        if motivo:
            raise UserError('%s\n\n%s' % (motivo, _(
                'Lo capturado en esta ventana no se guardó. Si hace falta una '
                'corrección, la pide el Responsable Sanitario.')))
        AnexoLine = self.env['amunet.quality.anexo.line']

        existing = check.anexo_line_ids.sorted(lambda l: (l.sequence, l.id))
        wizard_lines = self.line_ids.sorted(lambda l: (l.sequence, l.id))
        es_correccion = bool(existing)

        for i, wl in enumerate(wizard_lines):
            vals = {
                'sequence': wl.sequence,
                'muestra':  wl.muestra,
                'col1': wl.col1, 'col2': wl.col2, 'col3': wl.col3,
                'col4': wl.col4, 'col5': wl.col5, 'col6': wl.col6,
                'col7': wl.col7, 'col8': wl.col8,
            }
            if i < len(existing):
                existing[i].write(vals)
            else:
                AnexoLine.create({'check_id': check.id, **vals})

        for j in range(len(wizard_lines), len(existing)):
            existing[j].unlink()

        return es_correccion

    def action_guardar_progreso(self):
        """Guarda las líneas al análisis sin cerrar el diálogo."""
        self.ensure_one()
        self._sync_to_check()
        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'message': 'Progreso guardado. Puedes seguir capturando con tranquilidad.',
                'type': 'success',
                'sticky': False,
            },
        }

    def action_guardar_cerrar(self):
        """Guarda las líneas al análisis y cierra el diálogo."""
        self.ensure_one()
        es_correccion = self._sync_to_check()

        titulo = self.check_id.anexo_titulo or 'Anexo'
        usuario = self.env.user.name
        msg = (f'<b>Corrección de {titulo}</b> realizada por {usuario}.'
               if es_correccion
               else f'<b>Captura de {titulo}</b> realizada por {usuario}.')
        self.check_id.sudo().message_post(body=msg, message_type='comment', subtype_xmlid='mail.mt_note')

        return {'type': 'ir.actions.act_window_close'}
