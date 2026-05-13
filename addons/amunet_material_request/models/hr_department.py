from odoo import models, fields, api
from odoo.exceptions import ValidationError


class HrDepartment(models.Model):
    _inherit = 'hr.department'

    material_request_code = fields.Char(
        string='Codigo solicitudes (3 letras)',
        size=3,
        help='Codigo de 3 letras alfabeticas usado en el nombre de '
             'las transferencias de Solicitudes de Material. '
             'Ej: PRO (Produccion), CAL (Calidad), MAN (Mantenimiento).',
    )

    @api.constrains('material_request_code')
    def _check_material_request_code(self):
        for rec in self:
            if rec.material_request_code:
                code = rec.material_request_code
                if len(code) != 3 or not code.isalpha():
                    raise ValidationError(
                        f"El codigo de '{rec.name}' debe ser exactamente "
                        f"3 letras alfabeticas (A-Z). Recibido: '{code}'."
                    )

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if vals.get('material_request_code'):
                vals['material_request_code'] = vals['material_request_code'].upper()
        return super().create(vals_list)

    def write(self, vals):
        if vals.get('material_request_code'):
            vals['material_request_code'] = vals['material_request_code'].upper()
        return super().write(vals)
