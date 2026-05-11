# Auditoría de uso de `.sudo()` — `amunet_warehouse_access`

> Fecha: 2026-05-11
> Alcance: 18 invocaciones a `.sudo()` en el módulo `amunet_warehouse_access`
> Motivación: revisar si el bypass de seguridad que provoca `.sudo()` está
> justificado y protegido por restricciones de ACL apropiadas.

## Resumen

| Categoría | Cantidad |
|---|---|
| ✅ Legítimas y bien protegidas por ACL | 17 |
| ⚠️ Cuestionables (no son vulnerabilidades pero degradan privacidad) | 1 |
| 🔴 Vulnerabilidades reales | 0 |

**Conclusión:** el módulo está aceptablemente seguro dado el modelo de ACL
actual, pero su seguridad depende ENTERAMENTE de que las ACLs no se
debiliten en el futuro. No hay defensa en profundidad — si alguien afloja
una ACL del CSV, los `sudo()` se vuelven escalada de privilegios real.

## ACL del módulo (resumen)

`amunet.warehouse.access` y `amunet.warehouse.access.rule`:

| Grupo | read | write | create | unlink |
|---|---|---|---|---|
| `base.group_system` | ✓ | ✓ | ✓ | ✓ |
| `stock.group_stock_user` | ✓ | — | — | — |
| `stock.group_stock_manager` | ✓ | — | — | — |

Es decir: **solo admin (`base.group_system`) puede crear/modificar/eliminar**
registros que disparan los métodos con `sudo()`. Los usuarios de inventario
solo pueden leer.

## Análisis individual

### Legítimos (necesarios, bien protegidos)

#### `stock_picking_type.py:21` — `_read_group` con sudo
- **Propósito:** Mostrar contadores agregados en el kanban dashboard de inventario.
- **Justificación:** Sin `sudo()`, usuarios sin acceso a algún warehouse verían contadores en cero o errores.
- **Riesgo:** Bajo. Expone metadata agregada de pickings, no datos individuales.
- **Recomendación cosmética:** Podría filtrarse explícitamente por warehouses accesibles al user para no exponer recuento de operaciones de almacenes ajenos. No urgente.

#### `amunet_warehouse_access.py:306` — `sudo().search()` de propia config
- **Propósito:** Buscar la configuración de acceso del propio usuario antes de validar.
- **Justificación:** El user no tiene permiso de leer el modelo, pero NECESITA leer su propia config para que el check funcione. El filtro `('user_id', '=', user.id)` garantiza que solo ve su propio registro.
- **Riesgo:** Bajo.

#### `amunet_warehouse_access.py:386, 393, 409, 416` — `IrRule.sudo().create()` + `IrModelData.sudo().create()`
- **Propósito:** Crear las dos `ir.rule` globales de visibilidad "ver solo propios registros" durante setup.
- **Contexto:** Método ejecutado al instalar/actualizar el módulo (post-init hook).
- **Justificación:** Configuración inicial estructural del módulo.
- **Riesgo:** Bajo. No callable directamente por usuarios.

#### `amunet_warehouse_access_rule.py:214` — `ir.rule.sudo().create()`
- **Propósito:** Cuando un admin configura un `amunet.warehouse.access.rule` desde la UI, este código crea la `ir.rule` interna correspondiente.
- **Protegido por:** ACL admin-only sobre `amunet.warehouse.access.rule` (solo `base.group_system` tiene create/write).
- **Riesgo:** Bajo SI ACL no cambia.

#### `amunet_warehouse_access_rule.py:230` — `rule_id.sudo().write()`
- Mismo análisis que :214 (mantenimiento de regla creada por admin).

#### `amunet_warehouse_access_rule.py:265, 269, 272` — `res.groups.sudo().create()`, `.user_ids = [(4,...)]`, `IrModelData.sudo().create()`
- **Propósito:** Crear un grupo `res.groups` único por cada `user_id` en una regla de acceso, para luego aplicar Record Rules específicas.
- **Protegido por:** ACL admin-only sobre `amunet.warehouse.access.rule`.
- **Riesgo:** Bajo SI ACL no cambia.

#### `amunet_warehouse_access_rule.py:375, 398, 412, 423, 436` — `sudo().unlink()` en cleanup
- **Propósito:** Hook de desinstalación del módulo (`_uninstall_hook`). Borra reglas dinámicas, grupos, registros propios y XML IDs huérfanos.
- **Justificación:** Solo se ejecuta cuando un admin desinstala el módulo.
- **Riesgo:** Bajo.

### ⚠️ Cuestionable (degrada privacidad de filtros)

#### `res_users.py:147, 151` — `ir.filters.sudo().write()`
```python
def _assign_employee_filters(self, users):
    """Asignar filtros favoritos de hr.employee a los usuarios dados."""
    filters = self.env['ir.filters'].sudo().search([
        ('model_id', '=', 'hr.employee'),
    ])
    for f in filters:
        f.sudo().write({'user_ids': [(4, u.id) for u in users]})
```

- **Propósito:** Cuando se crea un usuario nuevo, este método le agrega TODOS los filtros guardados (favoritos) que existen para `hr.employee`.
- **Problema:** Si un usuario A había marcado un filtro como "Privado" (sus `user_ids` solo lo incluyen a él), este código modifica ese filtro para agregar también a cada user nuevo. Filtros privados se vuelven compartidos sin consentimiento de quien los creó.
- **No es vulnerabilidad** (el filtro guardado no tiene datos sensibles), pero sí degrada UX y privacidad.
- **Riesgo:** Bajo-medio. No expone datos pero modifica configs de otros users.
- **Recomendación:** Filtrar solo los `ir.filters` con `user_id IS NULL` (filtros públicos) o solo los marcados como compartidos por el dueño:
  ```python
  filters = self.env['ir.filters'].sudo().search([
      ('model_id', '=', 'hr.employee'),
      ('user_id', '=', False),  # solo filtros públicos
  ])
  ```

## Recomendaciones generales

1. **No hay vulnerabilidades de seguridad reales hoy.** Los `sudo()` están protegidos por ACL admin-only sobre los modelos que los disparan.

2. **Mejorar defensa en profundidad:** agregar checks explícitos `if not self.env.user.has_group('base.group_system'): raise AccessError(...)` ANTES de hacer las operaciones con `sudo()`. Eso protege en caso de:
   - ACL accidentalmente afloja
   - Método expuesto por error vía RPC
   - Reutilización del método desde otro contexto

3. **Arreglar `_assign_employee_filters`** para respetar filtros privados (cambio chico, 1 línea de filtro extra).

4. **Documentar en el módulo** cuándo `sudo()` es necesario (comentarios `# sudo() because <razón>` en cada call).
