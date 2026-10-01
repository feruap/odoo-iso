# -*- coding: utf-8 -*-

from odoo import models, api, _
from odoo.exceptions import AccessError, UserError
import logging

_logger = logging.getLogger(__name__)


class StockPicking(models.Model):
    """
    Extensión de stock.picking para validar accesos a almacenes.

    Agrega validaciones en:
    - action_confirm: Verificar acceso antes de confirmar
    - button_validate: Verificar acceso antes de validar

    Epic-033: Control de Acceso Dinámico por Almacén
    """
    _inherit = 'stock.picking'

    # ========== OVERRIDE METHODS ==========

    def action_confirm(self):
        """Override para validar acceso antes de confirmar picking."""
        # Validar acceso ANTES de confirmar
        for picking in self:
            picking._check_warehouse_access_permission(operation='confirmar')

        return super().action_confirm()

    def button_validate(self):
        """Override para validar acceso antes de validar picking."""
        # Validar acceso ANTES de validar
        for picking in self:
            picking._check_warehouse_access_permission(operation='validar')
            picking._amunet_check_origen_destino_iguales()

        return super().button_validate()

    def _amunet_check_origen_destino_iguales(self):
        """Bloquea validar cuando la LINEA DE OPERACION no mueve el material a
        donde dice el movimiento.

        EL BUG QUE ATRAPA. En Odoo el destino vive en DOS lugares: el del
        movimiento (lo que se ve en la pantalla del traslado) y el de la linea de
        operacion (lo que de verdad ejecuta el inventario, en la pestana de
        operaciones detalladas). Cuando el tipo de operacion trae un destino por
        defecto -- el de Burgos trae AMPB/Existencias, el MISMO que su origen- y el
        operador cambia el encabezado, la linea se queda con el valor viejo. Arriba
        se ve bien y abajo esta mal, y el material no llega a donde dice el papel.

        Paso cinco veces en agosto de 2026 con traslados Burgos -> Fabrica: quedaron
        'hechos' sin mover nada y el sistema decia que el material estaba en Fabrica
        mientras seguia en Burgos.

        DOS COMPROBACIONES, no una:

        1. origen == destino en la linea: el material no se moveria.
        2. el destino de la linea no esta dentro del destino de su movimiento: el
           material se moveria a OTRO lugar del que dice el traslado. Este caso el
           candado viejo no lo veia, y por eso se le escapo AMP/IN/00234, una
           recepcion con 487 piezas que el movimiento mandaba a Existencias y la
           linea dejo en cuarentena de Calidad.

        Corre en CUALQUIER tipo de operacion. El candado viejo solo miraba los
        traslados internos, asi que las recepciones y las salidas quedaban sin red.

        Se acepta que la linea apunte a una ubicacion HIJA del destino del
        movimiento: eso es legitimo en Odoo (reglas de ubicacion). Hoy Amunet no
        tiene ninguna regla de ubicacion configurada y no existe un solo movimiento
        historico que use esa flexibilidad, pero se respeta para no romper el dia
        que se usen.
        """
        self.ensure_one()

        sin_mover, otro_lugar = [], []
        for ml in self.move_line_ids:
            if not ml.quantity:
                continue
            destino_mov = ml.move_id.location_dest_id
            if ml.location_id == ml.location_dest_id:
                sin_mover.append(ml)
            elif destino_mov and ml.location_dest_id != destino_mov and not (
                    ml.location_dest_id.parent_path or '').startswith(
                    destino_mov.parent_path or '\0'):
                otro_lugar.append(ml)

        if not sin_mover and not otro_lugar:
            return

        def linea(ml, con_movimiento=False):
            txt = '- %s: %s -> %s' % (
                ml.product_id.default_code or ml.product_id.display_name,
                ml.location_id.complete_name, ml.location_dest_id.complete_name)
            if con_movimiento:
                txt += '   (el traslado dice: %s)' % (
                    ml.move_id.location_dest_id.complete_name or '?')
            return txt

        partes = []
        if sin_mover:
            partes.append(_(
                'Hay lineas cuyo DESTINO es el MISMO que el origen, asi que el '
                'material no se moveria:\n%s'
            ) % '\n'.join(linea(ml) for ml in sin_mover[:8]))
        if otro_lugar:
            partes.append(_(
                'Hay lineas que mandan el material a un lugar DISTINTO del que dice '
                'el traslado:\n%s'
            ) % '\n'.join(linea(ml, True) for ml in otro_lugar[:8]))

        raise UserError(_(
            'No se puede validar: lo que dice el traslado y lo que haran las lineas '
            'de operacion no coincide.\n\n%s\n\n'
            'Revisa la pestana de operaciones detalladas y corrige el destino de '
            'esas lineas (es el destino de abajo el que mueve el inventario, no el '
            'de arriba). Si cambias el destino del encabezado, las lineas se '
            'actualizan solas.'
        ) % '\n\n'.join(partes))

    def _amunet_propagar_destino_a_lineas(self):
        """Hace que las lineas sigan al encabezado: la causa del bug, no el sintoma.

        Cuando se cambia el origen o el destino del traslado, las lineas de
        operacion ya creadas conservaban el valor viejo y nadie lo veia. Esto las
        actualiza, para que lo que se ve en pantalla sea lo que se va a ejecutar.

        Solo toca lineas NO hechas (ni validadas ni canceladas): lo ya hecho es
        historial y no se reescribe.
        """
        for picking in self:
            for mv in picking.move_ids:
                if mv.state in ('done', 'cancel'):
                    continue
                cambios = {}
                if mv.location_id != picking.location_id:
                    cambios['location_id'] = picking.location_id.id
                if mv.location_dest_id != picking.location_dest_id:
                    cambios['location_dest_id'] = picking.location_dest_id.id
                if cambios:
                    mv.write(cambios)
                lineas = mv.move_line_ids.filtered(
                    lambda ml: ml.state not in ('done', 'cancel'))
                vals = {}
                if any(ml.location_id != mv.location_id for ml in lineas):
                    vals['location_id'] = mv.location_id.id
                if any(ml.location_dest_id != mv.location_dest_id for ml in lineas):
                    vals['location_dest_id'] = mv.location_dest_id.id
                if vals and lineas:
                    lineas.write(vals)

    @api.model_create_multi
    def create(self, vals_list):
        """Override para validar acceso al crear picking.

        Migrado a @api.model_create_multi (Odoo 18+) el 2026-05-09 para que
        la validacion de acceso por almacen se aplique tambien en creaciones
        en batch (importaciones masivas, jobs, modulos que crean varios
        pickings de golpe). Antes con @api.model la firma singular podia
        ser bypasseada en esos casos.
        """
        # Crear primero para tener acceso a campos relacionados
        pickings = super().create(vals_list)

        # Validar acceso para cada picking creado
        for picking in pickings:
            picking._check_warehouse_access_permission(operation='crear')

        return pickings

    def write(self, vals):
        """Override para validar acceso al modificar picking."""
        # Validar acceso antes de modificar
        critical_fields = {
            'picking_type_id', 'location_id', 'location_dest_id',
            'move_ids_without_package', 'move_line_ids_without_package'
        }

        if any(field in vals for field in critical_fields):
            for picking in self:
                picking._check_warehouse_access_permission(
                    operation='modificar'
                )

        res = super().write(vals)

        # Si se cambio el origen o el destino, las lineas de operacion tienen que
        # seguir al encabezado. Sin esto, el operador cambia el destino arriba, abajo
        # queda el viejo, y el material se mueve a donde nadie dijo. Es la causa de
        # los cinco traslados en falso de Burgos de agosto-2026.
        if 'location_id' in vals or 'location_dest_id' in vals:
            self.filtered(
                lambda p: p.state not in ('done', 'cancel')
            )._amunet_propagar_destino_a_lineas()

        return res

    def unlink(self):
        """Override para validar acceso al eliminar picking."""
        # Validar acceso antes de eliminar
        for picking in self:
            picking._check_warehouse_access_permission(
                operation='eliminar'
            )

        return super().unlink()

    # ========== VALIDATION METHODS ==========

    def _check_warehouse_access_permission(self, operation='acceder', raise_warning=True):
        """
        Validar que el usuario tenga permiso para operar en el almacén del picking.

        :param operation: str - Operación que se intenta realizar (confirmar, validar, etc.)
        :param raise_warning: bool - Si True, lanza AccessError en caso de no tener permiso
        :raises: AccessError si el usuario no tiene permiso
        """
        self.ensure_one()

        # Bypass para administradores
        if self.env.user.has_group('base.group_system'):
            return True

        # Bypass para operaciones del sistema (sudo, cron, etc.)
        if self.env.su:
            return True

        # Obtener almacén del picking
        warehouse = self.picking_type_id.warehouse_id

        if not warehouse:
            _logger.warning(
                f"Picking {self.name} (ID: {self.id}) no tiene almacén asociado. "
                f"No se puede validar acceso."
            )
            return True

        # Validar acceso usando método del modelo de acceso
        try:
            self.env['amunet.warehouse.access']._check_warehouse_access(
                user=self.env.user,
                warehouse=warehouse,
                operation_type=self.picking_type_id,
                raise_exception=True
            )
            return True

        except AccessError as e:
            if raise_warning:
                # Re-lanzar excepción con contexto adicional
                raise AccessError(
                    f"No tiene permiso para {operation} la operación '{self.name}'.\n\n"
                    f"Detalles:\n"
                    f"- Operación: {self.picking_type_id.name}\n"
                    f"- Almacén: {warehouse.name}\n\n"
                    f"{str(e)}"
                )
            else:
                _logger.warning(
                    f"Usuario '{self.env.user.name}' intentó {operation} picking "
                    f"'{self.name}' sin permisos suficientes: {str(e)}"
                )
                return False
