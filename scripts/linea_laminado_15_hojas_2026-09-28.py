# -*- coding: utf-8 -*-
"""LINEA DE LAMINADO: ruta de 9 actividades y receta completa de las 15 hojas.

Reproduce en cualquier entorno el estado que se armo en staging el 28-sep-2026,
con el proceso que explico Mery: lo que se hace despues de soluciones y
conjugados, cuando se juntan todos los componentes.

    1. Se surte el material.
    2. El conjugado, ya con su D.O., se imprime en la almohadilla de conjugado a
       volumen por cm. Por ahora 10 ul/cm en todas (decision de Mery: varia por
       hoja, se generaliza y se pule despues).
    3. En la membrana se imprime la solucion de LINEA DE PRUEBA, especial de cada
       hoja.
    4. Secado: conjugado en horno a 37 C por 30 min; membrana a temperatura
       ambiente 30 min. Van como DOS pasos porque son condiciones distintas y
       cada una pide su registro.
    5. Laminado sobre la tarjeta de soporte: membrana, absorbente, conjugado
       control y prueba, filtro o intermedias si hacen falta, y muestra.
    6. Corte a 0.3 cm.
    7. Muestreo de tiras para el analisis de Calidad de cada hoja fabricada.
       LAS TIRAS SE DESCUENTAN del rendimiento de la hoja (Mery, 28-sep-2026).
       Falta el numero por prueba, que lo da Calidad.

OJO CON LA ABSORBENTE: es SPALMA12, la pretratada -- NO MPAAB01, que solo
aparece en 2 recetas ajenas. Staging la habia PERDIDO en las 15 hojas mientras
produccion si la tenia: quien armo las capas nuevas borro la linea que ya
existia. Promover staging sin esto dejaba las 15 hojas de produccion sin
absorbente.

Idempotente: no duplica lineas ni operaciones que ya existan. Los centros de
trabajo se buscan por NOMBRE, no por id, para que funcione en cualquier entorno.
"""
# ── Datos extraidos de staging el 28-sep-2026 ──
RECETA = {
 "SPHMC01": [
  [
   "MPMNC02",
   1.0,
   "Units"
  ],
  [
   "MPTS01",
   1.0,
   "Units"
  ],
  [
   "SPALMA01",
   1.0,
   "Units"
  ],
  [
   "SPALMA03",
   1.0,
   "Units"
  ],
  [
   "SPALMA04",
   1.0,
   "Units"
  ],
  [
   "SPALMA12",
   1.0,
   "Units"
  ]
 ],
 "SPHMC18": [
  [
   "MPMNC03",
   1.0,
   "Units"
  ],
  [
   "MPTS01",
   1.0,
   "Units"
  ],
  [
   "SPALMA01",
   1.0,
   "Units"
  ],
  [
   "SPALMA03",
   1.0,
   "Units"
  ],
  [
   "SPALMA07",
   1.0,
   "Units"
  ],
  [
   "SPALMA09",
   1.0,
   "Units"
  ],
  [
   "SPALMA12",
   1.0,
   "Units"
  ],
  [
   "SPALMA13",
   1.0,
   "Units"
  ]
 ],
 "SPHMC19": [
  [
   "MPMNC03",
   1.0,
   "Units"
  ],
  [
   "MPTS01",
   1.0,
   "Units"
  ],
  [
   "SPALMA01",
   1.0,
   "Units"
  ],
  [
   "SPALMA03",
   1.0,
   "Units"
  ],
  [
   "SPALMA07",
   1.0,
   "Units"
  ],
  [
   "SPALMA09",
   1.0,
   "Units"
  ],
  [
   "SPALMA12",
   1.0,
   "Units"
  ],
  [
   "SPALMA13",
   1.0,
   "Units"
  ]
 ],
 "SPHMC15": [
  [
   "MPMNC03",
   1.0,
   "Units"
  ],
  [
   "MPTS01",
   1.0,
   "Units"
  ],
  [
   "SPALMA02",
   1.0,
   "Units"
  ],
  [
   "SPALMA03",
   1.0,
   "Units"
  ],
  [
   "SPALMA05",
   1.0,
   "Units"
  ],
  [
   "SPALMA12",
   1.0,
   "Units"
  ],
  [
   "SPALMA14",
   1.0,
   "Units"
  ]
 ],
 "SPHMC24": [
  [
   "MPMNC03",
   1.0,
   "Units"
  ],
  [
   "MPTS01",
   1.0,
   "Units"
  ],
  [
   "SPALMA01",
   1.0,
   "Units"
  ],
  [
   "SPALMA03",
   1.0,
   "Units"
  ],
  [
   "SPALMA07",
   1.0,
   "Units"
  ],
  [
   "SPALMA12",
   1.0,
   "Units"
  ],
  [
   "SPALMA13",
   1.0,
   "Units"
  ]
 ],
 "SPHMC38": [
  [
   "MPMNC03",
   1.0,
   "Units"
  ],
  [
   "MPTS01",
   1.0,
   "Units"
  ],
  [
   "SPALMA01",
   1.0,
   "Units"
  ],
  [
   "SPALMA03",
   1.0,
   "Units"
  ],
  [
   "SPALMA07",
   1.0,
   "Units"
  ],
  [
   "SPALMA12",
   1.0,
   "Units"
  ],
  [
   "SPALMA13",
   1.0,
   "Units"
  ]
 ],
 "SPHMC20": [
  [
   "MPMNC02",
   1.0,
   "Units"
  ],
  [
   "MPTS01",
   1.0,
   "Units"
  ],
  [
   "SPALMA01",
   1.0,
   "Units"
  ],
  [
   "SPALMA03",
   1.0,
   "Units"
  ],
  [
   "SPALMA05",
   1.0,
   "Units"
  ],
  [
   "SPALMA12",
   1.0,
   "Units"
  ]
 ],
 "SPHMC22": [
  [
   "MPMNC03",
   1.0,
   "Units"
  ],
  [
   "MPTS01",
   1.0,
   "Units"
  ],
  [
   "SPALMA01",
   1.0,
   "Units"
  ],
  [
   "SPALMA03",
   1.0,
   "Units"
  ],
  [
   "SPALMA07",
   1.0,
   "Units"
  ],
  [
   "SPALMA12",
   1.0,
   "Units"
  ],
  [
   "SPALMA13",
   1.0,
   "Units"
  ]
 ],
 "SPHMC23": [
  [
   "MPMNC03",
   1.0,
   "Units"
  ],
  [
   "MPTS01",
   1.0,
   "Units"
  ],
  [
   "SPALMA01",
   1.0,
   "Units"
  ],
  [
   "SPALMA03",
   1.0,
   "Units"
  ],
  [
   "SPALMA07",
   1.0,
   "Units"
  ],
  [
   "SPALMA12",
   1.0,
   "Units"
  ],
  [
   "SPALMA13",
   1.0,
   "Units"
  ]
 ],
 "SPHMC09": [
  [
   "MPMNC03",
   1.0,
   "Units"
  ],
  [
   "MPTS02",
   1.0,
   "Units"
  ],
  [
   "SPALMA01",
   1.0,
   "Units"
  ],
  [
   "SPALMA03",
   1.0,
   "Units"
  ],
  [
   "SPALMA07",
   1.0,
   "Units"
  ],
  [
   "SPALMA12",
   1.0,
   "Units"
  ],
  [
   "SPALMA13",
   1.0,
   "Units"
  ]
 ],
 "SPHMT01": [
  [
   "MPMNC02",
   1.0,
   "Units"
  ],
  [
   "MPTS01",
   1.0,
   "Units"
  ],
  [
   "SPALMA01",
   1.0,
   "Units"
  ],
  [
   "SPALMA03",
   1.0,
   "Units"
  ],
  [
   "SPALMA05",
   1.0,
   "Units"
  ],
  [
   "SPALMA12",
   1.0,
   "Units"
  ]
 ],
 "SPHMC07": [
  [
   "MPMNC03",
   1.0,
   "Units"
  ],
  [
   "MPTS01",
   1.0,
   "Units"
  ],
  [
   "SPALMA01",
   1.0,
   "Units"
  ],
  [
   "SPALMA03",
   1.0,
   "Units"
  ],
  [
   "SPALMA05",
   1.0,
   "Units"
  ],
  [
   "SPALMA12",
   1.0,
   "Units"
  ],
  [
   "SPALMA13",
   1.0,
   "Units"
  ]
 ],
 "SPHMC45": [
  [
   "MPMNC02",
   1.0,
   "Units"
  ],
  [
   "MPTS01",
   1.0,
   "Units"
  ],
  [
   "SPALMA01",
   1.0,
   "Units"
  ],
  [
   "SPALMA03",
   1.0,
   "Units"
  ],
  [
   "SPALMA05",
   1.0,
   "Units"
  ],
  [
   "SPALMA12",
   1.0,
   "Units"
  ]
 ],
 "SPHMC37": [
  [
   "MPMNC03",
   1.0,
   "Units"
  ],
  [
   "MPTS01",
   1.0,
   "Units"
  ],
  [
   "SPALMA01",
   1.0,
   "Units"
  ],
  [
   "SPALMA03",
   1.0,
   "Units"
  ],
  [
   "SPALMA07",
   1.0,
   "Units"
  ],
  [
   "SPALMA12",
   1.0,
   "Units"
  ],
  [
   "SPALMA13",
   1.0,
   "Units"
  ]
 ],
 "SPHMC52": [
  [
   "MPMNC03",
   1.0,
   "Units"
  ],
  [
   "MPTS01",
   1.0,
   "Units"
  ],
  [
   "SPALMA01",
   1.0,
   "Units"
  ],
  [
   "SPALMA03",
   1.0,
   "Units"
  ],
  [
   "SPALMA07",
   1.0,
   "Units"
  ],
  [
   "SPALMA12",
   1.0,
   "Units"
  ],
  [
   "SPALMA13",
   1.0,
   "Units"
  ]
 ]
}

RUTA = {
 "SPHMC01": [
  [
   5,
   "Almacén Materia Prima",
   "Surtido de materiales - Covinet Ag"
  ],
  [
   10,
   "Inyección",
   "Impresion de conjugado 10 ul/cm en SPALMA01 - Covinet Ag"
  ],
  [
   20,
   "Inyección",
   "Impresion de linea de prueba en membrana MPMNC02 - Covinet Ag"
  ],
  [
   30,
   "Laminado, Secado y Corte",
   "Secado de conjugado: horno 37 C por 30 min - Covinet Ag"
  ],
  [
   40,
   "Laminado, Secado y Corte",
   "Secado de membrana: ambiente 30 min - Covinet Ag"
  ],
  [
   50,
   "Laminado, Secado y Corte",
   "Laminado sobre tarjeta MPTS01: membrana MPMNC02, absorbente, conjugado control SPALMA03, conjugado prueba SPALMA01, muestra SPALMA04 - Covinet Ag"
  ],
  [
   60,
   "Laminado, Secado y Corte",
   "Corte a 0.3 cm - Covinet Ag"
  ],
  [
   70,
   "Control de Calidad",
   "Muestreo de tiras para analisis de Calidad - Covinet Ag"
  ],
  [
   80,
   "Almacén Materia Prima",
   "Entrega a almacen - Covinet Ag"
  ]
 ],
 "SPHMC18": [
  [
   5,
   "Almacén Materia Prima",
   "Surtido de materiales - Dengue IgG/IgM"
  ],
  [
   10,
   "Inyección",
   "Impresion de conjugado 10 ul/cm en SPALMA01 - Dengue IgG/IgM"
  ],
  [
   20,
   "Inyección",
   "Impresion de linea de prueba en membrana MPMNC03 - Dengue IgG/IgM"
  ],
  [
   30,
   "Laminado, Secado y Corte",
   "Secado de conjugado: horno 37 C por 30 min - Dengue IgG/IgM"
  ],
  [
   40,
   "Laminado, Secado y Corte",
   "Secado de membrana: ambiente 30 min - Dengue IgG/IgM"
  ],
  [
   50,
   "Laminado, Secado y Corte",
   "Laminado sobre tarjeta MPTS01: membrana MPMNC03, absorbente, conjugado control SPALMA03, conjugado prueba SPALMA01, filtro SPALMA13, intermedia SPALMA09, muestra SPALMA07 - Dengue IgG/IgM"
  ],
  [
   60,
   "Laminado, Secado y Corte",
   "Corte a 0.3 cm - Dengue IgG/IgM"
  ],
  [
   70,
   "Control de Calidad",
   "Muestreo de tiras para analisis de Calidad - Dengue IgG/IgM"
  ],
  [
   80,
   "Almacén Materia Prima",
   "Entrega a almacen - Dengue IgG/IgM"
  ]
 ],
 "SPHMC19": [
  [
   5,
   "Almacén Materia Prima",
   "Surtido de materiales - Dengue NS1"
  ],
  [
   10,
   "Inyección",
   "Impresion de conjugado 10 ul/cm en SPALMA01 - Dengue NS1"
  ],
  [
   20,
   "Inyección",
   "Impresion de linea de prueba en membrana MPMNC03 - Dengue NS1"
  ],
  [
   30,
   "Laminado, Secado y Corte",
   "Secado de conjugado: horno 37 C por 30 min - Dengue NS1"
  ],
  [
   40,
   "Laminado, Secado y Corte",
   "Secado de membrana: ambiente 30 min - Dengue NS1"
  ],
  [
   50,
   "Laminado, Secado y Corte",
   "Laminado sobre tarjeta MPTS01: membrana MPMNC03, absorbente, conjugado control SPALMA03, conjugado prueba SPALMA01, filtro SPALMA13, intermedia SPALMA09, muestra SPALMA07 - Dengue NS1"
  ],
  [
   60,
   "Laminado, Secado y Corte",
   "Corte a 0.3 cm - Dengue NS1"
  ],
  [
   70,
   "Control de Calidad",
   "Muestreo de tiras para analisis de Calidad - Dengue NS1"
  ],
  [
   80,
   "Almacén Materia Prima",
   "Entrega a almacen - Dengue NS1"
  ]
 ],
 "SPHMC15": [
  [
   5,
   "Almacén Materia Prima",
   "Surtido de materiales - Influenza A+B"
  ],
  [
   10,
   "Inyección",
   "Impresion de conjugado 10 ul/cm en SPALMA02 - Influenza A+B"
  ],
  [
   20,
   "Inyección",
   "Impresion de linea de prueba en membrana MPMNC03 - Influenza A+B"
  ],
  [
   30,
   "Laminado, Secado y Corte",
   "Secado de conjugado: horno 37 C por 30 min - Influenza A+B"
  ],
  [
   40,
   "Laminado, Secado y Corte",
   "Secado de membrana: ambiente 30 min - Influenza A+B"
  ],
  [
   50,
   "Laminado, Secado y Corte",
   "Laminado sobre tarjeta MPTS01: membrana MPMNC03, absorbente, conjugado control SPALMA03, conjugado prueba SPALMA02, intermedia SPALMA14, muestra SPALMA05 - Influenza A+B"
  ],
  [
   60,
   "Laminado, Secado y Corte",
   "Corte a 0.3 cm - Influenza A+B"
  ],
  [
   70,
   "Control de Calidad",
   "Muestreo de tiras para analisis de Calidad - Influenza A+B"
  ],
  [
   80,
   "Almacén Materia Prima",
   "Entrega a almacen - Influenza A+B"
  ]
 ],
 "SPHMC24": [
  [
   5,
   "Almacén Materia Prima",
   "Surtido de materiales - PSA cualitativa"
  ],
  [
   10,
   "Inyección",
   "Impresion de conjugado 10 ul/cm en SPALMA01 - PSA cualitativa"
  ],
  [
   20,
   "Inyección",
   "Impresion de linea de prueba en membrana MPMNC03 - PSA cualitativa"
  ],
  [
   30,
   "Laminado, Secado y Corte",
   "Secado de conjugado: horno 37 C por 30 min - PSA cualitativa"
  ],
  [
   40,
   "Laminado, Secado y Corte",
   "Secado de membrana: ambiente 30 min - PSA cualitativa"
  ],
  [
   50,
   "Laminado, Secado y Corte",
   "Laminado sobre tarjeta MPTS01: membrana MPMNC03, absorbente, conjugado control SPALMA03, conjugado prueba SPALMA01, filtro SPALMA13, muestra SPALMA07 - PSA cualitativa"
  ],
  [
   60,
   "Laminado, Secado y Corte",
   "Corte a 0.3 cm - PSA cualitativa"
  ],
  [
   70,
   "Control de Calidad",
   "Muestreo de tiras para analisis de Calidad - PSA cualitativa"
  ],
  [
   80,
   "Almacén Materia Prima",
   "Entrega a almacen - PSA cualitativa"
  ]
 ],
 "SPHMC38": [
  [
   5,
   "Almacén Materia Prima",
   "Surtido de materiales - PSA semicuantitativa"
  ],
  [
   10,
   "Inyección",
   "Impresion de conjugado 10 ul/cm en SPALMA01 - PSA semicuantitativa"
  ],
  [
   20,
   "Inyección",
   "Impresion de linea de prueba en membrana MPMNC03 - PSA semicuantitativa"
  ],
  [
   30,
   "Laminado, Secado y Corte",
   "Secado de conjugado: horno 37 C por 30 min - PSA semicuantitativa"
  ],
  [
   40,
   "Laminado, Secado y Corte",
   "Secado de membrana: ambiente 30 min - PSA semicuantitativa"
  ],
  [
   50,
   "Laminado, Secado y Corte",
   "Laminado sobre tarjeta MPTS01: membrana MPMNC03, absorbente, conjugado control SPALMA03, conjugado prueba SPALMA01, filtro SPALMA13, muestra SPALMA07 - PSA semicuantitativa"
  ],
  [
   60,
   "Laminado, Secado y Corte",
   "Corte a 0.3 cm - PSA semicuantitativa"
  ],
  [
   70,
   "Control de Calidad",
   "Muestreo de tiras para analisis de Calidad - PSA semicuantitativa"
  ],
  [
   80,
   "Almacén Materia Prima",
   "Entrega a almacen - PSA semicuantitativa"
  ]
 ],
 "SPHMC20": [
  [
   5,
   "Almacén Materia Prima",
   "Surtido de materiales - RSV"
  ],
  [
   10,
   "Inyección",
   "Impresion de conjugado 10 ul/cm en SPALMA01 - RSV"
  ],
  [
   20,
   "Inyección",
   "Impresion de linea de prueba en membrana MPMNC02 - RSV"
  ],
  [
   30,
   "Laminado, Secado y Corte",
   "Secado de conjugado: horno 37 C por 30 min - RSV"
  ],
  [
   40,
   "Laminado, Secado y Corte",
   "Secado de membrana: ambiente 30 min - RSV"
  ],
  [
   50,
   "Laminado, Secado y Corte",
   "Laminado sobre tarjeta MPTS01: membrana MPMNC02, absorbente, conjugado control SPALMA03, conjugado prueba SPALMA01, muestra SPALMA05 - RSV"
  ],
  [
   60,
   "Laminado, Secado y Corte",
   "Corte a 0.3 cm - RSV"
  ],
  [
   70,
   "Control de Calidad",
   "Muestreo de tiras para analisis de Calidad - RSV"
  ],
  [
   80,
   "Almacén Materia Prima",
   "Entrega a almacen - RSV"
  ]
 ],
 "SPHMC22": [
  [
   5,
   "Almacén Materia Prima",
   "Surtido de materiales - Sifilis"
  ],
  [
   10,
   "Inyección",
   "Impresion de conjugado 10 ul/cm en SPALMA01 - Sifilis"
  ],
  [
   20,
   "Inyección",
   "Impresion de linea de prueba en membrana MPMNC03 - Sifilis"
  ],
  [
   30,
   "Laminado, Secado y Corte",
   "Secado de conjugado: horno 37 C por 30 min - Sifilis"
  ],
  [
   40,
   "Laminado, Secado y Corte",
   "Secado de membrana: ambiente 30 min - Sifilis"
  ],
  [
   50,
   "Laminado, Secado y Corte",
   "Laminado sobre tarjeta MPTS01: membrana MPMNC03, absorbente, conjugado control SPALMA03, conjugado prueba SPALMA01, filtro SPALMA13, muestra SPALMA07 - Sifilis"
  ],
  [
   60,
   "Laminado, Secado y Corte",
   "Corte a 0.3 cm - Sifilis"
  ],
  [
   70,
   "Control de Calidad",
   "Muestreo de tiras para analisis de Calidad - Sifilis"
  ],
  [
   80,
   "Almacén Materia Prima",
   "Entrega a almacen - Sifilis"
  ]
 ],
 "SPHMC23": [
  [
   5,
   "Almacén Materia Prima",
   "Surtido de materiales - VIH p24"
  ],
  [
   10,
   "Inyección",
   "Impresion de conjugado 10 ul/cm en SPALMA01 - VIH p24"
  ],
  [
   20,
   "Inyección",
   "Impresion de linea de prueba en membrana MPMNC03 - VIH p24"
  ],
  [
   30,
   "Laminado, Secado y Corte",
   "Secado de conjugado: horno 37 C por 30 min - VIH p24"
  ],
  [
   40,
   "Laminado, Secado y Corte",
   "Secado de membrana: ambiente 30 min - VIH p24"
  ],
  [
   50,
   "Laminado, Secado y Corte",
   "Laminado sobre tarjeta MPTS01: membrana MPMNC03, absorbente, conjugado control SPALMA03, conjugado prueba SPALMA01, filtro SPALMA13, muestra SPALMA07 - VIH p24"
  ],
  [
   60,
   "Laminado, Secado y Corte",
   "Corte a 0.3 cm - VIH p24"
  ],
  [
   70,
   "Control de Calidad",
   "Muestreo de tiras para analisis de Calidad - VIH p24"
  ],
  [
   80,
   "Almacén Materia Prima",
   "Entrega a almacen - VIH p24"
  ]
 ],
 "SPHMC09": [
  [
   5,
   "Almacén Materia Prima",
   "Surtido de materiales - Vitamina D"
  ],
  [
   10,
   "Inyección",
   "Impresion de conjugado 10 ul/cm en SPALMA01 - Vitamina D"
  ],
  [
   20,
   "Inyección",
   "Impresion de linea de prueba en membrana MPMNC03 - Vitamina D"
  ],
  [
   30,
   "Laminado, Secado y Corte",
   "Secado de conjugado: horno 37 C por 30 min - Vitamina D"
  ],
  [
   40,
   "Laminado, Secado y Corte",
   "Secado de membrana: ambiente 30 min - Vitamina D"
  ],
  [
   50,
   "Laminado, Secado y Corte",
   "Laminado sobre tarjeta MPTS02: membrana MPMNC03, absorbente, conjugado control SPALMA03, conjugado prueba SPALMA01, filtro SPALMA13, muestra SPALMA07 - Vitamina D"
  ],
  [
   60,
   "Laminado, Secado y Corte",
   "Corte a 0.3 cm - Vitamina D"
  ],
  [
   70,
   "Control de Calidad",
   "Muestreo de tiras para analisis de Calidad - Vitamina D"
  ],
  [
   80,
   "Almacén Materia Prima",
   "Entrega a almacen - Vitamina D"
  ]
 ],
 "SPHMT01": [
  [
   5,
   "Almacén Materia Prima",
   "Surtido de materiales - Biotina"
  ],
  [
   10,
   "Inyección",
   "Impresion de conjugado 10 ul/cm en SPALMA01 - Biotina"
  ],
  [
   20,
   "Inyección",
   "Impresion de linea de prueba en membrana MPMNC02 - Biotina"
  ],
  [
   30,
   "Laminado, Secado y Corte",
   "Secado de conjugado: horno 37 C por 30 min - Biotina"
  ],
  [
   40,
   "Laminado, Secado y Corte",
   "Secado de membrana: ambiente 30 min - Biotina"
  ],
  [
   50,
   "Laminado, Secado y Corte",
   "Laminado sobre tarjeta MPTS01: membrana MPMNC02, absorbente, conjugado control SPALMA03, conjugado prueba SPALMA01, muestra SPALMA05 - Biotina"
  ],
  [
   60,
   "Laminado, Secado y Corte",
   "Corte a 0.3 cm - Biotina"
  ],
  [
   70,
   "Control de Calidad",
   "Muestreo de tiras para analisis de Calidad - Biotina"
  ],
  [
   80,
   "Almacén Materia Prima",
   "Entrega a almacen - Biotina"
  ]
 ],
 "SPHMC07": [
  [
   5,
   "Almacén Materia Prima",
   "Surtido de materiales - Hemoglobina"
  ],
  [
   10,
   "Inyección",
   "Impresion de conjugado 10 ul/cm en SPALMA01 - Hemoglobina"
  ],
  [
   20,
   "Inyección",
   "Impresion de linea de prueba en membrana MPMNC03 - Hemoglobina"
  ],
  [
   30,
   "Laminado, Secado y Corte",
   "Secado de conjugado: horno 37 C por 30 min - Hemoglobina"
  ],
  [
   40,
   "Laminado, Secado y Corte",
   "Secado de membrana: ambiente 30 min - Hemoglobina"
  ],
  [
   50,
   "Laminado, Secado y Corte",
   "Laminado sobre tarjeta MPTS01: membrana MPMNC03, absorbente, conjugado control SPALMA03, conjugado prueba SPALMA01, filtro SPALMA13, muestra SPALMA05 - Hemoglobina"
  ],
  [
   60,
   "Laminado, Secado y Corte",
   "Corte a 0.3 cm - Hemoglobina"
  ],
  [
   70,
   "Control de Calidad",
   "Muestreo de tiras para analisis de Calidad - Hemoglobina"
  ],
  [
   80,
   "Almacén Materia Prima",
   "Entrega a almacen - Hemoglobina"
  ]
 ],
 "SPHMC45": [
  [
   5,
   "Almacén Materia Prima",
   "Surtido de materiales - Salmonella typhi"
  ],
  [
   10,
   "Inyección",
   "Impresion de conjugado 10 ul/cm en SPALMA01 - Salmonella typhi"
  ],
  [
   20,
   "Inyección",
   "Impresion de linea de prueba en membrana MPMNC02 - Salmonella typhi"
  ],
  [
   30,
   "Laminado, Secado y Corte",
   "Secado de conjugado: horno 37 C por 30 min - Salmonella typhi"
  ],
  [
   40,
   "Laminado, Secado y Corte",
   "Secado de membrana: ambiente 30 min - Salmonella typhi"
  ],
  [
   50,
   "Laminado, Secado y Corte",
   "Laminado sobre tarjeta MPTS01: membrana MPMNC02, absorbente, conjugado control SPALMA03, conjugado prueba SPALMA01, muestra SPALMA05 - Salmonella typhi"
  ],
  [
   60,
   "Laminado, Secado y Corte",
   "Corte a 0.3 cm - Salmonella typhi"
  ],
  [
   70,
   "Control de Calidad",
   "Muestreo de tiras para analisis de Calidad - Salmonella typhi"
  ],
  [
   80,
   "Almacén Materia Prima",
   "Entrega a almacen - Salmonella typhi"
  ]
 ],
 "SPHMC37": [
  [
   5,
   "Almacén Materia Prima",
   "Surtido de materiales - TSH cualitativa"
  ],
  [
   10,
   "Inyección",
   "Impresion de conjugado 10 ul/cm en SPALMA01 - TSH cualitativa"
  ],
  [
   20,
   "Inyección",
   "Impresion de linea de prueba en membrana MPMNC03 - TSH cualitativa"
  ],
  [
   30,
   "Laminado, Secado y Corte",
   "Secado de conjugado: horno 37 C por 30 min - TSH cualitativa"
  ],
  [
   40,
   "Laminado, Secado y Corte",
   "Secado de membrana: ambiente 30 min - TSH cualitativa"
  ],
  [
   50,
   "Laminado, Secado y Corte",
   "Laminado sobre tarjeta MPTS01: membrana MPMNC03, absorbente, conjugado control SPALMA03, conjugado prueba SPALMA01, filtro SPALMA13, muestra SPALMA07 - TSH cualitativa"
  ],
  [
   60,
   "Laminado, Secado y Corte",
   "Corte a 0.3 cm - TSH cualitativa"
  ],
  [
   70,
   "Control de Calidad",
   "Muestreo de tiras para analisis de Calidad - TSH cualitativa"
  ],
  [
   80,
   "Almacén Materia Prima",
   "Entrega a almacen - TSH cualitativa"
  ]
 ],
 "SPHMC52": [
  [
   5,
   "Almacén Materia Prima",
   "Surtido de materiales - TSH semicuantitativa"
  ],
  [
   10,
   "Inyección",
   "Impresion de conjugado 10 ul/cm en SPALMA01 - TSH semicuantitativa"
  ],
  [
   20,
   "Inyección",
   "Impresion de linea de prueba en membrana MPMNC03 - TSH semicuantitativa"
  ],
  [
   30,
   "Laminado, Secado y Corte",
   "Secado de conjugado: horno 37 C por 30 min - TSH semicuantitativa"
  ],
  [
   40,
   "Laminado, Secado y Corte",
   "Secado de membrana: ambiente 30 min - TSH semicuantitativa"
  ],
  [
   50,
   "Laminado, Secado y Corte",
   "Laminado sobre tarjeta MPTS01: membrana MPMNC03, absorbente, conjugado control SPALMA03, conjugado prueba SPALMA01, filtro SPALMA13, muestra SPALMA07 - TSH semicuantitativa"
  ],
  [
   60,
   "Laminado, Secado y Corte",
   "Corte a 0.3 cm - TSH semicuantitativa"
  ],
  [
   70,
   "Control de Calidad",
   "Muestreo de tiras para analisis de Calidad - TSH semicuantitativa"
  ],
  [
   80,
   "Almacén Materia Prima",
   "Entrega a almacen - TSH semicuantitativa"
  ]
 ]
}


P = env['product.product'].sudo()
BOM = env['mrp.bom'].sudo()
Line = env['mrp.bom.line'].sudo()
OP = env['mrp.routing.workcenter'].sudo()
W = env['mrp.workcenter'].sudo()

centros = {}
for nom in {o[1] for ops in RUTA.values() for o in ops}:
    c = W.search([('name','=',nom)], limit=1)
    assert c, 'no existe el centro de trabajo "%s"' % nom
    centros[nom] = c
print('   centros resueltos: %s' % ', '.join('%s=%s' % (k, v.id) for k, v in centros.items()))
print('')
nl = no = 0
for cod in sorted(RECETA):
    p = P.search([('default_code','=',cod)], limit=1)
    if not p:
        print('   %-10s NO EXISTE el producto' % cod); continue
    bom = BOM.search([('product_tmpl_id','=',p.product_tmpl_id.id)], limit=1)
    if not bom:
        print('   %-10s sin BoM, se omite' % cod); continue
    ya_l = set(bom.bom_line_ids.mapped('product_id.default_code'))
    add_l = 0
    for comp, qty, uom in RECETA[cod]:
        if comp in ya_l: continue
        c = P.search([('default_code','=',comp)], limit=1)
        if not c:
            print('         %-10s NO EXISTE, se omite' % comp); continue
        u = env['uom.uom'].sudo().search([('name','=',uom)], limit=1) or c.uom_id
        Line.create({'bom_id': bom.id, 'product_id': c.id,
                     'product_qty': qty, 'product_uom_id': u.id})
        add_l += 1
    ya_o = set(bom.operation_ids.mapped('name'))
    add_o = 0
    for seq, centro, nombre in RUTA[cod]:
        if nombre in ya_o: continue
        OP.create({'bom_id': bom.id, 'name': nombre[:250],
                   'workcenter_id': centros[centro].id, 'sequence': seq,
                   'time_mode': 'manual', 'time_cycle_manual': 1.0})
        add_o += 1
    nl += add_l; no += add_o
    print('   %-10s %-24s +%s lineas  +%s operaciones   (total %s y %s)' % (
        cod, (p.name or '').replace('Hoja Maestra ','')[:24], add_l, add_o,
        len(bom.bom_line_ids), len(bom.operation_ids)))
env.flush_all(); env.cr.commit()
print('')
print('   agregado: %s lineas de receta y %s operaciones' % (nl, no))
