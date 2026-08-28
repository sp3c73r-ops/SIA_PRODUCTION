import { useEffect, useState } from "react";

import {
    getDocumentFields,
    createDocumentField,
    updateDocumentField,
    toggleDocumentFieldActive,
    deleteDocumentField,
} from "../services/documentFieldService";
import {
    getPhases,
    createPhase,
    updatePhase,
    deletePhase,
} from "../services/phaseService";

const FIELD_TYPES = [
    { value: "string", label: "String" },
    { value: "integer", label: "Integer" },
    { value: "decimal", label: "Decimal" },
    { value: "date", label: "Date" },
    { value: "datetime", label: "DateTime" },
    { value: "boolean", label: "Boolean" },
    { value: "text", label: "Text" },
];

export default function Parametres() {
    const [fields, setFields] = useState([]);
    const [natures, setNatures] = useState([]);
    const [loading, setLoading] = useState(true);
    const [loadingNatures, setLoadingNatures] = useState(true);
    const [saving, setSaving] = useState(false);
    const [savingNature, setSavingNature] = useState(false);
    const [error, setError] = useState("");
    const [success, setSuccess] = useState("");
    const [natureError, setNatureError] = useState("");
    const [natureSuccess, setNatureSuccess] = useState("");
    const [editingId, setEditingId] = useState(null);
    const [editingNatureId, setEditingNatureId] = useState(null);
    const [form, setForm] = useState({
        name: "",
        label: "",
        field_type: "string",
        required: false,
        active: true,
        order_index: 0,
        description: "",
    });
    const [natureForm, setNatureForm] = useState({
        libelle: "",
    });

    const loadFields = async () => {
        try {
            setLoading(true);
            const response = await getDocumentFields();
            const normalizedFields = Array.isArray(response?.data)
                ? response.data
                : Array.isArray(response)
                    ? response
                    : [];

            setFields(normalizedFields);
        } catch (err) {
            console.error("Erreur chargement champs :", err);
            setError("Impossible de charger les champs personnalisés.");
        } finally {
            setLoading(false);
        }
    };

    const loadNatures = async () => {
        try {
            setLoadingNatures(true);
            const response = await getPhases();
            const normalizedNatures = Array.isArray(response?.data)
                ? response.data
                : Array.isArray(response)
                    ? response
                    : [];

            setNatures(normalizedNatures);
        } catch (err) {
            console.error("Erreur chargement natures :", err);
            setNatureError("Impossible de charger les natures du document.");
        } finally {
            setLoadingNatures(false);
        }
    };

    useEffect(() => {
        loadFields();
        loadNatures();
    }, []);

    const resetForm = () => {
        setForm({
            name: "",
            label: "",
            field_type: "string",
            required: false,
            active: true,
            order_index: 0,
            description: "",
        });
        setEditingId(null);
    };

    const handleChange = (event) => {
        const { name, value, type, checked } = event.target;

        setForm((previous) => ({
            ...previous,
            [name]: type === "checkbox" ? checked : value,
        }));
    };

    const handleSubmit = async (event) => {
        event.preventDefault();
        setError("");
        setSuccess("");

        if (!form.name.trim() || !form.label.trim()) {
            setError("Le nom technique et le libellé sont obligatoires.");
            return;
        }

        try {
            setSaving(true);
            const payload = {
                ...form,
                name: form.name.trim(),
                label: form.label.trim(),
                description: form.description.trim() || null,
                order_index: Number(form.order_index || 0),
            };

            if (editingId) {
                await updateDocumentField(editingId, payload);
                setSuccess("Champ personnalisé mis à jour.");
            } else {
                await createDocumentField(payload);
                setSuccess("Champ personnalisé créé.");
            }

            resetForm();
            await loadFields();
        } catch (err) {
            console.error("Erreur sauvegarde champ :", err);
            setError(err.response?.data?.detail || "Impossible d’enregistrer le champ.");
        } finally {
            setSaving(false);
        }
    };

    const handleEdit = (field) => {
        setEditingId(field.id);
        setForm({
            name: field.name || "",
            label: field.label || "",
            field_type: field.field_type || "string",
            required: Boolean(field.required),
            active: Boolean(field.active),
            order_index: field.order_index ?? 0,
            description: field.description || "",
        });
        setError("");
        setSuccess("");
    };

    const handleToggleActive = async (field) => {
        try {
            await toggleDocumentFieldActive(field.id, !field.active);
            setSuccess(`Champ ${!field.active ? "activé" : "désactivé"}.`);
            await loadFields();
        } catch (err) {
            console.error("Erreur activation champ :", err);
            setError(err.response?.data?.detail || "Impossible de modifier le statut du champ.");
        }
    };

    const handleDelete = async (field) => {
        const confirmed = window.confirm(`Supprimer le champ "${field.label}" ?`);

        if (!confirmed) {
            return;
        }

        try {
            await deleteDocumentField(field.id);
            setSuccess("Champ supprimé.");
            await loadFields();
        } catch (err) {
            console.error("Erreur suppression champ :", err);
            setError(err.response?.data?.detail || "Impossible de supprimer ce champ.");
        }
    };

    const resetNatureForm = () => {
        setNatureForm({
            libelle: "",
        });
        setEditingNatureId(null);
    };

    const handleNatureChange = (event) => {
        const { name, value } = event.target;

        setNatureForm((previous) => ({
            ...previous,
            [name]: value,
        }));
    };

    const handleNatureSubmit = async (event) => {
        event.preventDefault();
        setNatureError("");
        setNatureSuccess("");

        if (!natureForm.libelle.trim()) {
            setNatureError("Le libellé de la nature est obligatoire.");
            return;
        }

        try {
            setSavingNature(true);
            const payload = {
                libelle: natureForm.libelle.trim(),
            };

            if (editingNatureId) {
                await updatePhase(editingNatureId, payload);
                setNatureSuccess("Nature mise à jour.");
            } else {
                await createPhase(payload);
                setNatureSuccess("Nature créée.");
            }

            resetNatureForm();
            await loadNatures();
        } catch (err) {
            console.error("Erreur sauvegarde nature :", err);
            setNatureError(err.response?.data?.detail || "Impossible d'enregistrer la nature.");
        } finally {
            setSavingNature(false);
        }
    };

    const handleEditNature = (nature) => {
        setEditingNatureId(nature.id);
        setNatureForm({
            libelle: nature.libelle || "",
        });
        setNatureError("");
        setNatureSuccess("");
    };

    const handleDeleteNature = async (nature) => {
        const confirmed = window.confirm(`Supprimer la nature "${nature.libelle}" ?`);

        if (!confirmed) {
            return;
        }

        try {
            await deletePhase(nature.id);
            setNatureSuccess("Nature supprimée.");
            await loadNatures();
        } catch (err) {
            console.error("Erreur suppression nature :", err);
            setNatureError(
                err.response?.data?.detail
                || "Cette nature est déjà utilisée par des documents et ne peut pas être supprimée."
            );
        }
    };

    const getTypeLabel = (typeValue) => FIELD_TYPES.find((type) => type.value === typeValue)?.label || typeValue;

    return (
        <div className="page-container">
            <div className="page-header">
                <h1>Paramètres</h1>
                <p>Configuration générale de la plateforme SIA.</p>
            </div>

            <div className="page-content" style={{ display: "grid", gridTemplateColumns: "1.55fr 1fr", gap: "24px", alignItems: "start" }}>
                <div className="panel" style={{ padding: "0", overflow: "hidden" }}>
                    <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", gap: "16px", padding: "22px 22px 16px", borderBottom: "1px solid #e8edf1" }}>
                        <div>
                            <h3 style={{ margin: 0, color: "#123b59", fontSize: "1.25rem" }}>Champs personnalisés</h3>
                            <p style={{ margin: "6px 0 0", color: "#6b7c8d", fontSize: "13px" }}>Gérez les champs additionnels disponibles pour les documents.</p>
                        </div>
                        <button type="button" className="btn-primary" onClick={resetForm} style={{ whiteSpace: "nowrap" }}>
                            + Nouveau champ
                        </button>
                    </div>

                    <div style={{ padding: "18px 18px 10px" }}>
                        {error && <div className="alert alert-error" style={{ marginBottom: "16px" }}>{error}</div>}
                        {success && <div className="alert alert-success" style={{ marginBottom: "16px" }}>{success}</div>}

                        {loading ? (
                            <div style={{ padding: "20px 12px", color: "#64748b" }}>Chargement...</div>
                        ) : fields.length === 0 ? (
                            <div style={{ padding: "18px 12px 8px", color: "#64748b" }}>Aucun champ personnalisé configuré.</div>
                        ) : (
                            <div style={{ width: "100%", overflowX: "auto" }}>
                                <table style={{ width: "100%", borderCollapse: "collapse", minWidth: "700px" }}>
                                    <thead>
                                        <tr style={{ background: "#f8fafc" }}>
                                            <th style={tableHeaderStyle}>Ordre</th>
                                            <th style={tableHeaderStyle}>Libellé</th>
                                            <th style={tableHeaderStyle}>Nom technique</th>
                                            <th style={tableHeaderStyle}>Type</th>
                                            <th style={tableHeaderStyle}>Obligatoire</th>
                                            <th style={tableHeaderStyle}>Actif</th>
                                            <th style={tableHeaderStyle}>Actions</th>
                                        </tr>
                                    </thead>
                                    <tbody>
                                        {fields.map((field) => (
                                            <tr key={field.id} style={{ borderTop: "1px solid #edf2f7" }}>
                                                <td style={tableCellStyle}>{field.order_index ?? 0}</td>
                                                <td style={tableCellStyle}>
                                                    <div style={{ fontWeight: 600, color: "#173d57" }}>{field.label}</div>
                                                </td>
                                                <td style={tableCellStyle}>
                                                    <span style={{ fontFamily: "ui-monospace, SFMono-Regular, Menlo, monospace", fontSize: "12px", color: "#52616f", background: "#f1f5f9", padding: "4px 7px", borderRadius: "6px" }}>
                                                        {field.name}
                                                    </span>
                                                </td>
                                                <td style={tableCellStyle}>
                                                    <span style={{ display: "inline-block", padding: "5px 9px", borderRadius: "999px", background: "#eaf4ff", color: "#0d5f9f", fontSize: "12px", fontWeight: 600 }}>
                                                        {getTypeLabel(field.field_type)}
                                                    </span>
                                                </td>
                                                <td style={tableCellStyle}>
                                                    <span style={{ color: field.required ? "#0f766e" : "#64748b", fontWeight: 600 }}>
                                                        {field.required ? "Oui" : "Non"}
                                                    </span>
                                                </td>
                                                <td style={tableCellStyle}>
                                                    <span style={{
                                                        display: "inline-flex",
                                                        alignItems: "center",
                                                        padding: "5px 9px",
                                                        borderRadius: "999px",
                                                        fontSize: "12px",
                                                        fontWeight: 600,
                                                        background: field.active ? "#ecfdf5" : "#f3f4f6",
                                                        color: field.active ? "#166534" : "#475569",
                                                    }}>
                                                        {field.active ? "Actif" : "Inactif"}
                                                    </span>
                                                </td>
                                                <td style={tableCellStyle}>
                                                    <div style={{ display: "flex", gap: "8px", flexWrap: "wrap" }}>
                                                        <button type="button" className="btn-secondary" onClick={() => handleEdit(field)} style={{ padding: "7px 10px", fontSize: "12px" }}>
                                                            Modifier
                                                        </button>
                                                        <button type="button" className="btn-primary" onClick={() => handleToggleActive(field)} style={{ padding: "7px 10px", fontSize: "12px" }}>
                                                            {field.active ? "Désactiver" : "Activer"}
                                                        </button>
                                                        <button type="button" className="btn-secondary" onClick={() => handleDelete(field)} style={{ padding: "7px 10px", fontSize: "12px", borderColor: "#f7c6c6", color: "#b42318" }}>
                                                            Supprimer
                                                        </button>
                                                    </div>
                                                </td>
                                            </tr>
                                        ))}
                                    </tbody>
                                </table>
                            </div>
                        )}
                    </div>
                </div>

                <div className="panel" style={{ padding: "0", overflow: "hidden" }}>
                    <div style={{ padding: "22px 22px 12px" }}>
                        <h3 style={{ margin: 0, color: "#123b59", fontSize: "1.2rem" }}>{editingId ? "Modifier un champ" : "Créer un champ"}</h3>
                        <p style={{ margin: "6px 0 0", color: "#6b7c8d", fontSize: "13px" }}>Définissez les propriétés du champ personnalisé.</p>
                    </div>

                    <form onSubmit={handleSubmit} style={{ display: "grid", gap: "16px", padding: "8px 22px 22px" }}>
                        <div style={{ display: "grid", gap: "14px" }}>
                            <div>
                                <label style={labelStyle}>Nom technique</label>
                                <input type="text" name="name" value={form.name} onChange={handleChange} placeholder="numero_dossier" style={inputStyle} />
                            </div>

                            <div>
                                <label style={labelStyle}>Libellé</label>
                                <input type="text" name="label" value={form.label} onChange={handleChange} placeholder="Numéro du dossier" style={inputStyle} />
                            </div>

                            <div style={{ display: "grid", gridTemplateColumns: "1.3fr 0.7fr", gap: "14px" }}>
                                <div>
                                    <label style={labelStyle}>Type</label>
                                    <select name="field_type" value={form.field_type} onChange={handleChange} style={inputStyle}>
                                        {FIELD_TYPES.map((type) => (
                                            <option key={type.value} value={type.value}>{type.label}</option>
                                        ))}
                                    </select>
                                </div>

                                <div>
                                    <label style={labelStyle}>Ordre</label>
                                    <input type="number" name="order_index" value={form.order_index} onChange={handleChange} min="0" style={inputStyle} />
                                </div>
                            </div>

                            <div>
                                <label style={labelStyle}>Description / aide</label>
                                <textarea name="description" value={form.description} onChange={handleChange} rows="4" placeholder="Information utile pour l'utilisateur" style={{ ...inputStyle, minHeight: "96px", resize: "vertical" }} />
                            </div>

                            <div style={{ display: "grid", gridTemplateColumns: "repeat(2, minmax(0, 1fr))", gap: "12px" }}>
                                <label style={checkRowStyle}>
                                    <input type="checkbox" name="required" checked={form.required} onChange={handleChange} style={{ width: "16px", height: "16px" }} />
                                    <span>
                                        <strong style={{ display: "block", color: "#173d57" }}>Obligatoire</strong>
                                        <small style={{ color: "#64748b" }}>Champ requis</small>
                                    </span>
                                </label>

                                <label style={checkRowStyle}>
                                    <input type="checkbox" name="active" checked={form.active} onChange={handleChange} style={{ width: "16px", height: "16px" }} />
                                    <span>
                                        <strong style={{ display: "block", color: "#173d57" }}>Actif</strong>
                                        <small style={{ color: "#64748b" }}>Visible dans le système</small>
                                    </span>
                                </label>
                            </div>
                        </div>

                        <div style={{ display: "flex", gap: "10px", justifyContent: "flex-end", paddingTop: "8px" }}>
                            <button type="button" className="btn-secondary" onClick={resetForm}>Réinitialiser</button>
                            <button type="submit" className="btn-primary" disabled={saving}>
                                {saving ? "Enregistrement..." : "Enregistrer"}
                            </button>
                        </div>
                    </form>
                </div>
            </div>

            <div className="page-content" style={{ display: "grid", gridTemplateColumns: "1.55fr 1fr", gap: "24px", alignItems: "start", marginTop: "24px" }}>
                <div className="panel" style={{ padding: "0", overflow: "hidden" }}>
                    <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", gap: "16px", padding: "22px 22px 16px", borderBottom: "1px solid #e8edf1" }}>
                        <div>
                            <h3 style={{ margin: 0, color: "#123b59", fontSize: "1.25rem" }}>Natures du document</h3>
                            <p style={{ margin: "6px 0 0", color: "#6b7c8d", fontSize: "13px" }}>Gérez les natures disponibles pour les documents.</p>
                        </div>
                        <button type="button" className="btn-primary" onClick={resetNatureForm} style={{ whiteSpace: "nowrap" }}>
                            + Nouvelle nature
                        </button>
                    </div>

                    <div style={{ padding: "18px 18px 10px" }}>
                        {natureError && <div className="alert alert-error" style={{ marginBottom: "16px" }}>{natureError}</div>}
                        {natureSuccess && <div className="alert alert-success" style={{ marginBottom: "16px" }}>{natureSuccess}</div>}

                        {loadingNatures ? (
                            <div style={{ padding: "20px 12px", color: "#64748b" }}>Chargement...</div>
                        ) : natures.length === 0 ? (
                            <div style={{ padding: "18px 12px 8px", color: "#64748b" }}>Aucune nature configurée.</div>
                        ) : (
                            <div style={{ width: "100%", overflowX: "auto" }}>
                                <table style={{ width: "100%", borderCollapse: "collapse", minWidth: "560px" }}>
                                    <thead>
                                        <tr style={{ background: "#f8fafc" }}>
                                            <th style={tableHeaderStyle}>ID</th>
                                            <th style={tableHeaderStyle}>Libellé</th>
                                            <th style={tableHeaderStyle}>Actions</th>
                                        </tr>
                                    </thead>
                                    <tbody>
                                        {natures.map((nature) => (
                                            <tr key={nature.id} style={{ borderTop: "1px solid #edf2f7" }}>
                                                <td style={tableCellStyle}>{nature.id}</td>
                                                <td style={tableCellStyle}>
                                                    <div style={{ fontWeight: 600, color: "#173d57" }}>{nature.libelle}</div>
                                                </td>
                                                <td style={tableCellStyle}>
                                                    <div style={{ display: "flex", gap: "8px", flexWrap: "wrap" }}>
                                                        <button type="button" className="btn-secondary" onClick={() => handleEditNature(nature)} style={{ padding: "7px 10px", fontSize: "12px" }}>
                                                            Modifier
                                                        </button>
                                                        <button type="button" className="btn-secondary" onClick={() => handleDeleteNature(nature)} style={{ padding: "7px 10px", fontSize: "12px", borderColor: "#f7c6c6", color: "#b42318" }}>
                                                            Supprimer
                                                        </button>
                                                    </div>
                                                </td>
                                            </tr>
                                        ))}
                                    </tbody>
                                </table>
                            </div>
                        )}
                    </div>
                </div>

                <div className="panel" style={{ padding: "0", overflow: "hidden" }}>
                    <div style={{ padding: "22px 22px 12px" }}>
                        <h3 style={{ margin: 0, color: "#123b59", fontSize: "1.2rem" }}>{editingNatureId ? "Modifier une nature" : "Créer une nature"}</h3>
                        <p style={{ margin: "6px 0 0", color: "#6b7c8d", fontSize: "13px" }}>Saisissez le libellé de la nature du document.</p>
                    </div>

                    <form onSubmit={handleNatureSubmit} style={{ display: "grid", gap: "16px", padding: "8px 22px 22px" }}>
                        <div style={{ display: "grid", gap: "14px" }}>
                            <div>
                                <label style={labelStyle}>Libellé</label>
                                <input type="text" name="libelle" value={natureForm.libelle} onChange={handleNatureChange} placeholder="Nature du document" style={inputStyle} />
                            </div>
                        </div>

                        <div style={{ display: "flex", gap: "10px", justifyContent: "flex-end", paddingTop: "8px" }}>
                            <button type="button" className="btn-secondary" onClick={resetNatureForm}>Réinitialiser</button>
                            <button type="submit" className="btn-primary" disabled={savingNature}>
                                {savingNature ? "Enregistrement..." : "Enregistrer"}
                            </button>
                        </div>
                    </form>
                </div>
            </div>
        </div>
    );
}

const tableHeaderStyle = {
    textAlign: "left",
    padding: "12px 12px",
    fontSize: "12px",
    fontWeight: 700,
    color: "#607484",
    letterSpacing: "0.02em",
    textTransform: "uppercase",
};

const tableCellStyle = {
    padding: "14px 12px",
    fontSize: "13px",
    color: "#334155",
    verticalAlign: "middle",
};

const labelStyle = {
    display: "block",
    marginBottom: "8px",
    fontSize: "13px",
    fontWeight: 600,
    color: "#334155",
};

const inputStyle = {
    width: "100%",
    border: "1px solid #dfe7ee",
    borderRadius: "10px",
    background: "#ffffff",
    color: "#1f2937",
    padding: "11px 12px",
    fontSize: "14px",
    boxSizing: "border-box",
    outline: "none",
    transition: "border-color 0.15s ease, box-shadow 0.15s ease",
};

const checkRowStyle = {
    display: "flex",
    alignItems: "center",
    gap: "10px",
    width: "100%",
    minHeight: "72px",
    padding: "10px 12px",
    border: "1px solid #e2e8f0",
    borderRadius: "10px",
    background: "#f8fafc",
    color: "#1f2937",
};