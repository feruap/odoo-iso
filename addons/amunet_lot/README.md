# Amunet - Gestión de Lotes

**Versión**: 19.0.1.0.0
**Categoría**: Inventory/Inventory
**Autor**: Rafael López Flores - DIC Consultores
**Licencia**: LGPL-3
**Estado**: ✅ **PRODUCCIÓN** ✅

---

## 📋 Descripción General

Sistema completo de gestión de lotes para manufactura de dispositivos médicos que implementa **trazabilidad dual** entre lotes de fábrica/proveedor y lotes internos secuenciales de Amunet.

### Concepto de Trazabilidad Dual

El sistema maneja **dos niveles de identificación de lotes**:

```
┌──────────────────────────────────────────────────┐
│ NIVEL 1: Lote de Fábrica (Proveedor)            │
│ ┌──────────────────────────────────────────────┐ │
│ │ Modelo: amunet.lot.factory                   │ │
│ │ Ejemplo: "FAB-2025-001"                      │ │
│ │ - Número asignado por el fabricante          │ │
│ │ - Único en el sistema                        │ │
│ │ - Rastreable a certificados del proveedor    │ │
│ └──────────────────────────────────────────────┘ │
└──────────────────────────────────────────────────┘
                    ↓ One2many: lot_ids
┌──────────────────────────────────────────────────┐
│ NIVEL 2: Lote Amunet (Interno Secuencial)       │
│ ┌──────────────────────────────────────────────┐ │
│ │ Modelo: stock.lot (nativo Odoo extendido)    │ │
│ │ Ejemplos: "CRI01112501", "CRI01112502"       │ │
│ │ - Generados automáticamente por producto     │ │
│ │ - Formato: PREFIJO + MMYY + NÚMERO          │ │
│ │ - Vinculados a lote de fábrica               │ │
│ │ - Campo: factory_lot_id → amunet.lot.factory │ │
│ └──────────────────────────────────────────────┘ │
└──────────────────────────────────────────────────┘
```

**¿Por qué trazabilidad dual?**
- **Cumplimiento normativo**: NOM-241-SSA-V-VIGENTE requiere trazabilidad completa hasta el fabricante
- **Control interno**: Lotes secuenciales Amunet facilitan seguimiento en planta
- **Flexibilidad**: Un lote de fábrica puede fraccionarse en múltiples lotes internos
- **Auditoría**: Vinculación completa entre materia prima y producto procesado

---

## ✨ Características Principales

### 🔗 Trazabilidad Dual Completa
- **Modelo dedicado** para lotes de fábrica (`amunet.lot.factory`)
- **Relación 1:N**: Un lote de fábrica → Múltiples lotes Amunet
- **Sincronización bidireccional** automática entre `stock.move.line` y `stock.lot`
- **Visible en todas las operaciones**: recepciones, control de calidad, almacenamiento, inventario

### 🔢 Generación Automática de Secuencias
- **Formato configurable**: `PREFIJO + %(month)s%(y)s + NÚMERO`
- **Ejemplo**: `CRI01112501` (Producto CRI, mes 11, año 25, secuencia 01)
- **Placeholders dinámicos**: El mes y año se actualizan automáticamente
- **Sin intervención manual**: Los lotes se crean automáticamente al validar recepciones

### 📅 Reinicio Mensual Automático
- **Cron job diario**: Verifica si es día 1 del mes
- **Actualización automática** de prefijos con nuevo mes/año
- **Reinicio de secuencia** a 1
- **Configurable por producto**: Activar/desactivar según necesidad

### 🏭 Tipos de Operación Especializados
- **Flags personalizados** en tipos de operación (picking types):
  - `is_reception`: Para recepciones de materia prima
  - `is_quality_control`: Para operaciones de control de calidad
  - `is_storage`: Para almacenamiento post-QC
- **Configuración automática** al instalar el módulo
- **Integración con amunet_quality**: Campos preparados para módulo de QC

### 🔄 Sincronización Inteligente
- **Bidireccional**: `stock.move.line.factory_lot_id` ↔ `stock.lot.factory_lot_id`
- **En creación y escritura**: Hooks en `create()` y `write()` de stock.move.line
- **En validación de picking**: Sincronización adicional en `_action_done()`
- **Carga automática**: Al seleccionar un lote, carga su factory_lot_id

---

## 🏗️ Arquitectura del Sistema

### Modelos de Datos

#### `amunet.lot.factory` - Lote de Fábrica
Modelo principal para lotes del proveedor.

**Campos principales**:
- `name` (Char) - Número de lote de fábrica (ÚNICO)
- `ref` (Char) - Referencia adicional
- `lot_ids` (One2many) → stock.lot - Lotes Amunet asociados
- `lot_count` (Integer, computed) - Cantidad de lotes Amunet

**Archivo**: `models/amunet_lot_factory.py`

**Constraint**: `name` debe ser único en todo el sistema

#### `stock.lot` - Lote Amunet (Extensión)
Extensión del modelo nativo de Odoo.

**Campos añadidos**:
- `factory_lot_id` (Many2one) → amunet.lot.factory - Lote de fábrica asociado
- `amunet_auto_generated` (Boolean) - Indica si fue generado automáticamente

**Archivo**: `models/stock_lot.py`

**Integración nativa**: Usa el modelo estándar de Odoo, mantiene compatibilidad completa

#### `stock.move.line` - Línea de Movimiento (Extensión)
Extensión para sincronización de factory_lot_id.

**Campo añadido**:
- `factory_lot_id` (Many2one) → amunet.lot.factory - Sincronizado con lot_id

**Métodos override**:
- `create()` - Sincroniza factory_lot_id al crear líneas
- `write()` - Sincroniza factory_lot_id al modificar líneas
- `_onchange_lot_id_factory()` - Carga factory_lot_id al seleccionar lote

**Archivo**: `models/stock_move_line.py`

**Lógica de sincronización**:
1. Si `lot_id` tiene `factory_lot_id`, lo copia a la línea
2. Si la línea tiene `factory_lot_id` y el lote no, lo sincroniza al lote
3. Sincronización en ambas direcciones (bidireccional)

#### `stock.quant` - Cantidad en Stock (Extensión)
Extensión para mostrar factory_lot_id en inventario.

**Campo añadido**:
- `factory_lot_id` (Many2one) - Related a `lot_id.factory_lot_id` (stored, readonly)

**Archivo**: `models/stock_quant.py`

**Propósito**: Mostrar lote de fábrica directamente en vistas de inventario sin hacer joins

#### `stock.picking` - Operación de Stock (Extensión)
Extensión para sincronización y flags de tipo de operación.

**Campos añadidos**:
- `is_quality_control` (Boolean, computed) - Es operación de QC
- `is_storage` (Boolean, computed) - Es operación de almacenamiento
- `is_reception` (Boolean, computed) - Es operación de recepción

**Método override**:
- `_action_done()` - Sincroniza factory_lot_id de líneas a lotes después de validar

**Archivo**: `models/stock_picking.py`

#### `stock.picking.type` - Tipo de Operación (Extensión)
Extensión para categorizar tipos de operaciones.

**Campos añadidos**:
- `is_quality_control` (Boolean) - Es tipo de QC
- `is_reception` (Boolean) - Es tipo de recepción
- `is_storage` (Boolean) - Es tipo de almacenamiento

**Método**:
- `_setup_amunet_operation_types()` - Configuración automática al instalar

**Archivo**: `models/stock_picking_type.py`

#### `product.template` - Plantilla de Producto (Extensión)
Extensión para configuración de secuencias de lotes.

**Campos añadidos**:
- `amunet_lot_reset_monthly` (Boolean) - Reiniciar secuencia mensualmente
- `amunet_lot_prefix` (Char, computed) - Prefijo base para lotes

**Métodos**:
- `_is_amunet_auto_lot_enabled()` - Verifica si auto-generación está activa
- `_compute_amunet_lot_prefix()` - Extrae prefijo base de la secuencia
- `_inverse_amunet_lot_prefix()` - Crea/actualiza secuencia con placeholders

**Archivo**: `models/product_template.py`

**Formato de secuencia**: `PREFIJO%(month)s%(y)s` (ej: `CRI%(month)s%(y)s`)

#### Modelos Adicionales
- `stock.move` - Extensiones de movimientos (`models/stock_move.py`)
- `stock.scrap` - Extensiones de desecho (`models/stock_scrap.py`)
- `stock.traceability.report` - Reportes de trazabilidad (`models/stock_traceability_report.py`)

---

## 🔄 Flujo Completo de Trazabilidad

### Fase 1: Configuración Inicial (Una vez por producto)

#### 1.1. Configurar Producto para Auto-Generación

```
Inventario → Productos → Productos → [Seleccionar Producto]
```

1. En pestaña **"Inventario"**, sección **"Trazabilidad"**:
   - ✅ Activar **"Seguimiento por lotes"** (tracking = 'lot')
   - Configurar **"Custom Lot/Serial"**: Ingresar prefijo base (ej: `CRI`)
2. **Guardar** → El sistema crea automáticamente la secuencia con formato `CRI%(month)s%(y)s`
3. (Opcional) Activar **"Reiniciar secuencia mensualmente"**

**Resultado**:
- Secuencia creada: código `amunet.lot.CRI.123`
- Prefijo dinámico: `CRI0125` (mes 01, año 25)
- Próximo lote: `CRI012501`, `CRI012502`, etc.

### Fase 2: Recepción de Materia Prima (Cada recepción)

#### 2.1. Crear Orden de Compra

1. Crear OC con producto configurado
2. Confirmar OC → Se genera recepción automáticamente

#### 2.2. Validar Recepción con Lote de Fábrica

1. Abrir recepción pendiente
2. En **"Operaciones detalladas"**, para cada línea:
   - **NO ingresar** Número de serie/lote manualmente
   - **Ingresar** "Número de serie/lote de fábrica" (factory_lot_id)
     - Puede ser nuevo (crear desde combo) o existente (seleccionar)
     - Ejemplo: `FAB-2025-001`
3. **Validar** recepción

**Sistema ejecuta automáticamente**:
1. Genera lote Amunet secuencial: `CRI012501`
2. Vincula `stock.lot.factory_lot_id` → `amunet.lot.factory`
3. Sincroniza `stock.move.line.factory_lot_id` ↔ `stock.lot.factory_lot_id`
4. Crea quants con ambos lotes (Amunet + fábrica)

#### 2.3. Resultado en Inventario

```
Inventario → Informes → Valoración de inventario
```

Verás:
- **Número de serie/lote**: `CRI012501` (Amunet, interno)
- **Número de serie/lote de fábrica**: `FAB-2025-001` (Proveedor)
- **Ubicación**: WH/Stock
- **Cantidad disponible**: X unidades

### Fase 3: Control de Calidad (Con amunet_quality)

1. Recepción validada → QC creado automáticamente
2. QC vinculado a:
   - `lot_id`: `CRI012501` (Amunet)
   - `factory_lot_id`: `FAB-2025-001` (Fábrica)
3. Analista ejecuta QC, sistema rastrea ambos lotes

### Fase 4: Almacenamiento y Uso

1. **Movimientos internos**: Mantienen vinculación de ambos lotes
2. **Consumo en producción**: Trazabilidad completa de fábrica a producto final
3. **Reportes de trazabilidad**: Incluyen ambos niveles de lote

---

## 🔧 Algoritmos Clave

### Sincronización Bidireccional de factory_lot_id

**En `stock.move.line.create()`**:
```python
for vals in vals_list:
    lot_id = vals.get('lot_id')
    factory_lot_id = vals.get('factory_lot_id')

    if lot_id and not factory_lot_id:
        # Cargar factory_lot_id desde el lote
        lot = self.env['stock.lot'].browse(lot_id)
        if lot.factory_lot_id:
            vals['factory_lot_id'] = lot.factory_lot_id.id

records = super().create(vals_list)

# Sincronizar factory_lot_id al lote si no lo tiene
for record in records:
    if record.factory_lot_id and record.lot_id and not record.lot_id.factory_lot_id:
        record.lot_id.sudo().write({'factory_lot_id': record.factory_lot_id.id})
```

**En `stock.move.line.write()`**:
```python
if 'lot_id' in vals and 'factory_lot_id' not in vals:
    lot_id = vals.get('lot_id')
    if lot_id:
        lot = self.env['stock.lot'].browse(lot_id)
        if lot.factory_lot_id:
            vals['factory_lot_id'] = lot.factory_lot_id.id

res = super().write(vals)

# Sincronizar factory_lot_id al lote si no lo tiene
for record in self:
    if record.factory_lot_id and record.lot_id and not record.lot_id.factory_lot_id:
        record.lot_id.sudo().write({'factory_lot_id': record.factory_lot_id.id})
```

**En `stock.picking._action_done()`**:
```python
res = super()._action_done()

# Sincronizar factory_lot_id de las líneas a los lotes
for picking in self:
    for line in picking.move_line_ids:
        if line.factory_lot_id and line.lot_id:
            if line.lot_id.factory_lot_id != line.factory_lot_id:
                line.lot_id.sudo().write({'factory_lot_id': line.factory_lot_id.id})

return res
```

### Reinicio Mensual de Secuencias

**Cron ejecutado diariamente** (`data/ir_cron_data.xml`):
```python
def _cron_reset_amunet_lot_sequences_monthly(self):
    """Ejecutado diariamente, solo actúa el día 1 del mes"""
    if datetime.now().day != 1:
        return

    # Buscar productos con reinicio mensual activo
    products = self.search([
        ('amunet_auto_lot', '=', True),
        ('amunet_lot_reset_monthly', '=', True),
        ('lot_sequence_id', '!=', False),
    ])

    for product in products:
        # Extraer prefijo base
        base_prefix = product.serial_prefix_format.strip()
        if len(base_prefix) > 4 and base_prefix[-4:].isdigit():
            base_prefix = base_prefix[:-4]

        # Actualizar prefijo con nuevo mes/año
        product.lot_sequence_id.write({
            'prefix': f"{base_prefix}{datetime.now().strftime('%m%y')}",
            'number_next': 1,  # Reiniciar contador
        })
```

---

## 📊 Estructura del Módulo

```
amunet_lot/
├── __init__.py
├── __manifest__.py
├── README.md
├── CLAUDE.md                                    # Documentación para IA
│
├── models/                                      # 11 archivos (~957 líneas)
│   ├── __init__.py
│   ├── amunet_lot_factory.py                   # Lote de fábrica (~66 líneas)
│   ├── stock_lot.py                            # Extensión stock.lot (~25 líneas)
│   ├── stock_move_line.py                      # Sincronización (~150 líneas)
│   ├── stock_quant.py                          # Related factory_lot_id (~16 líneas)
│   ├── stock_picking.py                        # Flags + sincronización (~72 líneas)
│   ├── stock_picking_type.py                   # Tipos de operación (~100 líneas)
│   ├── stock_move.py                           # Extensiones de movimientos
│   ├── stock_scrap.py                          # Extensiones de desecho
│   ├── stock_traceability_report.py            # Reportes de trazabilidad
│   └── product_template.py                     # Configuración secuencias (~180 líneas)
│
├── views/                                       # 11 archivos
│   ├── product_template_views.xml              # Config producto
│   ├── amunet_lot_factory_views.xml            # Gestión lotes fábrica
│   ├── stock_lot_views.xml                     # Vista lotes Amunet
│   ├── stock_quant_views.xml                   # Inventario con factory_lot
│   ├── stock_picking_views.xml                 # Operaciones con factory_lot
│   ├── stock_picking_type_views.xml            # Tipos de operación
│   ├── stock_move_line_views.xml               # Líneas de movimiento
│   ├── stock_move_line_actions.xml             # Acciones
│   ├── stock_move_operations_views.xml         # Operaciones detalladas
│   └── stock_scrap_views.xml                   # Desecho
│
├── data/                                        # 2 archivos
│   ├── ir_cron_data.xml                        # Cron reinicio mensual
│   └── stock_picking_type_data.xml             # Config automática tipos
│
├── security/
│   └── ir.model.access.csv                     # Permisos
│
└── static/src/
    └── xml/
        ├── stock_traceability_report.xml       # Template trazabilidad
        └── lots_dialog.xml                     # Diálogo lotes
```

---

## ⚙️ Configuración

### Instalación

```bash
# Desde el directorio del proyecto Odoo
cd /home/rafaelodoo/odooDocker18

# Instalar módulo
make install-module MODULE=amunet_lot DB=Amunet

# O actualizar si ya está instalado
make update-module MODULE=amunet_lot DB=Amunet
```

### Configuración Automática Post-Instalación

El módulo configura automáticamente:

1. **Tipos de operación de recepción** (`code='incoming'`):
   - `is_reception = True`
2. **Tipos con "control de calidad" en el nombre**:
   - `is_quality_control = True`
3. **Tipos con "almacenamiento" en el nombre**:
   - `is_storage = True`

**Verificar**: `Inventario → Configuración → Tipos de operación`

### Configuración Manual de Tipos de Operación

Si necesitas marcar manualmente un tipo:

```
Inventario → Configuración → Tipos de operación → [Seleccionar Tipo]
```

Activar checkboxes según corresponda:
- ☑️ Es Control de Calidad
- ☑️ Es recepción
- ☑️ Es almacenamiento

---

## 🎯 Casos de Uso

### Caso 1: Producto con Reinicio Mensual

**Configuración**:
- Producto: `[COCRI01] Cartucho Combo respiratorio`
- Prefijo base: `CRI`
- Reinicio mensual: ✅ Activado

**Noviembre 2025** (mes 11, año 25):
```
Recepción 1 con lote fábrica "FAB-2025-001":
  → Lote Amunet: CRI01112501
  → factory_lot_id: FAB-2025-001

Recepción 2 con lote fábrica "FAB-2025-001":
  → Lote Amunet: CRI01112502
  → factory_lot_id: FAB-2025-001 (mismo lote fábrica, distinto lote Amunet)

Recepción 3 con lote fábrica "FAB-2025-002":
  → Lote Amunet: CRI01112503
  → factory_lot_id: FAB-2025-002 (nuevo lote fábrica)
```

**Diciembre 2025** (mes 12, año 25):
```
Cron ejecuta el 1 de diciembre:
  → Actualiza prefijo: CRI0125 → CRI0126
  → Reinicia número_next: 1

Recepción 1 con lote fábrica "FAB-2025-003":
  → Lote Amunet: CRI01122501 (nueva secuencia)
  → factory_lot_id: FAB-2025-003
```

### Caso 2: Un Lote de Fábrica → Múltiples Lotes Amunet

**Escenario**: Recepción de 1000 unidades con lote fábrica `PROV-2025-123`, fraccionado en 3 recepciones:

```
Recepción 1 (300 unidades):
  Lote fábrica: PROV-2025-123
  Lote Amunet: MPC01112501
  → stock.lot.factory_lot_id = PROV-2025-123
  → 300 unidades en WH/Stock con CRI01112501

Recepción 2 (400 unidades):
  Lote fábrica: PROV-2025-123 (mismo)
  Lote Amunet: MPC01112502 (nuevo)
  → stock.lot.factory_lot_id = PROV-2025-123
  → 400 unidades en WH/Stock con CRI01112502

Recepción 3 (300 unidades):
  Lote fábrica: PROV-2025-123 (mismo)
  Lote Amunet: MPC01112503 (nuevo)
  → stock.lot.factory_lot_id = PROV-2025-123
  → 300 unidades en WH/Stock con CRI01112503
```

**Resultado en `amunet.lot.factory`**:
```
name: "PROV-2025-123"
lot_ids: [MPC01112501, MPC01112502, MPC01112503]
lot_count: 3
```

**Ventaja**: Control granular interno mientras se mantiene trazabilidad al certificado del proveedor.

### Caso 3: Múltiples Productos, Múltiples Lotes

| Producto | Prefijo | Lote Fábrica | Lote Amunet Generado |
|----------|---------|--------------|----------------------|
| Cartucho respiratorio | `CRI` | `FAB-2025-001` | `CRI01112501` |
| Mascarilla PVC | `MPC` | `FAB-2025-002` | `MPC01112501` |
| Sensor oxígeno | `SEN` | `FAB-2025-003` | `SEN01112501` |
| Cartucho respiratorio | `CRI` | `FAB-2025-004` | `CRI01112502` |

---

## 🐛 Troubleshooting

### Problema: Los lotes no se generan automáticamente

**Causas posibles**:
1. Producto no tiene seguimiento por lotes activado
2. Campo "Custom Lot/Serial" (serial_prefix_format) está vacío
3. Secuencia no existe

**Solución**:
1. Verificar **"Seguimiento por lotes"** = ✅
2. Ingresar prefijo en **"Custom Lot/Serial"** (ej: `CRI`)
3. **Guardar** producto → Secuencia se crea automáticamente
4. Verificar en `Configuración → Técnico → Secuencias` que existe `amunet.lot.CRI.123`

### Problema: factory_lot_id no se sincroniza

**Causas posibles**:
1. Lote de fábrica no ingresado en operaciones detalladas
2. Validación muy rápida (race condition)

**Solución**:
1. **Siempre ingresar** factory_lot_id en operaciones detalladas ANTES de validar
2. Verificar después de validar: `stock.lot` debe tener `factory_lot_id`
3. Si no sincronizó, ejecutar manualmente:
   ```python
   # En shell de Odoo
   lot = env['stock.lot'].browse(123)  # ID del lote
   lot.write({'factory_lot_id': factory_lot_id})
   ```

### Problema: Secuencia no se reinicia mensualmente

**Verificar**:
1. ✓ Campo **"Reiniciar secuencia mensualmente"** = ✅ en producto
2. ✓ Cron job está activo:
   ```
   Configuración → Técnico → Automatización → Acciones programadas
   Buscar: "Reinicio mensual de secuencias de lotes Amunet"
   ```
3. ✓ Cron ejecuta a las 00:01 del día 1 de cada mes

**Solución**:
- Activar cron si está inactivo
- Ejecutar manualmente para probar:
  ```python
  # En shell de Odoo
  env['product.template']._cron_reset_amunet_lot_sequences_monthly()
  ```

### Problema: Quiero cambiar el formato de la secuencia

**Editar** secuencia manualmente:

```
Configuración → Técnico → Secuencias e Identificadores → Secuencias
Buscar: amunet.lot.[PREFIJO].[ID_PRODUCTO]
```

Campos editables:
- **Prefijo**: `CRI%(month)s%(y)s`
- **Padding**: Número de dígitos (default: 2)
- **Incremento**: Siempre 1

**Ejemplo**:
- Prefijo: `CRI%(month)s%(y)s%(day)s` (agregar día)
- Padding: 3 (para tener 001, 002, etc.)

### Problema: No veo factory_lot_id en vistas

**Causas posibles**:
1. Vistas no cargadas correctamente
2. Permisos de acceso

**Solución**:
1. Actualizar módulo: `make update-module MODULE=amunet_lot`
2. Limpiar caché del navegador
3. Verificar permisos en `security/ir.model.access.csv`

---

## 🔗 Integración con Otros Módulos

### Integración con `amunet_quality`

El módulo está **preparado para integración** con el sistema de control de calidad:

**Campos preparados**:
- `stock.picking.is_quality_control` - Identifica operaciones de QC
- `stock.picking.is_storage` - Identifica almacenamiento post-QC
- `stock.picking.is_reception` - Identifica recepciones

**Flujo esperado con QC**:
```
1. Recepción validada (is_reception=True)
   → factory_lot_id + lot_id creados
   ↓
2. QC creado automáticamente
   → Vinculado a lot_id y factory_lot_id
   ↓
3. Muestreo QC (is_quality_control=True)
   → Movimiento con mismos lotes
   ↓
4. Almacenamiento post-QC (is_storage=True)
   → Movimiento con mismos lotes
```

**Campo clave**: `stock.lot.factory_lot_id` es usado por `amunet_quality.check` para rastrear lote de proveedor.

### Integración con Reportes Nativos

**Reporte de trazabilidad** (`stock.traceability.report`):
- Extensión con campo `factory_lot_id`
- Muestra trazabilidad completa: fábrica → Amunet → movimientos → ubicaciones

**Valoración de inventario**:
- Campo `factory_lot_id` visible en columnas
- Filtros por lote de fábrica disponibles

---

## 📈 Estadísticas del Módulo

| Métrica | Valor |
|---------|-------|
| **Modelos Python** | 11 archivos |
| **Líneas de código** | ~957 líneas |
| **Vistas XML** | 11 archivos |
| **Campos añadidos** | 12 campos |
| **Métodos override** | 6 métodos |
| **Cron jobs** | 1 (reinicio mensual) |
| **Constraints** | 1 (factory_lot unique) |

---

## 📚 Documentación Técnica

### Para Desarrolladores

- **CLAUDE.md** - Guía completa para IA sobre arquitectura
- **Código fuente**: Comentarios inline en español/inglés
- **Logging**: `_logger` en archivos críticos

### Arquitectura de Sincronización

**Prioridad de sincronización**:
1. `stock.move.line.create()` - Primera carga
2. `stock.move.line.write()` - Actualización
3. `stock.picking._action_done()` - Confirmación final

**Dirección de sincronización**:
- `lot_id.factory_lot_id` → `move_line.factory_lot_id` (carga)
- `move_line.factory_lot_id` → `lot_id.factory_lot_id` (sincronización)

**Uso de `sudo()`**:
- Necesario para escribir en `stock.lot` desde `stock.move.line`
- Solo en sincronización, no en creación/validación principal

---

## ⚠️ Consideraciones Importantes

### Unicidad de Lotes de Fábrica

- **`amunet.lot.factory.name` es ÚNICO** en todo el sistema
- No se pueden crear dos lotes de fábrica con el mismo número
- Si el proveedor reutiliza números, agregar prefijo: `PROV-ABC-123`

### Modificación de Lotes Validados

- **NO modificar** `factory_lot_id` en lotes con movimientos confirmados
- **NO modificar** `name` de lotes Amunet después de usarlos
- Para correcciones, crear nuevo lote y hacer transferencia

### Performance con Muchos Lotes

- Índices en `factory_lot_id` en todos los modelos
- Campo `factory_lot_id` en `stock.quant` es **stored** para optimizar consultas
- Filtros por lote de fábrica son eficientes

### Reinicio Mensual

- Cron ejecuta **todos los días** pero solo actúa el día 1
- Si el servidor está apagado el día 1, NO se ejecutará ese mes
- Ejecutar manualmente si es necesario:
  ```python
  env['product.template']._cron_reset_amunet_lot_sequences_monthly()
  ```

---

## 🆚 Comparación: amunet_lot vs Sistema Nativo de Odoo

| Característica | Odoo Nativo | amunet_lot |
|----------------|-------------|------------|
| **Modelo de lote** | stock.lot | stock.lot + amunet.lot.factory |
| **Trazabilidad** | Simple (1 nivel) | Dual (fábrica + interno) |
| **Generación automática** | ❌ Manual | ✅ Automática secuencial |
| **Formato configurable** | ❌ No | ✅ Sí (placeholders) |
| **Reinicio mensual** | ❌ No | ✅ Sí (automático) |
| **Lote de proveedor** | Campo texto | Modelo dedicado + relación |
| **Sincronización** | N/A | Bidireccional automática |
| **Reportes** | Estándar | Extendidos con factory_lot |
| **Complejidad** | Baja | Media |
| **Cumplimiento normativo** | Básico | NOM-241-SSA-V completo |

---

## 📄 Licencia

Este módulo está licenciado bajo **LGPL-3**.

---

## 👥 Autor y Soporte

**Desarrollador**: Rafael López Flores
**Consultora**: DIC Consultores
**Cliente**: Amunet S.A. de C.V.

**Repositorio**: `/Users/rafaelodoo/projects/odooDocker18/sh_repos/amunetdev/amunet_lot`

---

## 🎯 Conclusión

El módulo `amunet_lot` implementa un sistema **completo y robusto** de trazabilidad dual para dispositivos médicos regulados:

✅ **Trazabilidad dual completa** (fábrica + interno)
✅ **Generación automática** de lotes secuenciales
✅ **Sincronización bidireccional** inteligente
✅ **Reinicio mensual** automático
✅ **Integración nativa** con Odoo
✅ **Preparado para control de calidad** (amunet_quality)
✅ **Cumplimiento normativo** (NOM-241-SSA-V-VIGENTE)

**Estado**: ✅ Producción-ready para manufactura de dispositivos médicos regulados.
