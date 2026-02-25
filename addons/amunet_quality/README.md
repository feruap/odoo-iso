# Amunet - Control de Calidad

**Versión**: 19.0.2.0.0
**Categoría**: Quality
**Autor**: DIC Consultores - Rafael López Flores
**Licencia**: LGPL-3
**Estado**: 🚧 **EN DESARROLLO ACTIVO** 🚧

---

## ⚠️ Estado del desarrollo

**IMPORTANTE**: Este módulo está actualmente en desarrollo activo y requiere modificaciones y mejoras significativas:

### Implementado ✅
- [x] Arquitectura básica de 4 niveles para parámetros jerárquicos
- [x] 9 tipos de parámetros diferentes
- [x] Modelo de configuración por producto
- [x] Creación automática de QC en recepciones
- [x] Generación de líneas de test y detalles desde configuración
- [x] Evaluación automática básica (CUMPLE/NO CUMPLE)
- [x] Widget OWL2 para vista jerárquica expandible
- [x] Integración con sistema de lotes Amunet

### En desarrollo / Pendiente 🚧
- [ ] **🚨 CRÍTICO: Tipo de parámetro con matriz de decisión (MAVI-16) 🚨**
  - **Este es el parámetro MÁS COMPLEJO y CRÍTICO del sistema**
  - Requiere un nuevo tipo de parámetro: `decision_matrix` o `multi_step_conditional`
  - Basado en MAVI-16 "Visualización de apariencia colorimétrica"
  - **Características únicas**:
    - Flujo secuencial de 3 pasos de evaluación
    - Matriz de decisión con 13 escenarios posibles (tabla de verdad)
    - Evaluación basada en cruce de 3 variables independientes
    - Validación inmediata que invalida prueba completa (línea C no visible)
  - **Complejidad**:
    - Paso 1: Selección de concentración objetivo (Baja/Intermedia/Alta)
    - Paso 2.1: Verificación binaria (¿Línea C visible? Sí/No)
    - Paso 2.2: Comparación visual de intensidades (T≠R / T<R / T~R / T>R)
    - Evaluación: Cruce de las 3 variables en tabla de 13 filas
  - **Documentación**: Ver `docs/tickets/matrices/Matriz de control de calidad hojas maestras.md` (línea 85-115)
  - **Casos de uso**: SPHMC25, SPHMC38, SPHMC52
  - ⚠️ Sin este tipo, no se pueden configurar correctamente ~10 productos críticos
- [ ] **Parámetros MAVI especializados adicionales**
  - MAVI-07: Visualización líneas resultado base (condicional por tipo muestra)
  - MAVI-15: Visualización líneas resultado en rango (3 opciones condicionales)
  - Todos requieren lógica especializada similar a MAVI-16
- [ ] **Evaluación completa de todos los tipos de parámetros**
  - Ningún tipo está completamente implementado
  - Tipos condicionales requieren validación
  - Tipos de texto con patrón necesitan pruebas
- [ ] **Validación de especificaciones por tipo de parámetro**
  - Falta validación de coherencia entre tipo y especificaciones
  - Campos específicos por tipo requieren constraints
- [ ] **UI mejorada para configuración de parámetros**
  - Interfaz actual es funcional pero básica
  - Wizard de configuración guiada especialmente necesario para MAVI-16
- [ ] **Generación de PDF con análisis completo**
  - Plantilla QWeb pendiente
  - Certificado de calidad pendiente
- [ ] **Sistema de firmas electrónicas**
  - Básico implementado, requiere mejoras de seguridad
- [ ] **Movimientos de inventario para muestreo**
  - Lógica parcialmente implementada
  - Requiere validación en escenarios reales
- [ ] **Reportes y estadísticas de calidad**
  - No implementado
- [ ] **Migración de datos legacy**
  - No se requiere, se pueden eliminar campos y/o funciones deprecated
  - Cuidar que no afecte flujos funcionales
  - Sin temor a pérdida de datos: todos los datos actuales son de prueba para desarrollo

### Problemas Conocidos 🐛
1. Algunos tipos de evaluación no están totalmente probados en producción
2. La UI puede ser confusa al configurar parámetros complejos
3. Validaciones de rangos numéricos requieren más casos de prueba
4. Performance en productos con >20 parámetros no optimizada
5. Faltan mensajes de error descriptivos en validaciones

---

## Descripción General

Sistema de Control de Calidad para la manufactura de dispositivos médicos y productos farmacéuticos. Implementa un **sistema jerárquico de parámetros de 4 niveles** que permite modelar matrices de control de calidad complejas con evaluación automática granular.

### Características Principales

- ✅ **Sistema jerárquico de parámetros** (Código → Parámetro → Especificaciones → Configuración por Producto)
- ⚠️ **10 tipos de parámetros** (9 implementados + 1 crítico pendiente: matriz de decisión MAVI-16)
- ✅ **Configuración flexible por producto** (activar/desactivar especificaciones, override de valores)
- ✅ **Evaluación automática granular** (cada especificación evaluada independientemente)
- ✅ **Agregación jerárquica de dictámenes** (bottom-up: detalle → línea → QC)
- ✅ Flujo de estados con bloqueo progresivo de secciones (Numerales)
- ✅ Creación automática de QC al validar recepciones
- ✅ Sistema de firmas con segregación de funciones
- ✅ Generación de folio legal con secuencia diaria
- ✅ Soporte para pruebas destructivas y no destructivas
- ✅ Reanálisis con trazabilidad al original
- 🚨 **Bloqueador crítico**: ~10 productos requieren tipo `decision_matrix` (MAVI-16) no implementado

### Cumplimiento Normativo

- NOM-241-SSA-V-VIGENTE
- Buenas Prácticas de Fabricación (BPF)

---

## Arquitectura del Sistema de Parámetros

### Niveles de Jerarquía

El sistema se basa en **4 niveles jerárquicos** para máxima flexibilidad:

```
┌─────────────────────────────────────────────────────────────┐
│ NIVEL 1: Código Reutilizable                               │
│ ┌─────────────────────────────────────────────────────────┐ │
│ │ Código: "MAVI-04"                                       │ │
│ │ - Se reutiliza en múltiples productos                  │ │
│ │ - No es único (misma determinación para varios)        │ │
│ └─────────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────────┘
                           ↓
┌─────────────────────────────────────────────────────────────┐
│ NIVEL 2: Parámetro (Plantilla Reutilizable)                │
│ ┌─────────────────────────────────────────────────────────┐ │
│ │ Modelo: amunet.quality.check.parameter                  │ │
│ │                                                          │ │
│ │ • code: "MAVI-04"                                       │ │
│ │ • name: "Aspectos"                                      │ │
│ │                                                          │ │
│ │ Define QUÉ se va a medir (plantilla global)            │ │
│ └─────────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────────┘
                           ↓ One2many: specification_line_ids
┌─────────────────────────────────────────────────────────────┐
│ NIVEL 3: Especificaciones (Sub-criterios)                  │
│ ┌─────────────────────────────────────────────────────────┐ │
│ │ Modelo: amunet.quality.check.parameter.specification    │ │
│ │                                                          │ │
│ │ Especificación 1:                                       │ │
│ │   • name: "Polvo"                                       │ │
│ │   • evaluation_type: "binary_selection"                 │ │
│ │   • expected_value_binary: "Sin polvo"                  │ │
│ │                                                          │ │
│ │ Especificación 2:                                       │ │
│ │   • name: "Manchas y/o suciedad"                        │ │
│ │   • evaluation_type: "binary_selection"                 │ │
│ │   • expected_value_binary: "Sin manchas"                │ │
│ │                                                          │ │
│ │ Especificación 3:                                       │ │
│ │   • name: "Rasgaduras"                                  │ │
│ │   • evaluation_type: "binary_selection"                 │ │
│ │   • expected_value_binary: "Sin rasgaduras"             │ │
│ │                                                          │ │
│ │ Define CÓMO se evalúa cada aspecto                      │ │
│ └─────────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────────┘
                           ↓ Many2one: specification_id
┌─────────────────────────────────────────────────────────────┐
│ NIVEL 4: Configuración por Producto                        │
│ ┌─────────────────────────────────────────────────────────┐ │
│ │ Modelo: amunet.quality.parameter.product.rel             │ │
│ │   └─> amunet.quality.parameter.specification.config     │ │
│ │                                                          │ │
│ │ Producto: SPHMC01                                       │ │
│ │ Parámetro: MAVI-04                                      │ │
│ │                                                          │ │
│ │ ✅ Especificación 1: Polvo (active=True)                │ │
│ │ ✅ Especificación 2: Manchas (active=True)              │ │
│ │ ❌ Especificación 3: Rasgaduras (active=False)          │ │
│ │                                                          │ │
│ │ Define CUÁLES especificaciones aplican a este producto │ │
│ └─────────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────────┘
                           ↓ Copia valores al ejecutar QC
┌─────────────────────────────────────────────────────────────┐
│ NIVEL 5: Resultados en QC (Ejecución)                      │
│ ┌─────────────────────────────────────────────────────────┐ │
│ │ Modelo: amunet.quality.test.line                        │ │
│ │   └─> amunet.quality.test.line.detail                   │ │
│ │                                                          │ │
│ │ Test Line: MAVI-04 - Aspectos                           │ │
│ │ ├─ Detail 1: Polvo                                      │ │
│ │ │    • result_selection: "Sin polvo"                    │ │
│ │ │    • result_verdict: "pass" ✅                        │ │
│ │ ├─ Detail 2: Manchas                                    │ │
│ │ │    • result_selection: "Con manchas"                  │ │
│ │ │    • result_verdict: "fail" ❌                        │ │
│ │ └─ Verdict agregado: "fail" (uno falló)                 │ │
│ │                                                          │ │
│ │ Almacena resultados REALES del análisis                 │ │
│ └─────────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────────┘
```

### ¿Por qué esta arquitectura?

**Problema Original**:
- Las matrices de control de Amunet tienen códigos reutilizados (MAVI-04 aparece en 50+ productos)
- Cada producto puede necesitar diferentes sub-criterios del mismo código
- El sistema anterior solo permitía 1 especificación por parámetro

**Solución Implementada**:
1. **Código reutilizable**: Mismo código para múltiples productos (MAVI-04)
2. **Parámetro como plantilla**: Define la estructura general (4 tipos de "Aspectos")
3. **Especificaciones flexibles**: Cada producto activa solo las que necesita
4. **Evaluación granular**: Cada especificación se evalúa independientemente
5. **Agregación automática**: El dictamen del parámetro se calcula automáticamente

---

## Tipos de parámetros

El sistema soporta **10 tipos diferentes** de parámetros (9 implementados + 1 crítico pendiente):

### 1. Simple (`simple`)
Un parámetro con una sola especificación.

**Ejemplo**: MGA-0486 - Microorganismos Aerobios
- 1 especificación: Rango numérico (10-100 UFC/g)
- Evaluación: Un solo campo numérico

### 2. Compuesto (`composite`)
Múltiples especificaciones del mismo tipo de evaluación.

**Ejemplo**: MAVI-04 - Aspectos
- Especificación 1: Polvo (Sin/Con)
- Especificación 2: Manchas (Sin/Con)
- Especificación 3: Rasgaduras (Sin/Con)
- Especificación 4: Deformidad (Sin/Con)
- Evaluación: Todas deben pasar para que el parámetro pase

### 3. Multi-campo (`multi_field`)
Múltiples campos numéricos independientes.

**Ejemplo**: MAVI-11 - Dimensiones
- Campo 1: Largo (6.0 ± 0.5 cm)
- Campo 2: Ancho (2.0 ± 0.2 cm)
- Campo 3: Alto (0.5 ± 0.1 cm)
- Evaluación: Cada campo se evalúa independientemente

### 4. Multi-checkbox (`multi_checkbox`)
Múltiples checkboxes con evaluación combinada.

**Ejemplo**: VAMA-091 - Características visuales
- Checkbox 1: Color uniforme
- Checkbox 2: Sin burbujas
- Checkbox 3: Sin fracturas
- Evaluación: Todos los checkboxes deben estar marcados

### 5. Condicional numérico (`conditional_numeric`)
Selección que determina el rango numérico aplicable.

**Ejemplo**: MAVI-11 - Altura
- Selección: "6 cm" o "8 cm"
- Si "6 cm" → rango 5.5-6.5 cm
- Si "8 cm" → rango 7.5-8.5 cm
- Evaluación: Valor ingresado debe estar en rango de opción seleccionada

### 6. Texto con patrón (`text_pattern`)
Campo de texto que debe coincidir con un patrón regex.

**Ejemplo**: VAMA-112 - Código de lote
- Patrón: `^[A-Z]{3}\d{6}$`
- Evaluación: Texto debe cumplir patrón

### 7. Comparación esperado vs obtenido (`expected_vs_obtained`)
Dos selecciones que deben coincidir.

**Ejemplo**: VAMA-032 - Resultado de muestra
- Esperado: "Positivo"
- Obtenido: "Positivo"
- Evaluación: Ambas selecciones deben ser iguales

### 8. Binary con notas (`binary_with_notes`)
Selección binaria con campo de texto condicional.

**Ejemplo**: VAMA-063 - Observaciones especiales
- Selección: "Sí" / "No"
- Si "No" → campo de texto obligatorio para justificar
- Evaluación: Si "Sí" pasa, si "No" falla

### 9. Ternario con N/A (`ternary_with_na`)
Tres opciones incluyendo "No Aplica".

**Ejemplo**: MAVI-14 - Prueba opcional
- Opciones: "Cumple" / "No cumple" / "No aplica"
- Evaluación: "Cumple" pasa, "No cumple" falla, "N/A" se excluye del conteo

### 10. 🚨 Matriz de Decisión Multi-Paso (`decision_matrix`) - 🚧 **PENDIENTE DE DESARROLLO**

**EL TIPO MÁS CRÍTICO Y COMPLEJO DEL SISTEMA**

Parámetro con evaluación basada en matriz de decisión con múltiples pasos secuenciales.

**Ejemplo REAL (crítico)**: MAVI-16 - Visualización de apariencia colorimétrica
- Aplica a productos: SPHMC25, SPHMC38, SPHMC52
- **~10 productos bloqueados** sin este tipo de parámetro

**Estructura de evaluación**:

```
Paso 1: Selección de concentración objetivo
  ├─ Opción A: Baja (se espera T≠R o T<R)
  ├─ Opción B: Intermedia (se espera T~R)
  └─ Opción C: Alta (se espera T>R)

Paso 2.1: Verificación de línea de control
  ├─ ✅ Sí visible → Continuar a Paso 2.2
  └─ ❌ No visible → FALLO INMEDIATO (invalida prueba completa)

Paso 2.2: Comparación visual de intensidades
  ├─ T≠R: No hay formación de línea en región T
  ├─ T<R: Intensidad de T es menor que R
  ├─ T~R: Intensidad de T es similar/igual a R
  └─ T>R: Intensidad de T es mayor que R

Evaluación: Matriz de 13 escenarios
```

**Matriz de evaluación MAVI-16** (simplificada):

| # | Concentración Objetivo | Línea C | T vs R Observado | Resultado | Dictamen |
|---|------------------------|---------|------------------|-----------|----------|
| 1 | Cualquiera | NO | - | Inválido: Sin línea C | ❌ NO CUMPLE |
| 2 | Baja | Sí | T≠R | Esperado: Sin reacción | ✅ CUMPLE |
| 3 | Baja | Sí | T<R | Esperado: Menor intensidad | ✅ CUMPLE |
| 4 | Baja | Sí | T~R | Inconsistente: Se observó Intermedia | ❌ NO CUMPLE |
| 5 | Baja | Sí | T>R | Inconsistente: Se observó Alta | ❌ NO CUMPLE |
| 6 | Intermedia | Sí | T≠R | Inconsistente: Sin reacción | ❌ NO CUMPLE |
| 7 | Intermedia | Sí | T<R | Inconsistente: Se observó Baja | ❌ NO CUMPLE |
| 8 | Intermedia | Sí | T~R | Esperado: Intensidad similar | ✅ CUMPLE |
| 9 | Intermedia | Sí | T>R | Inconsistente: Se observó Alta | ❌ NO CUMPLE |
| 10 | Alta | Sí | T≠R | Inconsistente: Sin reacción | ❌ NO CUMPLE |
| 11 | Alta | Sí | T<R | Inconsistente: Se observó Baja | ❌ NO CUMPLE |
| 12 | Alta | Sí | T~R | Inconsistente: Se observó Intermedia | ❌ NO CUMPLE |
| 13 | Alta | Sí | T>R | Esperado: Mayor intensidad | ✅ CUMPLE |

**Requisitos técnicos para implementar**:
1. Nuevo modelo: `amunet.quality.parameter.decision.matrix` (13 filas de configuración)
2. Campos en `test.line.detail`:
   - `step1_selection` (Selection: baja/intermedia/alta)
   - `step2_1_control_visible` (Boolean)
   - `step2_2_comparison` (Selection: t_neq_r / t_lt_r / t_eq_r / t_gt_r)
   - `matrix_scenario` (Integer, computed: 1-13)
   - `matrix_expected_result` (Text, computed)
3. Widget especializado en frontend para flujo de pasos
4. Lógica de evaluación con tabla de decisión programática

**Complejidad**: ⭐⭐⭐⭐⭐ (Máxima)

**Documentación completa**:
- Archivo: `docs/tickets/matrices/Matriz de control de calidad hojas maestras.md` (líneas 85-115)
- Imágenes de referencia: `docs/tickets/matrices/imagenes/` (capturas del 2 de diciembre)

**Estado**: 🚧 No implementado - Bloqueador para ~10 productos críticos

---

## Tipos de Evaluación

Cada especificación tiene un `evaluation_type` que determina cómo se evalúa:

| Tipo | Descripción | Campos de Resultado | Algoritmo de Evaluación |
|------|-------------|---------------------|------------------------|
| `binary_selection` | Sin/Con | `result_selection` | `result == expected` → PASS |
| `numeric_range` | Rango min-max | `result_numeric` | `min <= result <= max` → PASS |
| `checkbox_combined` | Checkboxes múltiples | `result_checkboxes` (JSON) | Todos TRUE → PASS |
| `conditional_numeric_range` | Rango según opción | `result_option`, `result_numeric` | `min(option) <= result <= max(option)` → PASS |
| `text_pattern` | Regex | `result_text` | `re.match(pattern, text)` → PASS |
| `expected_vs_obtained` | Comparación | `result_expected`, `result_obtained` | `expected == obtained` → PASS |
| `binary_with_notes` | Sí/No + notas | `result_boolean`, `result_notes` | `result_boolean == True` → PASS |
| `ternary_with_na` | Cumple/No/N/A | `result_ternary` | `result == 'pass'` → PASS, `'na'` → N/A |
| `decision_matrix` 🚧 | Matriz multi-paso | `step1_selection`, `step2_1_control_visible`, `step2_2_comparison` | Búsqueda en tabla de decisión (13 escenarios) → PASS/FAIL |

### Algoritmo de Agregación Jerárquica

La evaluación fluye **de abajo hacia arriba**:

```python
# PASO 1: Evaluar cada detalle (especificación)
detail.result_verdict = evaluar_segun_tipo(detail.evaluation_type, detail.result_*)

# PASO 2: Agregar detalles a nivel de línea de test
test_line.result_verdict = agregar_detalles(test_line.detail_line_ids.result_verdict)

# Lógica de agregación:
if any(detail.verdict == 'fail'):
    test_line.verdict = 'fail'  # Si uno falla, toda la línea falla
elif all(detail.verdict == 'not_applicable'):
    test_line.verdict = 'not_applicable'  # Todos N/A
elif all(detail.verdict in ['pass', 'not_applicable']):
    test_line.verdict = 'pass'  # Todos pasan o son N/A
else:
    test_line.verdict = 'pending'  # Aún no completado

# PASO 3: Agregar líneas a nivel de QC
quality_check.result = agregar_lineas(quality_check.test_line_ids.result_verdict)
```

**Importante**: El flag `exclude_na_from_verdict` en especificaciones controla si N/A cuenta como fallo o se ignora.

---

## Flujo de uso completo

### Fase 1: Configuración (Una vez)

#### 1.1. Crear parámetros en catálogo

```
Calidad → Configuración → Parámetros de Calidad → Crear
```

1. Ingresar código (ej: MAVI-04)
2. Ingresar nombre (ej: Aspectos)
3. Seleccionar tipo de parámetro (ej: composite)
4. Agregar especificaciones:
   - Especificación 1: "Polvo" (binary_selection)
   - Especificación 2: "Manchas" (binary_selection)
   - Especificación 3: "Rasgaduras" (binary_selection)
5. Guardar

#### 1.2. Configurar Productos

```
Inventario → Productos → [Producto] → Pestaña "Control de Calidad"
```

1. Activar "Requiere Control de Calidad"
2. Seleccionar tipo de prueba (Destructiva/No Destructiva)
3. En "Parámetros de Calidad" → Agregar línea:
   - Seleccionar parámetro (MAVI-04)
   - Configurar cuáles especificaciones aplican:
     - ✅ Polvo (activo)
     - ✅ Manchas (activo)
     - ❌ Rasgaduras (inactivo - no aplica a este producto)
4. Guardar

### Fase 2: Ejecución (Cada Recepción)

#### 2.1. Recepción de Materia Prima

1. Crear Orden de Compra
2. Recepcionar
3. Validar recepción → **QC se crea automáticamente**

#### 2.2. Ejecutar Control de Calidad

```
Calidad → Controles de Calidad → [QC Nuevo]
```

**Estado: Por realizar (draft)**

1. Verificar datos generales (Numeral 1)
   - Producto
   - Lote
   - Fecha de fabricación

2. Clic en **"Iniciar"** → Estado cambia a **"En proceso"**

3. Completar muestreo (Numeral 4)
   - Cantidad de muestra
   - Tipo (destructiva/no destructiva)

4. Clic en **"Confirmar Muestreo"** → Genera movimientos de inventario

5. Registrar resultados (Numeral 5)
   - Sistema muestra tabla jerárquica de determinaciones
   - Cada parámetro se expande mostrando sus especificaciones activas
   - Llenar resultados por especificación
   - Sistema evalúa automáticamente cada detalle
   - Dictamen del parámetro se agrega automáticamente

6. Completar firmas (Numeral 8)
   - Realizó: Analista QC
   - Verificó: Supervisor QC
   - Autorizó: Responsable Sanitario

7. Clic en **"Finalizar"**
   - Sistema genera folio legal: AN-[CodEmpleado][DDMMYY]-[Seq]
   - Estado cambia a **"Finalizado"**
   - Si resultado = RECHAZADO → Estado = **"Pendiente disposición"**

---

## Modelos de Datos

### Catálogo de Parámetros

#### `amunet.quality.check.parameter`
Plantilla reutilizable de parámetro.

**Campos principales**:
- `code` (Char) - Código del parámetro (NO único)
- `name` (Char) - Nombre de la determinación
- `specification_line_ids` (One2many) → especificaciones
- `specification_count` (Integer, computed) - Cantidad de especificaciones

**Archivo**: `models/amunet_quality_parameter.py`

#### `amunet.quality.check.parameter.specification`
Especificación individual dentro de un parámetro.

**Campos principales**:
- `parameter_id` (Many2one) → parámetro padre
- `sequence` (Integer) - Orden de visualización
- `name` (Char) - Nombre de la especificación
- `acceptance_criteria` (Char) - Criterio descriptivo
- `evaluation_type` (Selection) - Tipo de evaluación
- `expected_value_*` - Valores esperados según tipo
- `exclude_na_from_verdict` (Boolean) - Si N/A no cuenta como fallo

**Archivo**: `models/amunet_quality_check_parameter_specification.py`

### Configuración por Producto

#### `amunet.quality.parameter.product.rel`
Relación producto-parámetro.

**Campos principales**:
- `product_tmpl_id` (Many2one) → producto
- `parameter_id` (Many2one) → parámetro
- `sequence` (Integer) - Orden en QC
- `specification_config_ids` (One2many) → configuraciones de especificaciones

**Archivo**: `models/amunet_quality_parameter_product_rel.py`

#### `amunet.quality.parameter.specification.config`
Configuración de especificación para un producto específico.

**Campos principales**:
- `rel_id` (Many2one) → relación producto-parámetro
- `specification_id` (Many2one) → especificación
- `sequence` (Integer) - Orden
- `active` (Boolean) - **Controla si esta especificación se usa**
- `override_*` - Valores override por producto (opcional)

**Archivo**: `models/amunet_quality_parameter_specification_config.py`

### Ejecución de QC

#### `amunet.quality.check`
Control de calidad principal.

**Campos principales**:
- `name` (Char) - Referencia interna
- `analysis_number` (Char) - Folio legal (generado al finalizar)
- `state` (Selection) - draft / in_progress / pending / done
- `product_id` (Many2one) → producto
- `lot_id` (Many2one) → lote Amunet
- `factory_lot_id` (Many2one) → lote de fábrica
- `picking_id` (Many2one) → recepción
- `test_line_ids` (One2many) → líneas de prueba
- `result` (Selection, computed) - APROBADO / RECHAZADO / PENDIENTE

**Archivo**: `models/amunet_quality_check.py` (~800 líneas)

#### `amunet.quality.test.line`
Línea de prueba (un parámetro en ejecución).

**Campos principales**:
- `check_id` (Many2one) → QC
- `parameter_id` (Many2one) → parámetro
- `parameter_rel_id` (Many2one) → configuración producto-parámetro
- `sequence` (Integer) - Orden
- `name` (Char) - Nombre de la determinación
- `code` (Char) - Código
- `detail_line_ids` (One2many) → detalles
- `result_verdict` (Selection, computed) - pending / pass / fail / not_applicable

**Archivo**: `models/amunet_quality_test_line.py` (~500 líneas)

#### `amunet.quality.test.line.detail`
Detalle de especificación (resultado individual).

**Campos principales**:
- `test_line_id` (Many2one) → línea de prueba
- `specification_config_id` (Many2one) → configuración de especificación
- `specification_id` (Many2one) → especificación
- `sequence` (Integer) - Orden
- `name` (Char) - Nombre de la especificación
- `evaluation_type` (Selection) - Tipo de evaluación
- `result_*` - Campos de resultado según tipo
- `result_verdict` (Selection, computed) - pending / pass / fail / not_applicable

**Archivo**: `models/amunet_quality_test_line_detail.py` (~600 líneas)

---

## Interfaz de Usuario

### Vista Jerárquica de Determinaciones

El módulo incluye un **widget personalizado OWL2** para mostrar los resultados de forma jerárquica expandible:

```xml
<field name="test_line_ids" widget="quality_test_line_hierarchy"/>
```

**Funcionalidad**:
- Filas expandibles por parámetro
- Al expandir, muestra especificaciones (detalles)
- Badges de color según dictamen:
  - 🟡 Amarillo: Pendiente
  - 🟢 Verde: Cumple
  - 🔴 Rojo: No Cumple
  - ⚪ Gris: N/A

**Archivos**:
- JS: `static/src/js/quality_test_line_hierarchy.js`
- XML: `static/src/xml/quality_test_line_hierarchy.xml`
- CSS: `static/src/css/quality_hierarchy.css`

### Bloqueo Progresivo de Secciones

La UI controla visibilidad según estado usando `invisible` en XML (NO `attrs`):

```xml
<!-- Numeral 1-3: Siempre visible -->
<group name="numeral_1">...</group>

<!-- Numeral 4-5: Visible solo en in_progress -->
<group name="numeral_4" invisible="state not in ['in_progress', 'pending', 'done']">
  ...
</group>

<!-- Numeral 8: Visible cuando hay test lines completadas -->
<group name="numeral_8" invisible="state not in ['in_progress', 'pending', 'done']">
  ...
</group>
```

---

## Dependencias

- `stock` (Inventario - Core Odoo)
- `product` (Productos - Core Odoo)
- `uom` (Unidades de Medida - Core Odoo)
- `amunet_lot` (Sistema de lotes Amunet - proporciona `factory_lot_id`)

---

## Instalación y Configuración

### Instalación

```bash
# Desde el directorio del proyecto Odoo
cd /home/rafaelodoo/odooDocker18

# Actualizar el módulo
make update-module MODULE=amunet_quality DB=Amunet

# O instalar por primera vez
make install-module MODULE=amunet_quality DB=Amunet
```

### Configuración de Usuarios

1. **Ir a**: Ajustes → Usuarios y Compañías → Usuarios
2. **Asignar grupos de calidad**:
   - `Analista QC` - Crear/editar QC, registrar resultados
   - `Supervisor QC` - + Firmar "Verificó"
   - `Responsable Sanitario` - + Firmar "Autorizó", finalizar
   - `Manager QC` - Acceso total + configuración de parámetros
3. **Configurar código de empleado** (para folio): Campo `employee_code` en usuario

---

## Grupos de Seguridad

| Grupo | XML ID | Permisos |
|-------|--------|----------|
| Analista QC | `group_quality_user` | Crear/editar QC, registrar resultados, firmar "Realizó" |
| Supervisor QC | `group_quality_supervisor` | + Firmar "Verificó" |
| Responsable Sanitario | `group_quality_responsible` | + Firmar "Autorizó", finalizar análisis |
| Manager QC | `group_quality_manager` | Acceso total, configuración de parámetros |

**Archivo**: `security/amunet_quality_security.xml`

---

## Estructura del Módulo

```
amunet_quality/
├── __init__.py
├── __manifest__.py
├── README.md
├── CLAUDE.md                                    # Documentación para IA
│
├── models/                                      # 15 archivos
│   ├── __init__.py
│   ├── amunet_quality_check.py                 # Modelo principal QC (~800 líneas)
│   ├── amunet_quality_parameter.py             # Catálogo parámetros (~400 líneas)
│   ├── amunet_quality_test_line.py             # Línea de prueba (~500 líneas)
│   ├── amunet_quality_test_line_detail.py      # Detalle especificación (~600 líneas)
│   ├── amunet_quality_check_parameter_specification.py  # Especificaciones
│   ├── amunet_quality_parameter_specification_config.py # Config por producto
│   ├── amunet_quality_parameter_product_rel.py          # Relación producto-parámetro
│   ├── amunet_quality_parameter_conditional_option.py   # Opciones condicionales
│   ├── product_template.py                     # Extensión producto (tab QC)
│   ├── product_product.py                      # Extensión variante
│   ├── stock_picking.py                        # Auto-creación QC (~200 líneas)
│   └── res_users.py                            # Código empleado
│
├── views/                                       # Vistas XML
│   ├── amunet_quality_check_views.xml          # Formulario QC principal
│   ├── amunet_quality_parameter_views.xml      # Catálogo parámetros
│   ├── product_template_views.xml              # Tab QC en producto
│   ├── stock_picking_views.xml                 # Botón QC en recepción
│   └── menus.xml                               # Menús de calidad
│
├── wizard/                                      # Asistentes
│   ├── __init__.py
│   ├── amunet_quality_reanalysis_wizard.py     # Re-análisis
│   └── amunet_quality_reanalysis_wizard_views.xml
│
├── security/                                    # Seguridad
│   ├── amunet_quality_security.xml             # Grupos de acceso
│   └── ir.model.access.csv                     # Permisos de modelos
│
├── data/                                        # Datos base
│   └── ir_sequence_data.xml                    # Secuencia de folios
│
├── static/src/                                  # Frontend
│   ├── js/
│   │   └── quality_test_line_hierarchy.js      # Widget OWL2 (~300 líneas)
│   ├── xml/
│   │   └── quality_test_line_hierarchy.xml     # Templates QWeb
│   └── css/
│       └── quality_hierarchy.css               # Estilos
│
├── reports/                                     # Reportes (pendiente)
│
└── docs/                                        # Documentación técnica
    └── tickets/
        ├── 031_parametros-calidad-jerarquicos/
        │   ├── EPIC.md                         # Épica completa
        │   ├── README.md                       # Especificación técnica (~2000 líneas)
        │   ├── HU-031-1.md                     # Historia de usuario 1
        │   ├── HU-031-2.md                     # Historia de usuario 2
        │   ├── TICKETS.md                      # Tickets técnicos
        │   ├── GUIA_PRUEBAS.md                 # Guía de pruebas
        │   └── ANALISIS_MATRIZ_EQUIPOS.md      # Análisis de matriz
        └── matrices/
            ├── Matriz de control de calidad hojas maestras.md
            ├── Matriz de control de calidad Goteros.md
            └── Matriz de control de calidad Equipos.md
```

---

## Documentación Técnica

### Para Desarrolladores

- **CLAUDE.md** - Guía completa para IA sobre arquitectura y patrones
- **docs/tickets/031_parametros-calidad-jerarquicos/**:
  - `README.md` - Especificación técnica completa (~2000 líneas)
  - `EPIC.md` - Visión general de la épica
  - `GUIA_PRUEBAS.md` - Casos de prueba
  - `TICKETS.md` - Tickets técnicos detallados

### Matrices de Control de Calidad

Las matrices originales del cliente se encuentran en `docs/tickets/matrices/`:
- Hojas maestras (SPHMC*)
- Goteros
- Equipos

---

## Testing y Validación

### Casos de Prueba Básicos

#### 1. Configuración de Parámetro Simple
```
1. Crear parámetro MGA-0486
2. Tipo: simple
3. 1 especificación: Rango numérico (10-100)
4. Asignar a producto
5. Crear recepción
6. Validar QC se crea con 1 test line, 1 detail
```

#### 2. Configuración de Parámetro Compuesto
```
1. Crear parámetro MAVI-04
2. Tipo: composite
3. 4 especificaciones (Polvo, Manchas, Rasgaduras, Deformidad)
4. Asignar a producto (solo activar 2 de 4)
5. Crear recepción
6. Validar QC se crea con 1 test line, 2 details
```

#### 3. Evaluación Automática
```
1. Abrir QC con MAVI-04 (2 especificaciones activas)
2. Iniciar QC
3. Llenar Detail 1: "Sin polvo" → Debe evaluar PASS ✅
4. Llenar Detail 2: "Con manchas" → Debe evaluar FAIL ❌
5. Verificar test_line.result_verdict = "fail" (agregación)
```

### Pruebas Pendientes ⚠️

- [ ] Validar todos los tipos de evaluación con datos reales
- [ ] Probar performance con productos de >20 parámetros
- [ ] Validar movimientos de inventario en muestreo
- [ ] Probar re-análisis con trazabilidad
- [ ] Validar generación de PDF
- [ ] Probar integración con sistema de firmas

---

## Troubleshooting

### Problema: No se generan test lines al iniciar QC

**Causa**: Producto no tiene parámetros configurados o ninguna especificación está activa.

**Solución**:
1. Ir a producto → Tab "Control de Calidad"
2. Verificar que "Requiere Control de Calidad" = ✅
3. Verificar que hay parámetros en la lista
4. Abrir configuración de parámetro
5. Verificar que al menos 1 especificación tiene `active=True`

### Problema: Evaluación automática no funciona

**Causa**: Campos de resultado no coinciden con tipo de evaluación.

**Solución**:
1. Verificar `evaluation_type` de la especificación
2. Verificar que se está llenando el campo correcto:
   - `binary_selection` → `result_selection`
   - `numeric_range` → `result_numeric`
   - etc.
3. Revisar método `_compute_result_verdict()` en `amunet_quality_test_line_detail.py`

### Problema: Widget jerárquico no se muestra

**Causa**: Assets no cargados o error en JS.

**Solución**:
1. Verificar que `web.assets_backend` incluye archivos JS/XML en `__manifest__.py`
2. Limpiar caché del navegador
3. Revisar consola del navegador por errores JS
4. Reiniciar servidor Odoo

---

## Roadmap de Desarrollo

### 🚨 PRIORIDAD CRÍTICA (Sprint actual)
- [ ] **Implementar tipo `decision_matrix` (MAVI-16)**
  - Bloqueador para ~10 productos críticos (SPHMC25, SPHMC38, SPHMC52, etc.)
  - Incluye matriz de 13 escenarios de evaluación
  - Widget UI especializado para flujo de 3 pasos
  - Documentación completa: ver líneas 290-357 de este README
- [ ] **Validar parámetros MAVI especializados**
  - MAVI-07, MAVI-15, MAVI-16
  - Crear casos de prueba para cada escenario

### Corto Plazo (Sprint actual)
- [ ] Validar tipos de evaluación existentes
- [ ] Mejorar mensajes de error en validaciones
- [ ] Agregar tooltips en configuración de parámetros
- [ ] Optimizar consultas para productos con muchos parámetros
- [ ] Limpiar campos deprecated sin afectar flujos funcionales

### Mediano Plazo (Próximo mes)
- [ ] Implementar generación de PDF completo con matriz de decisión
- [ ] Sistema de firmas electrónicas mejorado
- [ ] Reportes y estadísticas de calidad
- [ ] Wizard de configuración guiada (especialmente para MAVI-16)
- [ ] Validaciones de coherencia entre tipos y especificaciones

### Largo Plazo (Trimestre)
- [ ] Dashboard de calidad en tiempo real
- [ ] Alertas automáticas por productos rechazados
- [ ] Integración con sistema de no conformidades
- [ ] App móvil para registro de resultados (con soporte para matriz de decisión)
- [ ] Sistema de auditoría avanzado

---

## Changelog

Para ver el historial completo de cambios, consulta el archivo [CHANGELOG.md](CHANGELOG.md).

### Versión Actual: 19.0.3.0.0
- Epic-034: Sistema de permisos granulares por numeral
- Mejoras en gestión de estados y rendimiento

### Versiones Anteriores
- **19.0.2.0.0**: Sistema jerárquico de parámetros (Epic-031) e información adicional (Epic-032)
- **18.0.1.0.0**: Versión inicial con sistema simple

---

## Soporte y Contacto

**Desarrollador**: Rafael López Flores
**Consultora**: DIC Consultores
**Cliente**: Amunet S.A. de C.V.

**Repositorio**: `/Users/rafaelodoo/projects/odooDocker18/sh_repos/amunetdev/amunet_quality`

---

## Licencia

Este módulo está licenciado bajo **LGPL-3**.

---

## Notas Importantes

🚨 **BLOQUEADOR CRÍTICO - MAVI-16**:
- El tipo de parámetro `decision_matrix` es **EL MÁS CRÍTICO** del sistema
- Sin este tipo, **~10 productos** (SPHMC25, SPHMC38, SPHMC52, etc.) NO pueden configurarse
- Basado en matriz de decisión de 13 escenarios con flujo multi-paso
- **Prioridad máxima de desarrollo**: Ver líneas 26-42 y 290-357 de este README
- Documentación completa en: `docs/tickets/matrices/Matriz de control de calidad hojas maestras.md`

⚠️ **DESARROLLO ACTIVO**: Este módulo está en desarrollo continuo. Se recomienda:
1. **NO usar en producción** hasta implementar tipo `decision_matrix` (MAVI-16)
2. Revisar y probar cada tipo de parámetro antes de configurar productos
3. Consultar documentación técnica en `docs/` para detalles de implementación
4. Reportar bugs y sugerencias al equipo de desarrollo
5. Mantener respaldo de configuraciones antes de actualizar
6. Los datos actuales son de prueba - se pueden eliminar campos deprecated sin pérdida de datos reales

✅ **ARQUITECTURA SÓLIDA**: La arquitectura de 4 niveles es estable y extensible para futuras mejoras, incluido el tipo `decision_matrix`.

🚧 **CONFIGURACIÓN COMPLEJA**: La configuración de parámetros jerárquicos (especialmente MAVI-16) requiere:
- Comprensión profunda del sistema de evaluación
- Capacitación antes de uso en producción
- Wizard de configuración guiada (pendiente de desarrollo)
