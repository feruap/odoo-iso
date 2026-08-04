"""Solo lectura: nombres de los productos del mensaje de Mery."""
codigos = [
    'MPCAC01','MPCAR07','MPCAR21','MPCAR24','STGOT01','EQCBV01',
    'MPANT04','MPANT05','MPANT07','MPANT08','MPANT10','MPANT12','MPANT13',
    'MPCAR05','SPHMC66',
]
for cod in codigos:
    t = env['product.template'].with_context(active_test=False).search([
        ('default_code','=',cod)], limit=1)
    print(f"  [{cod}] {t.name if t else 'NO ENCONTRADO'}")
