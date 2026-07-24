# Recalcula el estado (vigente/proxima/vencida) de todas las capacitaciones.
# El campo state es almacenado y solo se recomputa al cambiar expiry_date, no
# con el paso del tiempo, por lo que quedan estados congelados (vencidas que
# siguen mostrandose "por vencer"). Este script fuerza el recalculo puntual.
Reg = env['amunet.registro.capacitacion']
estados = ('vigente', 'proxima', 'vencida', 'cancelada')
antes = {s: Reg.search_count([('state', '=', s)]) for s in estados}
recs = Reg.search([])
recs._compute_state()
recs.flush_recordset()
env.cr.commit()
despues = {s: Reg.search_count([('state', '=', s)]) for s in estados}
print('ANTES  :', antes)
print('DESPUES:', despues)
