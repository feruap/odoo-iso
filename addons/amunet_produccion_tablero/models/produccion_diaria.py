from odoo import fields, models, tools


class AmunetProduccionDiaria(models.Model):
    _name = 'amunet.produccion.diaria'
    _description = 'Producción diaria: piezas planeadas vs reales'
    _auto = False
    _order = 'fecha desc, tipo'

    fecha = fields.Date('Fecha', readonly=True)
    tipo = fields.Selection([('plan', 'Planeado'), ('real', 'Real')], string='Tipo', readonly=True)
    piezas = fields.Float('Piezas', readonly=True, aggregator='sum', digits=(16, 0))
    production_id = fields.Many2one('mrp.production', 'Orden de producción', readonly=True)
    product_id = fields.Many2one('product.product', 'Producto', readonly=True)
    categ_id = fields.Many2one('product.category', 'Categoría', readonly=True)
    state = fields.Selection([
        ('draft', 'Borrador'), ('confirmed', 'Confirmada'), ('progress', 'En proceso'),
        ('to_close', 'Por cerrar'), ('done', 'Hecha'), ('cancel', 'Cancelada'),
    ], string='Estado de la orden', readonly=True)

    def init(self):
        tools.drop_view_if_exists(self.env.cr, self._table)
        # Solo producto terminado (categorías bajo "Producto terminado"); fechas en hora de Puebla.
        self.env.cr.execute("""
            CREATE OR REPLACE VIEW %s AS (
                WITH pt AS (
                    SELECT id FROM product_category
                     WHERE complete_name = 'Producto terminado'
                        OR complete_name LIKE 'Producto terminado /%%'
                )
                SELECT m.id * 2 AS id,
                       (m.amunet_plan_fecha_fin AT TIME ZONE 'UTC' AT TIME ZONE 'America/Mexico_City')::date AS fecha,
                       'plan'::varchar AS tipo,
                       m.product_qty AS piezas,
                       m.id AS production_id, m.product_id, t.categ_id, m.state
                  FROM mrp_production m
                  JOIN product_product p ON p.id = m.product_id
                  JOIN product_template t ON t.id = p.product_tmpl_id
                 WHERE m.state <> 'cancel'
                   AND m.amunet_plan_fecha_fin IS NOT NULL
                   AND t.categ_id IN (SELECT id FROM pt)
                UNION ALL
                SELECT sm.id * 2 + 1 AS id,
                       (sm.date AT TIME ZONE 'UTC' AT TIME ZONE 'America/Mexico_City')::date AS fecha,
                       'real'::varchar AS tipo,
                       sm.quantity AS piezas,
                       m.id AS production_id, sm.product_id, t.categ_id, m.state
                  FROM stock_move sm
                  JOIN mrp_production m ON m.id = sm.production_id
                  JOIN product_product p ON p.id = sm.product_id
                  JOIN product_template t ON t.id = p.product_tmpl_id
                 WHERE sm.state = 'done'
                   AND sm.product_id = m.product_id
                   AND t.categ_id IN (SELECT id FROM pt)
            )
        """ % self._table)
