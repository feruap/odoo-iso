# -*- coding: utf-8 -*-
"""Ruta de la linea de LAMINADO para las 15 hojas maestras que se laminan aqui.

Explicado por Mery (28-sep-2026). Lo que se hace despues de soluciones y
conjugados: se juntan todos los componentes.

    1. Se surte el material para las impresiones.
    2. El conjugado, ya con su D.O. especial, se IMPRIME en la almohadilla de
       conjugado a un volumen por cm especifico.
    3. En la membrana se imprime la solucion de LINEA DE PRUEBA, especial para
       cada hoja.
    4. Se secan: los conjugados en horno a 37 C por 30 min; las membranas a
       temperatura ambiente por 30 min. Hay excepciones, pero por ahora todo
       igual.
    5. Se LAMINA: sobre la tarjeta de soporte se colocan la membrana, la
       almohadilla absorbente, la(s) de conjugado control y prueba, el filtro o
       las intermedias si hacen falta, y la almohadilla de muestra.
    6. Se CORTA a 0.3 cm.
    7. Se mandan tiras a Calidad para el analisis de cada hoja fabricada. El
       numero depende de la prueba y de si requiere replica.

VOLUMEN DEL CONJUGADO: varia por hoja. Decision de Mery: por ahora 10 ul/cm en
todas, para generalizar, y se pule despues.

El centro "Inyeccion" (id 19) existia sin usarse: es el de las impresiones, y
encaja con la secuencia del catalogo de calificacion (Soluciones > Lectura y
Pretratamiento > Inyeccion > Laminado/Secado/Corte > Encartuchado > Acond 1 y 2).

Idempotente: si la hoja ya tiene la ruta, no la duplica.
"""
P = env['product.product'].sudo()
BOM = env['mrp.bom'].sudo()
OP = env['mrp.routing.workcenter'].sudo()
W = env['mrp.workcenter'].sudo()

ALMACEN   = W.browse(5)    # Almacen Materia Prima
INYECCION = W.browse(19)   # Inyeccion
LAMINADO  = W.browse(7)    # Laminado, Secado y Corte
CALIDAD   = W.browse(9)    # Control de Calidad
for c in (ALMACEN, INYECCION, LAMINADO, CALIDAD):
    assert c.exists(), 'falta un centro de trabajo'

# clave -> (membrana, conj_control, conj_prueba, filtro, intermedia, muestra)
CAPAS = {
 'SPHMC01': ('MPMNC02','SPALMA03','SPALMA01',None,None,'SPALMA04'),
 'SPHMC18': ('MPMNC03','SPALMA03','SPALMA01','SPALMA13','SPALMA09','SPALMA07'),
 'SPHMC19': ('MPMNC03','SPALMA03','SPALMA01','SPALMA13','SPALMA09','SPALMA07'),
 'SPHMC15': ('MPMNC03','SPALMA03','SPALMA02',None,'SPALMA14','SPALMA05'),
 'SPHMC24': ('MPMNC03','SPALMA03','SPALMA01','SPALMA13',None,'SPALMA07'),
 'SPHMC38': ('MPMNC03','SPALMA03','SPALMA01','SPALMA13',None,'SPALMA07'),
 'SPHMC20': ('MPMNC02','SPALMA03','SPALMA01',None,None,'SPALMA05'),
 'SPHMC22': ('MPMNC03','SPALMA03','SPALMA01','SPALMA13',None,'SPALMA07'),
 'SPHMC23': ('MPMNC03','SPALMA03','SPALMA01','SPALMA13',None,'SPALMA07'),
 'SPHMC09': ('MPMNC03','SPALMA03','SPALMA01','SPALMA13',None,'SPALMA07'),
 'SPHMT01': ('MPMNC02','SPALMA03','SPALMA01',None,None,'SPALMA05'),
 'SPHMC07': ('MPMNC03','SPALMA03','SPALMA01','SPALMA13',None,'SPALMA05'),
 'SPHMC45': ('MPMNC02','SPALMA03','SPALMA01',None,None,'SPALMA05'),
 'SPHMC37': ('MPMNC03','SPALMA03','SPALMA01','SPALMA13',None,'SPALMA07'),
 'SPHMC52': ('MPMNC03','SPALMA03','SPALMA01','SPALMA13',None,'SPALMA07'),
}
TARJETA = {'SPHMC09': 'MPTS02'}   # la de 8x30; el resto usa MPTS01

hechas, saltadas = 0, []
for cod, (memb, cctrl, cprue, filt, inter, muestra) in CAPAS.items():
    p = P.search([('default_code','=',cod)], limit=1)
    if not p:
        saltadas.append((cod, 'no existe el producto')); continue
    bom = BOM.search([('product_tmpl_id','=',p.product_tmpl_id.id)], limit=1)
    if not bom:
        saltadas.append((cod, 'no tiene BoM')); continue
    if bom.operation_ids:
        saltadas.append((cod, 'ya tiene %s operaciones' % len(bom.operation_ids))); continue
    corto = (p.name or '').replace('Hoja Maestra ', '').strip()
    tarjeta = TARJETA.get(cod, 'MPTS01')
    capas = ['membrana %s' % memb, 'absorbente', 'conjugado control %s' % cctrl,
             'conjugado prueba %s' % cprue]
    if filt:  capas.append('filtro %s' % filt)
    if inter: capas.append('intermedia %s' % inter)
    capas.append('muestra %s' % muestra)
    PASOS = [
      (5,  'Surtido de materiales - %s' % corto, ALMACEN),
      (10, 'Impresion de conjugado 10 ul/cm en %s - %s' % (cprue, corto), INYECCION),
      (20, 'Impresion de linea de prueba en membrana %s - %s' % (memb, corto), INYECCION),
      (30, 'Secado de conjugado: horno 37 C por 30 min - %s' % corto, LAMINADO),
      (40, 'Secado de membrana: ambiente 30 min - %s' % corto, LAMINADO),
      (50, 'Laminado sobre tarjeta %s: %s - %s' % (tarjeta, ', '.join(capas), corto), LAMINADO),
      (60, 'Corte a 0.3 cm - %s' % corto, LAMINADO),
      (70, 'Muestreo de tiras para analisis de Calidad - %s' % corto, CALIDAD),
      (80, 'Entrega a almacen - %s' % corto, ALMACEN),
    ]
    for seq, nombre, centro in PASOS:
        OP.create({'bom_id': bom.id, 'name': nombre[:250], 'workcenter_id': centro.id,
                   'sequence': seq, 'time_mode': 'manual', 'time_cycle_manual': 1.0})
    hechas += 1
    print('   %-10s %-24s ruta de 9 pasos creada' % (cod, corto[:24]))
env.flush_all(); env.cr.commit()
print('')
print('   creadas: %s     saltadas: %s' % (hechas, len(saltadas)))
for c, m in saltadas: print('      %-10s %s' % (c, m))
