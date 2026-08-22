# Ver cómo está configurada una secuencia MPREC existente
prod = env['product.product'].search([('default_code', '=', 'MPREC01')], limit=1)
seq = prod.lot_sequence_id
if seq:
    print(f"Secuencia de MPREC01:")
    print(f"  code={seq.code}")
    print(f"  prefix={seq.prefix}")
    print(f"  padding={seq.padding}")
    print(f"  number_reset={seq.number_reset}")
    print(f"  amunet_lot_reset_monthly={getattr(seq, 'amunet_lot_reset_monthly', 'N/A')}")
