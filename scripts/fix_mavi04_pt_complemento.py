"""
COMPLEMENTO de fix_mavi04_pt_prod_corregido.py
==============================================
El script original resuelve Rasgaduras y Deformidad (sufijos Empaque/Prueba) y
agrega Polvo y Manchas. Le faltan las dos piezas del renglon 7 que pidio Diana
el 22-sep, y que dejan el esquema a medias si no se aplican:

  a) Los 12 PT que hoy tienen 'Sellado' deben pasar a 'Letra adecuada — Empaque'.
     Diana: "Sellado NO aplica a PT; solo a bolsas termosellables (MPBOL)".
  b) Los 69 PT que tienen 'Letra adecuada' sin sufijo deben llevar el sufijo.

Ademas arregla un problema de fondo que afecta a MAVI-16 (ver PASO 3).

CORRER DESPUES del script original.
Solicitado por: Diana Flores - Calidad. Complemento preparado por desarrollo.
"""
Spec   = env['amunet.quality.check.parameter.specification']
Config = env['amunet.quality.parameter.specification.config']

MAVI04 = 145   # 'Aspectos Visuales': el que usan los PT (hay 4 con ese codigo)
MAVI16 = 123
PT_PREFIJOS = ('DM', 'DL', 'DIAM', 'DRAM', 'DEMAM')

def es_pt(cfg):
    c = cfg.product_parameter_rel_id.product_tmpl_id.default_code or ''
    return any(c.upper().startswith(p) for p in PT_PREFIJOS)


# ── PASO 0: quitar los renglones viejos que quedaron duplicados ──────────────
# El script original cambiaba el renglon viejo a "— Empaque" y ademas agregaba
# uno nuevo "— Prueba". En los productos que YA tenian un segundo juego de
# renglones, los viejos se quedaron: el analisis muestra Rasgaduras dos veces,
# una con sufijo y otra sin. El original solo limpiaba 4 bloques por id fijo;
# los afectados son 44. Aqui se buscan por contenido.
VIEJAS_SIN_SUFIJO = [691, 692]   # 'Rasgaduras' y 'Deformidad o deterioro'
print("PASO 0: quitar renglones viejos duplicados")
sobrantes = Config.search([('specification_id', 'in', VIEJAS_SIN_SUFIJO),
                           ('active', '=', True)]).filtered(es_pt)
# solo sobra si su bloque YA tiene el equivalente con sufijo
def tiene_sufijo(cfg):
    hermanos = Config.search([
        ('product_parameter_rel_id', '=', cfg.product_parameter_rel_id.id),
        ('active', '=', True)])
    base = 'Rasgaduras' if cfg.specification_id.id == 691 else 'Deformidad o deterioro'
    return any((h.specification_name or '').startswith(base + ' —') for h in hermanos)

sobrantes = sobrantes.filtered(tiene_sufijo)
print("         renglones a desactivar: %s en %s productos" % (
    len(sobrantes),
    len(set(sobrantes.mapped('product_parameter_rel_id.product_tmpl_id.default_code')))))

# Desactivar el renglon NO afecta a los analisis ya creados: sus lineas son
# copias con su propio nombre, criterio y captura. Se comprobo sobre un clon:
# tras desactivar, el analisis conserva sus renglones y lo capturado. Lo unico
# que cambia es que deja de copiarse a los analisis NUEVOS, que es el objetivo.
env.cr.execute("""SELECT DISTINCT specification_config_id
                  FROM amunet_quality_test_line_detail
                  WHERE specification_config_id = ANY(%s)""", (sobrantes.ids or [0],))
con_capturas = {r[0] for r in env.cr.fetchall()}
if con_capturas:
    print("         de esos, %s ya aparecen en algun analisis; se desactivan "
          "igual y esos analisis no pierden nada" % len(con_capturas))
sobrantes.write({'active': False})
env.cr.flush()
print("         desactivados: %s" % len(sobrantes))

# ── PASO 1: la spec de catalogo con el nombre correcto ───────────────────────
destino = Spec.search([('name', '=', 'Letra adecuada — Empaque'),
                       ('parameter_id', '=', MAVI04)], limit=1)
if not destino:
    destino = Spec.create({'name': 'Letra adecuada — Empaque',
                           'parameter_id': MAVI04,
                           'evaluation_type': 'binary_selection',
                           'sequence': 80, 'active': True})
    print("PASO 1: creada spec de catalogo 'Letra adecuada — Empaque' id=%s" % destino.id)
else:
    print("PASO 1: ya existia 'Letra adecuada — Empaque' id=%s" % destino.id)

# Las specs viejas del catalogo que hay que reemplazar en los PT
viejas = Spec.with_context(active_test=False).search([
    ('parameter_id', '=', MAVI04),
    ('name', 'in', ['Sellado', 'Letra adecuada', 'Letra', 'Adecuado'])])
print("         specs viejas a reemplazar: %s" % [(s.id, s.name) for s in viejas])

# ── PASO 2: apuntar los renglones de PT a la spec correcta ───────────────────
cfgs = Config.search([('specification_id', 'in', viejas.ids), ('active', '=', True)])
cfgs = cfgs.filtered(es_pt)
antes = {}
for c in cfgs:
    antes.setdefault(c.specification_name, 0)
    antes[c.specification_name] += 1
print("\nPASO 2: renglones de PT a corregir: %s" % len(cfgs))
for n, v in sorted(antes.items(), key=lambda x: -x[1]):
    print("         %-28s %s" % (n, v))
cfgs.write({'specification_id': destino.id, 'sequence': 80})
env.cr.flush()

# ── PASO 3: MAVI-16, arreglar el nombre EN EL CATALOGO ───────────────────────
# El nombre que ve la analista es un campo related con store al catalogo: si se
# escribe en el renglon, cualquier recalculo lo revierte. Por eso los dos
# renglones de MAVI-16 volvian a llamarse igual ('Visualizacion Operativa') y
# Diana los veia como duplicados. Se corrige en el catalogo, que es estable.
NOMBRES_MAVI16 = {
    415: 'El color proporcionado corresponde al señalado por el patrón.',
    386: 'Visualización de líneas resultado en rango',
}
print("\nPASO 3: MAVI-16, corregir el catalogo (no el renglon)")
for sid, nombre in NOMBRES_MAVI16.items():
    s = Spec.with_context(active_test=False).browse(sid)
    if not s.exists() or s.parameter_id.id != MAVI16:
        print("         spec %s no es de MAVI-16, se omite" % sid)
        continue
    print("         %s: %r -> %r" % (sid, s.name, nombre[:40]))
    s.name = nombre
env.cr.flush()

# ── PASO 4: specs de catalogo con active en NULL ─────────────────────────────
# Un registro con active en NULL existe pero NO aparece, sin avisar.
sql = ("UPDATE amunet_quality_check_parameter_specification "
       "SET active = true WHERE active IS NULL")
env.cr.execute(sql)
print("\nPASO 4: specs de catalogo con 'active' en NULL corregidas: %s" % env.cr.rowcount)

# ── Verificacion ─────────────────────────────────────────────────────────────
print("\n--- COMO QUEDA EL RENGLON 7 EN LOS PT ---")
env.cr.execute("""
  SELECT sc.specification_name, count(*)
  FROM amunet_quality_parameter_specification_config sc
  JOIN amunet_quality_parameter_product_rel rel ON rel.id=sc.product_parameter_rel_id AND rel.active
  JOIN product_template pt ON pt.id=rel.product_tmpl_id AND pt.active
  WHERE sc.active AND rel.parameter_id=%s
    AND (sc.specification_name ILIKE '%%sellado%%' OR sc.specification_name ILIKE 'letra%%'
         OR sc.specification_name ILIKE 'adecuado%%')
    AND (pt.default_code LIKE 'DM%%' OR pt.default_code LIKE 'DL%%' OR pt.default_code LIKE 'DIAM%%'
         OR pt.default_code LIKE 'DRAM%%' OR pt.default_code LIKE 'DEMAM%%')
  GROUP BY 1 ORDER BY 2 DESC""", (MAVI04,))
for n, v in env.cr.fetchall():
    print("   %-30s %s" % (n, v))

print("\n--- MAVI-16 ---")
env.cr.execute("""
  SELECT sc.specification_name, count(*)
  FROM amunet_quality_parameter_specification_config sc
  JOIN amunet_quality_parameter_product_rel rel ON rel.id=sc.product_parameter_rel_id AND rel.active
  WHERE sc.active AND rel.parameter_id=%s GROUP BY 1 ORDER BY 2 DESC""", (MAVI16,))
for n, v in env.cr.fetchall():
    print("   %-62s %s" % (n[:62], v))

env.cr.commit()
print("\nGuardado.")
