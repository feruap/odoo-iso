# Marca, orden por orden, las de junio/julio cuyo analisis de calidad se hizo en
# papel antes de que el flujo existiera en Odoo. El candado que impide sacar un
# lote sin analisis aprobado las deja pasar.
#
# Se enumeran a mano a proposito: no hay corte por fecha, para que ninguna orden
# nueva quede exenta sola. 0926/01/CRD y 0826/01/DCZ NO estan en la lista aunque
# tambien esten en 'to_request': son actuales y su analisis si se debe solicitar.
#
# Detectado al revisar el punto 5 de Luis (dos lotes de DMCRD01 que no se podian
# dar de baja). Al medirlo eran 11 ordenes, no 2.
ORDENES = [
    '0626/01/GNA', '0626/01/TPS', '0626/01/PSC', '0626/01/CRD',
    '0726/01/CAB', '0726/01/DMD', '0726/01/CRD', '0726/01/SAL',
    '0726/01/R02', '0726/02/R03',
]
MOTIVO = ('Analisis de calidad realizado en PAPEL, anterior a que el flujo '
          'existiera en Odoo. Exencion registrada por Desarrollo a peticion de '
          'Almacen PT (Luis), 22-sep-2026.')

MO = env['mrp.production']
for nombre in ORDENES:
    mo = MO.search([('name', '=', nombre)], limit=1)
    if not mo:
        print('  NO EXISTE  %s' % nombre)
        continue
    if mo.quality_analysis_status == 'approved':
        print('  ya aprobada, no se toca  %s' % nombre)
        continue
    if mo.amunet_qc_previo_al_sistema:
        print('  ya marcada  %s' % nombre)
        continue
    mo.write({'amunet_qc_previo_al_sistema': True})
    mo.message_post(body=MOTIVO)
    print('  MARCADA  %-14s %-9s terminada %s  analisis=%s'
          % (nombre, mo.product_id.default_code, str(mo.date_finished)[:10],
             mo.quality_analysis_status))

env.cr.commit()
print('\nordenes marcadas en total: %s'
      % MO.search_count([('amunet_qc_previo_al_sistema', '=', True)]))
