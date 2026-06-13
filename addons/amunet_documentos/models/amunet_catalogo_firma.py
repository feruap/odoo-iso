# -*- coding: utf-8 -*-
from odoo import fields, models


class AmunetCatalogoFirma(models.Model):
    _name = 'amunet.catalogo.firma'
    _description = 'Catálogo de firmas electrónicas'
    _auto = False
    _rec_name = 'user_name'
    _order = 'tiene_pin asc, user_name asc'

    user_id = fields.Many2one('res.users', string='Usuario', readonly=True)
    user_name = fields.Char(string='Nombre', readonly=True)
    login = fields.Char(string='Correo electrónico', readonly=True)
    tiene_pin = fields.Boolean(string='PIN configurado', readonly=True)

    def init(self):
        self.env.cr.execute('''
            CREATE OR REPLACE VIEW amunet_catalogo_firma AS (
                SELECT
                    u.id               AS id,
                    u.id               AS user_id,
                    rp.name            AS user_name,
                    u.login            AS login,
                    (p.id IS NOT NULL) AS tiene_pin
                FROM res_users u
                JOIN res_partner rp ON rp.id = u.partner_id
                LEFT JOIN amunet_quality_signature_pin p ON p.user_id = u.id
                WHERE u.active = TRUE AND u.share = FALSE
            )
        ''')
