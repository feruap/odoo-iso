# -*- coding: utf-8 -*-
"""Tabla de reacciones de la Solucion de Nanoparticulas (SPNPS01).

Las nanoparticulas NO se preparan como una solucion de trabajo normal. Una
solucion se prepara una vez: se pesa, se afora, se homogeneiza y sale un lote.
Las nanoparticulas se hacen en REACCIONES: la instruccion INPSL-001 manda repetir
la sintesis "hasta tener aproximadamente 9 reacciones", medir CADA UNA en el
espectrofotometro, y hasta el final unirlas tomando 500 uL de cada una. Ese tubo
de union es el lote.

Ademas, la propia instruccion dice que "la cantidad del citrato de sodio y acido
cloroaurico CAMBIA durante cada reaccion, esto va a depender del tamano y
densidad optica de las nanoparticulas": el operador ajusta sobre la marcha. Por
eso los datos de cada reaccion no caben en la receta y necesitan su propia tabla.

Va DENTRO de la orden de fabricacion, no en el analisis de Calidad ni en una
bitacora aparte: son datos que toma Produccion durante la sintesis, de esa
produccion en concreto, y asi quedan amarrados al lote que salio de ahi.

Se llena durante la sintesis y se cierra con la orden, igual que las firmas
(Mery, 23-sep-2026).

ESTA TABLA NO EVALUA (Mery, 24-sep-2026). Es informacion e historial de como
salio el lote, nada mas: registra lo que se midio y no dice si un numero esta
bien o mal. Quien juzga la conformidad es el analisis de Calidad, con sus
especificaciones. Por eso aqui no hay rangos, ni avisos, ni semaforos: un
numero marcado en rojo en la orden se lee como un rechazo que produccion no
esta facultada para emitir, y ademas puede contradecir al analisis.
"""

from odoo import _, api, fields, models


class AmunetNpsReaccion(models.Model):
    _name = 'amunet.nps.reaccion'
    _description = 'Reacción de síntesis de nanopartículas'
    _order = 'production_id, secuencia, id'

    production_id = fields.Many2one(
        'mrp.production', string='Orden de fabricación',
        required=True, ondelete='cascade', index=True)
    secuencia = fields.Integer(string='Reacción', required=True, default=1)

    # Los dos reactivos van primero, en el orden en que se agregan a la
    # reaccion: el citrato y el oro. Es lo que el operador anota antes de
    # medir nada, asi que leer la tabla de izquierda a derecha sigue el
    # orden real del trabajo.
    citrato = fields.Float(string='Citrato (ml)', digits='Product Unit of Measure',
                           help='Citrato de sodio al 1% que se usó en esta reacción.')
    oro = fields.Float(string='Oro (ml)', digits='Product Unit of Measure',
                       help='Ácido cloroáurico al 1% que se usó en esta reacción.')

    # Antes se llamaba 'tamano' y decia 'Tamaño (nm)'. Lo que se mide en
    # cada reaccion es la DENSIDAD OPTICA, que no tiene unidad de longitud.
    # Se renombro el 24-sep-2026 por indicacion de Mery; no habia ningun
    # dato capturado ni calculo que lo usara.
    densidad_optica = fields.Float(string='D.O.', digits=(10, 2))
    lambda_max = fields.Float(
        string='λmax (nm)', digits=(10, 2),
        help='Longitud de onda del máximo, como salió de la lectura.')
    indice_agregacion = fields.Float(string='IA', digits=(10, 4),
                                     help='Índice de agregación.')
    indice_sintesis = fields.Float(string='IS', digits=(10, 4),
                                   help='Índice sobre la síntesis.')
    ama = fields.Float(string='AMA (nm)', digits=(10, 2),
                       help='Ancho a media altura del pico.')

    # La prueba de tolerancia se hace en DOS tubos, uno con SAB 20 mM 7.5 y otro
    # con 8.5, y lo que se observa es si se forma pellet. Van separadas para
    # poder filtrar y sacar estadistica despues; en una sola columna de texto
    # ese dato se pierde.
    tolera_75 = fields.Boolean(string='Tolera 7.5')
    tolera_85 = fields.Boolean(string='Tolera 8.5')

    observaciones = fields.Char(string='Observaciones')



class MrpProduction(models.Model):
    _inherit = 'mrp.production'

    amunet_nps_reaccion_ids = fields.One2many(
        'amunet.nps.reaccion', 'production_id',
        string='Reacciones de síntesis', copy=False)
    amunet_es_nps = fields.Boolean(
        string='Es solución de nanopartículas',
        compute='_compute_amunet_es_nps',
        help='Técnico: la pestaña de reacciones solo se muestra en estas órdenes.')
    amunet_nps_reacciones_llenas = fields.Integer(
        string='Reacciones con datos', compute='_compute_amunet_es_nps')

    @api.depends('product_id', 'amunet_nps_reaccion_ids.citrato',
                 'amunet_nps_reaccion_ids.oro',
                 'amunet_nps_reaccion_ids.lambda_max')
    def _compute_amunet_es_nps(self):
        for rec in self:
            rec.amunet_es_nps = (rec.product_id.default_code or '') == 'SPNPS01'
            # "con datos" = el operador escribio algo en esa reaccion. No se
            # exige llenar las 10: la instruccion habla de "aproximadamente 9".
            rec.amunet_nps_reacciones_llenas = len(
                rec.amunet_nps_reaccion_ids.filtered(
                    lambda r: r.citrato or r.oro or r.lambda_max or r.tamano
                    or r.indice_agregacion or r.indice_sintesis or r.ama
                    or r.observaciones))

    def _amunet_nps_prellenar(self):
        """Deja 10 renglones listos para capturar. No obliga a llenarlos."""
        Reaccion = self.env['amunet.nps.reaccion']
        for rec in self.filtered(lambda r: r.amunet_es_nps
                                 and not r.amunet_nps_reaccion_ids):
            Reaccion.create([{
                'production_id': rec.id, 'secuencia': i,
            } for i in range(1, 11)])

    @api.model_create_multi
    def create(self, vals_list):
        ordenes = super().create(vals_list)
        ordenes._amunet_nps_prellenar()
        return ordenes

    def write(self, vals):
        res = super().write(vals)
        if 'product_id' in vals:
            self._amunet_nps_prellenar()
        return res
