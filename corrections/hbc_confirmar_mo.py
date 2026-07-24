# MO 69 (0726/01/HBC): confirma la orden (draft -> confirmed) tras aceptar el
# preflight con excepcion. Autorizado por Fernando 2026-07-20.
mo = env['mrp.production'].browse(69)
print('Antes:', mo.name, mo.state)
if mo.state == 'draft':
    mo.action_confirm()
print('Despues:', mo.name, mo.state, '| reservado?', mo.reservation_state)
env.cr.commit()
