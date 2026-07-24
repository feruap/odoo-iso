Pin = env['amunet.quality.signature.pin'].sudo()
rec = Pin.search([('user_id','=',61)], limit=1)
if rec:
    rec.write({'pin': '2026'}); print('PIN Mery actualizado, rec', rec.id)
else:
    rec = Pin.create({'user_id': 61, 'pin': '2026'}); print('PIN Mery creado, rec', rec.id)
print('check 2026 ->', rec.check_pin('2026'))
env.cr.commit()
