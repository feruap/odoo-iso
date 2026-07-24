# Crea/actualiza el PIN de firma de Fernando (uid 67) a 2026. Solicitado por el
# propio Fernando 2026-07-20. Se guarda hasheado (pbkdf2).
Pin = env['amunet.quality.signature.pin'].sudo()
rec = Pin.search([('user_id','=',67)], limit=1)
if rec:
    rec.write({'pin': '2026'}); print('PIN actualizado, rec', rec.id)
else:
    rec = Pin.create({'user_id': 67, 'pin': '2026'}); print('PIN creado, rec', rec.id)
print('check 2026 ->', rec.check_pin('2026'))
env.cr.commit()
