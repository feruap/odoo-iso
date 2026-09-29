/** @odoo-module **/
import { Component, onWillStart, useState } from "@odoo/owl";
import { registry } from "@web/core/registry";
import { useService } from "@web/core/utils/hooks";

const COLUMNAS = [
    { id: "autorizar", nombre: "Por autorizar", ayuda: "Falta que autorice el jefe del área" },
    { id: "comprar", nombre: "Autorizada, falta comprar", ayuda: "Autorizada; la orden aún no se confirma ni se paga" },
    { id: "pagada", nombre: "Pagada o confirmada", ayuda: "Pagada o confirmada por el proveedor; todavía no sale" },
    { id: "transito", nombre: "En tránsito", ayuda: "Ya viene: el proveedor confirmó fecha de llegada o ya llegó una parte" },
    { id: "atrasada", nombre: "Atrasada", ayuda: "Ya pasó la fecha prometida y no ha llegado todo" },
    { id: "recibida", nombre: "Recibida", ayuda: "Llegó completa en los últimos días" },
];

const PESO_URGENCIA = { linea_detenida: 2, urge: 1, normal: 0 };

function normaliza(txt) {
    return (txt || "").toString().toLowerCase().normalize("NFD").replace(/[̀-ͯ]/g, "");
}

function ordena(etapa, a, b) {
    const u = (PESO_URGENCIA[b.urgencia] || 0) - (PESO_URGENCIA[a.urgencia] || 0);
    if (u) return u;
    if (etapa === "atrasada") return b.dias_atraso - a.dias_atraso;
    if (etapa === "transito" || etapa === "pagada") return (a.fecha_esperada || "9999").localeCompare(b.fecha_esperada || "9999");
    if (etapa === "recibida") return (b.fecha_llegada || "").localeCompare(a.fecha_llegada || "");
    return b.edad_dias - a.edad_dias;
}

export class ComprasTablero extends Component {
    static template = "amunet_compras_tablero.Tablero";
    static props = ["*"];

    setup() {
        this.orm = useService("orm");
        this.action = useService("action");
        this.columnas = COLUMNAS;
        this.state = useState({
            cargando: true,
            error: false,
            datos: null,
            q: "",
            tipo: "todo",
            soloUrgentes: false,
            verRecibidas: true,
            actualizado: "",
        });
        onWillStart(() => this.cargar());
    }

    async cargar() {
        this.state.cargando = true;
        this.state.error = false;
        try {
            this.state.datos = await this.orm.call("amunet.compras.tablero", "get_datos", []);
            const d = new Date();
            this.state.actualizado = d.toLocaleTimeString("es-MX", { hour: "2-digit", minute: "2-digit" });
        } catch (e) {
            this.state.error = (e && e.data && e.data.message) || (e && e.message) || "No se pudo cargar el tablero";
        }
        this.state.cargando = false;
    }

    get filtradas() {
        const datos = this.state.datos;
        if (!datos) return [];
        const q = normaliza(this.state.q).trim();
        const palabras = q ? q.split(/\s+/) : [];
        return datos.tarjetas.filter((t) => {
            if (this.state.tipo !== "todo" && t.tipo !== this.state.tipo) return false;
            if (this.state.soloUrgentes && t.urgencia === "normal") return false;
            if (palabras.length) {
                const h = normaliza(t.buscar + " " + t.folio + " " + t.titulo);
                return palabras.every((p) => h.includes(p));
            }
            return true;
        });
    }

    get columnasVisibles() {
        return this.columnas.filter((c) => c.id !== "recibida" || this.state.verRecibidas);
    }

    get porColumna() {
        const grupos = {};
        for (const c of this.columnas) grupos[c.id] = [];
        for (const t of this.filtradas) {
            (grupos[t.etapa] || (grupos[t.etapa] = [])).push(t);
        }
        for (const id in grupos) grupos[id].sort((a, b) => ordena(id, a, b));
        return grupos;
    }

    get resumen() {
        const g = this.porColumna;
        const vivas = this.filtradas.filter((t) => t.etapa !== "recibida");
        return {
            vivas: vivas.length,
            atrasadas: g.atrasada.length,
            pagadas: g.pagada.length + g.transito.length,
            urgentes: vivas.filter((t) => t.urgencia !== "normal").length,
            decidir: g.autorizar.length + g.comprar.length,
        };
    }

    setTipo(tipo) {
        this.state.tipo = tipo;
    }

    toggleUrgentes() {
        this.state.soloUrgentes = !this.state.soloUrgentes;
    }

    toggleRecibidas() {
        this.state.verRecibidas = !this.state.verRecibidas;
    }

    fechaCorta(iso) {
        if (!iso) return "";
        const [y, m, d] = iso.split("-").map(Number);
        const meses = ["ene", "feb", "mar", "abr", "may", "jun", "jul", "ago", "sep", "oct", "nov", "dic"];
        const hoy = this.state.datos && this.state.datos.hoy;
        const mismoAnio = hoy && Number(hoy.slice(0, 4)) === y;
        return `${d}-${meses[m - 1]}${mismoAnio ? "" : "-" + String(y).slice(2)}`;
    }

    edad(dias) {
        if (dias <= 0) return "hoy";
        if (dias === 1) return "ayer";
        if (dias < 60) return `hace ${dias} días`;
        return `hace ${Math.round(dias / 30)} meses`;
    }

    claseCard(t) {
        const c = ["o_ct_card"];
        if (t.urgencia === "linea_detenida") c.push("o_ct_urg2");
        else if (t.urgencia === "urge") c.push("o_ct_urg1");
        if (t.borrador) c.push("o_ct_borrador");
        return c.join(" ");
    }

    // Icono de la via: la capturada por Compras manda; si no hay, lo que
    // pidio el solicitante; si tampoco, la sugerencia por urgencia.
    via(t) {
        const ICON = { aereo: "fa-plane", maritimo: "fa-ship", terrestre: "fa-truck", mensajeria: "fa-archive" };
        const NOMBRE = { aereo: "Avión", maritimo: "Barco", terrestre: "Terrestre", mensajeria: "Mensajería" };
        if (t.via_code) {
            return { icon: ICON[t.via_code] || "fa-truck", texto: NOMBRE[t.via_code] || t.via, clase: "o_ct_via",
                     title: "Vía de embarque capturada por Compras" + (t.via_pref && t.via_pref !== t.via_code ? ` (el solicitante pidió ${NOMBRE[t.via_pref]})` : "") };
        }
        if (t.via_pref) {
            return { icon: ICON[t.via_pref], texto: "Pide " + NOMBRE[t.via_pref].toLowerCase(), clase: "o_ct_via o_ct_via_pref",
                     title: "Preferencia del solicitante. La vía final la decide Compras." };
        }
        if (t.via_sug) {
            return { icon: "fa-plane", texto: "aéreo sugerido", clase: "o_ct_via o_ct_via_sug",
                     title: "Sugerido por la urgencia de la solicitud. No está decidido." };
        }
        return null;
    }

    abrir(t) {
        this.action.doAction({
            type: "ir.actions.act_window",
            res_model: t.modelo,
            res_id: t.res_id,
            views: [[false, "form"]],
            target: "current",
        });
    }

    abrirListaOC() {
        if (this.state.datos && this.state.datos.accion_oc) {
            this.action.doAction(this.state.datos.accion_oc);
        }
    }
}

registry.category("actions").add("amunet_compras_tablero", ComprasTablero);
