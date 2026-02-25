# Listas de Materiales para Entregas

**Versión**: 19.0.1.0.0
**Autor**: DIC Consultores
**Cliente**: Amunet S.A. de C.V.

---

## Descripción

Este módulo permite configurar listas de materiales (BOMs) para productos y usarlas en entregas a clientes, generando automáticamente las líneas de componentes con cantidades calculadas.

### Beneficios

- ⏱️ **Eficiencia**: Reducción del 80% en tiempo de creación de entregas
- ✅ **Precisión**: Eliminación de errores por omisión de componentes
- 📦 **Trazabilidad**: Compatible con sistema de lotes Amunet
- 🔄 **Consistencia**: Garantiza componentes correctos siempre

---

## Instalación

### Requisitos

- Odoo 19.0
- Módulo `stock` (Inventario)
- Módulo `product` (Productos)
- Módulo `amunet_lot` (recomendado)

### Pasos

1. Copiar el módulo a la carpeta de addons
2. Actualizar lista de aplicaciones
3. Instalar "Listas de Materiales para Entregas"

---

## Configuración

### 1. Habilitar en Tipo de Operación

**Navegación**: Inventario → Configuración → Tipos de Operación

1. Abrir el tipo de operación "Entregas"
2. Activar: ☑ **Habilitar Entrega por Lista de Materiales**
3. Guardar

### 2. Configurar Lista de Materiales

**Navegación**: Inventario → Configuración → Listas de Materiales para Entregas

1. Crear nuevo
2. Seleccionar **Producto Principal** (ej: KIT_COCRI_001)
3. Definir **Cantidad Base**: 1.0
4. Agregar componentes en pestaña "Componentes":
   - Producto: COCRI01, Cantidad: 10.0 kg
   - Producto: COCRI02, Cantidad: 2.0 kg
   - Producto: COCRI03, Cantidad: 5.0 unidades
5. Guardar

---

## Uso

### Crear Entrega con Lista de Materiales

**Navegación**: Inventario → Operaciones → Entregas → Crear

1. Seleccionar cliente y ubicaciones
2. Activar: ☑ **Entrega por Lista de Materiales**
3. Seleccionar **Producto**: KIT_COCRI_001
4. Definir **Cantidad**: 3.0
5. **Sistema genera automáticamente**:
   - COCRI01: 30.0 kg (10 × 3)
   - COCRI02: 6.0 kg (2 × 3)
   - COCRI03: 15.0 unidades (5 × 3)
6. Verificar líneas en pestaña "Operaciones Detalladas"
7. Validar entrega

---

## Características

- **Generación Automática**: Onchange genera líneas al cambiar producto o cantidad
- **Cálculo de Cantidades**: Factor multiplicador automático
- **Visibilidad Condicional**: Solo visible en entregas habilitadas
- **Unicidad**: Una BOM por producto por compañía
- **Integración Amunet**: Compatible con lotes Amunet

---

## Limitaciones

- Solo funciona en entregas (outgoing)
- Una BOM por producto
- No valida stock disponible automáticamente
- Sin versionamiento de BOMs

---

## Soporte

- **Desarrollador**: Rafael López Flores
- **Consultora**: DIC Consultores
- **Cliente**: Amunet S.A. de C.V.

---

## Licencia

LGPL-3
