import { useEffect, useState } from "react";
import api from "../api/api";

import {
    getDocuments,
    createDocument,
    updateDocument,
    deleteDocument,
} from "../services/documentService";

import {
    getDocumentFields,
} from "../services/documentFieldService";

import {
    uploadAttachment,
    getAttachments,
    deleteAttachment,
    downloadAttachment,
} from "../services/attachmentService";

import "../styles/documents.css";


const CREATE_NATURE_OPTION = "__create_new_nature__";


export default function Documents() {

    const [documents, setDocuments] = useState([]);

    // ============================================================
    // RECHERCHE AVANCEE
    // ============================================================

    const [search, setSearch] = useState("");
    const [filterType, setFilterType] = useState("");
    const [filterNature, setFilterNature] = useState("");
    const [filterCirconscription, setFilterCirconscription] =
        useState("");
    const [showAdvancedSearch, setShowAdvancedSearch] =
        useState(false);

    const [types, setTypes] = useState([]);
    const [phases, setPhases] = useState([]);
    const [circonscriptions, setCirconscriptions] = useState([]);
    const [customFields, setCustomFields] = useState([]);

    const [loading, setLoading] = useState(true);
    const [saving, setSaving] = useState(false);
    const [uploading, setUploading] = useState(false);

    const [error, setError] = useState("");
    const [success, setSuccess] = useState("");

    const [showForm, setShowForm] = useState(false);
    const [editingId, setEditingId] = useState(null);

    // ============================================================
    // PIECE JOINTE APRES CREATION / MODIFICATION
    // ============================================================

    const [showAttachmentStep, setShowAttachmentStep] =
        useState(false);

    const [createdDocument, setCreatedDocument] =
        useState(null);

    const [selectedFiles, setSelectedFiles] =
        useState([]);

    // ============================================================
    // CONSULTATION DES PIECES JOINTES
    // ============================================================

    const [showAttachments, setShowAttachments] =
        useState(false);

    const [selectedDocumentForAttachments, setSelectedDocumentForAttachments] =
        useState(null);

    const [attachments, setAttachments] = useState([]);

    const [loadingAttachments, setLoadingAttachments] =
        useState(false);

    // ============================================================
    // NOUVELLE PIECE JOINTE DEPUIS LE MODAL
    // ============================================================

    const [attachmentFiles, setAttachmentFiles] =
        useState([]);

    const [addingAttachment, setAddingAttachment] =
        useState(false);

    // ============================================================
    // AJOUT NOUVELLE NATURE
    // ============================================================

    const [showNatureModal, setShowNatureModal] =
        useState(false);

    const [newNatureLabel, setNewNatureLabel] =
        useState("");

    const [creatingNature, setCreatingNature] =
        useState(false);

    // ============================================================
    // FORMULAIRE
    // ============================================================

    const [form, setForm] = useState({
        reference_archive: "",
        nom_document: "",
        date_creation: new Date()
            .toISOString()
            .split("T")[0],

        type_document_id: "",
        phase_id: "",
        circonscription_id: "",

        code_foncier: "",
        numero_ordre: "",
        remarque: "",
    });

    const [customFieldForm, setCustomFieldForm] =
        useState({});

    // ============================================================
    // CHARGEMENT DES DOCUMENTS
    // ============================================================

    const loadDocuments = async () => {

        try {

            setLoading(true);
            setError("");

            const response = await getDocuments();

            setDocuments(
                response.data || response || []
            );

        } catch (err) {

            console.error(
                "Erreur chargement documents :",
                err
            );

            setError(
                err.response?.data?.detail ||
                "Impossible de charger les documents."
            );

        } finally {

            setLoading(false);

        }
    };

    // ============================================================
    // CHARGEMENT DES REFERENCES
    // ============================================================

    const loadReferences = async () => {

        try {

            const [
                typesResponse,
                phasesResponse,
                circoResponse,
                customFieldsResponse,
            ] = await Promise.all([

                api.get("/document-types/"),

                api.get("/phases/"),

                api.get("/circonscriptions/"),

                getDocumentFields(),

            ]);

            setTypes(
                typesResponse.data || []
            );

            setPhases(
                phasesResponse.data || []
            );

            setCirconscriptions(
                circoResponse.data || []
            );

            const normalizedCustomFields =
                Array.isArray(customFieldsResponse?.data)
                    ? customFieldsResponse.data
                    : Array.isArray(customFieldsResponse)
                        ? customFieldsResponse
                        : [];

            setCustomFields(
                normalizedCustomFields
            );

        } catch (err) {

            console.error(
                "Erreur chargement références :",
                err
            );

            setError(
                "Impossible de charger les types, natures ou circonscriptions."
            );

        }
    };

    useEffect(() => {

        loadDocuments();

        loadReferences();

    }, []);

    // ============================================================
    // CHAMPS PERSONNALISES
    // ============================================================

    const activeCustomFields =
        customFields
            .filter(
                (field) => field.active
            )
            .sort((a, b) => {

                if (
                    a.order_index !==
                    b.order_index
                ) {
                    return (
                        (a.order_index ?? 0) -
                        (b.order_index ?? 0)
                    );
                }

                return (
                    (a.id ?? 0) -
                    (b.id ?? 0)
                );

            });

    const editableCustomFields =
        customFields
            .filter((field) => {

                if (field.active) {
                    return true;
                }

                return Object.prototype.hasOwnProperty.call(
                    customFieldForm,
                    field.name
                );

            })
            .sort((a, b) => {

                if (
                    a.order_index !==
                    b.order_index
                ) {
                    return (
                        (a.order_index ?? 0) -
                        (b.order_index ?? 0)
                    );
                }

                return (
                    (a.id ?? 0) -
                    (b.id ?? 0)
                );

            });

    const fieldsForForm =
        editingId
            ? editableCustomFields
            : activeCustomFields;

    const buildCustomFieldsPayload = () => {

        const payload = {};

        for (const field of fieldsForForm) {

            const rawValue =
                customFieldForm[
                    field.name
                ];

            if (field.field_type === "boolean") {

                payload[field.name] =
                    Boolean(rawValue);

                continue;

            }

            if (
                rawValue === undefined ||
                rawValue === null
            ) {

                payload[field.name] = null;

                continue;

            }

            const stringValue =
                String(rawValue).trim();

            if (stringValue === "") {

                payload[field.name] = null;

                continue;

            }

            payload[field.name] =
                stringValue;

        }

        return payload;

    };

    // ============================================================
    // FORMULAIRE
    // ============================================================

    const handleChange = (e) => {

        const {
            name,
            value,
        } = e.target;

        setForm((previous) => ({

            ...previous,

            [name]: value,

        }));

    };

    const handlePhaseChange = (e) => {

        const selectedValue = e.target.value;

        if (selectedValue === CREATE_NATURE_OPTION) {

            setShowNatureModal(true);

            setNewNatureLabel("");

            return;

        }

        setForm((previous) => ({

            ...previous,

            phase_id: selectedValue,

        }));

    };

    const closeNatureModal = () => {

        setShowNatureModal(false);

        setNewNatureLabel("");

    };

    const handleCreateNature = async () => {

        const libelle = newNatureLabel.trim();

        if (!libelle) {

            setError(
                "Le libellé de la nouvelle nature est obligatoire."
            );

            return;

        }

        try {

            setCreatingNature(true);

            setError("");

            const response = await api.post(
                "/phases/",
                {
                    libelle,
                }
            );

            const createdPhase =
                response?.data || response;

            const nextPhases = [
                ...phases,
                createdPhase,
            ].sort((a, b) =>
                (a.libelle || "").localeCompare(
                    b.libelle || "",
                    "fr",
                    {
                        sensitivity: "base",
                    }
                )
            );

            setPhases(nextPhases);

            setForm((previous) => ({

                ...previous,

                phase_id: String(createdPhase.id),

            }));

            closeNatureModal();

            setSuccess(
                "Nouvelle nature ajoutée avec succès."
            );

        } catch (err) {

            console.error(
                "Erreur création nature :",
                err
            );

            setError(
                err.response?.data?.detail ||
                "Impossible de créer la nouvelle nature."
            );

        } finally {

            setCreatingNature(false);

        }

    };

    const handleCustomFieldChange = (
        field,
        event
    ) => {

        const nextValue =
            field.field_type === "boolean"
                ? event.target.checked
                : event.target.value;

        setCustomFieldForm((previous) => ({

            ...previous,

            [field.name]: nextValue,

        }));

    };

    // ============================================================
    // RESET FORMULAIRE
    // ============================================================

    const resetForm = () => {

        const initialCustomValues = {};

        for (const field of activeCustomFields) {

            initialCustomValues[field.name] =
                field.field_type === "boolean"
                    ? false
                    : "";

        }

        setForm({

            reference_archive: "",

            nom_document: "",

            date_creation: new Date()
                .toISOString()
                .split("T")[0],

            type_document_id: "",

            phase_id: "",

            circonscription_id: "",

            code_foncier: "",

            numero_ordre: "",

            remarque: "",

        });

        setCustomFieldForm(
            initialCustomValues
        );

        setEditingId(null);

    };

    // ============================================================
    // OUVRIR CREATION
    // ============================================================

    const openCreateForm = () => {

        resetForm();

        setError("");

        setSuccess("");

        setSelectedFiles([]);

        setCreatedDocument(null);

        setShowAttachmentStep(false);

        setShowForm(true);

    };

    // ============================================================
    // OUVRIR MODIFICATION
    // ============================================================

    const openEditForm = (document) => {

        setError("");

        setSuccess("");

        setEditingId(document.id);

        setForm({

            reference_archive:
                document.reference_archive || "",

            nom_document:
                document.nom_document || "",

            date_creation:
                document.date_creation || "",

            type_document_id:
                document.type_document_id || "",

            phase_id:
                document.phase_id || "",

            circonscription_id:
                document.circonscription_id || "",

            code_foncier:
                document.code_foncier || "",

            numero_ordre:
                document.numero_ordre ?? "",

            remarque:
                document.remarque || "",

        });

        const existingCustomValues =
            document.custom_fields || {};

        const mergedCustomValues = {};

        for (const field of activeCustomFields) {

            const hasExistingValue =
                Object.prototype.hasOwnProperty.call(
                    existingCustomValues,
                    field.name
                );

            if (hasExistingValue) {

                mergedCustomValues[field.name] =
                    existingCustomValues[
                        field.name
                    ];

                continue;

            }

            mergedCustomValues[field.name] =
                field.field_type === "boolean"
                    ? false
                    : "";

        }

        for (const [key, value] of Object.entries(existingCustomValues)) {

            if (!Object.prototype.hasOwnProperty.call(mergedCustomValues, key)) {

                mergedCustomValues[key] = value;

            }

        }

        setCustomFieldForm(
            mergedCustomValues
        );

        setSelectedFiles([]);

        setShowAttachmentStep(false);

        setShowForm(true);

    };

    // ============================================================
    // FICHIER SELECTIONNE APRES CREATION / MODIFICATION
    // ============================================================

    const handleFileChange = (e) => {

        const files =
            Array.from(
                e.target.files || []
            );

        if (files.length === 0) {

            return;

        }

        setSelectedFiles((previous) => {

            const existingKeys =
                new Set(
                    previous.map((file) =>
                        `${file.name}-${file.size}-${file.lastModified}-${file.type}`
                    )
                );

            const uniqueNewFiles =
                files.filter((file) => {

                    const key =
                        `${file.name}-${file.size}-${file.lastModified}-${file.type}`;

                    if (existingKeys.has(key)) {
                        return false;
                    }

                    existingKeys.add(key);

                    return true;

                });

            return [
                ...previous,
                ...uniqueNewFiles,
            ];

        });

        // Permet de re-sélectionner le même fichier plus tard.
        e.target.value = "";

        setError("");

    };

    // ============================================================
    // FICHIER SELECTIONNE DEPUIS LE MODAL PIECES JOINTES
    // ============================================================

    const handleExistingAttachmentFileChange = (e) => {

        const files =
            Array.from(
                e.target.files || []
            );

        if (files.length === 0) {
            return;
        }

        setAttachmentFiles((previous) => {

            const existingKeys =
                new Set(
                    previous.map((file) =>
                        `${file.name}-${file.size}-${file.lastModified}-${file.type}`
                    )
                );

            const uniqueNewFiles =
                files.filter((file) => {

                    const key =
                        `${file.name}-${file.size}-${file.lastModified}-${file.type}`;

                    if (existingKeys.has(key)) {
                        return false;
                    }

                    existingKeys.add(key);

                    return true;

                });

            return [
                ...previous,
                ...uniqueNewFiles,
            ];

        });

        e.target.value = "";

        setError("");

    };

    // ============================================================
    // TERMINER PROCESSUS DOCUMENT + PIECE JOINTE
    // ============================================================

    const finishCreation = async () => {

        setSelectedFiles([]);

        setCreatedDocument(null);

        setShowAttachmentStep(false);

        setShowForm(false);

        resetForm();

        await loadDocuments();

    };

    // ============================================================
    // AJOUTER LA PIECE JOINTE APRES CREATION / MODIFICATION
    // ============================================================

    const handleAttachmentSubmit = async () => {

        if (!createdDocument?.id) {

            setError(
                "Impossible d'identifier le document concerné."
            );

            return;

        }

        if (selectedFiles.length === 0) {

            await finishCreation();

            setSuccess(
                "Document enregistré sans pièce jointe."
            );

            return;

        }

        try {

            setUploading(true);

            setError("");

            for (const file of selectedFiles) {

                await uploadAttachment(
                    createdDocument.id,
                    file
                );

            }

            await finishCreation();

            setSuccess(
                "Document et pièce jointe enregistrés avec succès."
            );

        } catch (err) {

            console.error(
                "Erreur upload pièce jointe :",
                err
            );

            setError(
                err.response?.data?.detail ||
                "Le document a été enregistré, mais la pièce jointe n'a pas pu être enregistrée."
            );

        } finally {

            setUploading(false);

        }

    };

    // ============================================================
    // ENREGISTREMENT
    // ============================================================

    const handleSubmit = async (e) => {

        e.preventDefault();

        setError("");

        setSuccess("");

        if (

            !form.reference_archive.trim() ||

            !form.nom_document.trim() ||

            !form.date_creation ||

            !form.type_document_id ||

            !form.phase_id ||

            !form.circonscription_id

        ) {

            setError(
                "Veuillez remplir tous les champs obligatoires."
            );

            return;

        }

        for (const field of activeCustomFields) {

            if (!field.required) {
                continue;
            }

            if (field.field_type === "boolean") {
                continue;
            }

            const value =
                customFieldForm[
                    field.name
                ];

            if (
                value === undefined ||
                value === null ||
                String(value).trim() === ""
            ) {

                setError(
                    `Le champ personnalisé "${field.label}" est obligatoire.`
                );

                return;

            }

        }

        try {

            setSaving(true);

            const payload = {

                reference_archive:
                    form.reference_archive.trim(),

                nom_document:
                    form.nom_document.trim(),

                date_creation:
                    form.date_creation,

                type_document_id:
                    Number(
                        form.type_document_id
                    ),

                phase_id:
                    Number(
                        form.phase_id
                    ),

                circonscription_id:
                    Number(
                        form.circonscription_id
                    ),

                code_foncier:
                    form.code_foncier.trim() || null,

                numero_ordre:
                    form.numero_ordre.trim() || null,

                remarque:
                    form.remarque.trim() || null,

                custom_fields:
                    buildCustomFieldsPayload(),

            };

            // ====================================================
            // MODIFICATION
            // ====================================================

            if (editingId) {

                const response =
                    await updateDocument(
                        editingId,
                        payload
                    );

                const updatedDocument =
                    response?.data || response;

                const documentForAttachment = {

                    ...payload,

                    ...updatedDocument,

                    id: editingId,

                };

                setCreatedDocument(
                    documentForAttachment
                );

                setSelectedFiles([]);

                setShowForm(false);

                setShowAttachmentStep(true);

                setSuccess(
                    "Document modifié avec succès."
                );

                await loadDocuments();

                return;

            }

            // ====================================================
            // CREATION
            // ====================================================

            const response =
                await createDocument(
                    payload
                );

            const newDocument =
                response?.data || response;

            if (!newDocument?.id) {

                throw new Error(
                    "Le document a été créé mais son identifiant n'a pas été retourné."
                );

            }

            // ====================================================
            // DOCUMENT CREE
            // ====================================================

            setCreatedDocument(
                newDocument
            );

            setSelectedFiles([]);

            setShowForm(false);

            setShowAttachmentStep(true);

            setSuccess(
                "Document créé avec succès."
            );

        } catch (err) {

            console.error(
                "Erreur enregistrement document :",
                err
            );

            setError(
                err.response?.data?.detail ||
                err.message ||
                "Impossible d'enregistrer le document."
            );

        } finally {

            setSaving(false);

        }

    };

    // ============================================================
    // SUPPRESSION DOCUMENT
    // ============================================================

    const handleDelete = async (document) => {

        const confirmed =
            window.confirm(
                `Voulez-vous vraiment supprimer "${document.nom_document}" ?`
            );

        if (!confirmed) {

            return;

        }

        try {

            setError("");

            setSuccess("");

            await deleteDocument(
                document.id
            );

            setSuccess(
                "Document supprimé avec succès."
            );

            await loadDocuments();

        } catch (err) {

            console.error(
                "Erreur suppression document :",
                err
            );

            setError(
                err.response?.data?.detail ||
                "Impossible de supprimer le document."
            );

        }

    };

    // ============================================================
    // HELPERS
    // ============================================================

    const getTypeName = (id) => {

        const item =
            types.find(
                (type) =>
                    type.id === id
            );

        return item?.libelle || "—";

    };

    const getNatureName = (id) => {

        const item =
            phases.find(
                (phase) =>
                    phase.id === id
            );

        return item?.libelle || "—";

    };

    const getCircoName = (id) => {

        const item =
            circonscriptions.find(
                (circo) =>
                    circo.id === id
            );

        return item?.nom || "—";

    };

    // ============================================================
    // RECHERCHE AVANCEE
    // ============================================================

    const filteredDocuments = documents.filter((document) => {

        const searchValue = search
            .trim()
            .toLowerCase();

        // --------------------------------------------------------
        // RECHERCHE GENERALE
        // --------------------------------------------------------

        const matchesSearch =
            !searchValue ||

            (
                document.reference_archive || ""
            )
                .toLowerCase()
                .includes(searchValue) ||

            (
                document.nom_document || ""
            )
                .toLowerCase()
                .includes(searchValue) ||

            (
                document.code_foncier || ""
            )
                .toLowerCase()
                .includes(searchValue) ||

            (
                document.numero_ordre || ""
            )
                .toLowerCase()
                .includes(searchValue);

        // --------------------------------------------------------
        // FILTRE TYPE
        // --------------------------------------------------------

        const matchesType =
            !filterType ||
            String(
                document.type_document_id
            ) === String(filterType);

        // --------------------------------------------------------
        // FILTRE NATURE
        // --------------------------------------------------------

        const matchesNature =
            !filterNature ||
            String(
                document.phase_id
            ) === String(filterNature);

        // --------------------------------------------------------
        // FILTRE CIRCONSCRIPTION
        // --------------------------------------------------------

        const matchesCirconscription =
            !filterCirconscription ||
            String(
                document.circonscription_id
            ) === String(filterCirconscription);

        return (
            matchesSearch &&
            matchesType &&
            matchesNature &&
            matchesCirconscription
        );

    });

    // ============================================================
    // REINITIALISER LA RECHERCHE
    // ============================================================

    const resetSearch = () => {

        setSearch("");

        setFilterType("");

        setFilterNature("");

        setFilterCirconscription("");

    };

    // ============================================================
    // OUVRIR LES PIECES JOINTES
    // ============================================================

    const openAttachments = async (document) => {

        try {

            setError("");

            setSuccess("");

            setSelectedDocumentForAttachments(
                document
            );

            setAttachments([]);

            setAttachmentFiles([]);

            setShowAttachments(true);

            setLoadingAttachments(true);

            const response =
                await getAttachments(
                    document.id
                );

            setAttachments(
                response.data || []
            );

        } catch (err) {

            console.error(
                "Erreur chargement pièces jointes :",
                err
            );

            setShowAttachments(true);

            setError(
                err.response?.data?.detail ||
                "Impossible de charger les pièces jointes."
            );

        } finally {

            setLoadingAttachments(false);

        }

    };

    // ============================================================
    // AJOUTER UNE PIECE JOINTE A UN DOCUMENT EXISTANT
    // ============================================================

    const handleAddExistingAttachment = async () => {

        if (
            !selectedDocumentForAttachments?.id
        ) {

            setError(
                "Impossible d'identifier le document concerné."
            );

            return;

        }

        if (attachmentFiles.length === 0) {

            setError(
                "Veuillez sélectionner un fichier."
            );

            return;

        }

        try {

            setAddingAttachment(true);

            setError("");

            setSuccess("");

            for (const file of attachmentFiles) {

                await uploadAttachment(
                    selectedDocumentForAttachments.id,
                    file
                );

            }

            const response =
                await getAttachments(
                    selectedDocumentForAttachments.id
                );

            setAttachments(
                response.data || []
            );

            setAttachmentFiles([]);

            const input =
                document.getElementById(
                    "existing-attachment-file"
                );

            if (input) {
                input.value = "";
            }

            setSuccess(
                "Pièce jointe ajoutée avec succès."
            );

        } catch (err) {

            console.error(
                "Erreur ajout pièce jointe :",
                err
            );

            setError(
                err.response?.data?.detail ||
                "Impossible d'ajouter la pièce jointe."
            );

        } finally {

            setAddingAttachment(false);

        }

    };

    // ============================================================
    // SUPPRIMER UNE PIECE JOINTE
    // ============================================================

    const handleDeleteAttachment = async (
        attachment
    ) => {

        const confirmed =
            window.confirm(
                `Voulez-vous supprimer la pièce jointe "${attachment.nom_original}" ?`
            );

        if (!confirmed) {

            return;

        }

        try {

            setError("");

            setSuccess("");

            await deleteAttachment(
                attachment.id
            );

            setAttachments(
                (previous) =>
                    previous.filter(
                        (item) =>
                            item.id !== attachment.id
                    )
            );

            setSuccess(
                "Pièce jointe supprimée avec succès."
            );

        } catch (err) {

            console.error(
                "Erreur suppression pièce jointe :",
                err
            );

            setError(
                err.response?.data?.detail ||
                "Impossible de supprimer la pièce jointe."
            );

        }

    };

    // ============================================================
    // OUVRIR UNE PIECE JOINTE
    // ============================================================

    const handleDownloadAttachment = async (
        attachment
    ) => {

        try {

            setError("");

            await downloadAttachment(
                attachment.id
            );

        } catch (err) {

            console.error(
                "Erreur ouverture pièce jointe :",
                err
            );

            setError(
                err.response?.data?.detail ||
                "Impossible d'ouvrir la pièce jointe."
            );

        }

    };

    // ============================================================
    // FERMER MODAL PIECES JOINTES
    // ============================================================

    const closeAttachmentsModal = () => {

        setShowAttachments(false);

        setSelectedDocumentForAttachments(
            null
        );

        setAttachments([]);

        setAttachmentFiles([]);

        setLoadingAttachments(false);

        setAddingAttachment(false);

    };

    // ============================================================
    // AFFICHAGE
    // ============================================================

    return (

        <div className="documents-page">

            {/* ==================================================
                EN-TÊTE
            ================================================== */}

            <div className="documents-header">

                <div>

                    <h1>
                        Documents
                    </h1>

                    <p>
                        Gestion et conservation
                        des archives foncières.
                    </p>

                </div>

                <button
                    className="btn-primary"
                    onClick={openCreateForm}
                >

                    <span>
                        ＋
                    </span>

                    Nouveau document

                </button>

            </div>

            {/* ==================================================
                MESSAGES
            ================================================== */}

            {error && (

                <div className="alert alert-error">
                    {error}
                </div>

            )}

            {success && (

                <div className="alert alert-success">
                    {success}
                </div>

            )}

            {/* ==================================================
                STATISTIQUES
            ================================================== */}

            <div className="document-stats">

                <div className="document-stat-card">

                    <div className="stat-icon">
                        📄
                    </div>

                    <div>

                        <span>
                            Documents actifs
                        </span>

                        <strong>
                            {documents.length}
                        </strong>

                    </div>

                </div>

                <div className="document-stat-card">

                    <div className="stat-icon">
                        📁
                    </div>

                    <div>

                        <span>
                            Types
                        </span>

                        <strong>
                            {types.length}
                        </strong>

                    </div>

                </div>

                <div className="document-stat-card">

                    <div className="stat-icon">
                        🏛️
                    </div>

                    <div>

                        <span>
                            Circonscriptions
                        </span>

                        <strong>
                            {circonscriptions.length}
                        </strong>

                    </div>

                </div>

                <div className="document-stat-card">

                    <div className="stat-icon">
                        📑
                    </div>

                    <div>

                        <span>
                            Natures
                        </span>

                        <strong>
                            {phases.length}
                        </strong>

                    </div>

                </div>

            </div>

            {/* ==================================================
                TABLE
            ================================================== */}

            <div className="documents-card">

                <div className="documents-card-header">

                    <div>

                        <h2>
                            Registre des documents
                        </h2>

                        <span>
                            Liste des documents enregistrés
                        </span>

                    </div>

                    <div className="documents-card-actions">

                        <button
                            type="button"
                            className="btn-refresh"
                            onClick={() =>
                                setShowAdvancedSearch(
                                    !showAdvancedSearch
                                )
                            }
                        >
                            🔎 Recherche
                        </button>

                        <button
                            type="button"
                            className="btn-refresh"
                            onClick={loadDocuments}
                            disabled={loading}
                        >
                            ↻ Actualiser
                        </button>

                    </div>

                </div>

                {/* ==================================================
                    RECHERCHE AVANCEE
                ================================================== */}

                {showAdvancedSearch && (

                    <div className="advanced-search-panel">

                        <div className="advanced-search-grid">

                            {/* RECHERCHE GENERALE */}

                            <div className="form-field search-main-field">

                                <label>
                                    Rechercher
                                </label>

                                <input
                                    type="text"
                                    value={search}
                                    onChange={(e) =>
                                        setSearch(
                                            e.target.value
                                        )
                                    }
                                    placeholder="Référence, document, cote, NumCad/Réf/Indice..."
                                />

                            </div>

                            {/* TYPE */}

                            <div className="form-field">

                                <label>
                                    Type
                                </label>

                                <select
                                    value={filterType}
                                    onChange={(e) =>
                                        setFilterType(
                                            e.target.value
                                        )
                                    }
                                >

                                    <option value="">
                                        Tous les types
                                    </option>

                                    {types.map(
                                        (type) => (

                                            <option
                                                key={
                                                    type.id
                                                }
                                                value={
                                                    type.id
                                                }
                                            >
                                                {
                                                    type.libelle
                                                }
                                            </option>

                                        )
                                    )}

                                </select>

                            </div>

                            {/* NATURE */}

                            <div className="form-field">

                                <label>
                                    Nature
                                </label>

                                <select
                                    value={filterNature}
                                    onChange={(e) =>
                                        setFilterNature(
                                            e.target.value
                                        )
                                    }
                                >

                                    <option value="">
                                        Toutes les natures
                                    </option>

                                    {phases.map(
                                        (phase) => (

                                            <option
                                                key={
                                                    phase.id
                                                }
                                                value={
                                                    phase.id
                                                }
                                            >
                                                {
                                                    phase.libelle
                                                }
                                            </option>

                                        )
                                    )}

                                </select>

                            </div>

                            {/* CIRCONSCRIPTION */}

                            <div className="form-field">

                                <label>
                                    Circonscription
                                </label>

                                <select
                                    value={
                                        filterCirconscription
                                    }
                                    onChange={(e) =>
                                        setFilterCirconscription(
                                            e.target.value
                                        )
                                    }
                                >

                                    <option value="">
                                        Toutes les circonscriptions
                                    </option>

                                    {circonscriptions.map(
                                        (circo) => (

                                            <option
                                                key={
                                                    circo.id
                                                }
                                                value={
                                                    circo.id
                                                }
                                            >
                                                {
                                                    circo.nom
                                                }
                                            </option>

                                        )
                                    )}

                                </select>

                            </div>

                        </div>

                        {/* RESULTATS */}

                        <div className="advanced-search-footer">

                            <span>

                                <strong>
                                    {
                                        filteredDocuments.length
                                    }
                                </strong>

                                {" "}résultat(s) sur{" "}

                                <strong>
                                    {
                                        documents.length
                                    }
                                </strong>

                                {" "}document(s)

                            </span>

                            {(search ||
                                filterType ||
                                filterNature ||
                                filterCirconscription) && (

                                <button
                                    type="button"
                                    className="btn-secondary"
                                    onClick={
                                        resetSearch
                                    }
                                >
                                    Réinitialiser
                                </button>

                            )}

                        </div>

                    </div>

                )}

                {loading ? (

                    <div className="documents-loading">

                        <div className="spinner"></div>

                        <p>
                            Chargement des documents...
                        </p>

                    </div>

                ) : documents.length === 0 ? (

                    <div className="documents-empty">

                        <div className="empty-icon">
                            📂
                        </div>

                        <h3>
                            Aucun document
                        </h3>

                        <p>
                            Aucun document n'est actuellement
                            enregistré dans le SIA.
                        </p>

                        <button
                            className="btn-primary"
                            onClick={openCreateForm}
                        >
                            ＋ Ajouter le premier document
                        </button>

                    </div>

                ) : filteredDocuments.length === 0 ? (

                    <div className="documents-empty">

                        <div className="empty-icon">
                            🔎
                        </div>

                        <h3>
                            Aucun résultat
                        </h3>

                        <p>
                            Aucun document ne correspond
                            aux critères de recherche.
                        </p>

                        <button
                            className="btn-secondary"
                            onClick={resetSearch}
                        >
                            Réinitialiser la recherche
                        </button>

                    </div>

                ) : (

                    <div className="table-wrapper">

                        <table className="documents-table">

                            <thead>

                                <tr>

                                    <th>
                                        Référence
                                    </th>

                                    <th>
                                        Document
                                    </th>

                                    <th>
                                        Type
                                    </th>

                                    <th>
                                        Nature
                                    </th>

                                    <th>
                                        Circonscription
                                    </th>

                                    <th>
                                        Date
                                    </th>

                                    <th>
                                        Actions
                                    </th>

                                </tr>

                            </thead>

                            <tbody>

                                {filteredDocuments.map(
                                    (document) => (

                                        <tr
                                            key={
                                                document.id
                                            }
                                        >

                                            <td>

                                                <span className="reference">

                                                    {
                                                        document.reference_archive
                                                    }

                                                </span>

                                            </td>

                                            <td>

                                                <div className="document-name">

                                                    <strong>

                                                        {
                                                            document.nom_document
                                                        }

                                                    </strong>

                                                    {document.code_foncier && (

                                                        <small>

                                                            Cote :
                                                            {" "}
                                                            {
                                                                document.code_foncier
                                                            }

                                                        </small>

                                                    )}

                                                    {document.numero_ordre && (

                                                        <small>

                                                            NumCad/Réf/Indice :
                                                            {" "}
                                                            {
                                                                document.numero_ordre
                                                            }

                                                        </small>

                                                    )}

                                                </div>

                                            </td>

                                            <td>

                                                <span className="badge badge-blue">

                                                    {
                                                        getTypeName(
                                                            document.type_document_id
                                                        )
                                                    }

                                                </span>

                                            </td>

                                            <td>

                                                <span className="badge badge-green">

                                                    {
                                                        getNatureName(
                                                            document.phase_id
                                                        )
                                                    }

                                                </span>

                                            </td>

                                            <td>

                                                {
                                                    getCircoName(
                                                        document.circonscription_id
                                                    )
                                                }

                                            </td>

                                            <td>

                                                {
                                                    document.date_creation
                                                        ? new Date(
                                                            document.date_creation
                                                        ).toLocaleDateString(
                                                            "fr-FR"
                                                        )
                                                        : "—"
                                                }

                                            </td>

                                            <td>

                                                <div className="action-buttons">

                                                    {/* MODIFIER */}

                                                    <button
                                                        className="btn-action btn-edit"
                                                        title="Modifier"
                                                        onClick={() =>
                                                            openEditForm(
                                                                document
                                                            )
                                                        }
                                                    >
                                                        ✏️
                                                    </button>

                                                    {/* PIECES JOINTES */}

                                                    <button
                                                        className="btn-action"
                                                        title="Pièces jointes"
                                                        onClick={() =>
                                                            openAttachments(
                                                                document
                                                            )
                                                        }
                                                    >
                                                        📎
                                                    </button>

                                                    {/* SUPPRIMER */}

                                                    <button
                                                        className="btn-action btn-delete"
                                                        title="Supprimer"
                                                        onClick={() =>
                                                            handleDelete(
                                                                document
                                                            )
                                                        }
                                                    >
                                                        🗑️
                                                    </button>

                                                </div>

                                            </td>

                                        </tr>

                                    )
                                )}

                            </tbody>

                        </table>

                    </div>

                )}

            </div>

            {/* ==================================================
                MODAL DOCUMENT
            ================================================== */}

            {showForm && (

                <div className="modal-overlay">

                    <div className="document-modal">

                        <div className="modal-header">

                            <div>

                                <h2>

                                    {editingId
                                        ? "Modifier le document"
                                        : "Nouveau document"}

                                </h2>

                                <p>
                                    Renseignez les informations
                                    archivistiques.
                                </p>

                            </div>

                            <button
                                className="modal-close"
                                onClick={() => {

                                    setShowForm(false);

                                    resetForm();

                                }}
                            >
                                ×
                            </button>

                        </div>

                        <form
                            className="document-form"
                            onSubmit={handleSubmit}
                        >

                            <div className="form-grid">

                                {/* REFERENCE */}

                                <div className="form-field">

                                    <label>
                                        Référence archive *
                                    </label>

                                    <input
                                        type="text"
                                        name="reference_archive"
                                        value={
                                            form.reference_archive
                                        }
                                        onChange={
                                            handleChange
                                        }
                                        placeholder="KN-GOM-B2-R2-C100-001"
                                    />

                                </div>

                                {/* NOM */}

                                <div className="form-field">

                                    <label>
                                        Nom du document *
                                    </label>

                                    <input
                                        type="text"
                                        name="nom_document"
                                        value={
                                            form.nom_document
                                        }
                                        onChange={
                                            handleChange
                                        }
                                        placeholder="Titre immobilier Gombe 001"
                                    />

                                </div>

                                {/* DATE */}

                                <div className="form-field">

                                    <label>
                                        Date *
                                    </label>

                                    <input
                                        type="date"
                                        name="date_creation"
                                        value={
                                            form.date_creation
                                        }
                                        onChange={
                                            handleChange
                                        }
                                    />

                                </div>

                                {/* TYPE */}

                                <div className="form-field">

                                    <label>
                                        Type de document *
                                    </label>

                                    <select
                                        name="type_document_id"
                                        value={
                                            form.type_document_id
                                        }
                                        onChange={
                                            handleChange
                                        }
                                    >

                                        <option value="">
                                            Sélectionner
                                        </option>

                                        {types.map(
                                            (type) => (

                                                <option
                                                    key={
                                                        type.id
                                                    }
                                                    value={
                                                        type.id
                                                    }
                                                >

                                                    {
                                                        type.libelle
                                                    }

                                                </option>

                                            )
                                        )}

                                    </select>

                                </div>

                                {/* NATURE */}

                                <div className="form-field">

                                    <label>
                                        Nature du document *
                                    </label>

                                    <select
                                        name="phase_id"
                                        value={
                                            form.phase_id
                                        }
                                        onChange={
                                            handlePhaseChange
                                        }
                                    >

                                        <option value="">
                                            Sélectionner
                                        </option>

                                        {phases.map(
                                            (phase) => (

                                                <option
                                                    key={
                                                        phase.id
                                                    }
                                                    value={
                                                        phase.id
                                                    }
                                                >

                                                    {
                                                        phase.libelle
                                                    }

                                                </option>

                                            )
                                        )}

                                        <option value={CREATE_NATURE_OPTION}>
                                            + Ajouter une nouvelle nature
                                        </option>

                                    </select>

                                </div>

                                {/* CIRCONSCRIPTION */}

                                <div className="form-field">

                                    <label>
                                        Circonscription *
                                    </label>

                                    <select
                                        name="circonscription_id"
                                        value={
                                            form.circonscription_id
                                        }
                                        onChange={
                                            handleChange
                                        }
                                    >

                                        <option value="">
                                            Sélectionner
                                        </option>

                                        {circonscriptions.map(
                                            (circo) => (

                                                <option
                                                    key={
                                                        circo.id
                                                    }
                                                    value={
                                                        circo.id
                                                    }
                                                >

                                                    {
                                                        circo.nom
                                                    }

                                                </option>

                                            )
                                        )}

                                    </select>

                                </div>

                                {/* COTE FONCIER */}

                                <div className="form-field">

                                    <label>
                                        Cote foncier
                                    </label>

                                    <input
                                        type="text"
                                        name="code_foncier"
                                        value={
                                            form.code_foncier
                                        }
                                        onChange={
                                            handleChange
                                        }
                                        placeholder="KN-GOM-B2-R2-C100"
                                    />

                                </div>

                                {/* NUMCAD / REF / INDICE */}

                                <div className="form-field">

                                    <label>
                                        NumCad/Réf/Indice
                                    </label>

                                    <input
                                        type="text"
                                        name="numero_ordre"
                                        value={
                                            form.numero_ordre
                                        }
                                        onChange={
                                            handleChange
                                        }
                                        placeholder="JA/56/GOMBE"
                                    />

                                </div>

                                {fieldsForForm.map((field) => {

                                    const value =
                                        customFieldForm[
                                            field.name
                                        ];

                                    const helpText =
                                        field.description?.trim();

                                    return (

                                        <div
                                            key={field.id}
                                            className="form-field"
                                        >

                                            <label>
                                                {field.label}
                                                {field.required ? " *" : ""}
                                            </label>

                                            {field.field_type === "text" && (
                                                <textarea
                                                    value={
                                                        value ?? ""
                                                    }
                                                    onChange={(event) =>
                                                        handleCustomFieldChange(
                                                            field,
                                                            event
                                                        )
                                                    }
                                                    rows="3"
                                                />
                                            )}

                                            {field.field_type === "string" && (
                                                <input
                                                    type="text"
                                                    value={
                                                        value ?? ""
                                                    }
                                                    onChange={(event) =>
                                                        handleCustomFieldChange(
                                                            field,
                                                            event
                                                        )
                                                    }
                                                />
                                            )}

                                            {field.field_type === "integer" && (
                                                <input
                                                    type="number"
                                                    step="1"
                                                    value={
                                                        value ?? ""
                                                    }
                                                    onChange={(event) =>
                                                        handleCustomFieldChange(
                                                            field,
                                                            event
                                                        )
                                                    }
                                                />
                                            )}

                                            {field.field_type === "decimal" && (
                                                <input
                                                    type="number"
                                                    step="any"
                                                    value={
                                                        value ?? ""
                                                    }
                                                    onChange={(event) =>
                                                        handleCustomFieldChange(
                                                            field,
                                                            event
                                                        )
                                                    }
                                                />
                                            )}

                                            {field.field_type === "date" && (
                                                <input
                                                    type="date"
                                                    value={
                                                        value ?? ""
                                                    }
                                                    onChange={(event) =>
                                                        handleCustomFieldChange(
                                                            field,
                                                            event
                                                        )
                                                    }
                                                />
                                            )}

                                            {field.field_type === "datetime" && (
                                                <input
                                                    type="datetime-local"
                                                    value={
                                                        value ?? ""
                                                    }
                                                    onChange={(event) =>
                                                        handleCustomFieldChange(
                                                            field,
                                                            event
                                                        )
                                                    }
                                                />
                                            )}

                                            {field.field_type === "boolean" && (
                                                <label
                                                    style={{
                                                        display: "inline-flex",
                                                        alignItems: "center",
                                                        gap: "10px",
                                                    }}
                                                >
                                                    <input
                                                        type="checkbox"
                                                        checked={
                                                            Boolean(value)
                                                        }
                                                        onChange={(event) =>
                                                            handleCustomFieldChange(
                                                                field,
                                                                event
                                                            )
                                                        }
                                                    />
                                                    <span>
                                                        Oui / Non
                                                    </span>
                                                </label>
                                            )}

                                            {helpText && (
                                                <small
                                                    style={{
                                                        color: "#64748b",
                                                        marginTop: "6px",
                                                        display: "block",
                                                    }}
                                                >
                                                    {helpText}
                                                </small>
                                            )}

                                        </div>

                                    );

                                })}

                                {/* REMARQUE */}

                                <div className="form-field form-field-full">

                                    <label>
                                        Remarque
                                    </label>

                                    <textarea
                                        name="remarque"
                                        value={
                                            form.remarque
                                        }
                                        onChange={
                                            handleChange
                                        }
                                        rows="4"
                                        placeholder="Observation ou remarque..."
                                    />

                                </div>

                            </div>

                            <div className="modal-footer">

                                <button
                                    type="button"
                                    className="btn-secondary"
                                    onClick={() => {

                                        setShowForm(false);

                                        resetForm();

                                    }}
                                    disabled={
                                        saving
                                    }
                                >
                                    Annuler
                                </button>

                                <button
                                    type="submit"
                                    className="btn-primary"
                                    disabled={
                                        saving
                                    }
                                >

                                    {saving

                                        ? "Enregistrement..."

                                        : editingId

                                            ? "Enregistrer les modifications"

                                            : "Créer le document"

                                    }

                                </button>

                            </div>

                        </form>

                    </div>

                </div>

            )}

            {/* ==================================================
                ETAPE PIECE JOINTE APRES CREATION / MODIFICATION
            ================================================== */}

            {showAttachmentStep && (

                <div className="modal-overlay">

                    <div className="document-modal">

                        <div className="modal-header">

                            <div>

                                <h2>
                                    {editingId
                                        ? "Document modifié avec succès"
                                        : "Document créé avec succès"}
                                </h2>

                                <p>
                                    Voulez-vous ajouter une pièce
                                    jointe à ce document ?
                                </p>

                            </div>

                            <button
                                className="modal-close"
                                onClick={finishCreation}
                                disabled={uploading}
                            >
                                ×
                            </button>

                        </div>

                        <div
                            style={{
                                padding: "24px",
                            }}
                        >

                            <div
                                style={{
                                    marginBottom: "20px",
                                    padding: "16px",
                                    borderRadius: "10px",
                                    background: "#f8fafc",
                                    border: "1px solid #e2e8f0",
                                }}
                            >

                                <strong>
                                    {
                                        createdDocument?.nom_document
                                    }
                                </strong>

                                <div
                                    style={{
                                        marginTop: "6px",
                                        fontSize: "14px",
                                        color: "#64748b",
                                    }}
                                >

                                    Référence :
                                    {" "}
                                    {
                                        createdDocument?.reference_archive
                                    }

                                </div>

                            </div>

                            <div
                                style={{
                                    border: "2px dashed #cbd5e1",
                                    borderRadius: "12px",
                                    padding: "28px",
                                    textAlign: "center",
                                }}
                            >

                                <div
                                    style={{
                                        fontSize: "36px",
                                        marginBottom: "10px",
                                    }}
                                >
                                    📎
                                </div>

                                <h3
                                    style={{
                                        marginBottom: "8px",
                                    }}
                                >
                                    Pièce jointe facultative
                                </h3>

                                <p
                                    style={{
                                        color: "#64748b",
                                        marginBottom: "18px",
                                    }}
                                >
                                    Ajoutez le fichier numérisé
                                    ou tout autre document associé.
                                </p>

                                <input
                                    id="attachment-file"
                                    type="file"
                                    multiple
                                    accept=".pdf,.jpg,.jpeg,.png,.tif,.tiff,.doc,.docx"
                                    onChange={
                                        handleFileChange
                                    }
                                    disabled={
                                        uploading
                                    }
                                    style={{
                                        display: "none",
                                    }}
                                />

                                <label
                                    htmlFor="attachment-file"
                                    className="btn-primary"
                                    style={{
                                        display: "inline-block",
                                        cursor: uploading
                                            ? "not-allowed"
                                            : "pointer",
                                    }}
                                >
                                    Choisir un fichier
                                </label>

                                {selectedFiles.length > 0 && (

                                    <div
                                        style={{
                                            marginTop: "18px",
                                            padding: "12px",
                                            background: "#f1f5f9",
                                            borderRadius: "8px",
                                            textAlign: "left",
                                        }}
                                    >

                                        {selectedFiles.map((file) => (

                                            <div
                                                key={`${file.name}-${file.size}-${file.lastModified}-${file.type}`}
                                                style={{
                                                    marginBottom: "8px",
                                                }}
                                            >

                                                <strong>
                                                    📄 {file.name}
                                                </strong>

                                                <div
                                                    style={{
                                                        marginTop: "4px",
                                                        color: "#64748b",
                                                        fontSize: "13px",
                                                    }}
                                                >

                                                    {(
                                                        file.size /
                                                        1024
                                                    ).toFixed(1)}{" "}
                                                    Ko

                                                </div>

                                            </div>

                                        ))}

                                    </div>

                                )}

                            </div>

                            <div
                                className="modal-footer"
                                style={{
                                    marginTop: "24px",
                                }}
                            >

                                <button
                                    type="button"
                                    className="btn-secondary"
                                    onClick={
                                        finishCreation
                                    }
                                    disabled={
                                        uploading
                                    }
                                >
                                    Passer
                                </button>

                                <button
                                    type="button"
                                    className="btn-primary"
                                    onClick={
                                        handleAttachmentSubmit
                                    }
                                    disabled={
                                        uploading
                                    }
                                >

                                    {uploading

                                        ? "Envoi du fichier..."

                                        : selectedFiles.length > 0

                                            ? "Ajouter et terminer"

                                            : "Terminer sans pièce jointe"

                                    }

                                </button>

                            </div>

                        </div>

                    </div>

                </div>

            )}

            {/* ==================================================
                MODAL AJOUT NATURE
            ================================================== */}

            {showNatureModal && (

                <div className="modal-overlay">

                    <div className="document-modal">

                        <div className="modal-header">

                            <div>

                                <h2>
                                    Nouvelle nature
                                </h2>

                                <p>
                                    Ajouter une nouvelle nature de document.
                                </p>

                            </div>

                            <button
                                className="modal-close"
                                onClick={
                                    closeNatureModal
                                }
                                disabled={
                                    creatingNature
                                }
                            >
                                ×
                            </button>

                        </div>

                        <div
                            style={{
                                padding: "24px",
                            }}
                        >

                            <div className="form-field">

                                <label>
                                    Libellé *
                                </label>

                                <input
                                    type="text"
                                    value={
                                        newNatureLabel
                                    }
                                    onChange={(event) =>
                                        setNewNatureLabel(
                                            event.target.value
                                        )
                                    }
                                    placeholder="Ex: Contrat de concession Ordinaire (RCO)"
                                />

                            </div>

                            <div className="modal-footer">

                                <button
                                    type="button"
                                    className="btn-secondary"
                                    onClick={
                                        closeNatureModal
                                    }
                                    disabled={
                                        creatingNature
                                    }
                                >
                                    Annuler
                                </button>

                                <button
                                    type="button"
                                    className="btn-primary"
                                    onClick={
                                        handleCreateNature
                                    }
                                    disabled={
                                        creatingNature
                                    }
                                >
                                    {creatingNature
                                        ? "Création..."
                                        : "Créer la nature"}
                                </button>

                            </div>

                        </div>

                    </div>

                </div>

            )}

            {/* ==================================================
                MODAL LISTE DES PIECES JOINTES
            ================================================== */}

            {showAttachments && (

                <div className="modal-overlay">

                    <div className="document-modal">

                        <div className="modal-header">

                            <div>

                                <h2>
                                    Pièces jointes
                                </h2>

                                <p>
                                    {
                                        selectedDocumentForAttachments
                                            ?.nom_document
                                    }
                                </p>

                            </div>

                            <button
                                className="modal-close"
                                onClick={
                                    closeAttachmentsModal
                                }
                                disabled={
                                    addingAttachment
                                }
                            >
                                ×
                            </button>

                        </div>

                        <div
                            style={{
                                padding: "24px",
                            }}
                        >

                            {/* INFORMATIONS DOCUMENT */}

                            <div
                                style={{
                                    marginBottom: "20px",
                                    padding: "16px",
                                    borderRadius: "10px",
                                    background: "#f8fafc",
                                    border: "1px solid #e2e8f0",
                                }}
                            >

                                <strong>
                                    {
                                        selectedDocumentForAttachments
                                            ?.nom_document
                                    }
                                </strong>

                                <div
                                    style={{
                                        marginTop: "6px",
                                        fontSize: "14px",
                                        color: "#64748b",
                                    }}
                                >

                                    Référence :
                                    {" "}
                                    {
                                        selectedDocumentForAttachments
                                            ?.reference_archive
                                    }

                                </div>

                            </div>

                            {/* ==================================================
                                AJOUTER UNE NOUVELLE PIECE JOINTE
                            ================================================== */}

                            <div
                                style={{
                                    marginBottom: "22px",
                                    padding: "18px",
                                    borderRadius: "10px",
                                    background: "#f8fafc",
                                    border: "1px solid #e2e8f0",
                                }}
                            >

                                <div
                                    style={{
                                        fontWeight: "600",
                                        marginBottom: "10px",
                                    }}
                                >
                                    Ajouter une pièce jointe
                                </div>

                                <div
                                    style={{
                                        display: "flex",
                                        alignItems: "center",
                                        gap: "10px",
                                        flexWrap: "wrap",
                                    }}
                                >

                                    <input
                                        id="existing-attachment-file"
                                        type="file"
                                        multiple={true}
                                        accept=".pdf,.jpg,.jpeg,.png,.tif,.tiff,.doc,.docx"
                                        onChange={
                                            handleExistingAttachmentFileChange
                                        }
                                        disabled={
                                            addingAttachment
                                        }
                                    />

                                    <button
                                        type="button"
                                        className="btn-primary"
                                        onClick={
                                            handleAddExistingAttachment
                                        }
                                        disabled={
                                            addingAttachment ||
                                            attachmentFiles.length === 0
                                        }
                                    >

                                        {addingAttachment
                                            ? "Ajout..."
                                            : "Ajouter"}

                                    </button>

                                </div>

                                {attachmentFiles.length > 0 && (

                                    <div
                                        style={{
                                            marginTop: "10px",
                                            fontSize: "13px",
                                            color: "#64748b",
                                        }}
                                    >

                                        Fichiers sélectionnés :
                                        {" "}
                                        <strong>
                                            {attachmentFiles.map((file) => file.name).join(", ")}
                                        </strong>

                                    </div>

                                )}

                            </div>

                            {/* ==================================================
                                CHARGEMENT
                            ================================================== */}

                            {loadingAttachments ? (

                                <div
                                    style={{
                                        textAlign: "center",
                                        padding: "30px",
                                    }}
                                >
                                    Chargement des pièces jointes...
                                </div>

                            ) : attachments.length === 0 ? (

                                <div
                                    style={{
                                        textAlign: "center",
                                        padding: "35px",
                                        color: "#64748b",
                                        border: "1px dashed #cbd5e1",
                                        borderRadius: "10px",
                                    }}
                                >

                                    <div
                                        style={{
                                            fontSize: "35px",
                                            marginBottom: "10px",
                                        }}
                                    >
                                        📎
                                    </div>

                                    <strong>
                                        Aucune pièce jointe
                                    </strong>

                                    <p>
                                        Ce document ne possède
                                        actuellement aucune pièce
                                        jointe.
                                    </p>

                                </div>

                            ) : (

                                <div>

                                    {attachments.map(
                                        (attachment) => (

                                            <div
                                                key={
                                                    attachment.id
                                                }
                                                style={{
                                                    display: "flex",
                                                    alignItems: "center",
                                                    justifyContent: "space-between",
                                                    gap: "15px",
                                                    padding: "14px",
                                                    marginBottom: "10px",
                                                    borderRadius: "10px",
                                                    background: "#f8fafc",
                                                    border: "1px solid #e2e8f0",
                                                }}
                                            >

                                                <div
                                                    style={{
                                                        minWidth: 0,
                                                        flex: 1,
                                                    }}
                                                >

                                                    <strong
                                                        style={{
                                                            display: "block",
                                                            overflow: "hidden",
                                                            textOverflow: "ellipsis",
                                                            whiteSpace: "nowrap",
                                                        }}
                                                    >

                                                        📄{" "}
                                                        {
                                                            attachment.nom_original
                                                        }

                                                    </strong>

                                                    <span
                                                        style={{
                                                            display: "block",
                                                            marginTop: "5px",
                                                            fontSize: "13px",
                                                            color: "#64748b",
                                                        }}
                                                    >

                                                        {
                                                            (
                                                                attachment.taille /
                                                                1024
                                                            ).toFixed(1)
                                                        }{" "}
                                                        Ko

                                                        {" • "}

                                                        {
                                                            attachment.type_mime
                                                        }

                                                    </span>

                                                </div>

                                                <div
                                                    style={{
                                                        display: "flex",
                                                        gap: "8px",
                                                    }}
                                                >

                                                    <button
                                                        type="button"
                                                        className="btn-secondary"
                                                        onClick={() =>
                                                            handleDownloadAttachment(
                                                                attachment
                                                            )
                                                        }
                                                    >
                                                        Ouvrir
                                                    </button>

                                                    <button
                                                        type="button"
                                                        className="btn-action btn-delete"
                                                        title="Supprimer"
                                                        onClick={() =>
                                                            handleDeleteAttachment(
                                                                attachment
                                                            )
                                                        }
                                                    >
                                                        🗑️
                                                    </button>

                                                </div>

                                            </div>

                                        )
                                    )}

                                </div>

                            )}

                            {/* BOUTON FERMER */}

                            <div
                                className="modal-footer"
                                style={{
                                    marginTop: "24px",
                                }}
                            >

                                <button
                                    type="button"
                                    className="btn-secondary"
                                    onClick={
                                        closeAttachmentsModal
                                    }
                                    disabled={
                                        addingAttachment
                                    }
                                >
                                    Fermer
                                </button>

                            </div>

                        </div>

                    </div>

                </div>

            )}

        </div>

    );

}