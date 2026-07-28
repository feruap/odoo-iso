# -*- coding: utf-8 -*-
# Genera las etiquetas de caja en PPTX (tabloide 11x17) directamente desde
# la orden de fabricacion, usando python-pptx (instalado en la imagen) y las
# plantillas PLANTILLA_S/H/P/M.pptx que viven en static/templates/ del modulo.
# Los datos (producto, REF, lote, caducidad, contenedor, accesorio, registro
# sanitario, presentaciones autorizadas) se leen del producto y de la MO en
# Odoo; NO depende de ningun Excel externo.
import io
import os
import re
import base64

from odoo import models, fields, api, _
from odoo.exceptions import UserError

# Namespace DrawingML: los textos de las formas viven en elementos <a:t>.
_A_NS = "http://schemas.openxmlformats.org/drawingml/2006/main"


class MrpProduction(models.Model):
    _inherit = 'mrp.production'

    def _etiqueta_datos(self):
        """Datos fijos de la etiqueta (sin la cantidad por caja).
        Devuelve (subtipo, lot_name, placeholders)."""
        self.ensure_one()
        prod = self.product_id
        tmpl = prod.product_tmpl_id
        subtipo = tmpl.etiqueta_subtipo
        if not subtipo:
            raise UserError(_(
                'El producto "%s" no tiene "Subtipo de etiqueta" configurado. '
                'Capturalo en la ficha del producto (pestana Etiqueta) antes de '
                'generar la etiqueta de caja.') % prod.display_name)

        # Lote producido: en Odoo 19 la MO no tiene lot_producing_id; el lote
        # sale de las lineas de movimiento del producto terminado.
        lote = self.move_finished_ids.move_line_ids.filtered(
            lambda ml: ml.lot_id and ml.product_id == prod
        ).mapped('lot_id')[:1]
        lot_name = lote.name if lote else self.name
        exp = lote.expiration_date if lote else False
        caducidad = str(exp)[:7] if exp else '????-??'

        # Contenedor y accesorio van justo despues de "{{N}} " en la etiqueta
        # (ej. "-20 tubos..."). La primera letra debe ir en MAYUSCULA aunque en
        # la ficha del producto se haya capturado en minuscula.
        def _cap(s):
            s = s or ''
            return s[0].upper() + s[1:] if s else s

        datos = {
            '{{PRODUCTO}}': tmpl.nombre_etiqueta or prod.name,
            '{{REF}}': prod.default_code or '',
            '{{LOT}}': lot_name,
            '{{CADUCIDAD}}': caducidad,
            '{{CONTENEDOR}}': _cap(tmpl.etiqueta_contenedor),
            '{{ACCESORIO}}': _cap(tmpl.etiqueta_accesorio),
            '{{REG_SANITARIO}}': tmpl.registro_sanitario or '',
        }
        return subtipo, lot_name, datos

    def _etiqueta_plan_lineas(self):
        """Cuantas etiquetas y de que tamano generar, a partir del PLAN DE
        EMPAQUE aprobado de la orden: por cada linea, se generan
        approved_box_qty etiquetas (una por caja) con su pzas/caja.
        Devuelve (lista de tuplas (pzas_caja, num_cajas), origen_plan_bool)."""
        self.ensure_one()
        lineas = []
        Plan = self.env['amunet.packaging.plan'] if 'amunet.packaging.plan' in self.env else None
        plan = False
        if Plan is not None:
            plan = Plan.search(
                [('production_id', '=', self.id), ('state', 'in', ('approved', 'done'))],
                order='id desc', limit=1)
            if not plan:
                plan = Plan.search([('production_id', '=', self.id)], order='id desc', limit=1)
        if plan:
            for ln in plan.line_ids.filtered(lambda l: l.approved_box_qty > 0):
                lineas.append((ln.package_qty, ln.approved_box_qty))
            if lineas:
                return lineas, True
        # Fallback: sin plan de empaque -> 1 etiqueta por presentacion autorizada.
        if 'amunet.packaging.presentation' in self.env:
            pres = self.env['amunet.packaging.presentation'].search([
                ('product_tmpl_id', '=', self.product_id.product_tmpl_id.id),
                ('is_authorized', '=', True),
            ])
            for p in pres:
                lineas.append((p.package_qty, 1))
        if not lineas:
            lineas = [(0, 1)]
        return lineas, False

    def _etiqueta_clonar_slide(self, prs, src):
        """Duplica la diapositiva `src` dentro del MISMO pptx (mismo paquete,
        asi las imagenes/diseno se conservan) y devuelve la nueva."""
        import copy
        from pptx.oxml.ns import qn
        dst = prs.slides.add_slide(src.slide_layout)
        # Quitar los placeholders que el layout agrega por defecto.
        for shp in list(dst.shapes):
            shp._element.getparent().remove(shp._element)
        # Copiar cada forma de la diapositiva origen.
        for shp in src.shapes:
            dst.shapes._spTree.append(copy.deepcopy(shp._element))
        # Reapuntar relaciones de imagenes/medios (r:embed / r:link) a las
        # mismas partes ya presentes en el paquete.
        for attr in (qn('r:embed'), qn('r:link')):
            for el in dst.shapes._spTree.iter():
                rid = el.get(attr)
                if rid and rid in src.part.rels:
                    rel = src.part.rels[rid]
                    nuevo = dst.part.relate_to(rel.target_part, rel.reltype)
                    el.set(attr, nuevo)
        return dst

    # Rejilla de la hoja tabloide (11x17"): 3 columnas x 6 filas = 18 etiquetas.
    _GRID_COLS_IN = (0.19, 3.73, 7.27)
    _GRID_ROW0_IN = 0.25
    _GRID_ROW_PITCH_IN = 2.74
    _GRID_ROWS = 6

    def _etiqueta_llenar_element(self, el, placeholders):
        """Reemplaza los {{...}} en todos los textos dentro de un elemento XML."""
        for t in el.iter('{%s}t' % _A_NS):
            if not t.text:
                continue
            nuevo = t.text
            for k, v in placeholders.items():
                nuevo = nuevo.replace(k, v)
            t.text = nuevo

    def _etiqueta_mover_grupo(self, grp_el, x_emu, y_emu):
        """Mueve un grupo (p:grpSp) fijando su offset absoluto en la hoja."""
        from pptx.oxml.ns import qn
        xfrm = grp_el.find('%s/%s' % (qn('p:grpSpPr'), qn('a:xfrm')))
        off = xfrm.find(qn('a:off'))
        off.set('x', str(int(x_emu)))
        off.set('y', str(int(y_emu)))

    def _etiqueta_remap_rels(self, el, src_part, dst_part):
        """Reapunta las relaciones de imagen/medios (r:embed / r:link) de un
        elemento a la hoja destino, creando la relacion hacia la MISMA parte de
        imagen. Sin esto, las imagenes de la etiqueta no cargan en las hojas
        clonadas (2+) y el formato se ve roto."""
        from pptx.oxml.ns import qn
        for attr in (qn('r:embed'), qn('r:link')):
            for node in el.iter():
                rid = node.get(attr)
                if rid and rid in src_part.rels:
                    rel = src_part.rels[rid]
                    nuevo = dst_part.relate_to(rel.target_part, rel.reltype)
                    node.set(attr, nuevo)

    def _etiqueta_construir_pptx(self, subtipo, datos, lineas):
        """Arma UN pptx tabloide con las etiquetas necesarias TILEADAS en una
        rejilla 3x6 (18 por hoja); si se necesitan mas de 18, agrega hojas.
        Cada plantilla ya trae el marco + la etiqueta chica (grupo); se copia
        el grupo por cada caja y se posiciona en la rejilla."""
        import copy
        from pptx import Presentation
        from pptx.util import Inches
        ruta = os.path.join(
            os.path.dirname(__file__), '..', 'static', 'templates',
            'PLANTILLA_%s.pptx' % subtipo)
        if not os.path.exists(ruta):
            raise UserError(_('No existe la plantilla PLANTILLA_%s.pptx en el modulo.') % subtipo)

        # Una entrada de valores por caja.
        etiquetas = []
        for n, cajas in lineas:
            for _i in range(cajas):
                d = dict(datos)
                d['{{N}}'] = str(n)
                etiquetas.append(d)
        if not etiquetas:
            etiquetas = [dict(datos, **{'{{N}}': '0'})]

        prs = Presentation(ruta)
        base = prs.slides[0]

        # Localizar la etiqueta chica (el grupo) y separarla del marco.
        grupo = None
        for sh in base.shapes:
            if sh.shape_type == 6:  # MSO_SHAPE_TYPE.GROUP
                grupo = sh
                break
        if grupo is None:
            raise UserError(_('La plantilla PLANTILLA_%s.pptx no tiene la etiqueta como grupo.') % subtipo)
        unidad_xml = copy.deepcopy(grupo._element)
        grupo._element.getparent().remove(grupo._element)
        # Ahora `base` es una hoja con SOLO el marco. Servira de fondo por hoja.
        # `base.part` conserva las relaciones de imagen de la etiqueta (rId2/3/4).
        base_part = base.part

        # Posiciones de la rejilla (row-major: izq->der, arriba->abajo).
        posiciones = []
        for r in range(self._GRID_ROWS):
            for c in self._GRID_COLS_IN:
                posiciones.append((
                    Inches(c),
                    Inches(self._GRID_ROW0_IN + r * self._GRID_ROW_PITCH_IN),
                ))
        por_hoja = len(posiciones)  # 18

        import math
        num_hojas = max(1, math.ceil(len(etiquetas) / por_hoja))
        hojas = [base]
        for _h in range(1, num_hojas):
            hojas.append(self._etiqueta_clonar_slide(prs, base))  # marco solo

        for idx, vals in enumerate(etiquetas):
            hoja = hojas[idx // por_hoja]
            x_emu, y_emu = posiciones[idx % por_hoja]
            nuevo = copy.deepcopy(unidad_xml)
            self._etiqueta_mover_grupo(nuevo, x_emu, y_emu)
            self._etiqueta_llenar_element(nuevo, vals)
            hoja.shapes._spTree.append(nuevo)
            # Crear en esta hoja las relaciones de imagen que usa la etiqueta.
            self._etiqueta_remap_rels(nuevo, base_part, hoja.part)

        buf = io.BytesIO()
        prs.save(buf)
        return buf.getvalue()

    def action_generar_etiqueta_pptx(self):
        """Boton en la MO: arma UN solo PPTX con todas las etiquetas que pide el
        plan de empaque (una diapositiva por caja), lo adjunta a la orden y lo
        descarga directo."""
        self.ensure_one()
        subtipo, lot_name, datos = self._etiqueta_datos()
        lineas, origen_plan = self._etiqueta_plan_lineas()
        Attachment = self.env['ir.attachment']
        safe = re.sub(r'[/\\:*?"<>|]', '-', lot_name)
        ref = self.product_id.default_code or 'SREF'
        total = sum(c for _n, c in lineas)

        contenido = self._etiqueta_construir_pptx(subtipo, datos, lineas)

        # Reemplaza el archivo previo de esta orden para no acumular.
        Attachment.search([
            ('res_model', '=', 'mrp.production'),
            ('res_id', '=', self.id),
            ('name', '=like', 'Etiquetas_%.pptx'),
        ]).unlink()

        nombre = 'Etiquetas_%s_%s_%setiq.pptx' % (ref, safe, total)
        att = Attachment.create({
            'name': nombre,
            'type': 'binary',
            'datas': base64.b64encode(contenido),
            'mimetype': ('application/vnd.openxmlformats-officedocument'
                         '.presentationml.presentation'),
            'res_model': 'mrp.production',
            'res_id': self.id,
        })

        resumen = ', '.join('%s cajas de %s pzas' % (c, n) for n, c in lineas)
        origen = _('plan de empaque') if origen_plan else _(
            'presentaciones autorizadas (esta orden no tiene plan de empaque aprobado)')
        self.message_post(body=_(
            'Etiquetas de caja generadas: %(cant)s en un archivo (%(resumen)s), segun %(origen)s.',
            cant=total, resumen=resumen, origen=origen))

        # Descarga directa del unico archivo.
        return {
            'type': 'ir.actions.act_url',
            'url': '/web/content/%s?download=true' % att.id,
            'target': 'self',
        }
