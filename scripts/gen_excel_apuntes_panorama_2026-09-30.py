# -*- coding: utf-8 -*-
"""Los apuntes de Mery del 30-sep, convertidos en pendientes con verificacion."""
import openpyxl
from openpyxl.styles import Font, Alignment, PatternFill, Border, Side
from openpyxl.utils import get_column_letter
B='/tmp/claude-1001/-home-agentia-odoo-odoo-workspace/40e1928e-dd87-4d8e-b8a3-401e8c22dfcd/scratchpad/'

# ficha, producto, tu apunte, accion, que verifique, quien, listo para aplicar
A=[
 ('2159','Base caldo Half Fraser granulado 500 g','MPREC29 es este','FUSIONAR con MPREC29',
  'MPREC29 "Medio de cultivo Fraser" existe, 82.5 de existencia y 7 movimientos. Cuadra. Y de paso resuelve lo de MPREC100: ya no hace falta clave nueva',
  'Listo para aplicar','SÍ'),
 ('2157','Báscula de precisión Rhino','Es la EQBSD01 · revisar que también tiene liga','FUSIONAR con EQBSD01',
  'EQBSD01 "Balanza semianalítica digital" existe y YA ESTÁ PUBLICADO: hoy hay dos renglones para lo mismo en el catálogo',
  'Listo para aplicar','SÍ'),
 ('2164','Cubrezapatos desechables','COZAP01 es este','FUSIONAR con COZAP01',
  'COZAP01 "Zapatones", Consumible/EPP, 3 pz y 1 movimiento. Cuadra',
  'Listo para aplicar','SÍ'),
 ('2207','Centrífuga para laboratorio','Eliminar, ya no se compra desde aquí','BORRAR la ficha',
  'Sin movimientos, sin existencia, sin uso. Se puede borrar sin rastro',
  'Listo para aplicar','SÍ'),
 ('2155','Varilla agitadora magnética','Quitar, la compra estuvo mal','BORRAR la ficha',
  'Sin movimientos, sin existencia. Se puede borrar',
  'Listo para aplicar','SÍ'),
 ('2187','Escuadra profesional 9 cm sin bisel','Codificar como COESC01','CODIFICAR COESC01',
  'Abreviatura nueva, no hay escuadras en el catálogo',
  'Listo para aplicar','SÍ'),
 ('2176','Puntero láser verde recargable','Codificar como COPLA01','CODIFICAR COPLA01',
  'Abreviatura nueva',
  'Listo para aplicar','SÍ'),
 ('2167','Tijeras para zurdos 21 cm','¿Hay tijeras en inventario?','CODIFICAR COTIJ01',
  'RESUELTO: busqué y NO hay ninguna tijera en el catálogo. Es alta nueva',
  'Listo para aplicar','SÍ'),
 ('2206','Higrómetro digital termómetro despertador','Revisar cómo está codificado un equipo de uso interno','NO codificar: va por equipo de uso interno',
  'RESUELTO: los equipos de uso interno NO se codifican uno por uno. Hay un producto genérico EQUIPO-USO-INTERNO y el equipo concreto se registra con una solicitud de ingreso (SOL-EQ-0001 a 0003, las tres por validar)',
  'Confirma el criterio','—'),
 ('2205','Termohigrómetro digital HTC-1','Equipo de uso interno','NO codificar: va por equipo de uso interno',
  'Mismo criterio que el anterior',
  'Confirma el criterio','—'),
 ('2150','Tablet uso rudo HOTWAV','Equipo de uso interno','NO codificar: va por equipo de uso interno',
  'Mismo criterio. OJO: esta ficha tiene la solicitud SMP/26/00338 pendiente desde el 21-sep; hay que resolverla antes de tocarla',
  'Confirma el criterio','—'),
 ('2148','Esponja facial de celulosa 12 piezas','es STESP01','NO ESTOY DE ACUERDO, revísalo',
  'STESP01 es "Esponja para toma de muestra", de Distribución, 62 pz. Una esponja facial de celulosa (limpieza) no me parece lo mismo que una esponja de muestreo microbiológico. Si son la misma, la fusiono',
  'Tú decides','—'),
 ('2184','Bote de residuos peligrosos 21 L','COCRP01 · corroborar el volumen','DUDA, revísalo',
  'COCRP01 es "Contenedor RPBI para LÍQUIDOS", 15 pz. Un bote de residuos peligrosos suele ser para sólidos. Además COCRP01 no indica volumen, así que no hay con qué comparar los 21 L',
  'Tú decides','—'),
 ('2185','Hielera de unicel No. 4','Ver foto o medidas para saber cuál es','DUDA, revísalo',
  'Lo más cercano es STHIE04 "Hielera con asa", que YA está publicado, 12 movimientos. Pero una hielera de unicel desechable no es una hielera con asa',
  'Tú decides','—'),
 ('2163','Tubo PCR 0.2 ml tapa plana (MUHWA)','¿Es el mismo que el de 0.2 normal?','DUDA, revísalo',
  'COTUB01 "Tubo de 0.2 ml" tiene 19,000 pz y 27 movimientos, y ya está publicado. Misma capacidad. La diferencia sería la tapa plana y que el de MUHWA viene por bolsa de 1000',
  'Tú decides','—'),
 ('2200','Botella boca ancha polietileno ámbar 1000 ml','Hay que ver imagen','FALTA VER LA FOTO',
  'No encontré botellas de polietileno ámbar en el catálogo. Sería abreviatura nueva COBOT',
  'Ver la foto','—'),
 ('2201','Botella boca ancha polietileno ámbar 250 ml','Hay que ver imagen','FALTA VER LA FOTO',
  'Igual que la anterior',
  'Ver la foto','—'),
 ('2175','Jeringa de vidrio borosilicato','Ver foto o medidas','FALTA VER LA FOTO',
  'Existen COJER03, 05, 10 y 50, numeradas por CAPACIDAD y no por consecutivo. Sin saber los ml no se puede asignar clave',
  'Ver la foto','—'),
 ('2178','Microplaca ELISA 96 pozos','Foto para ver cuál es','FALTA VER LA FOTO',
  'Existe "Placa de Elisa" en el catálogo; hay que confirmar si es la misma',
  'Ver la foto','—'),
 ('2153','Placas Petri plásticas 60 x 15 mm','Foto para ver cuál es','FALTA VER LA FOTO',
  'Existen COPLP01 Placa Petri, COPLP02 con división y COPLP03 pequeña. Hay que ver si el 60x15 es una de esas',
  'Ver la foto','—'),
 ('2197','Termómetro Brannan inmersión parcial','Foto para ver cuál es','FALTA VER LA FOTO',
  'Existe EQTRV01 "Termómetro de varilla". Hay que ver si es el mismo',
  'Ver la foto','—'),
 ('2174','Probeta plástico 10 ml graduada','Ver compras para saber si se da de alta','PREGUNTAR A COMPRAS',
  'Existen COPRB01 a 05, todas de CRISTALERÍA; esta es de plástico',
  'Compras','—'),
 ('2165','Puntas de pipeta 5 ml','Ver compras para saber si se da de alta','PREGUNTAR A COMPRAS',
  'Existen COPUN01 a 05: blancas 100 µl, amarillas 200 µl y azules 1 ml. No hay de 5 ml',
  'Compras','—'),
]
azul=PatternFill('solid',fgColor='1F4E78'); verde=PatternFill('solid',fgColor='E8F4E8')
ambar=PatternFill('solid',fgColor='FFF2CC'); rojo=PatternFill('solid',fgColor='FCE4E4')
borde=Border(*[Side(style='thin',color='BFBFBF')]*4)

def enc(ws,t,sub,cols):
    ws['A1']=t; ws['A1'].font=Font(size=14,bold=True,color='1F4E78')
    ws['A2']=sub; ws['A2'].font=Font(size=9,italic=True,color='808080')
    for i,(h,w) in enumerate(cols,1):
        c=ws.cell(row=4,column=i,value=h); c.font=Font(bold=True,color='FFFFFF'); c.fill=azul
        c.alignment=Alignment(horizontal='center',vertical='center',wrap_text=True); c.border=borde
        ws.column_dimensions[get_column_letter(i)].width=w
    ws.row_dimensions[4].height=32; ws.freeze_panes='A5'

def fila(ws,r,v,rell=None,alto=46):
    for i,x in enumerate(v,1):
        c=ws.cell(row=r,column=i,value=x); c.border=borde
        c.alignment=Alignment(vertical='top',wrap_text=True)
        if rell: c.fill=rell
    ws.row_dimensions[r].height=alto

wb=openpyxl.Workbook(); ws=wb.active; ws.title='Tus 22 apuntes'
enc(ws,'Tus apuntes del panorama, verificados uno por uno',
    'Verde = listo para aplicar, solo di que sí. Ámbar = necesita una foto o preguntar a Compras. Rojo = revisé y no estoy de acuerdo, o hay duda de fondo.',
    [('Ficha',8),('Producto',40),('Tu apunte',30),('Acción',32),('Qué verifiqué',76),('Quién sigue',18),('¿Aplico ya?',12)])
r=5
for a in A:
    acc=a[3]
    col = verde if a[6]=='SÍ' else (rojo if ('NO ESTOY' in acc or 'DUDA' in acc) else ambar)
    fila(ws,r,list(a),col); r+=1

ws2=wb.create_sheet('Resumen')
enc(ws2,'Cómo quedan tus 22 apuntes','Ocho se pueden aplicar en cuanto digas que sí.',
    [('Grupo',30),('Cuántos',11),('Cuáles',96)])
RES=[('Listos para aplicar','8','3 fusiones (MPREC29, EQBSD01, COZAP01) · 2 borrados (centrífuga, varilla) · 3 altas (escuadra, puntero, tijeras)'),
     ('Resueltos por mí, confirma el criterio','3','Higrómetro, Termohigrómetro y Tablet: van por el flujo de equipo de uso interno, NO se codifican'),
     ('Necesitan una foto','6','Las 2 botellas ámbar, jeringa de vidrio, microplaca ELISA, placas Petri y termómetro Brannan'),
     ('Revisé y no estoy de acuerdo','1','Esponja facial contra STESP01: una es de limpieza y la otra de toma de muestra'),
     ('Duda de fondo','3','Bote de residuos (líquidos vs sólidos), hielera de unicel, tubo PCR tapa plana'),
     ('Preguntar a Compras','2','Probeta de plástico 10 ml y puntas de 5 ml: no existen equivalentes')]
for n,f in enumerate(RES):
    col = verde if f[1]=='8' else (rojo if f[1] in ('1','3') and 'acuerdo' in f[0] else ambar)
    fila(ws2,5+n,list(f),col,36)

wb.save(B+'Apuntes_panorama_2026-09-30.xlsx')
print('OK: %d apuntes' % len(A))
