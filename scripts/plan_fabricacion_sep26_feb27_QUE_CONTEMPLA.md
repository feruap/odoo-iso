# Plan de fabricación sep-2026 a feb-2027 — qué contempla y qué no

Archivo de datos: `plan_fabricacion_sep26_feb27.csv` (separador `;`, abre en Excel)

## Cómo se calcula cada columna

| Columna | De dónde sale |
|---|---|
| `temp_24_25` | piezas vendidas sep-2024 a feb-2025 |
| `temp_25_26` | piezas vendidas sep-2025 a feb-2026 |
| `factor` | `temp_25_26 / temp_24_25`, **acotado entre 0.50x y 2.00x** |
| `proyeccion` | `temp_25_26 × factor` |
| `en_distribucion` | existencia en todas las ubicaciones ADT |
| `en_PT` | existencia en APT, **excluyendo Control de calidad y Rechazo** |
| `en_ordenes` | de las órdenes abiertas: `plan − producido` |
| `A_FABRICAR` | `proyeccion − distribucion − PT − ordenes`, mínimo 0 |
| `cajas` | piezas de esa presentación ÷ piezas por caja |

La mezcla de presentaciones sale de las ventas **desde sep-2025**, para reflejar
cómo se vende hoy.

## SÍ se contempla

- **Lo que se está fabricando ahora.** Columna `ordenes_abiertas` con nombre y
  estado de cada orden. Ejemplos reales:
  - `DIAM-024` COVFLU: `0926/01/CCF` en proceso, **3,600 pz pendientes** → por eso
    solo faltan 2,595 y no 6,195.
  - `DMCRD01` Combo: `0926/01/CRD` por cerrar, 3,368 ya producidas (contadas en PT)
    y 272 pendientes.
- **El producto terminado en PT**, no solo lo que ya llegó a Distribución.
- **La estacionalidad**, comparando temporada contra temporada.
- **Que el stock sea vendible.** Se verificó lote por lote: todo lo que se
  descuenta tiene orden aprobada, es previo al sistema, o está exenta con
  `amunet_qc_previo_al_sistema`. Nada bloqueado se cuenta como disponible.
- **Se excluye** de "disponible" lo que está en Control de calidad o Rechazo.

## NO se contempla — hay que decidirlo aparte

1. **Ventas fuera de la tienda.** Esto es demanda de Woo. Venta directa,
   licitaciones y distribuidores no están, si no pasan por la tienda.
2. **Capacidad de producción.** Dice qué se necesita, no si cabe. 1,304 cajas de
   Combo Respiratorio en cinco meses hay que cruzarlo con rutas y centros.
3. **Materia prima.** No se revisó si hay cartuchos, membrana, conjugados ni
   empaque para estas cantidades.
4. **Caducidades del stock existente.** Se descuenta la existencia sin mirar si
   caduca antes de febrero.
5. **Septiembre 2026.** El histórico llega a agosto: el mes en curso no está.
6. **Agosto 2026 puede estar incompleto**: 2,717 pz contra 14,280 de julio. No se
   usó como base, pero si está incompleto los factores quedan algo bajos.

## Tres números que NO defiendo, y por qué

1. **DMADB01 Antidoping Saliva — 5,691 pz.** Su temporada 25-26 fueron 4,298 pz y
   **2,920 cayeron en un solo mes** (sep-2025). La demanda de fondo es ~200 pz/mes.
   Si esos picos son un cliente que compra por tandas, sobra fabricar 5,691.
   **El sistema no dice quién compra.**
2. **Seis factores tocaron el techo de 2.00x** (Hemoglobina, PROSTATINET,
   VITAMINET D, Estreptococo, TSH, NT-proBNP). Su crecimiento real es mayor; la
   proyección quedó conservadora a propósito.
3. **DMDEN01 Dengue cayó 87%** (28,260 → 3,725 pz). Con el piso de 0.50x salen
   222 pz. Si se dejó de vender, no hay que fabricar nada.

## Errores de método que se corrigieron al armarlo

- El primer cálculo comparaba **mar-ago 2026 contra sep25-feb26**. Mal: mar-ago es
  temporada BAJA de respiratorias. El Combo salía −37% cuando la temporada real
  cayó 8%.
- El segundo proyectaba sobre **promedios contaminados por picos**. El Antidoping
  Saliva aparecía con +529%, pero 15,057 de sus 15,978 pz de mar-ago 2026 cayeron
  en marzo. Sin picos está plano.

Lección: mirar la serie mensual antes de proyectar sobre cualquier promedio.
