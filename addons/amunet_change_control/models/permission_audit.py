# -*- coding: utf-8 -*-

from odoo import api, fields, models


class AmunetPermissionAuditLog(models.Model):
    _name = 'amunet.permission.audit.log'
    _description = 'Auditoria de cambios de permisos'
    _order = 'create_date desc, id desc'

    changed_by_id = fields.Many2one(
        'res.users',
        string='Modificado por',
        required=True,
        readonly=True,
        default=lambda self: self.env.user,
    )
    target_user_id = fields.Many2one(
        'res.users',
        string='Usuario afectado',
        required=True,
        readonly=True,
        ondelete='cascade',
    )
    change_type = fields.Selection([
        ('groups', 'Cambio de grupos'),
    ], string='Tipo', required=True, readonly=True, default='groups')
    old_groups = fields.Text(string='Grupos anteriores', readonly=True)
    new_groups = fields.Text(string='Grupos nuevos', readonly=True)
    added_groups = fields.Text(string='Grupos agregados', readonly=True)
    removed_groups = fields.Text(string='Grupos retirados', readonly=True)


class ResUsers(models.Model):
    _inherit = 'res.users'

    @api.model_create_multi
    def create(self, vals_list):
        users = super().create(vals_list)
        for user, vals in zip(users, vals_list):
            if vals.get('group_ids'):
                user._amunet_log_group_change(set(), set(user.group_ids.ids))
        return users

    def write(self, vals):
        track_groups = 'group_ids' in vals and not self.env.context.get('amunet_skip_permission_audit')
        before = {}
        if track_groups:
            for user in self.sudo():
                before[user.id] = set(user.group_ids.ids)
        result = super().write(vals)
        if track_groups:
            for user in self.sudo():
                user._amunet_log_group_change(before.get(user.id, set()), set(user.group_ids.ids))
        return result

    def _amunet_log_group_change(self, old_group_ids, new_group_ids):
        if old_group_ids == new_group_ids:
            return
        group_model = self.env['res.groups'].sudo()
        old_groups = group_model.browse(sorted(old_group_ids))
        new_groups = group_model.browse(sorted(new_group_ids))
        added_groups = group_model.browse(sorted(new_group_ids - old_group_ids))
        removed_groups = group_model.browse(sorted(old_group_ids - new_group_ids))
        self.env['amunet.permission.audit.log'].sudo().create({
            'changed_by_id': self.env.user.id,
            'target_user_id': self.id,
            'old_groups': ', '.join(old_groups.mapped('display_name')),
            'new_groups': ', '.join(new_groups.mapped('display_name')),
            'added_groups': ', '.join(added_groups.mapped('display_name')),
            'removed_groups': ', '.join(removed_groups.mapped('display_name')),
        })
