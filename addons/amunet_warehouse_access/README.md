# Amunet - Control de Acceso Dinámico por Almacén

**Versión**: 19.0.1.0.0
**Epic**: [EPIC-033: Control de Acceso Dinámico por Almacén](amunet_quality/docs/tickets/033_control-acceso-almacenes/EPIC.md)
**Licencia**: LGPL-3

---

## Descripción

Este módulo implementa un sistema de **control de acceso granular a almacenes** que permite asignar permisos específicos a usuarios para acceder a almacenes y realizar operaciones de inventario.

### Características Principales

✅ **Configuración Gráfica**: Asignar accesos desde la interfaz sin modificar código
✅ **Granularidad**: Control por almacén completo o por operaciones específicas
✅ **Generación Automática de Record Rules**: El sistema crea reglas de Odoo dinámicamente
✅ **Validación Backend**: Seguridad adicional más allá de Record Rules en UI
✅ **Vista de Matriz**: Gestión masiva de accesos desde una sola pantalla
✅ **Auditoría**: Visibilidad completa de quién tiene acceso a qué almacenes

---

## Casos de Uso

### Ejemplo 1: Usuario de Recepción

**Configuración**:
- Usuario: "María González"
- Almacén: "Almacén Principal"
- Tipo: Acceso Restringido
- Operaciones: Solo "Recepciones"

**Resultado**:
- ✅ María puede ver y validar recepciones en Almacén Principal
- ❌ María NO puede ver entregas ni transferencias internas
- ❌ María NO puede acceder a otros almacenes

### Ejemplo 2: Usuario de Producción

**Configuración**:
- Usuario: "Juan Pérez"
- Almacén: "Almacén de Producción"
- Tipo: Acceso Completo

**Resultado**:
- ✅ Juan puede realizar TODAS las operaciones en Almacén de Producción
- ✅ Juan puede ver ubicaciones, quants, movimientos
- ❌ Juan NO puede acceder a otros almacenes

---

## Instalación

### Requisitos

- Odoo 19 Community o Enterprise
- Módulo `stock` instalado
- Módulo `base` instalado

### Pasos de Instalación

```bash
# 1. Copiar módulo a addons path
cd /Users/rafaelodoo/projects/odooDocker18/sh_repos/amunetdev
git pull

# 2. Instalar módulo
cd /Users/rafaelodoo/projects/odooDocker18
make install-module MODULE=amunet_warehouse_access DB=Amunet

# 3. Verificar instalación
make shell
>>> env['ir.module.module'].search([('name', '=', 'amunet_warehouse_access')]).state
'installed'
```

---

## Configuración

### 1. Configurar Acceso para un Usuario

**Ruta**: `Configuración → Usuarios y Compañías → Usuarios`

1. Seleccionar usuario (ej: "María González")
2. Ir a tab **"Accesos a Almacenes"**
3. Click en "Agregar línea"
4. Seleccionar almacén: "Almacén Principal"
5. Seleccionar tipo de acceso:
   - **Acceso Completo**: Todas las operaciones
   - **Acceso Restringido**: Seleccionar operaciones específicas
6. Si es restringido, seleccionar operaciones permitidas (ej: "Recepciones")
7. Guardar

**Automático**: El sistema genera Record Rules de Odoo inmediatamente.

### 2. Ver Matriz de Accesos

**Ruta**: `Configuración → Usuarios y Compañías → Accesos a Almacenes`

Vista de lista con todos los accesos configurados:
- Filtrar por usuario, almacén, tipo de acceso
- Agrupar por usuario o almacén
- Editar directamente desde la lista

### 3. Ver Usuarios con Acceso a un Almacén

**Ruta**: `Inventario → Configuración → Almacenes`

1. Seleccionar almacén (ej: "Almacén Principal")
2. Ir a tab **"Usuarios con Acceso"**
3. Ver lista de usuarios configurados
4. Editar accesos directamente

---

## Funcionamiento Técnico

### Flujo de Datos

```
1. ADMIN configura acceso en formulario de usuario
   ↓
2. Sistema crea registro en amunet.warehouse.access
   ↓
3. Sistema genera Record Rules automáticamente (ir.rule)
   ↓
4. Usuario intenta acceder a stock.picking
   ↓
5. Record Rules filtran automáticamente (solo ve sus almacenes)
   ↓
6. Usuario intenta validar picking
   ↓
7. Validación backend verifica permiso
   ↓
8. Si NO tiene permiso: AccessError
   ↓
9. Si SÍ tiene permiso: Continúa normalmente
```

### Modelos Principales

**`amunet.warehouse.access`**
- Configuración de acceso usuario-almacén-operación
- Genera Record Rules automáticamente al guardar

**`amunet.warehouse.access.rule`**
- Metadatos de reglas generadas
- Relación con `ir.rule` de Odoo

**`res.users`** (extendido)
- `warehouse_access_ids`: Configuraciones de acceso
- `warehouse_ids`: Almacenes permitidos (computed)

**`stock.warehouse`** (extendido)
- `user_access_ids`: Usuarios con acceso
- `allowed_user_ids`: Usuarios permitidos (computed)

---

## Validaciones de Seguridad

### Validaciones Backend

El módulo valida permisos en **backend** (Python) para mayor seguridad:

#### `stock.picking`
- `action_confirm()`: Validar acceso antes de confirmar
- `button_validate()`: Validar acceso antes de validar
- `create()`: Validar acceso al crear
- `write()`: Validar acceso al modificar
- `unlink()`: Validar acceso al eliminar

#### `stock.location`
- `create()`: Validar acceso al crear ubicación
- `write()`: Validar acceso al modificar ubicación
- `unlink()`: Validar acceso al eliminar ubicación

#### `stock.quant`
- `create()`: Validar acceso al crear quant (ajustes)
- `write()`: Validar acceso al modificar quant
- `unlink()`: Validar acceso al eliminar quant

### Bypass de Validaciones

**Administradores del sistema** (`base.group_system`):
- Tienen acceso completo automáticamente
- No se les aplican restricciones

**Operaciones en modo sudo**:
- Cron jobs, procesos automatizados
- No se validan para evitar bloqueos

---

## Arquitectura de Record Rules

### Generación Automática

Al crear/modificar un acceso, el sistema genera reglas para 4 modelos:

1. **`stock.picking`**: Operaciones de inventario
   - Dominio: `[('picking_type_id.warehouse_id', '=', WAREHOUSE_ID)]`
   - Si restringido: + `[('picking_type_id', 'in', OPERATION_IDS)]`

2. **`stock.location`**: Ubicaciones
   - Dominio: `[('warehouse_id', '=', WAREHOUSE_ID)]`

3. **`stock.warehouse`**: Almacenes visibles
   - Dominio: `[('id', '=', WAREHOUSE_ID)]`

4. **`stock.quant`**: Existencias
   - Dominio: `[('location_id.warehouse_id', '=', WAREHOUSE_ID)]`

### Grupos Dinámicos

Cada usuario con accesos personalizados obtiene un **grupo único**:

- XML ID: `amunet_warehouse_access.group_warehouse_access_user_{USER_ID}`
- Nombre: `Acceso Almacenes: {USER_NAME}`
- Las Record Rules se asignan a este grupo

**Ventaja**: Cada usuario tiene reglas independientes sin conflictos.

---

## API de Programación

### Verificar Acceso en Código

```python
# Verificar si usuario tiene acceso a almacén
user = self.env.user
warehouse = self.env['stock.warehouse'].browse(1)

has_access = self.env['amunet.warehouse.access']._check_warehouse_access(
    user=user,
    warehouse=warehouse,
    operation_type=None,  # Opcional: filtrar por operación
    raise_exception=False  # True: lanza AccessError si no tiene acceso
)

# Usando método del usuario
has_access = user.has_warehouse_access(warehouse, operation_type=None)

# Obtener almacenes permitidos de un usuario
warehouses = user.get_allowed_warehouses()

# Obtener operaciones permitidas
operations = user.get_allowed_operation_types(warehouse=warehouse)
```

### Verificar Acceso desde Almacén

```python
warehouse = self.env['stock.warehouse'].browse(1)
user = self.env.user

# Verificar acceso
has_access = warehouse.user_has_access(user, operation_type=None)

# Obtener usuarios con acceso
users = warehouse.get_users_with_access(operation_type=None)
```

---

## Permisos de Seguridad

### Grupos

| Grupo | Permisos |
|-------|----------|
| `base.group_system` (Admin) | Crear, editar, eliminar accesos |
| `stock.group_stock_user` (Usuario Inventario) | Ver accesos (solo lectura) |
| `stock.group_stock_manager` (Manager Inventario) | Ver accesos (solo lectura) |

### Reglas de Acceso (ir.model.access)

- Solo administradores pueden configurar accesos
- Usuarios de inventario pueden ver su configuración
- Managers pueden ver configuraciones de su equipo

---

## Troubleshooting

### Usuario no ve almacenes esperados

**Verificar**:
1. ¿Tiene acceso configurado activo? (campo `active = True`)
2. ¿Las Record Rules se generaron correctamente?
   - Ir a: `Configuración → Técnico → Seguridad → Reglas de Registro`
   - Buscar: `Acceso {Usuario} - {Almacén}`
3. ¿El usuario está asignado al grupo correcto?
   - Ir a: `Configuración → Usuarios → {Usuario} → Grupos`
   - Buscar: `Acceso Almacenes: {Usuario}`

**Solución**:
```bash
# Regenerar reglas
make shell
>>> access = env['amunet.warehouse.access'].search([('user_id.login', '=', 'user@example.com')])
>>> access._regenerate_record_rules()
```

### ValidationError al intentar validar picking

**Error**: "No tiene permiso para validar la operación..."

**Causas comunes**:
1. Usuario no tiene acceso al almacén configurado
2. Acceso restringido sin la operación específica seleccionada
3. Acceso desactivado temporalmente

**Solución**:
1. Verificar configuración de acceso del usuario
2. Si es acceso restringido, agregar la operación necesaria
3. Verificar que `active = True`

### Reglas no se aplican

**Verificar**:
1. ¿Se guardó la configuración? (Las reglas se generan en `create/write`)
2. ¿El usuario cerró sesión y volvió a entrar? (Cache de reglas)
3. ¿La regla está activa en Configuración Técnica?

**Limpiar cache**:
```bash
# Reiniciar servidor Odoo
make restart-dev
```

---

## Compatibilidad

- **Odoo 19**: ✅ Totalmente compatible (desarrollado para esta versión)
- **Odoo 18**: ⚠️ Compatible con ajustes menores
- **Odoo 17 o anterior**: ❌ No compatible (usa sintaxis moderna de Odoo 19)

---

## Roadmap

### Versión Actual: 19.0.1.0.0

✅ Control de acceso por almacén completo
✅ Control de acceso por operaciones específicas
✅ Generación automática de Record Rules
✅ Validaciones backend
✅ Interfaz gráfica completa

### Versiones Futuras

**Epic-034**: Restricción por ubicación específica (no solo almacén)
**Epic-035**: Restricción por producto dentro de almacén
**Epic-036**: Restricción por cantidad/horarios
**Epic-037**: Dashboard de auditoría de accesos

---

## Soporte

**Reportar Bugs**: Crear issue en repositorio del proyecto
**Contacto**: [email protected]
**Documentación Técnica**: Ver `docs/tickets/033_control-acceso-almacenes/`

---

## Licencia

Este módulo se distribuye bajo licencia LGPL-3.
Copyright (c) 2025 Amunet S.A. de C.V.

---

## Créditos

- **Desarrollado por**: Equipo de Desarrollo Amunet
- **Basado en**: Odoo 19 Community/Enterprise
- **Inspirado en**: Requerimientos de cumplimiento normativo GMP (NOM-241-SSA-V)
