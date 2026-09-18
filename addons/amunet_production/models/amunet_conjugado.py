# -*- coding: utf-8 -*-
"""Actividades de fabricacion de CONJUGADOS (INSPR-003).

El checklist generico de soluciones (bitacora, calculos, dilucion, aforar) no
describe lo que de verdad se hace al preparar un conjugado: centrifugar el oro,
resuspender el boton, incubar en horno, bloquear, alicuotar y leer densidad
optica. Aforar ni siquiera aplica.

Aqui viven los parametros de receta (en el producto) y la captura de lo que
realmente ocurrio (en la orden). Solo aplica a productos marcados como
conjugado: el resto de las soluciones no se ve afectado.
"""

from odoo import api, fields, models, _


class ProductTemplate(models.Model):
    _inherit = 'product.template'

    amunet_es_conjugado = fields.Boolean(
        string='Es conjugado', default=False, index=True,
        help='Activa las actividades de fabricacion de conjugado (INSPR-003) '
             'en las ordenes de este producto.')

    # --- Parametros de receta (INSPR-003 / matriz de conjugados) ---
    amunet_conj_ph_sab = fields.Selection(
        [('7.5', '7.5'), ('8.5', '8.5')],
        string='pH de la solucion para conjugar',
        help='pH del borato 20 mM en el que se resuspende el boton de oro.')
    amunet_conj_agente_bloqueo = fields.Selection(
        [('cas', 'Caseina'), ('bsa', 'BSA'), ('cb', 'Caseina y BSA')],
        string='Agente de bloqueo')
    amunet_conj_horas_conjugacion = fields.Float(
        string='Conjugacion (horas)',
        help='Tiempo en horno a 37 C antes de agregar el bloqueo.')
    amunet_conj_min_bloqueo = fields.Float(
        string='Bloqueo (minutos)', default=30.0,
        help='Tiempo en horno a 37 C despues de agregar el bloqueo.')
    amunet_conj_do_objetivo = fields.Float(
        string='D.O. objetivo', digits=(5, 2),
        help='Densidad optica a la que se diluye el conjugado final.')
    amunet_conj_vol_resuspension = fields.Float(
        string='Volumen de resuspension (uL)', default=30.0,
        help='Volumen de diluyente en que se resuspende el boton final.')
    amunet_conj_proceso = fields.Selection(
        [('estandar', 'Estandar'), ('largo', 'Largo (con botones)')],
        string='Tipo de proceso', default='estandar',
        help='El proceso LARGO agrega la etapa de botones y la incubacion a '
             'temperatura ambiente (PSA, TSH, NS1).')
    # Centrifugado: iguales para todos hoy, pero configurables por si cambian.
    amunet_conj_centrif_rpm = fields.Integer(string='Centrifugado (rpm)', default=12300)
    amunet_conj_centrif_temp = fields.Float(string='Centrifugado (C)', default=4.0)
    amunet_conj_centrif_min = fields.Float(string='Centrifugado (min)', default=15.0)


class MrpProduction(models.Model):
    _inherit = 'mrp.production'

    amunet_es_conjugado = fields.Boolean(
        related='product_id.product_tmpl_id.amunet_es_conjugado', readonly=True)

    # Parametros de la receta, a la vista del operador mientras trabaja.
    amunet_conj_ph_sab = fields.Selection(
        related='product_id.product_tmpl_id.amunet_conj_ph_sab', readonly=True)
    amunet_conj_horas_conjugacion = fields.Float(
        related='product_id.product_tmpl_id.amunet_conj_horas_conjugacion', readonly=True)
    amunet_conj_min_bloqueo = fields.Float(
        related='product_id.product_tmpl_id.amunet_conj_min_bloqueo', readonly=True)
    amunet_conj_do_objetivo = fields.Float(
        related='product_id.product_tmpl_id.amunet_conj_do_objetivo', readonly=True)
    amunet_conj_proceso = fields.Selection(
        related='product_id.product_tmpl_id.amunet_conj_proceso', readonly=True)

    # 1. Despeje de linea (PNOPR-001)
    amunet_conj_despeje = fields.Boolean(string='Despeje de linea realizado')
    # 2. Bitacora de conjugados FPR-030
    amunet_conj_folio_bitacora = fields.Char(string='Folio bitacora FPR-030')
    # 3. Alicuotado de nanoparticulas
    amunet_conj_vol_nps = fields.Float(string='Nanoparticulas alicuotadas (mL)')
    # 4. Centrifugado 1
    amunet_conj_c1_hora = fields.Datetime(string='Centrifugado 1 - hora')
    amunet_conj_c1_rpm = fields.Integer(string='Centrifugado 1 - rpm')
    amunet_conj_c1_temp = fields.Float(string='Centrifugado 1 - C')
    amunet_conj_c1_min = fields.Float(string='Centrifugado 1 - min')
    # 5. Resuspension del boton en solucion para conjugar
    amunet_conj_vol_sab = fields.Float(string='Solucion para conjugar agregada (mL)')
    # 6. Calculo del anticuerpo (C1V1=C2V2)
    amunet_conj_conc_ac_inicial = fields.Float(
        string='Concentracion del anticuerpo (ug/uL)', digits=(8, 3))
    amunet_conj_conc_ac_objetivo = fields.Float(
        string='Concentracion requerida (ug/mL)', digits=(8, 3))
    amunet_conj_vol_ac = fields.Float(
        string='Volumen de anticuerpo agregado (uL)', digits=(8, 2))
    # 7. Horno - conjugacion
    amunet_conj_horno1_inicio = fields.Datetime(string='Conjugacion - inicio')
    amunet_conj_horno1_fin = fields.Datetime(string='Conjugacion - fin')
    # 7b. Solo proceso LARGO
    amunet_conj_botones_hora = fields.Datetime(string='Botones - hora')
    amunet_conj_ta_inicio = fields.Datetime(string='Temp. ambiente - inicio')
    amunet_conj_ta_fin = fields.Datetime(string='Temp. ambiente - fin')
    # 8. Bloqueo
    amunet_conj_vol_bloqueo = fields.Float(string='Solucion de bloqueo agregada (mL)')
    amunet_conj_horno2_inicio = fields.Datetime(string='Bloqueo - inicio')
    amunet_conj_horno2_fin = fields.Datetime(string='Bloqueo - fin')
    # 9. Centrifugado 2
    amunet_conj_c2_hora = fields.Datetime(string='Centrifugado 2 - hora')
    amunet_conj_c2_rpm = fields.Integer(string='Centrifugado 2 - rpm')
    amunet_conj_c2_temp = fields.Float(string='Centrifugado 2 - C')
    amunet_conj_c2_min = fields.Float(string='Centrifugado 2 - min')
    # 10. Lectura D.O. inicial (triplicado, x factor de dilucion)
    amunet_conj_do_i_l1 = fields.Float(string='D.O. inicial - lectura 1', digits=(6, 3))
    amunet_conj_do_i_l2 = fields.Float(string='D.O. inicial - lectura 2', digits=(6, 3))
    amunet_conj_do_i_l3 = fields.Float(string='D.O. inicial - lectura 3', digits=(6, 3))
    amunet_conj_do_i_factor = fields.Integer(string='D.O. inicial - factor', default=200)
    amunet_conj_do_inicial = fields.Float(
        string='D.O. inicial', compute='_compute_amunet_conj_do', store=True, digits=(6, 2))
    # 11. Dilucion a D.O. objetivo y lectura final
    amunet_conj_vol_concentrado = fields.Float(string='Conjugado concentrado usado (uL)')
    amunet_conj_vol_diluyente = fields.Float(string='Diluyente agregado (uL)')
    amunet_conj_do_f_l1 = fields.Float(string='D.O. final - lectura 1', digits=(6, 3))
    amunet_conj_do_f_l2 = fields.Float(string='D.O. final - lectura 2', digits=(6, 3))
    amunet_conj_do_f_l3 = fields.Float(string='D.O. final - lectura 3', digits=(6, 3))
    amunet_conj_do_f_factor = fields.Integer(string='D.O. final - factor', default=200)
    amunet_conj_do_final = fields.Float(
        string='D.O. final', compute='_compute_amunet_conj_do', store=True, digits=(6, 2))

    @api.depends('amunet_conj_do_i_l1', 'amunet_conj_do_i_l2', 'amunet_conj_do_i_l3',
                 'amunet_conj_do_i_factor', 'amunet_conj_do_f_l1', 'amunet_conj_do_f_l2',
                 'amunet_conj_do_f_l3', 'amunet_conj_do_f_factor')
    def _compute_amunet_conj_do(self):
        """D.O. = promedio de las tres lecturas por el factor de dilucion."""
        for mo in self:
            ini = [v for v in (mo.amunet_conj_do_i_l1, mo.amunet_conj_do_i_l2,
                               mo.amunet_conj_do_i_l3) if v]
            fin = [v for v in (mo.amunet_conj_do_f_l1, mo.amunet_conj_do_f_l2,
                               mo.amunet_conj_do_f_l3) if v]
            mo.amunet_conj_do_inicial = (
                sum(ini) / len(ini) * (mo.amunet_conj_do_i_factor or 0)) if ini else 0.0
            mo.amunet_conj_do_final = (
                sum(fin) / len(fin) * (mo.amunet_conj_do_f_factor or 0)) if fin else 0.0

    # ------------------------------------------------------------------
    # Prellenado: al elegir el producto, la orden trae los parametros de
    # centrifugado de la receta para que el operador solo confirme.
    # ------------------------------------------------------------------
    @api.onchange('product_id')
    def _onchange_product_conjugado(self):
        tmpl = self.product_id.product_tmpl_id
        if tmpl.amunet_es_conjugado:
            self.amunet_conj_c1_rpm = tmpl.amunet_conj_centrif_rpm
            self.amunet_conj_c1_temp = tmpl.amunet_conj_centrif_temp
            self.amunet_conj_c1_min = tmpl.amunet_conj_centrif_min
            self.amunet_conj_c2_rpm = tmpl.amunet_conj_centrif_rpm
            self.amunet_conj_c2_temp = tmpl.amunet_conj_centrif_temp
            self.amunet_conj_c2_min = tmpl.amunet_conj_centrif_min
