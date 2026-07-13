# -*- coding: utf-8 -*-
import base64
import io
import logging

from odoo import models, fields, api

_logger = logging.getLogger(__name__)

try:
    import qrcode
except ImportError:
    qrcode = None
    _logger.warning("amunet_n3000_access: libreria 'qrcode' no disponible; el QR no se generara.")


class HrEmployee(models.Model):
    _inherit = 'hr.employee'

    n3000_card_no = fields.Char(
        string='Tarjeta de acceso (N3000)',
        help='Numero de tarjeta que abre la puerta. Es el contenido del codigo QR.',
        tracking=True,
        groups='hr.group_hr_user',
    )
    n3000_access_enabled = fields.Boolean(
        string='Acceso a puerta habilitado',
        default=True,
        groups='hr.group_hr_user',
    )
    n3000_valid_from = fields.Date(string='Vigente desde', groups='hr.group_hr_user')
    n3000_valid_to = fields.Date(string='Vigente hasta', groups='hr.group_hr_user')
    n3000_qr = fields.Binary(
        string='QR de acceso',
        compute='_compute_n3000_qr',
        groups='hr.group_hr_user',
        help='El empleado muestra este QR a la camara de la puerta para entrar.',
    )

    @api.depends('n3000_card_no')
    def _compute_n3000_qr(self):
        for emp in self:
            value = False
            if emp.n3000_card_no and qrcode:
                qr = qrcode.QRCode(
                    error_correction=qrcode.constants.ERROR_CORRECT_M,
                    box_size=8, border=2,
                )
                qr.add_data(emp.n3000_card_no)
                qr.make(fit=True)
                img = qr.make_image(fill_color='black', back_color='white')
                buf = io.BytesIO()
                img.save(buf, format='PNG')
                value = base64.b64encode(buf.getvalue())
            emp.n3000_qr = value
