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
                    # dos actos distintos (Mery, 09-sep-2026), de dos areas
                    # distintas y en momentos distintos. El analisis NO cierra
                    # la orden: solo deja el lote APROBADO. Produccion cierra
                    # cuando le toca.
                    #
                    # Antes se llamaba button_mark_done() aqui. Eso encadenaba
                    # el cierre de la MO a la firma del analisis y a la
                    # aceptacion de material por Almacen: si la orden traia
                    # cualquier candado (firmas de supervision/inspeccion
                    # pendientes en linea corta, alta manual de inventario),
                    # el UserError del cierre REVENTABA la operacion de quien
                    # si estaba trabajando. Caso real 17-sep-2026: Almacen no
                    # podia aceptar la devolucion de 3 pzs del lote
                    # 0926/01/HIT porque la orden tenia 9 inspecciones sin
                    # firmar -- un tema que no le toca resolver a Almacen.
                    #
                    # Las ordenes de SOLUCION conservan su cierre automatico
                    # (bloque de awaiting_reception arriba): ahi producir al
                    # aprobar es intencional (custodia de Calidad, Opcion B).
                    if mo.state not in ('done', 'cancel'):
                        cuerpo = _(
                            'Análisis <b>%(qc)s</b> finalizado: el lote queda '
                            '<b>APROBADO</b>.<br/>La orden permanece abierta; '
                            'Producción la cierra cuando corresponda.'
                        ) % {'qc': check.name}
                        if mo.amunet_alta_manual_qty:
                            cuerpo += _(
                                '<br/><b>Atención:</b> esta orden tiene %(qty)s '
                                'pieza(s) dadas de alta a mano en el inventario. '
                                'Cerrarla sin resolver eso duplicaría el producto. '
                                'Almacén y Calidad deben decidir cuál registro '
                                'vale: retirar el alta manual y cerrar normal, o '
                                'cerrar la orden en cero.'
                            ) % {'qty': mo.amunet_alta_manual_qty}
                        mo.sudo().message_post(body=cuerpo)
                        
        return res
