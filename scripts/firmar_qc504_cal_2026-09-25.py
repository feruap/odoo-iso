# Cierre de la prueba del rediseno de declaracion: se llena y firma el analisis
# COMPLETO de 0926/01/CAL (QC/2026/00504, 30 pz).
#
# Se capturan los resultados UNO POR UNO, no se fuerza el `verdict`: el dictamen
# de cada linea se COMPUTA desde sus detalles, asi que escribirlo a mano se
# pierde en la siguiente recomputacion y deja el analisis con cara de aprobado
# pero sin datos detras.
#
# Firmas espejo del parcial QC/2026/00495: Diana realiza y verifica, Patricia
# (Responsable Sanitario) autoriza.
import json

QC_ID = 931
DIANA = 64      # Diana Flores Vera  -- Realizo / Verifico
PATY = 68       # Patricia Leany Segundo Ibanez -- Autorizo (RS)

q = env['amunet.quality.check'].browse(QC_ID)
print('== %s  estado inicial: %s ==' % (q.name, q.state))

if q.state == 'draft':
    q.with_user(DIANA).action_start()
    q.invalidate_recordset()
    print('   -> iniciado (%s)' % q.state)

# ---- resultados conformes, por tipo de evaluacion -------------------------
PATRON = {'Muestra negativa': 'result_5',    # solo linea control  -> cumple
          'Muestra positiva': 'result_2'}    # control + prueba    -> cumple
SEGUNDOS = {'Liberación de conjugado': 10.0,  # rango 1-30 s
            'Migración de conjugado': 90.0}   # rango 30-180 s

for linea in q.test_line_ids:
    for d in linea.detail_line_ids:
        t = d.evaluation_type
        if t == 'binary_selection':
            # El evaluador compara contra la frase de binary_option_pass, no
            # contra la clave 'pass'.
            d.result_selection = d.binary_option_pass
        elif t == 'numeric_range':
            d.result_numeric = SEGUNDOS.get(d.name, (d.min_value + d.max_value) / 2.0)
            if 'result_numeric_filled' in d._fields:
                d.result_numeric_filled = True
        elif t == 'vama_multi_check':
            d.multi_check_results_json = json.dumps({'0': PATRON[d.name]})
        else:
            raise Exception('tipo de evaluacion sin cubrir: %s en %s' % (t, d.name))

q.invalidate_recordset()
print()
print('   dictamen por linea:')
for linea in q.test_line_ids:
    print('     %-10s %-46s %s' % (linea.code or '-', linea.name[:46], linea.verdict))
print('   DICTAMEN GLOBAL: %s' % q.global_result)
assert q.global_result == 'pass', 'el analisis no quedo en CUMPLE'

falta = q._get_empty_required_additional_info_fields()
assert not falta, 'info adicional pendiente: %s' % falta

# ---- las tres firmas ------------------------------------------------------
# Se invoca la logica interna porque action_sign_* solo abre el wizard del PIN,
# y el PIN no se puede teclear desde el shell.
q.with_user(DIANA)._action_sign_realized_logic()
q.invalidate_recordset()
print()
print('   Realizo  : %s' % q.user_realized_id.name)
q.with_user(DIANA).sudo()._action_sign_verified_logic()
q.invalidate_recordset()
print('   Verifico : %s' % q.user_verified_id.name)
# Autorizo dispara la finalizacion por dentro (fusion hecha el 22-jul-2026).
q.with_user(PATY).sudo()._action_sign_authorized_logic()
env.cr.commit()

q = env['amunet.quality.check'].browse(QC_ID)
print('   Autorizo : %s' % q.user_authorized_id.name)
print()
print('== resultado ==')
print('   estado   : %s' % q.state)
print('   folio    : %s' % q.analysis_number)
print('   dictamen : %s' % q.global_result)
mo = q.amunet_production_id
print('   orden    : %s  estado=%s  analisis=%s'
      % (mo.name, mo.state, mo.quality_analysis_status))
