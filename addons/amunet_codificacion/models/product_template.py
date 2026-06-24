# -*- coding: utf-8 -*-
import re
import unicodedata
from odoo import models, fields, api, _
from odoo.exceptions import UserError

CLASIFICACIONES = [
    ('MP', 'MP - Materia Prima'),
    ('MI', 'MI - Material Impreso'),
    ('SP', 'SP - Producto Semiprocesado (granel)'),
    ('ST', 'ST - Producto Semiterminado'),
    ('PT', 'PT - Producto Terminado'),
]

# Palabras vacias (no significativas) para comparar nombres
_STOP = {
    'de', 'del', 'la', 'el', 'los', 'las', 'un', 'una', 'unos', 'unas',
    'para', 'con', 'sin', 'por', 'y', 'o', 'en', 'a', 'al', 'tipo', 'the',
}

# Palabras frecuentes en ingles (solo sugiere espanol, no bloquea)
_ENG = {
    'blood', 'water', 'box', 'dropper', 'test', 'strip', 'card', 'buffer',
    'solution', 'green', 'dye', 'ladder', 'gold', 'protease', 'inhibitor', 'dna',
    'rna', 'nucleic', 'acid', 'stain', 'sample', 'plus', 'kit', 'tube', 'cap',
    'with', 'for', 'and', 'control', 'reagent', 'powder', 'white', 'blue',
}


def _norm(txt):
    """minusculas, sin acentos, espacios colapsados."""
    txt = (txt or '').strip().lower()
    txt = ''.join(c for c in unicodedata.normalize('NFD', txt)
                  if unicodedata.category(c) != 'Mn')
    return re.sub(r'\s+', ' ', txt)


def _palabras_sig(txt):
    return [w for w in re.findall(r'\w+', _norm(txt), re.UNICODE)
            if w not in _STOP and len(w) > 2]


class ProductTemplate(models.Model):
    _inherit = 'product.template'

    amunet_clasificacion = fields.Selection(
        CLASIFICACIONES, string='Clasificación (clave)')
    amunet_abreviatura_id = fields.Many2one(
        'amunet.clave.abreviatura', string='Sub-categoría / Abreviatura',
        domain="[('clasificacion','=',amunet_clasificacion)]")
    amunet_analito = fields.Char(
        string='Analito / Enfermedad',
        help="Para Producto Terminado: enfermedad o analito que detecta.")
    amunet_clave_propuesta = fields.Char(
        string='Clave propuesta', compute='_compute_amunet_clave', store=False)
    amunet_clave_aviso = fields.Char(
        string='Aviso de nombre', compute='_compute_amunet_clave', store=False)
    amunet_clave_bloqueada = fields.Boolean(
        string='Alta bloqueada por duplicado', compute='_compute_amunet_clave',
        store=False)

    @api.depends('amunet_clasificacion', 'amunet_abreviatura_id', 'name')
    def _compute_amunet_clave(self):
        Reg = self.env['amunet.clave.registro']
        for r in self:
            prop = False
            ab = r.amunet_abreviatura_id
            if ab and r.amunet_clasificacion and ab.clasificacion == r.amunet_clasificacion:
                prop = Reg._amunet_siguiente_clave(ab.prefijo)
            r.amunet_clave_propuesta = prop

            avisos = []
            equiv = r._amunet_buscar_equivalente()
            if equiv:
                avisos.append(_(
                    "BLOQUEADO: ya existe un producto equivalente: '%s' (%s). "
                    "Usa ese producto. Si de verdad es distinto, ajusta el nombre "
                    "para diferenciarlo (por ejemplo, agrega la presentación)."
                ) % (equiv.name, equiv.default_code or 'sin clave'))
            if r._amunet_tiene_ingles():
                avisos.append(_(
                    "Sugerencia: el nombre parece tener palabras en inglés; usa "
                    "español y unifica con los nombres ya usados."))
            r.amunet_clave_bloqueada = bool(equiv)
            r.amunet_clave_aviso = "  ".join(avisos) or False

    @api.model
    def _amunet_equivalente_de(self, nombre, excluir_id=0):
        """Producto existente equivalente a `nombre` (mismo material) o False.

        Equivalente = duplicado exacto (normalizado) O todas las palabras
        significativas del nombre nuevo estan dentro de un producto existente
        (ej. 'Caja Drogas' es subconjunto de 'Caja caple Drogas'). El subconjunto
        solo cuenta con 2+ palabras, para no sobre-bloquear nombres genericos.
        """
        nm = (nombre or '').strip()
        if not nm:
            return False
        palabras = _palabras_sig(nm)
        if not palabras:
            return False
        norm = _norm(nm)
        domain = [('id', '!=', excluir_id or 0)] + [('name', 'ilike', w) for w in palabras]
        for c in self.with_context(active_test=False).search(domain, limit=30):
            cnorm = _norm(c.name or '')
            if cnorm == norm:
                return c
            cwords = set(re.findall(r'\w+', cnorm, re.UNICODE))
            if len(palabras) >= 2 and set(palabras).issubset(cwords):
                return c
        return False

    def _amunet_buscar_equivalente(self):
        self.ensure_one()
        return self.env['product.template']._amunet_equivalente_de(
            self.name, excluir_id=self._origin.id or 0)

    @api.model_create_multi
    def create(self, vals_list):
        # Candado duro: no permitir GUARDAR un producto del flujo de alta Amunet
        # (clasificacion puesta, sin clave aun) si el nombre es duplicado/equivalente.
        for vals in vals_list:
            if vals.get('amunet_clasificacion') and vals.get('name') and not vals.get('default_code'):
                equiv = self._amunet_equivalente_de(vals['name'])
                if equiv:
                    raise UserError(_(
                        "No se puede guardar: ya existe un producto equivalente "
                        "'%s' (%s).\n\nUsa ese producto. Si de verdad es distinto, "
                        "ajusta el nombre para diferenciarlo (por ejemplo, agrega "
                        "la presentación)."
                    ) % (equiv.name, equiv.default_code or 'sin clave'))
        return super().create(vals_list)

    def _amunet_tiene_ingles(self):
        self.ensure_one()
        return bool(set(re.findall(r'[a-zA-Z]+', (self.name or '').lower())) & _ENG)

    def action_amunet_asignar_clave(self):
        self.ensure_one()
        ab = self.amunet_abreviatura_id
        if not ab or not self.amunet_clasificacion or ab.clasificacion != self.amunet_clasificacion:
            raise UserError(_(
                "Selecciona una Clasificación y una Sub-categoría/Abreviatura coherentes antes de asignar la clave."))
        if self.default_code:
            raise UserError(_(
                "Este producto ya tiene clave (%s). El auto-codificador es solo para productos nuevos.") % self.default_code)
        equiv = self._amunet_buscar_equivalente()
        if equiv:
            raise UserError(_(
                "No se puede generar la clave: ya existe un producto equivalente "
                "'%s' (%s).\n\nUsa ese producto. Si de verdad es distinto, ajusta "
                "el nombre para diferenciarlo (por ejemplo, agrega la presentación)."
            ) % (equiv.name, equiv.default_code or 'sin clave'))
        clave = self.env['amunet.clave.registro']._amunet_siguiente_clave(ab.prefijo)
        self.default_code = clave
        self.env['amunet.clave.registro'].create({
            'clave': clave,
            'name': self.amunet_analito or self.name,
            'area': ab.name,
            'clasificacion': self.amunet_clasificacion,
            'product_tmpl_id': self.id,
            'fecha_alta': fields.Date.context_today(self),
            'origen': 'sistema',
        })
        self._amunet_notificar_almacen(clave)
        return {
            'type': 'ir.actions.client', 'tag': 'display_notification',
            'params': {
                'title': _('Clave asignada'),
                'message': _("Clave %s asignada y registrada en Documentación.") % clave,
                'type': 'success', 'sticky': False,
                'next': {'type': 'ir.actions.act_window_close'},
            }}

    def _amunet_notificar_almacen(self, clave):
        """Fase 3: aviso por correo al grupo Almacen al registrar un producto.

        Solo se envia si el parametro 'amunet_codificacion.email_almacen_activo'
        es '1' (se activa en produccion). Asi staging no manda correos reales al
        probar.
        """
        self.ensure_one()
        if self.env['ir.config_parameter'].sudo().get_param(
                'amunet_codificacion.email_almacen_activo') != '1':
            return
        template = self.env.ref(
            'amunet_codificacion.mail_template_nuevo_producto', raise_if_not_found=False)
        group = self.env.ref('stock.group_stock_user', raise_if_not_found=False)
        if not template or not group:
            return
        emails = group.user_ids.filtered(
            lambda u: u.active and u.email).mapped('email')
        if not emails:
            return
        template.send_mail(
            self.id, force_send=False,
            email_values={'email_to': ','.join(sorted(set(emails)))})
