# Fix de acceso: el modelo amunet.quality.check.equipment.unit solo daba
# lectura a los 3 grupos QC, pero amunet.quality.check lo leen ademas
# base.group_user (todos los internos) y group_quality_sanitary (RS). Al abrir
# un analisis con equipos, esos usuarios truenan al leer equipment_unit_ids.
# Se agrega LECTURA (solo) para RS y usuario interno base. Con xmlid para que
# el -u posterior de amunet_quality los reconozca (update, no duplica).
# Autorizado por Fernando 2026-07-22 (bug reportado por Patricia = RS).
Access = env['ir.model.access'].sudo()
IMD = env['ir.model.data'].sudo()
model = env['ir.model'].sudo().search([('model', '=', 'amunet.quality.check.equipment.unit')], limit=1)
assert model, 'no existe el modelo equipment.unit'

specs = [
    ('access_amunet_quality_check_equipment_unit_sanitary',
     env.ref('amunet_quality.group_quality_sanitary'), 'sanitary'),
    ('access_amunet_quality_check_equipment_unit_base',
     env.ref('base.group_user'), 'base read'),
]
for xmlid_name, group, label in specs:
    existing = Access.search([('model_id', '=', model.id), ('group_id', '=', group.id)], limit=1)
    if existing:
        print('ya existe acceso para', group.name, '-> aseguro solo lectura')
        existing.write({'perm_read': True})
        acc = existing
    else:
        acc = Access.create({
            'name': 'amunet.quality.check.equipment.unit ' + label,
            'model_id': model.id,
            'group_id': group.id,
            'perm_read': True, 'perm_write': False,
            'perm_create': False, 'perm_unlink': False,
        })
        print('creado acceso lectura', label, 'para', group.name)
    if not IMD.search([('module', '=', 'amunet_quality'), ('name', '=', xmlid_name)], limit=1):
        IMD.create({'module': 'amunet_quality', 'name': xmlid_name,
                    'model': 'ir.model.access', 'res_id': acc.id, 'noupdate': False})
        print('  xmlid registrado:', xmlid_name)

env.cr.commit()
print('LISTO')
