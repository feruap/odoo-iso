campos = env['ir.sequence'].fields_get(['implementation','number_reset','number_increment','prefix','padding','suffix'])
for k,v in campos.items():
    print(f"{k}: {v.get('type')}")
