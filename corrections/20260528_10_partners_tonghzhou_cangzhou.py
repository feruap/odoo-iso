# Idempotente: crea/actualiza proveedores Tonghzhou y Cangzhou
def upsert_partner(name, vals):
    p = env['res.partner'].search([('name','=',name)], limit=1)
    if not p:
        p = env['res.partner'].create({'name':name, **vals})
        env.cr.commit()
        print(f"  CREADO {name} id={p.id}")
    else:
        # actualizar solo campos vacios para no pisar datos manuales
        update={k:v for k,v in vals.items() if not getattr(p,k,None)}
        if update:
            p.write(update); env.cr.commit()
            print(f"  ACTUALIZADO {name} id={p.id} ({list(update)})")
        else:
            print(f"  YA OK {name} id={p.id}")
    return p

cn = env.ref('base.cn').id
upsert_partner('Hangzhou Tongzhou Biotechnology Co., Ltd.', {
    'is_company': True, 'company_type':'company', 'country_id':cn,
    'street': 'Room 102, Building 4, No. 191, Xintian Road',
    'street2': 'Yunhe Street, Linping District',
    'city': 'Hangzhou', 'zip': '311100', 'phone': '+86-571-86113700',
    'email': 'info@tongzhoubio.com', 'website': 'https://tongzhoubio.com',
    'ref': 'TONGZHOU-CN',
    'comment': 'Proveedor de hojas maestras (uncut sheets), cassettes y accesorios.\nBank: China CITIC Bank, HANGZHOU Branch.\nAccount No: 8110 8140 1330 2209 277 (USD).\nSWIFT: CIBKCNBJ310.\nBeneficiary: HangZhou Tongzhou Biotechnology Co.,Ltd.\nPayment Terms: 50% confirmacion, 50% 45 dias post-envio.',
})
upsert_partner('Cangzhou ShengFeng Plastic Product Co., Ltd.', {
    'is_company': True, 'company_type':'company', 'country_id':cn,
    'city': 'Cangzhou', 'street': 'Beijing Road, Hebei', 'ref':'CANGZHOU-CN',
    'comment': 'Proveedor de cassettes plasticos impresos por prueba y accesorios.\nBank: BANK OF CHINA CANGZHOU BRANCH\nAccount No: 101370947655\nSWIFT: BKCHCNBJ220',
})
