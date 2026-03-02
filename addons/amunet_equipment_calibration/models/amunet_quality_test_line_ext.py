# -*- coding: utf-8 -*-

from odoo import models, fields, api
from odoo.exceptions import ValidationError

class AmunetQualityTestLine(models.Model):
    _inherit = 'amunet.quality.test.line'

    # Campo nuevo para la trazabilidad individual por línea
    equipment_id = fields.Many2one('amunet.equipment', string='Equipo Utilizado', tracking=True)

    @api.constrains('equipment_id', 'value')
    def _check_equipment_validity(self):
        """ 
        Regla Fuerte No. 2 (Tiempo Real):
        No permitir registrar resultados con un equipo Vencido o Fuera de Servicio
        (Aunque se muestre en el menú desplegable, bloquea el guardado)
        """
        for line in self:
            if line.equipment_id:
                # Si el campo estado no es active
                if line.equipment_id.state != 'active':
                    raise ValidationError(f"Auditoría Requerida: El equipo '{line.equipment_id.name}' seleccionado se encuentra '{dict(line.equipment_id._fields['state'].selection).get(line.equipment_id.state)}'. No se autoriza su uso para liberar esta prueba.")
                
                # Validación de vigencia redundante por si el cron no ha corrido
                if line.equipment_id.next_calibration_date and line.equipment_id.next_calibration_date < fields.Date.today():
                    raise ValidationError(f"Auditoría Requerida: El equipo '{line.equipment_id.name}' seleccionado tiene su calibración vencida. No se autoriza su uso.")
