"""
Configura parámetros QC para DMHBC01 (Prueba rápida de Hemoglobina Cualitativa).
Grupo A — cualitativa normal (mismo patrón que DMHBA01).

14 spec_configs:
  MAVI-04 × 8  — Empaque (polvo/manchas/rasgaduras/letra/deformidad) + Prueba (manchas/rasgaduras/deformidad)
  MAVI-07 × 2  — Muestra negativa (#5) | Muestra positiva (#1-#4) — mavi_07_ternary
  MAVI-09 × 2  — Liberación (1-30 s) | Migración (30-180 s)
  MGA-0486 × 1 — Hermeticidad (ausencia de colorante)
  INC-002 × 1  — Contenido de empaque

Documentos referencia: RAPT-048 / CERPT-048 Hemoglobina cualitativa v1
Autorizado por: Diana Flores (s.controldecalidad@amunet.com.mx)
Fecha: 2026-08-21
"""

# IDs de parámetros maestros (igual a DMHBA01)
PARAM_MAVI04  = 145
PARAM_MAVI07  = 65
PARAM_MAVI09  = 69
PARAM_MGA0486 = 90
PARAM_INC002  = 149

product = env['product.product'].search(
    [('default_code', '=', 'DMHBC01')], limit=1)
if not product:
    product = env['product.product'].with_context(active_test=False).search(
        [('default_code', '=', 'DMHBC01')], limit=1)
if not product:
    print("ERROR: DMHBC01 no encontrado")
    raise SystemExit(1)

tmpl = product.product_tmpl_id
tmpl_id = tmpl.id
print(f"DMHBC01 — tmpl_id={tmpl_id}")

# Asignar códigos de reporte y certificado
tmpl.sudo().write({
    'report_document_code':        'RAPT-048',
    'report_version':              1,
    'report_replaces_version':     False,
    'certificate_document_code':   'CERPT-048',
    'certificate_version':         1,
    'certificate_replaces_version': False,
})
print("  Códigos asignados: RAPT-048 v1 / CERPT-048 v1")

# Crear ParamRels
ParamRel = env['amunet.quality.parameter.product.rel']
Param    = env['amunet.quality.check.parameter']
param_ids = [PARAM_MAVI04, PARAM_MAVI07, PARAM_MAVI09, PARAM_MGA0486, PARAM_INC002]
rels = {}
for pid in param_ids:
    param = Param.browse(pid)
    rel = ParamRel.search([('product_tmpl_id','=',tmpl_id),('parameter_id','=',pid)], limit=1)
    if not rel:
        rel = ParamRel.create({
            'product_tmpl_id': tmpl_id,
            'parameter_id':    pid,
            'parameter_code':  param.code,
            'parameter_name':  param.name,
        })
        print(f"  ParamRel creado: {param.code}")
    rels[pid] = rel.id

env.cr.commit()

# Limpiar y recrear spec_configs
for pid, rel_id in rels.items():
    env.cr.execute(
        "DELETE FROM amunet_quality_parameter_specification_config WHERE product_parameter_rel_id=%s",
        (rel_id,))

rel04 = rels[PARAM_MAVI04]
rel07 = rels[PARAM_MAVI07]
rel09 = rels[PARAM_MAVI09]
relM  = rels[PARAM_MGA0486]
relI  = rels[PARAM_INC002]

# MAVI-04 (8 inspecciones visuales)
mavi04 = [
    (706,'Empaque: Polvo',               'Sin polvo',                  10),
    (707,'Empaque: Manchas o suciedad',  'Sin manchas o suciedad',     20),
    (708,'Empaque: Rasgaduras',          'Sin rasgaduras',             30),
    (709,'Empaque: Letra adecuada',      'Letra adecuada',             40),
    (710,'Empaque: Deformidad o deterioro','Sin deformidad o deterioro',50),
    (711,'Prueba: Manchas',              'Sin manchas',                60),
    (712,'Prueba: Rasgaduras',           'Sin rasgaduras',             70),
    (713,'Prueba: Deformidad o deterioro','Sin deformidad o deterioro',80),
]
for spec_id, name, criteria, seq in mavi04:
    env.cr.execute("""
        INSERT INTO amunet_quality_parameter_specification_config
          (product_parameter_rel_id,specification_id,specification_name,
           evaluation_type,acceptance_criteria,
           binary_option_pass,binary_option_fail,
           min_value,max_value,sequence,
           create_date,write_date,create_uid,write_uid)
        VALUES(%s,%s,%s,'binary_selection',%s,'','',%s,%s,%s,NOW(),NOW(),1,1)
    """, (rel04, spec_id, name, criteria, 0, 0, seq))

# MAVI-07 (mavi_07_ternary — formato PT)
env.cr.execute("""
    INSERT INTO amunet_quality_parameter_specification_config
      (product_parameter_rel_id,specification_id,specification_name,
       evaluation_type,acceptance_criteria,
       min_value,max_value,sequence,
       create_date,write_date,create_uid,write_uid)
    VALUES
      (%s,628,'Muestra negativa','mavi_07_ternary','#5',              0,0,10,NOW(),NOW(),1,1),
      (%s,629,'Muestra positiva','mavi_07_ternary','#1, #2, #3 y #4',0,0,20,NOW(),NOW(),1,1)
""", (rel07, rel07))

# MAVI-09 (tiempos)
env.cr.execute("""
    INSERT INTO amunet_quality_parameter_specification_config
      (product_parameter_rel_id,specification_id,specification_name,
       evaluation_type,acceptance_criteria,
       min_value,max_value,sequence,
       create_date,write_date,create_uid,write_uid)
    VALUES
      (%s,71,'Liberación de conjugado','numeric_range','1 a 30 segundos',  0,0,10,NOW(),NOW(),1,1),
      (%s,72,'Migración de conjugado', 'numeric_range','30 a 180 segundos',0,0,20,NOW(),NOW(),1,1)
""", (rel09, rel09))

# MGA-0486 (hermeticidad)
env.cr.execute("""
    INSERT INTO amunet_quality_parameter_specification_config
      (product_parameter_rel_id,specification_id,specification_name,
       evaluation_type,acceptance_criteria,
       binary_option_pass,binary_option_fail,
       min_value,max_value,sequence,
       create_date,write_date,create_uid,write_uid)
    VALUES(%s,385,'Hermeticidad','binary_selection','Ausencia de colorante',
           'Ausencia de colorante','Presencia de colorante',0,0,10,NOW(),NOW(),1,1)
""", (relM,))

# INC-002 (contenido de empaque)
env.cr.execute("""
    INSERT INTO amunet_quality_parameter_specification_config
      (product_parameter_rel_id,specification_id,specification_name,
       evaluation_type,acceptance_criteria,
       binary_option_pass,binary_option_fail,
       min_value,max_value,sequence,
       create_date,write_date,create_uid,write_uid)
    VALUES(%s,705,'Contenido requerido e indicado en manual','binary_selection',
           'Coincidencia con el contenido especificado en el manual vigente. Presencia del dispositivo de prueba y desecante en empaque primario.',
           '','',0,0,10,NOW(),NOW(),1,1)
""", (relI,))

env.cr.commit()
print(f"\n✅ DMHBC01 — 14 controles QC configurados (Grupo A, igual a DMHBA01)")
print("   RAPT-048 v1 / CERPT-048 v1 asignados.")
