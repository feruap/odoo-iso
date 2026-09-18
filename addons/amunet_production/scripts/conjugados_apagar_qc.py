# Los conjugados llevan DOS banderas de analisis y cada candado lee una
# distinta. Mery pidio dejar el analisis apagado hasta revisar la fabricacion,
# asi que se apagan las dos.
t = env['product.template'].search([('amunet_es_conjugado', '=', True)])
print('conjugados: %s' % len(t))
print('antes  -> qc_required=%s  amunet_req_quality_control=%s' % (
    len(t.filtered('qc_required')), len(t.filtered('amunet_req_quality_control'))))
t.write({'qc_required': False, 'amunet_req_quality_control': False})
t.invalidate_recordset()
print('despues-> qc_required=%s  amunet_req_quality_control=%s' % (
    len(t.filtered('qc_required')), len(t.filtered('amunet_req_quality_control'))))
env.cr.commit()
print('COMMIT OK')
