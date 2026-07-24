# -*- coding: utf-8 -*-
# Crea MICAJ17 (Caja Caple ANTIDOPING-NET) y MICAJ18 (Caja Caple COVINET
# Ag-SALIVA) en produccion, reutilizando la logica IDEMPOTENTE de la propia
# migracion 3.30.0 de amunet_quality (ya presente en prod). Solo estos 2
# productos; no toca el resto. Autorizado por Fernando 2026-07-11.
# Ademas imprime un resumen de config de MICAJ16/17/18/19 para revision.
import importlib.util

PATH = '/opt/amunet-addons/amunet_quality/migrations/19.0.3.30.0/post-migrate.py'
spec = importlib.util.spec_from_file_location('mig330', PATH)
mig = importlib.util.module_from_spec(spec)
spec.loader.exec_module(mig)

cr = env.cr
inscc = mig._get_inscc001_id(cr)
pt = mig._get_picking_type_id(cr)
print("INSCC-001 id:", inscc, "| picking_type:", pt)

for caja in [mig.MICAJ17, mig.MICAJ18]:
    r = mig._crear_qp_caja(cr, caja, inscc, pt)
    print("  crear %s -> %s" % (caja['code'], 'creado' if r else 'ya existia / omitido'))

cr.commit()

# Revision de MICAJ16/17/18/19: QP, parametros y spec_configs
cr.execute("""
    SELECT pt.default_code,
           (SELECT COUNT(*) FROM amunet_quality_point_product_product_rel rel
              JOIN product_product pp2 ON pp2.id=rel.product_product_id
             WHERE pp2.product_tmpl_id=pt.id) AS qps,
           (SELECT string_agg(pr.parameter_code, ',' ORDER BY pr.parameter_code)
              FROM amunet_quality_parameter_product_rel pr WHERE pr.product_tmpl_id=pt.id) AS params,
           (SELECT COUNT(*) FROM amunet_quality_parameter_specification_config sc
             WHERE sc.product_tmpl_id=pt.id) AS specs
    FROM product_template pt
    WHERE pt.default_code IN ('MICAJ16','MICAJ17','MICAJ18','MICAJ19')
    ORDER BY pt.default_code
""")
print("=== REVISION MICAJ16-19 (clave | QPs | params | #spec_configs) ===")
for row in cr.fetchall():
    print("  ", row)
print("LISTO")
