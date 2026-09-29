# -*- coding: utf-8 -*-
"""Lo que queda pendiente al 29-sep-2026, por quien lo tiene que resolver."""
import openpyxl
from openpyxl.styles import Font, Alignment, PatternFill, Border, Side
from openpyxl.utils import get_column_letter
B='/tmp/claude-1001/-home-agentia-odoo-odoo-workspace/40e1928e-dd87-4d8e-b8a3-401e8c22dfcd/scratchpad/'

# quien, tema, que falta, detalle, que desbloquea, donde quedo
P = [
 # ---- MERY ----
 ('Mery','Marketplace','Decidir 3 propuestas con duda',
  'Bata desechable AZUL contra COBDE01 que no dice color · Etanol contra MPREC18 que es al 96% · Biotina, no se sabe para que se pide',
  'Cierra 3 de las 15 propuestas abiertas','Propuestas en estado En revision'),
 ('Mery','Marketplace','Clasificación de 24 fichas sin casa',
  'Mobiliario, cómputo, instalaciones y mantenimiento. Las 5 clasificaciones oficiales (MP, MI, SP, ST, PT) son todas de producto sanitario y no los contemplan',
  'Permite codificar 24 de las 45 fichas','Excel Fichas_sin_clave_propuesta_2026-09-29'),
 ('Mery','Marketplace','Validar 21 claves propuestas',
  'Encajan en la codificación actual; 10 necesitan abreviatura nueva. Tras tu visto bueno las libera Documentación',
  'Permite codificar 21 fichas','Excel Fichas_sin_clave_propuesta_2026-09-29, pestaña 21 con clave'),
 ('Mery','Normativa','MPREC llegó a 99',
  'El siguiente reactivo sería MPREC100 y la normativa dice consecutivo de DOS dígitos. Esa serie está llena',
  'Desbloquea el alta de reactivos nuevos','Detectado al codificar el caldo Half Fraser'),
 ('Mery','Laminado','Línea de referencia de las 2 semicuantitativas',
  'SPHMC38 PSA y SPHMC52 TSH la llevan y no está definida: qué anticuerpo y a qué concentración',
  'Cierra las 15 recetas de laminado','Es lo único que falta del cruce de hojas'),
 ('Mery','Soluciones','Procesar la hoja de trabajo que subiste',
  'Soluciones_de_captura_2026-09-28mery.xlsx, subida el 29-sep 19:48 con cantidad de anticuerpo, diluyente y volumen de impresión',
  'Con eso se arman las recetas de las 30 soluciones','Sin abrir todavía'),
 ('Mery','Almacén','Lote PL04092602 en producción',
  'Nació sin la C. Está LIBERADO y su análisis lo firmó la RS, así que el sistema impide renombrarlo. O se queda como testimonio, o se renombra registrando una desviación',
  'Cierra el tema STCPL04 con Karla','Karla ya avisada de las dos opciones'),
 ('Mery','Catálogo','Duplicado muerto STCON01',
  'Control negativo duplicado: STCON01 sin categoría y sin existencia contra STCNL01 con 78 pz y 18 movimientos',
  'Quita una confusión del catálogo','Detectado en el cruce de nombres repetidos'),
 # ---- DIANA / CALIDAD ----
 ('Diana (Calidad)','Calidad','SPHMT03-05 sin parámetros',
  'VPH, Pylorinet y TB-DxNet tienen CERO parámetros y CERO puntos de control: hoy NO SE PUEDEN ANALIZAR. La copia se frenó porque la plantilla archivada trae "Deformidad o deterioro" DOS VECES y el sistema no deja duplicarla',
  'Tres productos vuelven a ser analizables','Preguntado el 28-sep, sin respuesta'),
 ('Diana (Calidad)','Calidad','SPHMC85-88, cancelar 3 análisis',
  'El script arranca cancelando QC/2026/00503, 00504 y 00505, que están vivos. Falta confirmar que se cancelan y con qué motivo, para que quede asentado',
  'Limpia 24 spec_configs duplicados','Preguntado el 28-sep, sin respuesta'),
 ('Diana (Calidad)','Calidad','Regla de la fecha de reanálisis',
  'El análisis la calcula como caducidad menos 30 DÍAS y el lote como menos UN MES: no coinciden en meses de 31 días. Ya se quitó del certificado, pero sigue en la solicitud-reporte y en el lote',
  'Deja una sola fecha en todo el sistema','Avisada el 29-sep'),
 ('Diana (Calidad)','Calidad','STHIS07, 08 y 09 sin descripción',
  'La lista de hisopos iba del 01 al 06; esos tres se quedaron sin texto en reportes y certificados',
  'Completa los certificados de hisopos','Avisada el 29-sep'),
 # ---- KARLA / ALMACEN MP ----
 ('Karla (Almacén MP)','Almacén','4 movimientos de Control de calidad',
  'AMP/STOR/00094 y 00098 sacan 930 cm donde hay 900 · 00100 pide 100 de STCPL04 y quedan 27 · 00119 manda 8,970 piezas a cuarentena de una compra',
  'Cierra la lista de 24 que empezamos','Preguntado el 29-sep'),
 ('Karla (Almacén MP)','Almacén','Conteo físico de los 60 combos fantasma',
  '30 de antidoping saliva en Existencias y 30 de sangre en Control de calidad. La causa ya se cerró y se verificó; falta el conteo para ajustar',
  'Permite ajustar y cerrar el tema con Fernando','Preguntado el 29-sep. Mery pidió NO avisar a Fernando hasta tener el conteo'),
 # ---- STACY / DOCUMENTACION ----
 ('Stacy (Documentación)','Claves','Liberar las 30 claves de soluciones de captura',
  'SPSCA01-28 más SPSCA29 Treponema y SPSCA30 vitamina D',
  'Formaliza el alta de las 30','Avisada el 28-sep'),
 ('Stacy (Documentación)','Claves','Cotejar su Lista Maestra contra Odoo',
  'MPREC35 Ácido cloroáurico figura activa pero el producto se borró · 46 claves de la lista no tienen producto en Odoo',
  'Deja la lista de claves confiable','Actividad en Odoo, vence el 30-sep'),
 ('Stacy (Documentación)','Módulo','amunet_lista_claves no está en producción',
  'El módulo vive solo en staging. Conviene subirlo cuando ella cierre el cotejo',
  'Pone la lista de claves al alcance de todos','Commiteado el 28-sep'),
 # ---- LUIS ----
 ('Luis (Almacén PT)','Catálogo','Dos probetas duplicadas',
  'Probeta 1 L: COPRB05 en catálogo y con movimientos contra PTCRS03 en Distribución sin usar. Igual la de 250 ml',
  'Resuelve 2 duplicados del catálogo','Detectado el 29-sep, sin avisar aún'),
 # ---- DESARROLLO ----
 ('Desarrollo (nosotros)','Marketplace','Aviso de existencia en la solicitud',
  'La solicitud de compra NO muestra lo que ya hay. Con Tris-HCl publicado y 7,999 g en almacén, se puede pedir una compra encima. Mery eligió publicar primero y dejar el aviso para después',
  'Evita comprar lo que ya está','Pospuesto el 29-sep por decisión de Mery'),
 ('Desarrollo (nosotros)','Catálogo','10 pares MPREC/PTREC con el mismo nombre',
  'CHAPS, DTT, HEPES, IPTG, MES, MOPS, TCEP-HCl, Tris base, Tris-HCl, Guanidine. No son duplicados: MPREC es granel y PTREC reenvasado, pero se llaman igual y no hay cómo distinguirlos al pedirlos',
  'Evita que se pida el frasco equivocado','Detectado el 29-sep'),
 ('Desarrollo (nosotros)','Almacén','Cotejar 7 reactivos del conteo de Karla',
  'Sulfato de magnesio, ácido nitriloacético, hidróxido de amonio, SDS, azul brillante, calceína y metilenbis: comparar su conteo físico contra el sistema',
  'Cierra el conteo de los 19 lotes','Karla mandó el conteo el 25-sep'),
 ('Desarrollo (nosotros)','Git','Ramas sin integrar de 4 áreas',
  'RRHH 3, Calidad 2, Almacén 2 una y Documentación una. Ya se les avisó a cada área; falta que respondan',
  'Deja de sonar la alarma diaria del guardián','Avisado el 29-sep'),
]

azul=PatternFill('solid',fgColor='1F4E78'); ambar=PatternFill('solid',fgColor='FFF2CC')
rojo=PatternFill('solid',fgColor='FCE4E4'); verde=PatternFill('solid',fgColor='E8F4E8')
gris=PatternFill('solid',fgColor='F2F2F2')
borde=Border(*[Side(style='thin',color='BFBFBF')]*4)
COLOR={'Mery':ambar,'Diana (Calidad)':rojo,'Karla (Almacén MP)':verde,
       'Stacy (Documentación)':None,'Luis (Almacén PT)':None,'Desarrollo (nosotros)':gris}

def enc(ws,t,sub,cols):
    ws['A1']=t; ws['A1'].font=Font(size=14,bold=True,color='1F4E78')
    ws['A2']=sub; ws['A2'].font=Font(size=9,italic=True,color='808080')
    for i,(h,w) in enumerate(cols,1):
        c=ws.cell(row=4,column=i,value=h); c.font=Font(bold=True,color='FFFFFF'); c.fill=azul
        c.alignment=Alignment(horizontal='center',vertical='center',wrap_text=True); c.border=borde
        ws.column_dimensions[get_column_letter(i)].width=w
    ws.row_dimensions[4].height=30; ws.freeze_panes='A5'

def fila(ws,r,v,rell=None,alto=42):
    for i,x in enumerate(v,1):
        c=ws.cell(row=r,column=i,value=x); c.border=borde
        c.alignment=Alignment(vertical='top',wrap_text=True)
        if rell: c.fill=rell
    ws.row_dimensions[r].height=alto

wb=openpyxl.Workbook()
ws=wb.active; ws.title='Pendientes'
enc(ws,'Lo que falta — 29 de septiembre de 2026',
    'Ordenado por quién lo tiene que resolver. En ámbar lo tuyo, en rojo lo de Calidad, en verde lo de Almacén.',
    [('Quién lo resuelve',20),('Tema',14),('Qué falta',36),('Detalle',66),('Qué desbloquea',32),('Dónde quedó',34)])
r=5
for p in P:
    fila(ws,r,list(p),COLOR.get(p[0])); r+=1

ws2=wb.create_sheet('Resumen')
enc(ws2,'Cuántos pendientes tiene cada quién','Y qué es lo más urgente de cada uno.',
    [('Quién',22),('Pendientes',12),('Lo más urgente',86)])
URG={
 'Mery':'La línea de referencia y la hoja de trabajo: con esas dos se cierran las 15 recetas de laminado.',
 'Diana (Calidad)':'SPHMT03-05: tres productos que HOY no se pueden analizar. Solo falta que confirme si la especificación duplicada se copia una vez.',
 'Karla (Almacén MP)':'El conteo de los 60 combos fantasma: sin él no se puede ajustar ni cerrar el tema con Fernando.',
 'Stacy (Documentación)':'Su cotejo de la Lista Maestra, que vence el 30-sep.',
 'Luis (Almacén PT)':'Las dos probetas duplicadas; todavía no se le avisa.',
 'Desarrollo (nosotros)':'El aviso de existencia: hoy se puede comprar Tris-HCl teniendo 7,999 g.',
}
from collections import Counter
cnt=Counter(p[0] for p in P)
r=5
for quien,n in sorted(cnt.items(), key=lambda x:-x[1]):
    fila(ws2,r,[quien,n,URG.get(quien,'')],COLOR.get(quien),32); r+=1

wb.save(B+'Pendientes_2026-09-29.xlsx')
print('OK: %d pendientes, %d responsables' % (len(P), len(cnt)))
