# Changelog: amunet_warehouse_access

Todos los cambios notables de este módulo se documentarán en este archivo.

El formato está basado en [Keep a Changelog](https://keepachangelog.com/es-ES/1.0.0/).

---

## [19.0.1.0.0] - 2025-12-04

### Agregado (Epic-033)

#### Modelos
- Modelo `amunet.warehouse.access` - Configuración de acceso usuario-almacén-operación
- Modelo `amunet.warehouse.access.rule` - Metadatos de Record Rules generadas
- Extensión `res.users` con campos `warehouse_access_ids` y `warehouse_ids`
- Extensión `stock.warehouse` con campos `user_access_ids` y `allowed_user_ids`

#### Funcionalidades Principales
- **Configuración Gráfica**: Asignar almacenes y operaciones desde UI sin código
- **Acceso Completo**: Permitir todas las operaciones en un almacén
- **Acceso Restringido**: Limitar a operaciones específicas (Recepciones, Entregas, etc.)
- **Generación Automática de Record Rules**: Sistema crea `ir.rule` dinámicamente
- **Validación Backend**: Verificación de permisos en `create/write/unlink` de:
  - `stock.picking` - Operaciones de inventario
  - `stock.location` - Ubicaciones
  - `stock.quant` - Existencias
- **Bypass para Administradores**: Acceso completo automático sin configuración

#### Vistas
- Tab "Accesos a Almacenes" en formulario de usuario (`res.users`)
- Vista de lista "Matriz de Accesos" (`amunet.warehouse.access`)
- Formulario de configuración individual de acceso
- Tab "Usuarios con Acceso" en formulario de almacén (`stock.warehouse`)
- Vista de reglas generadas (`amunet.warehouse.access.rule`)

#### Validaciones
- Constraint SQL: Unicidad `(user_id, warehouse_id)`
- Constraint Python: Acceso restringido debe tener operaciones
- Constraint Python: Operaciones deben pertenecer al almacén configurado
- Validación backend en `action_confirm()` y `button_validate()` de pickings
- Validación backend en operaciones de ubicaciones y quants

#### Seguridad
- Archivo `ir.model.access.csv` con permisos por grupo
- Grupos dinámicos por usuario (formato: `group_warehouse_access_user_{USER_ID}`)
- Record Rules generadas automáticamente para 4 modelos:
  - `stock.picking`
  - `stock.location`
  - `stock.warehouse`
  - `stock.quant`

#### Utilidades
- Método helper `_check_warehouse_access()` reutilizable
- Método `has_warehouse_access()` en `res.users`
- Método `get_allowed_warehouses()` en `res.users`
- Método `get_allowed_operation_types()` en `res.users`
- Método `user_has_access()` en `stock.warehouse`
- Método `get_users_with_access()` en `stock.warehouse`

#### Tests
- Test suite `test_warehouse_access_config.py` (8 tests)
- Test suite `test_warehouse_access_rules.py` (6 tests)
- Test suite `test_warehouse_access_validation.py` (7 tests)
- Total: 21 tests automatizados

#### Documentación
- `README.md` - Documentación de usuario completa
- `TESTING.md` - Guía de pruebas manuales y automatizadas
- `CHANGELOG.md` - Este archivo
- Comentarios extensivos en código Python
- Script de demostración `demo/demo_warehouse_access.py`

### Cambiado
- N/A (primera versión del módulo)

### Deprecado
- N/A

### Eliminado
- N/A

### Corregido
- N/A

### Seguridad
- Implementación de validaciones backend además de Record Rules para doble capa de seguridad
- Bypass automático para administradores del sistema
- Validación de operaciones del sistema (sudo, cron) para evitar bloqueos

---

## Roadmap Futuro

### [19.0.2.0.0] - Planeado (Epic-034)
- Restricción por ubicación específica dentro de almacén
- Control granular por zona/pasillo/rack

### [19.0.3.0.0] - Planeado (Epic-035)
- Restricción por producto dentro de almacén
- Control de acceso a categorías de productos

### [19.0.4.0.0] - Planeado (Epic-036)
- Restricción por cantidad (límites de movimiento)
- Control de acceso por horarios/turnos

### [19.0.5.0.0] - Planeado (Epic-037)
- Dashboard de auditoría de accesos
- Reportes de actividad por usuario/almacén

---

## Notas de Desarrollo

### Decisiones Arquitectónicas

**¿Por qué módulo independiente?**
- Separación de responsabilidades
- Reutilización en otros contextos
- Mantenibilidad aislada
- Escalabilidad para futuras features

**¿Por qué generar Record Rules dinámicamente?**
- Performance: Odoo cachea reglas eficientemente
- Compatibilidad: Funciona con búsquedas nativas
- Transparencia: Reglas visibles en configuración técnica

**¿Por qué validaciones backend adicionales?**
- Seguridad: Doble capa de protección
- Flexibilidad: Lógica de negocio compleja
- Debugging: Mensajes de error claros

### Convenciones de Código

- **Logging**: Nivel INFO para operaciones exitosas, WARNING para intentos bloqueados
- **Naming**: Prefijo `amunet_` para todos los modelos nuevos
- **Documentación**: Docstrings en español/inglés para métodos públicos
- **Tests**: Tag `warehouse_access` para suite completa

### Compatibilidad

- **Odoo 19**: ✅ Totalmente compatible (desarrollado específicamente)
- **Odoo 18**: ⚠️ Compatible con ajustes menores en vistas XML
- **Odoo 17 o anterior**: ❌ No compatible (usa sintaxis moderna)

---

## Créditos

- **Desarrollado por**: Equipo de Desarrollo Amunet S.A. de C.V.
- **Epic Owner**: IT Manager
- **Aprobado por**: Gerente de Operaciones
- **Basado en**: Requerimientos de cumplimiento normativo GMP

---

## Licencia

LGPL-3
Copyright (c) 2025 Amunet S.A. de C.V.
