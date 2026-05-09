"""Remove legacy broad ACLs for electronic signature PINs.

This script is idempotent and is run through ``odoo shell`` by the deploy
workflow. It removes manual/base-user access to amunet.quality.signature.pin so
only the ACLs declared by amunet_quality remain in force.
"""

PinModel = env['ir.model']._get('amunet.quality.signature.pin')
group_user = env.ref('base.group_user', raise_if_not_found=False)

if PinModel and group_user:
    legacy_acls = env['ir.model.access'].sudo().search([
        ('model_id', '=', PinModel.id),
        ('group_id', '=', group_user.id),
    ])
    for acl in legacy_acls:
        print(f"Removing legacy signature PIN ACL: {acl.name} (id={acl.id})")
    legacy_acls.unlink()
    env.cr.commit()
