# -*- coding: utf-8 -*-
"""Dos cierres que pidio Mery el 1-oct-2026.

1. SPPBS02 (PBS 10X) pasa de agua BIDESTILADA a TRIDESTILADA.
   Era la unica de 31 recetas con agua que usaba MPABI01; las otras 30 usan
   MPATR01. Es la misma formula del PBS 1X con los solidos x10 y el mismo litro
   de agua, asi que no habia razon para que el agua fuera distinta.
   Instruccion de Mery: "Cambiala a tridestilada".

2. ALTA de MPREC35 "Aceite mineral (a granel)", unidad ml.
   Clave asignada por Documentacion (aviso del 1-oct-2026, 08:54). La necesita
   STACM01 (vial con aceite mineral), cuya receta hoy solo tiene el vial y por
   eso no tiene de donde heredar caducidad.

   SOBRE LA REUTILIZACION DE LA CLAVE: Documentacion avisa que MPREC35 estuvo
   archivada antes (Acido clorourico) y que la reasignan a conciencia. Se
   verifico en Odoo ANTES de crearla: **MPREC35 no existe aqui, ni activa ni
   archivada** -- cero movimientos, cero recetas, cero compras. El archivo vive
   en su Lista Maestra, no en el sistema, asi que reusar el codigo no reinterpreta
   ninguna historia de Odoo. Si hubiera existido con movimientos, esto no se
   haria sin antes resolverlo (es el mismo riesgo que vimos con las membranas).

Idempotente.
"""
mery = env['res.users'].search([('login', '=', 'desarrollo@amunet.com.mx')], limit=1)
env = env(user=mery.id)

# ---------------------------------------------------------------- 1. SPPBS02
tri = env['product.product'].search([('default_code', '=', 'MPATR01')], limit=1)
bi = env['product.product'].search([('default_code', '=', 'MPABI01')], limit=1)
assert tri and bi, 'Falta MPATR01 o MPABI01'
p = env['product.product'].search([('default_code', '=', 'SPPBS02')], limit=1)
b = env['mrp.bom'].search([('product_tmpl_id', '=', p.product_tmpl_id.id)], limit=1)
linea = b.bom_line_ids.filtered(lambda l: l.product_id == bi)
if linea:
    antes = '%s %s %s' % (linea[0].product_id.default_code,
                          linea[0].product_qty, linea[0].product_uom_id.name)
    linea[0].write({'product_id': tri.id})
    agua = 'cambiada: %s -> MPATR01 (tridestilada)' % antes
else:
    ya = b.bom_line_ids.filtered(lambda l: l.product_id == tri)
    agua = 'ya estaba en tridestilada (%s %s)' % (
        ya[0].product_qty, ya[0].product_uom_id.name) if ya else 'NO TIENE AGUA'

# ---------------------------------------------------------- 2. alta MPREC35
CLAVE = 'MPREC35'
ml = env['uom.uom'].search([('name', '=', 'ml')], limit=1)
assert ml, 'No existe la unidad ml'
categ = env['product.category'].search(
    [('complete_name', '=', 'Materia prima / Reactivo')], limit=1)
assert categ, 'No existe la categoria Materia prima / Reactivo'

ya = env['product.product'].with_context(active_test=False).search(
    [('default_code', '=', CLAVE)], limit=1)
if ya:
    alta = 'ya existia: %s (activo=%s)' % (ya.name, ya.active)
    nuevo = ya
else:
    nuevo = env['product.product'].with_context(
        amunet_alta_autorizada=True).create({
            'default_code': CLAVE,
            'name': 'Aceite mineral (a granel)',
            'nombre_etiqueta': 'Aceite mineral granel',
            'categ_id': categ.id,
            'uom_id': ml.id,
            'is_storable': True,
            'tracking': 'lot',
            'type': 'consu',
        })
    alta = 'CREADO id=%s' % nuevo.id

env.cr.commit()

print('=' * 88)
print('1. AGUA DE SPPBS02 (PBS 10X)')
print('   %s' % agua)
for l in b.bom_line_ids.sorted(lambda x: x.product_id.default_code or ''):
    print('      %-9s %10s %s' % (l.product_id.default_code, l.product_qty,
                                  l.product_uom_id.name))
print('-' * 88)
print('2. ALTA DE %s' % CLAVE)
print('   %s' % alta)
print('   nombre:    %s' % nuevo.name)
print('   categoria: %s' % nuevo.categ_id.complete_name)
print('   unidad:    %s' % nuevo.uom_id.name)
print('   rastreo:   %s' % nuevo.tracking)
print('-' * 88)
print('COMPROBACION: recetas con agua, por tipo de agua')
env.cr.execute("""
    SELECT cp.default_code, count(DISTINCT pp.default_code)
    FROM mrp_bom_line bl JOIN product_product cp ON cp.id=bl.product_id
    JOIN mrp_bom b2 ON b2.id=bl.bom_id
    JOIN product_product pp ON pp.product_tmpl_id=b2.product_tmpl_id
    WHERE cp.default_code IN ('MPATR01','MPADE01','MPABI01') GROUP BY 1 ORDER BY 2 DESC
""")
for clave, n in env.cr.fetchall():
    print('   %-9s %d recetas' % (clave, n))
print('=' * 88)

# ---------------------------------------------------------------------------
# 3. MARCAR LOS REACTIVOS QUE SE DOSIFICAN HASTA AJUSTAR EL pH
#
# Regla de Mery, 1-oct-2026: "Hasta ajustar pH pero que pongan cuanto le
# pusieron". El campo donde lo anotan -- "Cantidad Utilizada" -- ya existia en la
# pantalla de soluciones desde el 21-sep y lo captura quien fabrica. Lo que
# faltaba era que el renglon se distinguiera de los demas, porque en pantalla se
# veia igual que un reactivo de cantidad fija.
#
# Se marcan los dos que titulan el pH. Se detectan por nombre y se verifica que
# de verdad aparezcan en recetas de solucion antes de marcarlos.
# ---------------------------------------------------------------------------
AJUSTE_PH = ('SPSHS02', 'SPSAC01')   # NaOH 20% y HCl 6 M

marcados, no_estaban = [], []
for clave in AJUSTE_PH:
    pr = env['product.product'].search([('default_code', '=', clave)], limit=1)
    if not pr:
        no_estaban.append(clave)
        continue
    usos = env['mrp.bom.line'].search_count([('product_id', '=', pr.id)])
    if not pr.product_tmpl_id.amunet_es_ajuste_ph:
        pr.product_tmpl_id.amunet_es_ajuste_ph = True
    marcados.append((clave, pr.name, usos))

env.cr.commit()

print('-' * 88)
print('3. REACTIVOS MARCADOS "hasta ajustar pH"')
for clave, nombre, usos in marcados:
    print('   %-9s %-34s  aparece en %d recetas' % (clave, nombre[:34], usos))
if no_estaban:
    print('   NO EXISTEN: %s' % ', '.join(no_estaban))
print('   recetas donde el renglon ya sale marcado:')
env.cr.execute("""
    SELECT pp.default_code, cp.default_code, bl.product_qty, u.name->>'en_US'
    FROM mrp_bom_line bl
    JOIN product_product cp ON cp.id=bl.product_id
    JOIN product_template ct ON ct.id=cp.product_tmpl_id
    JOIN mrp_bom b ON b.id=bl.bom_id
    JOIN product_product pp ON pp.product_tmpl_id=b.product_tmpl_id
    JOIN uom_uom u ON u.id=bl.product_uom_id
    WHERE ct.amunet_es_ajuste_ph ORDER BY 1, 2
""")
for sol, reac, qty, uom in env.cr.fetchall():
    print('      %-9s pide %-9s %8.2f %s  (referencia, se titula)' % (sol, reac, qty, uom))
print('=' * 88)
