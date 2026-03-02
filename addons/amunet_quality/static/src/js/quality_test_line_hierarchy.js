/** @odoo-module **/

/**
 * Epic-031: Sistema de Parámetros de Calidad Jerárquicos
 * Componente OWL2 para vista jerárquica de determinaciones en QC
 * 
 * Este componente permite expandir/colapsar los detalles de especificaciones
 * dentro de una línea de test de control de calidad.
 */

import { Component, useState, onWillStart, onWillUpdateProps, onMounted } from "@odoo/owl";
import { registry } from "@web/core/registry";
import { useService } from "@web/core/utils/hooks";
import { _t } from "@web/core/l10n/translation";
import { standardFieldProps } from "@web/views/fields/standard_field_props";

console.log(">>> Amunet Quality Hierarchy Row: Original Widgets Restored <<<");

import { DecisionMatrixWidget } from "@amunet_quality/js/decision_matrix_widget";
import { VAMA034Widget } from "@amunet_quality/js/vama034_widget";
import { MAVI07Widget } from "@amunet_quality/js/mavi07_widget";
import { VAMA044Widget } from "@amunet_quality/js/vama044_widget";
import { VAMA078Widget } from "@amunet_quality/js/vama078_widget";
import { VAMA112Widget } from "@amunet_quality/js/vama112_widget";
import { MGA0981Widget } from "@amunet_quality/js/mga0981_widget";
import { VAMAMultiCheckWidget } from "@amunet_quality/js/vama_multi_check_widget";
import { MultiConditionWidget } from "@amunet_quality/js/multi_condition_widget";

/**
 * Componente para mostrar el resumen del dictamen con badge coloreado
 */
export class QualityVerdictBadge extends Component {
    static template = "amunet_quality.QualityVerdictBadge";
    static props = {
        verdict: { type: String },
        summary: { type: String, optional: true },
    };

    get verdictClass() {
        const classes = {
            'pending': 'bg-warning text-dark',
            'pass': 'bg-success text-white',
            'fail': 'bg-danger text-white',
            'not_applicable': 'bg-secondary text-white',
        };
        return classes[this.props.verdict] || 'bg-secondary';
    }

    get verdictLabel() {
        const labels = {
            'pending': _t('⏳ Pendiente'),
            'pass': _t('✅ Cumple'),
            'fail': _t('❌ No Cumple'),
            'not_applicable': _t('⚪ N/A'),
        };
        return labels[this.props.verdict] || _t('Pendiente');
    }
}

/**
 * Fila expandible de determinación con detalles de especificaciones
 */
export class QualityTestLineRow extends Component {
    static template = "amunet_quality.QualityTestLineRow";
    static components = { 
        QualityVerdictBadge,
        DecisionMatrixWidget,
        VAMA034Widget,
        MAVI07Widget,
        VAMA044Widget,
        VAMA078Widget,
        VAMA112Widget,
        MGA0981Widget,
        VAMAMultiCheckWidget,
        MultiConditionWidget
    };
    static props = {
        testLine: { type: Object },
        readonly: { type: Boolean },
        onUpdate: { type: Function, optional: true },
        expandedAll: { type: Boolean, optional: true },
    };

    setup() {
        console.log("QualityTestLineRow setup - New handlers present:", !!this.onVama067ParticlesClick);
        this.state = useState({
            expanded: false,
            loading: false,
            details: [],
        });
        this.orm = useService("orm");
        
        // El resto del setup permanece igual
        onWillUpdateProps(async (nextProps) => {
            if (this.props.expandedAll !== nextProps.expandedAll) {
                await this.handleExpandAllChange(nextProps.expandedAll);
            }
        });
        
        onMounted(async () => {
            if (this.props.expandedAll && this.canExpand) {
                await this.handleExpandAllChange(true);
            }
        });
    }

    get hasDetails() {
        return this.props.testLine.has_details || false;
    }

    get canExpand() {
        return this.hasDetails && this.props.testLine.detail_count > 0;
    }

    async toggleExpand() {
        if (!this.canExpand) return;

        if (!this.state.expanded && this.state.details.length === 0) {
            await this.loadDetails();
        }
        this.state.expanded = !this.state.expanded;
    }

    async handleExpandAllChange(shouldExpand) {
        if (!this.canExpand) return;
        
        if (shouldExpand && !this.state.expanded) {
            // Expandir: cargar detalles si no están cargados
            if (this.state.details.length === 0) {
                await this.loadDetails();
            }
            this.state.expanded = true;
        } else if (!shouldExpand && this.state.expanded) {
            // Colapsar
            this.state.expanded = false;
        }
    }

    async loadDetails() {
        this.state.loading = true;
        try {
            const details = await this.orm.searchRead(
                "amunet.quality.test.line.detail",
                [["test_line_id", "=", this.props.testLine.id]],
                [
                    "id", "sequence", "name", "acceptance_criteria",
                    "evaluation_type", "result_display", "verdict",
                    "verdict_display", "verdict_message",
                    // Campos de resultado básicos
                    "result_selection", "result_numeric",
                    "result_checkbox_1", "result_checkbox_2",
                    "result_text_pattern", "constructed_phrase",
                    "result_expected_type", "result_obtained_type",
                    "result_binary_option", "result_notes",
                    "result_ternary",
                    // VAMA-034: Two-step widget fields
                    "vama034_sample_type", "vama034_observed_result",
                    // VAMA-006: Color scale
                    "vama006_color_value",
                    // VAMA-067: 2-step centrifuge widget
                    "vama067_particles", "vama067_color",
                    // Configuración básica
                    "min_value", "max_value", "uom_id",
                    "binary_option_pass", "binary_option_fail",
                    "checkbox_label_1", "checkbox_label_2",
                    "text_pattern_expected",
                    // Conditional Numeric Range
                    "available_conditional_option_ids",
                    "result_conditional_option_id",
                    "result_conditional_value",
                    // Decision Matrix
                    "result_dm_step1_concentration",
                    "result_dm_step2_1_control_visible",
                    "result_dm_step2_2_comparison",
                    "dm_step2_1_unlocked",
                    "dm_step2_2_unlocked",
                    "dm_current_step",
                    "dm_matched_scenario_id",
                    // Campos adicionales para widgets especializados
                    "vama044_num_gotas", "vama044_num_gotas_min",
                    "vama044_vol_gota", "vama044_vol_gota_min", "vama044_vol_gota_max",
                    "vama044_union", "vama044_vol_llenado", 
                    "vama044_vol_llenado_min", "vama044_vol_llenado_max",
                    "vama078_color", "vama078_forma", "vama078_textura", "vama078_humedad",
                    "vama112_cond1", "vama112_cond2", "vama112_cond3", "vama112_cond4", "vama112_cond5",
                    "mga0981_vol_declarado", "mga0981_vol_obtenido",
                    "vama105_nominal_volume", "vama105_measured_volume",
                    "multi_check_results_json", "text_phrase_mapping",
                    "multi_cond_binary", "multi_cond_num1", "multi_cond_num1_min",
                    "multi_cond_num2", "multi_cond_num2_min", "multi_cond_num2_max",
                    "mavi07_sample_type", "mavi07_expected_result", "mavi07_observed_result",
                    // Expected vs Obtained (VAMA-032)
                    "expected_options", "obtained_options",
                ],
                { order: "sequence, id" }
            );
            
            // Para conditional_numeric_range, cargar las opciones disponibles
            for (const detail of details) {
                if (detail.evaluation_type === 'conditional_numeric_range' && 
                    detail.available_conditional_option_ids && 
                    detail.available_conditional_option_ids.length > 0) {
                    const options = await this.orm.read(
                        "amunet.quality.parameter.conditional.option",
                        detail.available_conditional_option_ids,
                        ["id", "name", "min_value", "max_value", "uom_id"]
                    );
                    detail.conditional_options = options;
                }
                
                // Para VAMA-105, parsear text_phrase_mapping y extraer opciones de volumen
                if (detail.evaluation_type === 'vama_105' && detail.text_phrase_mapping) {
                    try {
                        const mapping = JSON.parse(detail.text_phrase_mapping);
                        if (mapping.positions && mapping.positions[0] && mapping.positions[0].options) {
                            detail.vama105_volume_options = mapping.positions[0].options.map(opt => ({
                                label: opt.label,
                                value: opt.value
                            }));
                        }
                        if (mapping.evaluation && mapping.evaluation.rules) {
                            detail.vama105_rules = mapping.evaluation.rules;
                        }
                    } catch (e) {
                        console.error("Error parsing VAMA-105 mapping:", e);
                        // Fallback a valores por defecto
                        detail.vama105_volume_options = [
                            {label: '5 µL', value: '5'},
                            {label: '25 µL', value: '25'},
                            {label: '50 µL', value: '50'}
                        ];
                    }
                }
            }
            
            this.state.details = details;
        } catch (error) {
            console.error("Error loading details:", error);
        } finally {
            this.state.loading = false;
        }
    }

    // Removed inline handlers for specialized widgets as they are now components

    // Método genérico para múltiples campos
    async updateDetailFields(detailId, values) {
        if (this.props.readonly) return;
        try {
            await this.orm.write("amunet.quality.test.line.detail", [detailId], values);
            // Reload details so verdict is recalculated and UI reflects the change
            await this.loadDetails();
            // Notify parent to update the line-level verdict
            if (this.props.onUpdate) {
                await this.props.onUpdate(this.props.testLine.id);
            }
        } catch (error) {
            console.error("Error updating detail fields:", error);
        }
    }

    async updateDetailField(detailId, field, value) {
        return this.onDetailChange(detailId, field, value);
    }

    async onDetailChange(detailId, field, value) {
        if (this.props.readonly) return;

        try {
            await this.orm.write("amunet.quality.test.line.detail", [detailId], {
                [field]: value,
            });
            
            // Recargar detalles para actualizar dictamen
            await this.loadDetails();
            
            // Notificar al padre para actualizar dictamen de línea
            if (this.props.onUpdate) {
                await this.props.onUpdate(this.props.testLine.id);
            }
        } catch (error) {
            console.error("Error updating detail:", error);
        }
    }

    // Métodos helper para handlers de eventos (usan data-* attributes)
    onNumericChange(ev) {
        const detailId = parseInt(ev.target.dataset.detailId);
        const value = parseFloat(ev.target.value) || 0;
        this.onDetailChange(detailId, 'result_numeric', value);
        // Ensure the filled flag is set so the backend triggers evaluation
        this.orm.write("amunet.quality.test.line.detail", [detailId], {
            result_numeric_filled: true,
        });
    }

    onSelectionChange(ev) {
        const detailId = parseInt(ev.target.dataset.detailId);
        this.onDetailChange(detailId, 'result_selection', ev.target.value);
    }

    onTextPatternChange(ev) {
        const detailId = parseInt(ev.target.dataset.detailId);
        const value = ev.target.value.toUpperCase();
        this.onDetailChange(detailId, 'result_text_pattern', value);
    }

    async onCheckboxChange(ev) {
        const detailId = parseInt(ev.target.dataset.detailId);
        const field = ev.target.dataset.field;
        const checked = ev.target.checked;
        
        if (this.props.readonly) return;

        try {
            // Para checkbox_combined, también marcar checkbox_result_confirmed = True
            await this.orm.write("amunet.quality.test.line.detail", [detailId], {
                [field]: checked,
                checkbox_result_confirmed: true,
            });
            
            // Recargar detalles para actualizar dictamen
            await this.loadDetails();
            
            // Notificar al padre para actualizar dictamen de línea
            if (this.props.onUpdate) {
                await this.props.onUpdate(this.props.testLine.id);
            }
        } catch (error) {
            console.error("Error updating checkbox:", error);
        }
    }

    onExpectedTypeChange(ev) {
        const detailId = parseInt(ev.target.dataset.detailId);
        this.onDetailChange(detailId, 'result_expected_type', ev.target.value);
    }

    onObtainedTypeChange(ev) {
        const detailId = parseInt(ev.target.dataset.detailId);
        this.onDetailChange(detailId, 'result_obtained_type', ev.target.value);
    }

    onTernaryChange(ev) {
        const detailId = parseInt(ev.target.dataset.detailId);
        this.onDetailChange(detailId, 'result_ternary', ev.target.value);
    }

    onBinaryOptionChange(ev) {
        const detailId = parseInt(ev.target.dataset.detailId);
        this.onDetailChange(detailId, 'result_binary_option', ev.target.value);
    }

    onNotesChange(ev) {
        const detailId = parseInt(ev.target.dataset.detailId);
        this.onDetailChange(detailId, 'result_notes', ev.target.value);
    }

    // Conditional Numeric Range handlers
    onConditionalOptionChange(ev) {
        const detailId = parseInt(ev.target.dataset.detailId);
        const optionId = parseInt(ev.target.value) || false;
        this.onDetailChange(detailId, 'result_conditional_option_id', optionId);
    }

    onConditionalValueChange(ev) {
        const detailId = parseInt(ev.target.dataset.detailId);
        const value = parseFloat(ev.target.value) || 0;
        this.onDetailChange(detailId, 'result_conditional_value', value);
        // Ensure the filled flag is set
        this.orm.write("amunet.quality.test.line.detail", [detailId], {
            result_conditional_value_filled: true,
        });
    }

    onConditionalOptionClick(ev) {
        const detailId = parseInt(ev.currentTarget.dataset.detailId);
        const optionId = parseInt(ev.currentTarget.dataset.optionId);
        this.onDetailChange(detailId, 'result_conditional_option_id', optionId);
    }

    // Decision Matrix handlers
    onDmStep1Change(ev) {
        const detailId = parseInt(ev.target.dataset.detailId);
        this.onDetailChange(detailId, 'result_dm_step1_concentration', ev.target.value);
    }

    onDmStep2_1Change(ev) {
        const detailId = parseInt(ev.target.dataset.detailId);
        this.onDetailChange(detailId, 'result_dm_step2_1_control_visible', ev.target.value);
    }

    onDmStep2_2Change(ev) {
        const detailId = parseInt(ev.target.dataset.detailId);
        this.onDetailChange(detailId, 'result_dm_step2_2_comparison', ev.target.value);
    }

    // VAMA-034 handlers
    onVama034SampleTypeClick(ev, type) {
        const detailId = parseInt(ev.target.dataset.detailId);
        this.onDetailChange(detailId, 'vama034_sample_type', type);
    }

    onVama034ObservedResultClick(ev, result) {
        const detailId = parseInt(ev.target.dataset.detailId);
        this.onDetailChange(detailId, 'vama034_observed_result', result);
    }

    // VAMA-006 handler
    async onVama006ColorClick(ev, shade) {
        const detailId = parseInt(ev.currentTarget.dataset.detailId, 10);
        if (!detailId) return;
        await this.onDetailChange(detailId, 'vama006_color_value', shade);
    }

    // VAMA-067 handlers
    async onVama067ParticlesClick(ev, value) {
        const detailId = parseInt(ev.currentTarget.dataset.detailId, 10);
        if (!detailId) return;
        
        // Reset color when particles change (standard Odoo behavior for dependent fields)
        if (this.props.readonly) return;
        try {
            await this.orm.write("amunet.quality.test.line.detail", [detailId], {
                vama067_particles: value,
                vama067_color: false
            });
            await this.loadDetails();
            if (this.props.onUpdate) {
                await this.props.onUpdate(this.props.testLine.id);
            }
        } catch (error) {
            console.error("Error saving VAMA-067 particles:", error);
        }
    }

    async onVama067ColorClick(ev, value) {
        const detailId = parseInt(ev.currentTarget.dataset.detailId, 10);
        if (!detailId) return;
        await this.onDetailChange(detailId, 'vama067_color', value);
    }

    // VAMA-105 handlers
    async onVama105VolumeClick(ev) {
        const detailId = parseInt(ev.currentTarget.dataset.detailId, 10);
        const volume = ev.currentTarget.dataset.volume;
        if (!detailId || !volume) return;
        await this.onDetailChange(detailId, 'vama105_nominal_volume', volume);
    }

    async onVama105MeasuredChange(ev) {
        const detailId = parseInt(ev.currentTarget.dataset.detailId, 10);
        const value = parseFloat(ev.currentTarget.value);
        if (!detailId || isNaN(value)) return;
        await this.onDetailChange(detailId, 'vama105_measured_volume', value);
    }


    getEvaluationTypeLabel(type) {
        const labels = {
            'binary_selection': _t('Selección'),
            'numeric_range': _t('Numérico'),
            'checkbox_combined': _t('Checkboxes'),
            'conditional_numeric_range': _t('Condicional'),
            'text_pattern': _t('Patrón'),
            'expected_vs_obtained': _t('Comparación'),
            'binary_with_notes': _t('Con Notas'),
            'ternary_with_na': _t('Ternario'),
            'vama_006': _t('Escala Color'),
            'vama_067': _t('Centrifugación'),
            'decision_matrix': _t('Matriz de Decisión'),
            'vama_044': _t('Funcionalidad Tubo'),
            'vama_078': _t('Visual Liofilizado'),
            'vama_112': _t('Multi-Centrífuga'),
            'mga_0981': _t('Variación Volumen'),
            'vama_multi_check': _t('Multi-Check'),
            'multi_condition_numeric': _t('Multi-Condición'),
            'vama_105': _t('Volumen Micropipeta'),
        };
        return labels[type] || type;
    }
}


/**
 * Componente principal: Tabla jerárquica de determinaciones (standalone)
 */
export class QualityTestLineHierarchy extends Component {
    static template = "amunet_quality.QualityTestLineHierarchy";
    static components = { QualityTestLineRow, QualityVerdictBadge };
    static props = {
        testLines: { type: Array },
        readonly: { type: Boolean },
        checkId: { type: Number, optional: true },
        onGlobalUpdate: { type: Function, optional: true },
    };

    setup() {
        this.state = useState({
            expandedAll: false,
            searchQuery: "",
        });
        this.orm = useService("orm");
    }

    get filteredTestLines() {
        if (!this.state.searchQuery) {
            return this.props.testLines;
        }
        const query = this.state.searchQuery.toLowerCase();
        return this.props.testLines.filter(line => {
            const nameMatch = line.name && line.name.toLowerCase().includes(query);
            const codeMatch = line.code && line.code.toLowerCase().includes(query);
            return nameMatch || codeMatch;
        });
    }

    onSearchInput(ev) {
        this.state.searchQuery = ev.target.value;
    }

    toggleExpandAll() {
        this.state.expandedAll = !this.state.expandedAll;
    }

    async onLineUpdate(lineId) {
        if (this.props.onGlobalUpdate) {
            await this.props.onGlobalUpdate();
        }
    }
}

/**
 * Widget de campo One2many que renderiza la jerarquía de test lines
 * 
 * Epic-031: Integración con campos One2many de Odoo 19
 * 
 * Uso en XML:
 * <field name="test_line_ids" widget="quality_test_line_hierarchy"/>
 * 
 * Arquitectura:
 * - QualityTestLineHierarchyField: Widget que carga datos desde Odoo
 * - QualityTestLineHierarchy: Componente standalone que renderiza la tabla
 * - QualityTestLineRow: Fila expandible con detalles
 */
export class QualityTestLineHierarchyField extends Component {
    static template = "amunet_quality.QualityTestLineHierarchyField";
    // Usa QualityTestLineHierarchy como componente hijo
    static components = { QualityTestLineHierarchy };
    static props = {
        ...standardFieldProps,
    };
    
    setup() {
        this.state = useState({
            testLines: [],
            loading: true,
        });
        this.orm = useService("orm");
        
        onWillStart(async () => {
            await this.loadTestLines();
        });
        
        onMounted(() => {
            // Si no se cargaron las líneas, reintentar
            if (this.state.testLines.length === 0 && this.props.record?.resId) {
                this.loadTestLines();
            }
        });
        
        onWillUpdateProps(async (nextProps) => {
            await this.loadTestLines(nextProps);
        });
    }

    async loadTestLines(props = this.props) {
        const record = props.record;
        
        if (!record) {
            this.state.loading = false;
            return;
        }

        // FIX: Epic-031 Usability
        // Only set loading to true if we don't have data yet.
        // This prevents the UI from "flashing" or resetting scroll/expansion
        // when an update occurs (e.g., after editing a value).
        if (this.state.testLines.length === 0) {
            this.state.loading = true;
        }

        try {
            // Obtener el ID del QC
            const checkId = record.resId || record.data?.id || record._values?.id;
            
            if (!checkId) {
                this.state.testLines = [];
                this.state.loading = false;
                return;
            }

            // Cargar test lines desde el backend
            const testLines = await this.orm.searchRead(
                "amunet.quality.test.line",
                [["check_id", "=", checkId]],
                [
                    "id", "sequence", "code", "name",
                    "has_details", "detail_count", "verdict", "verdict_summary",
                    "verdict_display"
                ],
                { order: "sequence, id" }
            );
            
            this.state.testLines = testLines;
        } catch (error) {
            console.error("QualityTestLineHierarchyField - Error loading test lines:", error);
            this.state.testLines = [];
        } finally {
            this.state.loading = false;
        }
    }

    async onGlobalUpdate() {
        await this.loadTestLines();
        // Recargar el record completo para actualizar contadores
        if (this.props.record?.model?.root) {
            await this.props.record.model.root.load();
        }
    }

    get readonly() {
        return this.props.readonly;
    }

    get checkId() {
        return this.props.record?.resId || null;
    }
}

// Registrar el widget de campo
export const qualityTestLineHierarchyField = {
    component: QualityTestLineHierarchyField,
    displayName: _t("Jerarquía de Determinaciones"),
    supportedTypes: ["one2many"],
    extractProps: ({ attrs, options }, dynamicInfo) => {
        return {};
    },
};

registry.category("fields").add("quality_test_line_hierarchy", qualityTestLineHierarchyField);
