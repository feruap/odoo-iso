# -*- coding: utf-8 -*-
from odoo import api, fields, models, _
from odoo.exceptions import ValidationError


AREA_SELECTION_CONFIG = [
    ('GE', 'Generales (PNOGE)'),
    ('PR', 'Produccion (PNOPR)'),
    ('CC', 'Control de Calidad (PNOCC)'),
    ('AS', 'Aseguramiento de Calidad (PNOAS)'),
    ('AL', 'Almacen (PNOAL)'),
    ('IN', 'Ingenieria (PNOIN)'),
    ('RH', 'Recursos Humanos (PNORH)'),
    ('OTRO', 'Otra'),
]


class AmunetDocumentoFirmaConfig(models.Model):
    _name = 'amunet.documento.firma.config'
    _description = 'Politica de firmas de documentos controlados'
    _order = 'sequence, name'
    _inherit = ['mail.thread']

    name = fields.Char(string='Nombre de la politica', required=True, tracking=True)
    sequence = fields.Integer(default=10)
    active = fields.Boolean(default=True, tracking=True)
    area = fields.Selection(
        AREA_SELECTION_CONFIG, string='Aplica al area',
        help='Esta politica se usa para documentos del area indicada. '
             'Dejalo vacio si quieres una politica que aplique a todas las areas.',
        tracking=True)

    revisor_user_ids = fields.Many2many(
        'res.users', 'amunet_firma_config_revisor_rel',
        'config_id', 'user_id',
        string='Pueden revisar',
        help='Usuarios habilitados para ser asignados como revisores. '
             'Si lo dejas vacio, cualquiera puede ser revisor.',
        tracking=True)
    revisor_default_id = fields.Many2one(
        'res.users', string='Revisor por defecto',
        help='Se selecciona automaticamente al crear un nuevo documento en esta area.',
        tracking=True)

    autorizador_user_ids = fields.Many2many(
        'res.users', 'amunet_firma_config_autorizador_rel',
        'config_id', 'user_id',
        string='Pueden autorizar',
        help='Usuarios habilitados para ser asignados como autorizadores. '
             'Tipicamente: Responsable Sanitario y Direccion General.',
        tracking=True)
    autorizador_default_id = fields.Many2one(
        'res.users', string='Autorizador por defecto',
        help='Se selecciona automaticamente al crear un nuevo documento en esta area. '
             'Usalo cuando siempre autoriza la misma persona.',
        tracking=True)

    descripcion = fields.Text(
        string='Notas',
        help='Notas internas sobre esta politica. No afecta el comportamiento.')

    @api.constrains('revisor_default_id', 'revisor_user_ids')
    def _check_revisor_default(self):
        for r in self:
            if r.revisor_default_id and r.revisor_user_ids \
                    and r.revisor_default_id not in r.revisor_user_ids:
                raise ValidationError(_(
                    'El revisor por defecto (%s) debe estar dentro de la lista '
                    '"Pueden revisar". Agregalo o cambialo.'
                ) % r.revisor_default_id.name)

    @api.constrains('autorizador_default_id', 'autorizador_user_ids')
    def _check_autorizador_default(self):
        for r in self:
            if r.autorizador_default_id and r.autorizador_user_ids \
                    and r.autorizador_default_id not in r.autorizador_user_ids:
                raise ValidationError(_(
                    'El autorizador por defecto (%s) debe estar dentro de la lista '
                    '"Pueden autorizar". Agregalo o cambialo.'
                ) % r.autorizador_default_id.name)

    @api.model
    def _find_for_area(self, area):
        """Devuelve la politica vigente para el area dada, o la "Todas las areas" si no hay especifica."""
        config = self.search([('area', '=', area), ('active', '=', True)], limit=1)
        if not config:
            config = self.search([('area', '=', False), ('active', '=', True)], limit=1)
        return config
