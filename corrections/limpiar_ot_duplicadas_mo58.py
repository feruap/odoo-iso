# Limpia las 7 ordenes de trabajo duplicadas de la MO 58 (0726/02/R01).
# Planificar se ejecuto dos veces (17:53 y 17:55 del 2026-07-10), generando
# dos juegos de las mismas 7 operaciones. El primer juego (321-327) esta done;
# el segundo (328-334) quedo ready/blocked, sin produccion ni tiempos. Se borra
# el segundo juego (duplicado). Confirmado por Fernando.
WO = env['mrp.workorder']
ids = [328, 329, 330, 331, 332, 333, 334]
victims = WO.browse(ids).exists()

assert all(w.production_id.id == 58 for w in victims), 'Alguna WO no pertenece a la MO 58'
assert all((w.qty_produced or 0.0) == 0.0 for w in victims), 'Alguna WO tiene produccion registrada'
assert all(w.state not in ('done', 'progress') for w in victims), 'Alguna WO esta done/en progreso'

antes = WO.search_count([('production_id', '=', 58)])
victims.sudo().unlink()
env.cr.commit()
despues = WO.search_count([('production_id', '=', 58)])

mo = env['mrp.production'].browse(58)
restantes = mo.workorder_ids.sorted('id')
print('WO antes:', antes, '-> despues:', despues)
print('MO state:', mo.state)
print('WO restantes:', restantes.mapped('id'), '| estados:', restantes.mapped('state'))
