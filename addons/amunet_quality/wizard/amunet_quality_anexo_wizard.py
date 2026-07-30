# -*- coding: utf-8 -*-
from odoo import models, fields, api


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


class AmunetQualityAnexoWizard(models.TransientModel):
    _name = 'amunet.quality.anexo.wizard'
    _description = 'Captura de Datos del Anexo'

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
            'col7': line.col7,
        }) for line in check.anexo_line_ids]

    def action_guardar_cerrar(self):
        """Escribe las líneas del wizard al QC sin borrar datos del reporte."""
        self.ensure_one()
        check = self.check_id
        AnexoLine = self.env['amunet.quality.anexo.line']

        existing = check.anexo_line_ids.sorted(lambda l: (l.sequence, l.id))
        wizard_lines = self.line_ids.sorted(lambda l: (l.sequence, l.id))
        es_correccion = bool(existing)  # Si ya había datos, es una corrección

        for i, wl in enumerate(wizard_lines):
            vals = {
                'sequence': wl.sequence,
                'muestra':  wl.muestra,
                'col1': wl.col1, 'col2': wl.col2, 'col3': wl.col3,
                'col4': wl.col4, 'col5': wl.col5, 'col6': wl.col6,
                'col7': wl.col7,
            }
            if i < len(existing):
                existing[i].write(vals)
            else:
                AnexoLine.create({'check_id': check.id, **vals})

        # Eliminar sólo las líneas que el usuario quitó del wizard
        for j in range(len(wizard_lines), len(existing)):
            existing[j].unlink()

        # Registrar en el historial del análisis quién capturó/modificó el anexo
        titulo = check.anexo_titulo or 'Anexo'
        usuario = self.env.user.name
        if es_correccion:
            msg = f'<b>Corrección de {titulo}</b> realizada por {usuario}.'
        else:
            msg = f'<b>Captura de {titulo}</b> realizada por {usuario}.'
        check.sudo().message_post(body=msg, message_type='comment', subtype_xmlid='mail.mt_note')

        return {'type': 'ir.actions.act_window_close'}
