# -*- coding: utf-8 -*-
from odoo import models, fields, api, _

SURFACE_SEL = [
    ('piso', 'Piso'),
    ('paredes_techo', 'Paredes y techo'),
    ('mobiliario', 'Mobiliario'),
]
FREQ_SEL = [
    ('diario', 'Diario'),
    ('semanal', 'Semanal'),
    ('mensual', 'Mensual'),
]
SANITIZER_SEL = [
    ('rotativo', 'Rotativo (Cloro / Sales cuaternarias)'),
    ('alcohol', 'Alcohol 70%'),
]


class AmunetLimpiezaItem(models.Model):
    _name = 'amunet.limpieza.item'
    _description = 'Item de limpieza por area (que se limpia, cada cuando)'
    _order = 'area_id, sequence, surface'

    area_id = fields.Many2one(
        'amunet.temp.area', string='Area', required=True,
        ondelete='cascade', index=True,
        help='Se reutilizan las mismas areas del Monitor de Temperatura.')
    surface = fields.Selection(SURFACE_SEL, string='Que se limpia', required=True)
    name = fields.Char(compute='_compute_name', store=True)
    sequence = fields.Integer(default=10)
    frequency = fields.Selection(FREQ_SEL, string='Frecuencia', required=True, default='diario')
    weekday = fields.Integer(
        string='Dia de la semana (0=Lun..6=Dom)', default=5,
        help='Para frecuencia semanal: en que dia se genera la tarea (default sabado).')
    sanitizer_rule = fields.Selection(
        SANITIZER_SEL, string='Sanitizante', required=True, default='rotativo')
    active = fields.Boolean(default=True)

    _sql_constraints = [
        ('area_surface_uniq', 'unique(area_id, surface)',
         'Ya existe ese item de limpieza para esta area.'),
    ]

    @api.depends('area_id', 'surface')
    def _compute_name(self):
        labels = dict(SURFACE_SEL)
        for r in self:
            r.name = '%s - %s' % (r.area_id.name or '', labels.get(r.surface, ''))

    @api.model
    def _amunet_seed_items(self):
        """Crea los items por area segun su perfil:
        - Almacenes (codigo TMP-ALM*): SOLO Piso diario (mobiliario/equipo es del
          almacenista, fuera de alcance; paredes/techo no aplica rutinario).
        - Resto (Produccion, CC, Estabilidad): Piso y Paredes/techo DIARIO, y
          Mobiliario SEMANAL (alcohol 70%).
        """
        Area = self.env['amunet.temp.area'].sudo().search([('active', '=', True)])
        for area in Area:
            es_almacen = (area.code or '').upper().startswith('TMP-ALM')
            if es_almacen:
                plan = [('piso', 'diario', 'rotativo', 5)]
            else:
                plan = [
                    ('piso', 'diario', 'rotativo', 5),
                    ('paredes_techo', 'diario', 'rotativo', 5),
                    ('mobiliario', 'semanal', 'alcohol', 5),
                ]
            for surface, freq, sani, wd in plan:
                exists = self.sudo().search([
                    ('area_id', '=', area.id), ('surface', '=', surface)], limit=1)
                if not exists:
                    self.sudo().create({
                        'area_id': area.id, 'surface': surface,
                        'frequency': freq, 'sanitizer_rule': sani, 'weekday': wd,
                    })
        return True
