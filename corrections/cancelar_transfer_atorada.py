# Cancela la transferencia interna AMP/QC/00370 (SPHMC75/76 de Entrada -> Control
# de calidad), que quedo atorada porque esos lotes ya se liberaron y movieron a
# AMP/Existencias por correccion. Autorizado por Fernando 2026-07-17.
pk = env['stock.picking'].sudo().search([('name', '=', 'AMP/QC/00370')], limit=1)
if not pk:
    print('no existe AMP/QC/00370')
else:
    print('antes:', pk.name, pk.state)
    pk.action_cancel()
    print('despues:', pk.name, pk.state)
    env.cr.commit()
