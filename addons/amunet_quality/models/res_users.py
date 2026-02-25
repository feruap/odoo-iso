# -*- coding: utf-8 -*-
from odoo import models, fields, api

class ResUsers(models.Model):
    _inherit = 'res.users'

    # Restaurando campo necesario para reportes de calidad
    employee_code = fields.Char(string="Código de Empleado", help="Código único para firmas en reportes de calidad.")

    # signature_pin: MOVIDO a modelo independiente 'amunet.quality.signature.pin'
    # No definir aquí para evitar errores de actualización de esquema en docker.

    # ========================================================================
    # CAMPOS COMPUTADOS PARA PERMISOS DE FIRMA
    # ========================================================================
    # Estos campos facilitan la visualización y edición de grupos de calidad
    # desde la vista "Permisos de Firma"

    in_group_quality_user = fields.Boolean(
        string='Analista QC',
        compute='_compute_quality_groups',
        inverse='_inverse_group_quality_user',
        readonly=False,
        help='Puede crear y editar controles de calidad. Puede firmar "Realizó".'
    )

    in_group_quality_supervisor = fields.Boolean(
        string='Supervisor QC',
        compute='_compute_quality_groups',
        inverse='_inverse_group_quality_supervisor',
        readonly=False,
        help='Puede firmar "Verificó" + permisos de Analista.'
    )

    in_group_quality_sanitary = fields.Boolean(
        string='Responsable Sanitario',
        compute='_compute_quality_groups',
        inverse='_inverse_group_quality_sanitary',
        readonly=False,
        help='Puede firmar "Autorizó" + permisos de Supervisor.'
    )

    in_group_quality_manager = fields.Boolean(
        string='Manager QC',
        compute='_compute_quality_groups',
        inverse='_inverse_group_quality_manager',
        readonly=False,
        help='Acceso total: configuración, eliminación + permisos de Responsable Sanitario.'
    )

    @api.depends('group_ids')
    def _compute_quality_groups(self):
        """Calcula si el usuario pertenece a cada grupo de calidad"""
        for user in self:
            # Usar has_group para considerar herencia
            user.in_group_quality_user = user.has_group('amunet_quality.group_quality_user')
            user.in_group_quality_supervisor = user.has_group('amunet_quality.group_quality_supervisor')
            user.in_group_quality_sanitary = user.has_group('amunet_quality.group_quality_sanitary')
            user.in_group_quality_manager = user.has_group('amunet_quality.group_quality_manager')

    def _inverse_group_quality_user(self):
        grp = self.env.ref('amunet_quality.group_quality_user')
        higher = [
            self.env.ref('amunet_quality.group_quality_supervisor'),
            self.env.ref('amunet_quality.group_quality_sanitary'),
            self.env.ref('amunet_quality.group_quality_manager'),
        ]
        for user in self:
            if user.in_group_quality_user:
                user.write({'group_ids': [(4, grp.id)]})
            else:
                commands = [(3, grp.id)] + [(3, h.id) for h in higher]
                user.write({'group_ids': commands})

    def _inverse_group_quality_supervisor(self):
        grp = self.env.ref('amunet_quality.group_quality_supervisor')
        higher = [
            self.env.ref('amunet_quality.group_quality_sanitary'),
            self.env.ref('amunet_quality.group_quality_manager'),
        ]
        for user in self:
            if user.in_group_quality_supervisor:
                user.write({'group_ids': [(4, grp.id)]})
            else:
                commands = [(3, grp.id)] + [(3, h.id) for h in higher]
                user.write({'group_ids': commands})

    def _inverse_group_quality_sanitary(self):
        grp = self.env.ref('amunet_quality.group_quality_sanitary')
        higher = [self.env.ref('amunet_quality.group_quality_manager')]
        for user in self:
            if user.in_group_quality_sanitary:
                user.write({'group_ids': [(4, grp.id)]})
            else:
                commands = [(3, grp.id)] + [(3, h.id) for h in higher]
                user.write({'group_ids': commands})

    def _inverse_group_quality_manager(self):
        grp = self.env.ref('amunet_quality.group_quality_manager')
        for user in self:
            if user.in_group_quality_manager:
                user.write({'group_ids': [(4, grp.id)]})
            else:
                user.write({'group_ids': [(3, grp.id)]})

    # ========================================================================
    # HARDENING: POLÍTICA DE CONTRASEÑAS (21 CFR Part 11 / NOM-241)
    # ========================================================================
    password_last_set = fields.Datetime(
        string='Última actualización de contraseña',
        default=fields.Datetime.now,
        readonly=True,
        help="Fecha en que se cambió la contraseña por última vez."
    )

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if vals.get('password'):
                vals['password_last_set'] = fields.Datetime.now()
        return super(ResUsers, self).create(vals_list)

    def write(self, vals):
        if vals.get('password'):
            vals['password_last_set'] = fields.Datetime.now()
        return super(ResUsers, self).write(vals)

    password_expiration_date = fields.Datetime(
        string='Fecha de Expiración de Contraseña',
        compute='_compute_password_expiration',
        store=True,
        help="Fecha en que la contraseña expirará (90 días desde la última actualización)."
    )

    password_expired = fields.Boolean(
        string='Contraseña Expirada',
        compute='_compute_password_expiration',
        store=True,
        help="Indica si el usuario debe cambiar su contraseña."
    )

    @api.depends('password_last_set')
    def _compute_password_expiration(self):
        """Cálculo de expiración a 90 días (Hardening NOM-241 / 21 CFR Part 11)"""
        from datetime import timedelta
        for user in self:
            if user.password_last_set:
                user.password_expiration_date = user.password_last_set + timedelta(days=90)
                user.password_expired = fields.Datetime.now() > user.password_expiration_date
            else:
                user.password_expiration_date = False
                user.password_expired = False


