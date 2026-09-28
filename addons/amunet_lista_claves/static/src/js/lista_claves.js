/** @odoo-module */
import { Component, useState, onWillStart } from "@odoo/owl";
import { registry } from "@web/core/registry";
import { useService } from "@web/core/utils/hooks";

const CLASIFICACIONES = {
    mp: { label: "Materia Prima",          icon: "fa-cubes",       color: "#2d6a4f" },
    sp: { label: "Semiprocesado",          icon: "fa-flask",       color: "#1d3557" },
    st: { label: "Semiterminado",          icon: "fa-cogs",        color: "#6f42c1" },
    mi: { label: "Material de Impresión",  icon: "fa-print",       color: "#c53030" },
    pt: { label: "Producto Terminado",     icon: "fa-box",         color: "#e85d04" },
    ptr: { label: "PT Reactivos",          icon: "fa-flask",       color: "#d62828" },
    eq: { label: "Equipos",               icon: "fa-wrench",      color: "#0d6efd" },
};

export class AmunetListaClaves extends Component {
    static template = "amunet_lista_claves.ListaClaves";

    setup() {
        this.orm    = useService("orm");
        this.action = useService("action");
        this.state  = useState({
            vista:            "hub",
            clasificacion:    null,
            claves:           [],
            clavesInactivas:  [],
            counts:           {},
            loading:          true,
            tabActiva:        null,
        });
        onWillStart(() => this._cargarConteos());
    }

    async _cargarConteos() {
        this.state.loading = true;
        const claves = await this.orm.searchRead(
            "amunet.clave",
            [["estado", "=", "activa"]],
            ["clasificacion"],
        );
        const counts = {};
        for (const c of claves) {
            counts[c.clasificacion] = (counts[c.clasificacion] || 0) + 1;
        }
        this.state.counts  = counts;
        this.state.loading = false;
    }

    async abrirClasificacion(key) {
        this.state.loading = true;
        const claves = await this.orm.searchRead(
            "amunet.clave",
            [["clasificacion", "=", key]],
            ["id", "clave", "nombre", "subcategoria", "estado"],
            { order: "subcategoria, clave", limit: 5000 },
        );
        this.state.claves           = claves.filter(c => c.estado === "activa");
        this.state.clavesInactivas  = claves.filter(c => c.estado !== "activa");
        this.state.clasificacion    = key;
        this.state.vista            = "clasificacion";
        this.state.loading          = false;
        const conTab = this._gruposConPestana(this.state.claves);
        this.state.tabActiva = conTab.length ? conTab[0].nombre : null;
    }

    volverHub() {
        this.state.vista         = "hub";
        this.state.clasificacion = null;
        this.state.claves        = [];
        this._cargarConteos();
    }

    setTab(nombre) { this.state.tabActiva = nombre; }

    _agrupar(claves) {
        const map = {};
        for (const c of claves) {
            const sub = c.subcategoria || "Sin subcategoría";
            if (!map[sub]) map[sub] = [];
            map[sub].push(c);
        }
        return Object.entries(map).map(([nombre, items]) => ({ nombre, items }));
    }

    _gruposConPestana(claves)  { return this._agrupar(claves).filter(g => g.items.length >= 2); }
    _gruposSinPestana(claves)  { return this._agrupar(claves).filter(g => g.items.length < 2); }

    get clasificacionActual()  { return CLASIFICACIONES[this.state.clasificacion] || {}; }
    get clasificacionesList()  {
        return Object.entries(CLASIFICACIONES).map(([key, meta]) => ({
            key, ...meta,
            count: this.state.counts[key] || 0,
        }));
    }
    get gruposConPestana() { return this._gruposConPestana(this.state.claves); }
    get gruposSinPestana() { return this._gruposSinPestana(this.state.claves); }
    get hayInactivas()     { return this.state.clavesInactivas.length > 0; }

    async nuevaClave() {
        await this.action.doAction({
            type:      "ir.actions.act_window",
            name:      "Nueva clave",
            res_model: "amunet.clave",
            view_mode: "form",
            views:     [[false, "form"]],
            target:    "new",
            context:   { default_clasificacion: this.state.clasificacion },
        });
        await this.abrirClasificacion(this.state.clasificacion);
    }

    async abrirClave(id) {
        await this.action.doAction({
            type:      "ir.actions.act_window",
            name:      "Clave",
            res_model: "amunet.clave",
            res_id:    id,
            view_mode: "form",
            views:     [[false, "form"]],
            target:    "new",
        });
        await this.abrirClasificacion(this.state.clasificacion);
    }
}

registry.category("actions").add("amunet_lista_claves_hub", AmunetListaClaves);
