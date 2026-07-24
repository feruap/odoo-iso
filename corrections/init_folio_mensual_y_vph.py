# -*- coding: utf-8 -*-
# Ajuste puntual tras activar el reinicio MENSUAL de folios (2026-07-13):
#  1) Marcar amunet_last_period='072026' en las secuencias de productos que YA
#     tienen ordenes de julio, para que NO reinicien a mitad de mes (conservan
#     su numeracion de julio). Los que NO tienen orden de julio quedan en NULL
#     -> su primera orden de julio saldra con 01.
#  2) Corregir la orden en borrador 0726/11/VPH -> 0726/01/VPH (lo que pidio
#     Fernando: la primera del mes debe ser 01) y ajustar la secuencia de VPH.
# NO renombra ordenes confirmadas (folios/lotes regulados) — solo el borrador VPH.
MES = '072026'
PREFIJO = '0726/'  # prefijo de folio de julio 2026 (mmYY/)
Pt = env['product.template']
MO = env['mrp.production']

n_set = 0
for pt in Pt.search([('mo_sequence_id', '!=', False)]):
    seq = pt.mo_sequence_id
    tiene_julio = MO.search_count([
        ('product_id', 'in', pt.product_variant_ids.ids),
        ('name', '=like', PREFIJO + '%'),
    ]) > 0
    if tiene_julio and seq.amunet_last_period != MES:
        seq.amunet_last_period = MES
        n_set += 1
print("secuencias con ordenes de julio marcadas (no reinician a mitad de mes):", n_set)

# VPH: corregir la orden borrador y la secuencia
orden = MO.search([('name', '=', '0726/11/VPH')], limit=1)
if orden:
    if orden.state != 'draft':
        print("OJO: la orden 0726/11/VPH NO esta en borrador (%s) -> NO se renombra" % orden.state)
    elif MO.search_count([('name', '=', '0726/01/VPH')]):
        print("OJO: ya existe 0726/01/VPH -> NO se renombra")
    else:
        orden.name = '0726/01/VPH'
        seq_vph = orden.product_id.product_tmpl_id.mo_sequence_id
        seq_vph.write({'number_next': 2, 'amunet_last_period': MES})
        print("orden 60 renombrada -> 0726/01/VPH | secuencia VPH: next=2, periodo=%s" % MES)
else:
    print("no se encontro la orden 0726/11/VPH")

env.cr.commit()
print("LISTO")
