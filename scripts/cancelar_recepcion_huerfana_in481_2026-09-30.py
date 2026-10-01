pk = env['stock.picking'].search([('name', '=', 'AMP/IN/00481')])
print('picking', pk.name, pk.state, 'solicitud', pk.amunet_solicitud_compra_id.name,
      pk.amunet_solicitud_compra_id.state)
pk.action_cancel()
pk.message_post(body=(
    'Cancelada el 30-sep-2026 a peticion de Mery: su solicitud de compra '
    '%s esta cancelada, asi que las 30 hieleras nunca se compraron y esta '
    'entrada no debe validarse. No entro material: ninguna linea quedaba '
    'marcada como surtida. Se cancela y no se borra para que el folio siga '
    'explicando que paso. Queda pendiente en desarrollo que al cancelar una '
    'solicitud se cancelen solas sus recepciones.'
) % pk.amunet_solicitud_compra_id.name)
env.cr.commit()
pk.invalidate_recordset()
print('AHORA ->', pk.state, '| moves:', pk.move_ids.mapped('state'))
