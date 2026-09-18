# -*- coding: utf-8 -*-
from odoo import models, fields

class ProductTemplate(models.Model):
    _inherit = 'product.template'

    amunet_ph_requerido = fields.Boolean(
        string='Requiere ajuste de pH',
        default=False,
        help='La elaboracion de esta solucion incluye ajustar el pH a un '
             'objetivo. Si esta marcado, NO se puede terminar la orden sin '
             'capturar el pH final.\n\n'
             'Se marca por producto y no se deduce del pH objetivo: entre el pH '
             'obtenido y el objetivo SIEMPRE hay diferencia, asi que el valor no '
             'sirve como criterio. Ademas un pH objetivo en cero es ambiguo: no '
             'distingue "no aplica" de "nadie lo capturo".\n\n'
             'Las soluciones madre y reactivos concentrados (HCl, NaOH, azida, '
             'acido cloroaurico) NO llevan ajuste: son lo que son. Los buffers y '
             'soluciones de corrimiento, bloqueo y pretratamiento SI.\n\n'
             'Lista validada por Mery el 2026-09-14: 20 requieren, 9 no.')

    # Secuencia para el folio de la ORDEN DE PRODUCCION cuando se
    # fabrica este producto. Si esta vacio, la MO usa la secuencia
    # generica del picking_type (AMP/MO/NNNNN). Si esta lleno, el
    # folio sigue el patron Amunet (0526/01/VIH) y ese mismo nombre
    # se hereda al stock.lot del producto fabricado.
    mo_sequence_id = fields.Many2one(
        'ir.sequence',
        string='Secuencia de folio MO',
        help='Si esta definida, las ordenes de produccion de este '
             'producto usaran esta secuencia (formato Amunet '
             '"MMAA/NN/ABR") y el lote del producto fabricado '
             'heredara el mismo nombre. Si esta vacia, se usa la '
             'secuencia generica del tipo de operacion.',
    )

    # Resguardo en el Almacen de reactivos en uso (ARU)
    #
    # ARU no es un almacen rival del de materia prima: es donde se resguarda el
    # STOCK PARA USO. Un reactivo puede estar en los dos -- lo cerrado en el
    # almacen, lo disponible para trabajar en ARU -- y por eso su categoria
    # dirige a ARU y el area lo toma directo, sin pedirlo.
    #
    # La excepcion se marca aqui, por producto. Caso real: el acido cloroaurico
    # (MPREC35) NO se resguarda en ARU, solo en el almacen, asi que hay que
    # pedirlo aunque sea un reactivo. Regla de Mery, 18-sep-2026.
    amunet_resguardo_aru = fields.Selection(
        [('categoria', 'Según su categoría'),
         ('si', 'Sí se resguarda en ARU'),
         ('no', 'No se resguarda en ARU')],
        string='Resguardo en ARU', default='categoria', required=True,
        help='Si el producto se resguarda en el Almacen de reactivos en uso. '
             'Cuando se resguarda, el area lo toma directo y no se le pide a '
             'Almacen. "Segun su categoria" deja que mande la categoria, que es '
             'lo normal.')

    # Configuracion Actividades Produccion (Checklist de Fabricacion)
    amunet_req_history_log = fields.Boolean(string='Requiere Registro en Bitácora', default=True)
    amunet_req_calculations = fields.Boolean(string='Requiere Cálculos', default=True)
    amunet_weighing_range_text = fields.Char(string='Rango de Pesaje', default='± 0.0007', help='Ejemplo: ± 0.0007')
    amunet_req_dilution = fields.Boolean(string='Requiere Dilución de Reactivos', default=True)
    amunet_ph_adj_range_text = fields.Char(string='Tolerancia Ajuste pH', default='± 0.05', help='Ejemplo: ± 0.05')
    amunet_req_aforar = fields.Boolean(string='Requiere Aforar', default=True)
    amunet_req_quality_control = fields.Boolean(string='Requiere Análisis C.C', default=True, help='Si se desmarca, control de calidad no bloqueará la producción de este producto.')

    # Producto generico de SOLUCION DE DESARROLLO. Si esta activo, toda orden de
    # este producto es de desarrollo automaticamente: receta ajustable, sin
    # analisis de Calidad, entra a ARU/Desarrollo y requiere supervision del
    # jefe. Se usa UN solo producto generico (STDES01) para no dar de alta un
    # producto por cada prueba; la trazabilidad se lleva por lote + nombre.
    amunet_es_desarrollo = fields.Boolean(
        string='Producto de desarrollo', default=False)

    # Soluciones que NO salen del area: ajuste de pH y las que sirven de pie
    # para otra solucion. Se fabrican con su orden, su lote y su receta, pero
    # no se analizan ni se entregan a almacen -- se quedan en el inventario
    # interno del area (ARU/Stock). Clasificacion de Mery, 08-sep-2026.
    #
    # Que NO lleven analisis se controla aparte, apagando qc_required del
    # producto: los candados del sistema ya respetan esa bandera. Este campo
    # sirve para el DESTINO.
    amunet_solucion_interna = fields.Boolean(
        string='Solución de uso interno',
        default=False,
        help='La solución se queda en el área (ARU/Stock): no se entrega a '
             'Materia Prima. Se sigue fabricando con orden, lote y receta.')

    # Excepcion al enrutamiento a ARU. Por categoria, todos los reactivos se
    # consumen desde el almacen de reactivos en uso, porque el area los tiene
    # en su resguardo. Pero hay reactivos que NO se resguardan y se piden a
    # Materia Prima en cada orden -- el acido cloroaurico es el caso: es el
    # oro de las nanoparticulas (Mery, 08-sep-2026).
    #
    # Sin esta bandera el sistema los buscaria en ARU, no los encontraria, y la
    # orden se quedaria sin material aunque haya existencia en Materia Prima.
    amunet_surtir_desde_mp = fields.Boolean(
        string='Se surte desde Materia Prima',
        default=False,
        help='Este reactivo NO se resguarda en el área: se pide a Materia Prima '
             'en cada orden. Marca la excepción al consumo desde ARU.')

    # Parametros Adicionales extraidos del Excel
    amunet_solution_dependency_id = fields.Many2one('product.product', string='Solución Requerida Previamente', help='Si requiere que otra solución se prepare primero (para lanzar la advertencia).')
    amunet_initial_ph = fields.Float(string='pH Inicial', help='El pH por defecto esperado para la solución (ej. 7.4)')
    amunet_expiration_text = fields.Char(string='Caducidad (Texto)', help='Tiempo de vida útil. Ejemplo: 6 Meses, 2.6 años')
