# Marca como supervisada la solucion 280926-01. Pedido por Mery, 28-sep-2026.
# SOLO STAGING.
#
# Se invoca _signature_amunet_supervision directamente porque
# action_amunet_do_supervision solo abre el wizard del PIN, y el PIN no se puede
# teclear desde el shell. El metodo revalida _amunet_check_supervision_signer
# por dentro, asi que la firma pasa por los mismos candados que en la pantalla:
# no la puede firmar quien elaboro, ni nadie fuera del jefe asignado.
MO_ID = 191
mo = env['mrp.production'].browse(MO_ID)
assert mo.amunet_supervision_state == 'requested', \
    'la supervision esta en %s, no en requested' % mo.amunet_supervision_state

firmante = mo.amunet_supervisor_id
print('=== antes ===')
print('  supervision : %s' % mo.amunet_supervision_state)
print('  asignada a  : %s' % firmante.name)
print('  elaboro     : %s' % mo.amunet_elaborated_by_id.name)

mo.with_user(firmante.id)._signature_amunet_supervision()
env.cr.commit()

mo = env['mrp.production'].browse(MO_ID)
print()
print('=== despues ===')
print('  supervision   : %s' % mo.amunet_supervision_state)
print('  supervisada por: %s' % (mo.amunet_supervised_by_id.name or '-'))
print('  fecha          : %s' % mo.amunet_supervised_date)
pend = mo.activity_ids.filtered(lambda a: 'upervis' in (a.summary or ''))
print('  actividad de supervision pendiente: %s' % (pend.mapped('summary') or 'ninguna, se cerro'))
print()
print('=== que se destraba ahora ===')
print('  estado de la orden        : %s' % mo.state)
print('  puede pedir analisis      : %s' % getattr(mo, 'amunet_puede_pedir_analisis', '-'))
print('  solucion terminada        : %s' % mo.amunet_solucion_terminada)
