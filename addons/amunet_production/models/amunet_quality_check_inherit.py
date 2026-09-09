# -*- coding: utf-8 -*-
from odoo import models, fields, api, _

class AmunetQualityCheck(models.Model):
    _inherit = 'amunet.quality.check'

    amunet_production_id = fields.Many2one('mrp.production', string='Orden de Producción Vinculada', readonly=True)
    # Piezas del lote que ampara ESTE analisis. Permite analizar un lote por
    # partes: varias solicitudes sobre la misma orden, cada una con su tramo.
    amunet_qty_analizada = fields.Float(
        string='Piezas que ampara', readonly=True,
        help='Cuantas piezas del lote cubre este analisis. La suma de todos '
             'los analisis de la orden no puede pasar de las piezas fabricadas.')
    amunet_analisis_parcial = fields.Boolean(
        string='Análisis parcial', readonly=True,
        help='Marcado cuando el analisis cubre solo una parte del lote.')

    def write(self, vals):
        res = super(AmunetQualityCheck, self).write(vals)
        if 'state' in vals:
            for check in self:
                if not check.amunet_production_id:
                    continue
                
                new_state = check.state
                mo = check.amunet_production_id

                # "en el qc cuando este en el estado de "Pendiente recepcion almacen" igual se marcara como confirmado en produccion"
                if new_state == 'awaiting_reception':
                    mo.quality_analysis_status = 'approved'
                    # Custodia de Calidad (Opcion B): al APROBAR se produce el
                    # terminado de la SOLUCION en Control de calidad (destino ya
                    # ruteado ahi) ANTES de que la disposicion del QC genere la
                    # recepcion Control de calidad -> existencias (que Almacen
                    # valida) y merme el muestreo. Asi el stock ya existe cuando
                    # la recepcion lo necesita. No-soluciones conservan el flujo
                    # original (producen al finalizar el QC).
                    if mo.amunet_is_solution_product and mo.state not in ('done', 'cancel'):
                        # Registrar la cantidad producida y producir saltando los
                        # asistentes de MRP (consumo vs BoM y backorder): el consumo
                        # real ya se capturo en el flujo y la solucion se produce
                        # completa. Asi el terminado queda posteado en Control de
                        # calidad antes de que corra la disposicion del QC.
                        if not mo.qty_producing:
                            mo.qty_producing = mo.product_qty
                        mo.with_context(
                            skip_consumption=True,
                            skip_backorder=True,
                        ).button_mark_done()

                # "y cuando sea "finalizado" este en produccion sera "Hecho""
                elif new_state == 'done':
                    if mo.quality_analysis_status != 'approved':
                        mo.quality_analysis_status = 'approved'

                    # LIBERAR el lote como aprobado NO es CERRAR la orden: son
                    # dos actos distintos (Mery, 09-sep-2026). Si la orden trae
                    # un candado que le impide cerrarse -- hoy, el lote dado de
                    # alta a mano en inventario --, el analisis se finaliza
                    # igual y la orden se queda abierta hasta que Almacen y
                    # Calidad decidan que registro vale.
                    #
                    # Antes, ese candado reventaba la FIRMA del analisis: la
                    # Responsable Sanitario no podia liberar producto que ya
                    # estaba aprobado, por un tema de inventario que no le toca
                    # resolver a ella.
                    if mo.state not in ('done', 'cancel'):
                        if mo.amunet_alta_manual_qty:
                            mo.sudo().message_post(body=_(
                                'Análisis <b>%(qc)s</b> finalizado: el lote queda '
                                '<b>APROBADO</b>.<br/>La orden <b>no se cerró</b> '
                                'porque tiene %(qty)s pieza(s) dadas de alta a mano '
                                'en el inventario. Cerrarla ahora duplicaría el '
                                'producto. Almacén y Calidad deben decidir cuál '
                                'registro vale: retirar el alta manual y cerrar '
                                'normal, o cerrar la orden en cero.'
                            ) % {'qc': check.name, 'qty': mo.amunet_alta_manual_qty})
                        else:
                            mo.button_mark_done()
                        
        return res
