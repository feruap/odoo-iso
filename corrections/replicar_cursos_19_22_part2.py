# -*- coding: utf-8 -*-
# Parte 2 capacitacion: replicar de staging a prod los cursos de renovacion
# "Julio 2026" (staging ids 19-22) + su evidencia (PDF de asistencia) + los 13
# registros de capacitacion ligados. Autorizado por Fernando 2026-07-11.
# Datos extraidos de staging a /tmp/part2.json (IDs de empleados/usuarios son
# consistentes entre staging y prod, verificado). Idempotente.
import json
import base64  # noqa

data = json.load(open('/tmp/part2.json'))
CTX = {'tracking_disable': True, 'mail_create_nolog': True, 'mail_notrack': True}
Course = env['hr.training.course'].with_context(**CTX)
Att = env['ir.attachment']
Reg = env['amunet.registro.capacitacion'].with_context(**CTX)

id_map = {}
c_created = c_reused = a_created = 0
for c in data['cursos']:
    ex = Course.search([('name', '=', c['name'])], limit=1)
    if ex:
        course = ex
        c_reused += 1
    else:
        vals = {
            'name': c['name'],
            'state': c['state'],
            'date_start': c['date_start'] or False,
            'date_end': c['date_end'] or False,
            'validez_meses': c['validez_meses'],
            'tipo_evaluacion': c['tipo_evaluacion'],
            'nota_minima_aprobatoria': c['nota_minima_aprobatoria'],
            'speaker_id': c['speaker_id'] or False,
            'speaker_confirmed': c['speaker_confirmed'],
            'hr_confirmed': c['hr_confirmed'],
            'hr_confirmed_by': c['hr_confirmed_by'] or False,
            'sgc_notes': c['sgc_notes'] or False,
            'participant_ids': [(6, 0, c['participant_ids'])],
        }
        # Prod puede tener una version mas vieja del modulo (le falta
        # tipo_evaluacion, etc.). Solo enviar campos que existen en prod.
        vals = {k: v for k, v in vals.items() if k in Course._fields}
        course = Course.create(vals)
        c_created += 1
    id_map[str(c['staging_id'])] = course.id
    if c['att_datas']:
        exa = Att.search([('res_model', '=', 'hr.training.course'),
                          ('res_id', '=', course.id), ('name', '=', c['att_name'])], limit=1)
        if not exa:
            Att.create({
                'name': c['att_name'], 'type': 'binary', 'datas': c['att_datas'],
                'res_model': 'hr.training.course', 'res_id': course.id,
                'mimetype': c['att_mimetype'],
            })
            a_created += 1
    print("  [CURSO] %s -> prod id %s (asistentes=%s, pdf=%s)" % (
        c['name'][:40], course.id, len(c['participant_ids']), bool(c['att_datas'])))

r_created = r_skip = 0
for r in data['registros']:
    pcid = id_map.get(str(r['course_staging_id']))
    if not pcid:
        continue
    ex = Reg.search([('user_id', '=', r['user_id']), ('hr_course_id', '=', pcid)], limit=1)
    if ex:
        r_skip += 1
        continue
    Reg.create({
        'user_id': r['user_id'],
        'trainer_id': r['trainer_id'] or False,
        'training_type': r['training_type'],
        'training_date': r['training_date'],
        'expiry_date': r['expiry_date'],
        'hr_course_id': pcid,
    })
    r_created += 1

env.cr.commit()
print("CURSOS creados:", c_created, "| reusados:", c_reused, "| PDFs:", a_created)
print("REGISTROS creados:", r_created, "| saltados:", r_skip)
print("MAP staging->prod:", id_map)
