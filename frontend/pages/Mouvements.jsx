import { useEffect, useMemo, useState } from "react";

import api from "../api/api";

import {
    getMovements,
    createMovement,
    returnMovement,
} from "../services/movementService";

import {
    searchDocuments,
} from "../services/documentService";

import "../styles/mouvements.css";


export default function Mouvements() {

    // ============================================================
    // ETATS
    // ============================================================

    const [movements, setMovements] = useState([]);

    const [documents, setDocuments] = useState([]);

    const [loading, setLoading] = useState(true);

    const [saving, setSaving] = useState(false);

    const [error, setError] = useState("");

    const [success, setSuccess] = useState("");

    const [search, setSearch] = useState("");

    const [statusFilter, setStatusFilter] = useState("TOUS");

    const [showModal, setShowModal] = useState(false);

    const [returningId, setReturningId] = useState(null);

    // ============================================================
    // RECHERCHE DOCUMENT + BUREAU DESTINATION (creation mouvement)
    // ============================================================

    const [docSearchTerm, setDocSearchTerm] = useState("");

    const [docSearchResults, setDocSearchResults] = useState([]);

    const [docSearchLoading, setDocSearchLoading] =
        useState(false);

    const [docSearched, setDocSearched] = useState(false);

    const [selectedDocument, setSelectedDocument] =
        useState(null);

    const [bureaux, setBureaux] = useState([]);

    const [bureauxLoading, setBureauxLoading] =
        useState(false);


    const [form, setForm] = useState({
        document_id: "",
        bureau_destination_id: "",
        type_mouvement: "SORTIE",
        motif: "",
    });


    // ============================================================
    // CHARGER LES DOCUMENTS
    // ============================================================

    const loadDocuments = async () => {

        try {

            const response = await api.get(
                "/documents/"
            );

            setDocuments(
                response.data || []
            );

        } catch (err) {

            console.error(
                "Erreur chargement documents :",
                err
            );

        }
    };


    // ============================================================
    // CHARGER LES BUREAUX DE LA CIRCONSCRIPTION
    // (backend : bureaux actifs de la circonscription de l'utilisateur)
    // ============================================================

    const loadBureaux = async () => {

        try {

            setBureauxLoading(true);

            const response = await api.get(
                "/bureaux/"
            );

            setBureaux(
                response.data || []
            );

        } catch (err) {

            console.error(
                "Erreur chargement bureaux :",
                err
            );

        } finally {

            setBureauxLoading(false);

        }
    };


    // ============================================================
    // NOM D'UN BUREAU PAR ID
    // ============================================================

    const getBureauName = (bureauId) => {

        if (!bureauId) {
            return null;
        }

        const bureau = bureaux.find(
            (item) => item.id === bureauId
        );

        return bureau?.nom || `Bureau #${bureauId}`;

    };


    // ============================================================
    // CHARGER LES MOUVEMENTS
    // ============================================================

    const loadMovements = async () => {

        try {

            setLoading(true);

            setError("");

            const response =
                await getMovements();

            setMovements(
                response.data || []
            );

        } catch (err) {

            console.error(
                "Erreur chargement mouvements :",
                err
            );

            setError(
                "Impossible de charger les mouvements."
            );

        } finally {

            setLoading(false);

        }
    };


    // ============================================================
    // CHARGEMENT INITIAL
    // ============================================================

    useEffect(() => {

        loadDocuments();

        loadMovements();

        loadBureaux();

    }, []);


    // ============================================================
    // RECHERCHE DOCUMENT PAR ID
    // ============================================================

    const getDocumentInfo = (documentId) => {

        return documents.find(
            (document) =>
                document.id === documentId
        );

    };


    // ============================================================
    // FORMATAGE DATE
    // ============================================================

    const formatDate = (date) => {

        if (!date) {
            return "—";
        }

        return new Date(
            date
        ).toLocaleString(
            "fr-FR",
            {
                day: "2-digit",
                month: "2-digit",
                year: "numeric",
                hour: "2-digit",
                minute: "2-digit",
            }
        );

    };


    // ============================================================
    // FILTRAGE
    // ============================================================

    const filteredMovements = useMemo(() => {

        const term =
            search
                .trim()
                .toLowerCase();

        return movements.filter(
            (movement) => {

                const document =
                    getDocumentInfo(
                        movement.document_id
                    );

                const reference =
                    document?.reference_archive
                    || "";

                const nomDocument =
                    document?.nom_document
                    || "";

                const motif =
                    movement.motif
                    || "";

                const type =
                    movement.type_mouvement
                    || "";

                const matchesSearch =
                    !term ||
                    reference
                        .toLowerCase()
                        .includes(term) ||
                    nomDocument
                        .toLowerCase()
                        .includes(term) ||
                    motif
                        .toLowerCase()
                        .includes(term) ||
                    type
                        .toLowerCase()
                        .includes(term);

                const matchesStatus =
                    statusFilter === "TOUS" ||
                    movement.statut ===
                        statusFilter;

                return (
                    matchesSearch &&
                    matchesStatus
                );

            }
        );

    }, [
        movements,
        documents,
        search,
        statusFilter,
    ]);


    // ============================================================
    // STATISTIQUES
    // ============================================================

    const totalMovements =
        movements.length;

    const activeMovements =
        movements.filter(
            (movement) =>
                movement.statut ===
                "EN_COURS"
        ).length;

    const returnedMovements =
        movements.filter(
            (movement) =>
                movement.statut ===
                "RETOURNE"
        ).length;


    // ============================================================
    // OUVRIR FORMULAIRE
    // ============================================================

    const openCreateModal = () => {

        setForm({
            document_id: "",
            bureau_destination_id: "",
            type_mouvement: "SORTIE",
            motif: "",
        });

        setDocSearchTerm("");

        setDocSearchResults([]);

        setDocSearchLoading(false);

        setDocSearched(false);

        setSelectedDocument(null);

        setError("");

        setSuccess("");

        setShowModal(true);

    };


    // ============================================================
    // FERMER FORMULAIRE
    // ============================================================

    const closeCreateModal = () => {

        if (saving) {
            return;
        }

        setShowModal(false);

        setDocSearchTerm("");

        setDocSearchResults([]);

        setDocSearched(false);

        setSelectedDocument(null);

    };


    // ============================================================
    // RECHERCHE D'UN DOCUMENT (GET /documents/search)
    // ============================================================

    const handleDocumentSearch = async () => {

        const term = docSearchTerm.trim();

        if (!term) {
            setError(
                "Veuillez saisir une recherche."
            );
            return;
        }

        try {

            setDocSearchLoading(true);

            setError("");

            setDocSearched(false);

            // La recherche porte sur reference_archive,
            // nom_document, code_foncier et numero_ordre
            // (recherche texte partielle cote backend).
            const results = await searchDocuments({
                reference_archive: term,
            });

            let finalResults =
                Array.isArray(results)
                    ? results
                    : [];

            // Si aucun resultat sur la reference, on tente
            // les autres champs texte supportes.
            if (finalResults.length === 0) {
                const byName =
                    await searchDocuments({
                        nom_document: term,
                    });

                finalResults =
                    Array.isArray(byName)
                        ? byName
                        : [];
            }

            if (finalResults.length === 0) {
                const byCode =
                    await searchDocuments({
                        code_foncier: term,
                    });

                finalResults =
                    Array.isArray(byCode)
                        ? byCode
                        : [];
            }

            if (finalResults.length === 0) {
                const byNumero =
                    await searchDocuments({
                        numero_ordre: term,
                    });

                finalResults =
                    Array.isArray(byNumero)
                        ? byNumero
                        : [];
            }

            setDocSearchResults(finalResults);

            setDocSearched(true);

        } catch (err) {

            console.error(
                "Erreur recherche document :",
                err
            );

            setError(
                err?.response?.data?.detail ||
                "Impossible de rechercher le document."
            );

            setDocSearchResults([]);

            setDocSearched(true);

        } finally {

            setDocSearchLoading(false);

        }

    };


    // ============================================================
    // SELECTION D'UN DOCUMENT
    // ============================================================

    const selectDocument = (document) => {

        setSelectedDocument(document);

        setForm(
            (previous) => ({
                ...previous,
                document_id: document.id,
            })
        );

    };


    // ============================================================
    // CHANGER DE DOCUMENT
    // ============================================================

    const clearSelectedDocument = () => {

        setSelectedDocument(null);

        setForm(
            (previous) => ({
                ...previous,
                document_id: "",
                bureau_destination_id: "",
            })
        );

    };


    // ============================================================
    // MODIFICATION FORMULAIRE
    // ============================================================

    const handleChange = (event) => {

        const {
            name,
            value,
        } = event.target;

        setForm(
            (previous) => ({
                ...previous,
                [name]: value,
            })
        );

    };


    // ============================================================
    // CREER UN MOUVEMENT
    // ============================================================

    const handleSubmit = async (event) => {

        event.preventDefault();

        setError("");

        setSuccess("");


        if (!form.document_id) {

            setError(
                "Veuillez sélectionner un document."
            );

            return;

        }


        if (!form.bureau_destination_id) {

            setError(
                "Veuillez sélectionner un bureau destination."
            );

            return;

        }


        try {

            setSaving(true);

            await createMovement({
                document_id:
                    Number(
                        form.document_id
                    ),

                bureau_destination_id:
                    Number(
                        form.bureau_destination_id
                    ),

                type_mouvement:
                    form.type_mouvement,

                motif:
                    form.motif.trim()
                    || null,
            });


            setShowModal(false);

            setForm({
                document_id: "",
                bureau_destination_id: "",
                type_mouvement: "SORTIE",
                motif: "",
            });

            setSelectedDocument(null);

            setDocSearchTerm("");

            setDocSearchResults([]);

            setDocSearched(false);


            await loadMovements();


            setSuccess(
                "Le mouvement a été enregistré avec succès."
            );

        } catch (err) {

            console.error(
                "Erreur création mouvement :",
                err
            );

            const detail =
                err?.response?.data?.detail;

            setError(
                detail ||
                "Impossible d'enregistrer le mouvement."
            );

        } finally {

            setSaving(false);

        }

    };


    // ============================================================
    // ENREGISTRER LE RETOUR
    // ============================================================

    const handleReturn = async (
        movementId
    ) => {

        const confirmed =
            window.confirm(
                "Confirmer le retour de ce document ?"
            );

        if (!confirmed) {
            return;
        }


        try {

            setReturningId(
                movementId
            );

            setError("");

            setSuccess("");


            await returnMovement(
                movementId
            );


            await loadMovements();


            setSuccess(
                "Le retour du document a été enregistré."
            );

        } catch (err) {

            console.error(
                "Erreur retour document :",
                err
            );

            const detail =
                err?.response?.data?.detail;

            setError(
                detail ||
                "Impossible d'enregistrer le retour."
            );

        } finally {

            setReturningId(null);

        }

    };


    // ============================================================
    // AFFICHAGE
    // ============================================================

    return (

        <div className="movements-page">

            {/* =====================================================
                HEADER
            ====================================================== */}

            <div className="movements-header">

                <div>

                    <h1>
                        Mouvements des archives
                    </h1>

                    <p>
                        Gestion des retraits, retours et historique.
                    </p>

                </div>


                <button
                    className="btn-primary"
                    onClick={
                        openCreateModal
                    }
                >
                    + Nouveau mouvement
                </button>

            </div>


            {/* =====================================================
                ALERTES
            ====================================================== */}

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


            {/* =====================================================
                STATISTIQUES
            ====================================================== */}

            <div className="movement-stats">

                <div className="movement-stat-card">

                    <div className="stat-icon">
                        📋
                    </div>

                    <div>

                        <span>
                            Total mouvements
                        </span>

                        <strong>
                            {totalMovements}
                        </strong>

                    </div>

                </div>


                <div className="movement-stat-card">

                    <div className="stat-icon">
                        📤
                    </div>

                    <div>

                        <span>
                            Documents en circulation
                        </span>

                        <strong>
                            {activeMovements}
                        </strong>

                    </div>

                </div>


                <div className="movement-stat-card">

                    <div className="stat-icon">
                        ✅
                    </div>

                    <div>

                        <span>
                            Documents retournés
                        </span>

                        <strong>
                            {returnedMovements}
                        </strong>

                    </div>

                </div>

            </div>


            {/* =====================================================
                FILTRES
            ====================================================== */}

            <div className="movements-filters">

                <div className="search-box">

                    <span>
                        🔎
                    </span>

                    <input
                        type="text"
                        placeholder="Rechercher un document, une référence ou un motif..."
                        value={search}
                        onChange={(event) =>
                            setSearch(
                                event.target.value
                            )
                        }
                    />

                </div>


                <select
                    value={statusFilter}
                    onChange={(event) =>
                        setStatusFilter(
                            event.target.value
                        )
                    }
                >

                    <option value="TOUS">
                        Tous les statuts
                    </option>

                    <option value="EN_COURS">
                        En cours
                    </option>

                    <option value="RETOURNE">
                        Retournés
                    </option>

                </select>


                <button
                    className="btn-refresh"
                    onClick={
                        loadMovements
                    }
                >
                    ↻ Actualiser
                </button>

            </div>


            {/* =====================================================
                TABLEAU
            ====================================================== */}

            <div className="movements-card">

                <div className="movements-card-header">

                    <div>

                        <h2>
                            Registre des mouvements
                        </h2>

                        <span>
                            Historique des mouvements d'archives
                        </span>

                    </div>

                </div>


                {loading ? (

                    <div className="movements-loading">

                        <div className="spinner"></div>

                        <p>
                            Chargement des mouvements...
                        </p>

                    </div>

                ) : filteredMovements.length === 0 ? (

                    <div className="movements-empty">

                        <div className="empty-icon">
                            📋
                        </div>

                        <h3>
                            Aucun mouvement
                        </h3>

                        <p>
                            Aucun mouvement ne correspond aux critères actuels.
                        </p>

                        <button
                            className="btn-primary"
                            onClick={
                                openCreateModal
                            }
                        >
                            + Enregistrer un mouvement
                        </button>

                    </div>

                ) : (

                    <div className="table-wrapper">

                        <table className="movements-table">

                            <thead>

                                <tr>

                                    <th>
                                        Document
                                    </th>

                                    <th>
                                        Mouvement
                                    </th>

                                    <th>
                                        Motif
                                    </th>

                                    <th>
                                        Bureau origine
                                    </th>

                                    <th>
                                        Bureau destination
                                    </th>

                                    <th>
                                        Date sortie
                                    </th>

                                    <th>
                                        Retour
                                    </th>

                                    <th>
                                        Statut
                                    </th>

                                    <th>
                                        Actions
                                    </th>

                                </tr>

                            </thead>


                            <tbody>

                                {filteredMovements.map(
                                    (movement) => {

                                        const document =
                                            getDocumentInfo(
                                                movement.document_id
                                            );


                                        return (

                                            <tr
                                                key={
                                                    movement.id
                                                }
                                            >

                                                <td>

                                                    <div className="movement-document">

                                                        <strong>
                                                            {
                                                                document?.nom_document
                                                                ||
                                                                `Document #${movement.document_id}`
                                                            }
                                                        </strong>

                                                        <small>
                                                            {
                                                                document?.reference_archive
                                                                ||
                                                                `ID ${movement.document_id}`
                                                            }
                                                        </small>

                                                    </div>

                                                </td>


                                                <td>

                                                    <span
                                                        className={
                                                            `movement-type movement-type-${(
                                                                movement.type_mouvement
                                                                || ""
                                                            ).toLowerCase()}`
                                                        }
                                                    >
                                                        {
                                                            movement.type_mouvement
                                                        }
                                                    </span>

                                                </td>


                                                <td>

                                                    <span className="movement-motif">

                                                        {
                                                            movement.motif
                                                            ||
                                                            "—"
                                                        }

                                                    </span>

                                                </td>


                                                <td>

                                                    <span className="movement-user">

                                                        {
                                                            getBureauName(
                                                                movement.bureau_origine_id
                                                            ) || "—"
                                                        }

                                                    </span>

                                                </td>


                                                <td>

                                                    <span className="movement-user">

                                                        {
                                                            movement.bureau_destination_id
                                                                ? getBureauName(
                                                                    movement.bureau_destination_id
                                                                )
                                                                : "Historique"
                                                        }

                                                    </span>

                                                </td>


                                                <td>

                                                    {
                                                        formatDate(
                                                            movement.date_mouvement
                                                        )
                                                    }

                                                </td>


                                                <td>

                                                    {
                                                        formatDate(
                                                            movement.date_retour
                                                        )
                                                    }

                                                </td>


                                                <td>

                                                    <span
                                                        className={
                                                            movement.statut ===
                                                            "EN_COURS"
                                                                ? "status-badge status-active"
                                                                : "status-badge status-returned"
                                                        }
                                                    >
                                                        {
                                                            movement.statut ===
                                                            "EN_COURS"
                                                                ? "En cours"
                                                                : "Retourné"
                                                        }
                                                    </span>

                                                </td>


                                                <td>

                                                    {movement.statut ===
                                                        "EN_COURS" ? (

                                                        <button
                                                            className="btn-return"
                                                            disabled={
                                                                returningId ===
                                                                movement.id
                                                            }
                                                            onClick={() =>
                                                                handleReturn(
                                                                    movement.id
                                                                )
                                                            }
                                                        >

                                                            {returningId ===
                                                            movement.id
                                                                ? "..."
                                                                : "↩ Retour"}

                                                        </button>

                                                    ) : (

                                                        <span className="movement-complete">
                                                            ✓ Terminé
                                                        </span>

                                                    )}

                                                </td>

                                            </tr>

                                        );

                                    }
                                )}

                            </tbody>

                        </table>

                    </div>

                )}

            </div>


            {/* =====================================================
                MODAL NOUVEAU MOUVEMENT
            ====================================================== */}

            {showModal && (

                <div
                    className="modal-overlay"
                    onMouseDown={(event) => {

                        if (
                            event.target ===
                            event.currentTarget
                        ) {

                            closeCreateModal();

                        }

                    }}
                >

                    <div className="movement-modal">

                        <div className="modal-header">

                            <div>

                                <h2>
                                    Nouveau mouvement
                                </h2>

                                <p>
                                    Enregistrer le retrait ou la consultation d'un document.
                                </p>

                            </div>


                            <button
                                className="modal-close"
                                onClick={
                                    closeCreateModal
                                }
                            >
                                ×
                            </button>

                        </div>


                        <form
                            className="movement-form"
                            onSubmit={
                                handleSubmit
                            }
                        >

                            {/* ==================================
                                RECHERCHE DU DOCUMENT
                            ================================== */}

                            <div className="form-field">

                                <label>
                                    Document *
                                </label>

                                <div className="doc-search-row">

                                    <input
                                        type="text"
                                        className="doc-search-input"
                                        placeholder="Référence, nom, code foncier ou n° d'ordre..."
                                        value={
                                            docSearchTerm
                                        }
                                        onChange={(event) =>
                                            setDocSearchTerm(
                                                event.target.value
                                            )
                                        }
                                        onKeyDown={(event) => {
                                            if (
                                                event.key ===
                                                "Enter"
                                            ) {
                                                event.preventDefault();
                                                handleDocumentSearch();
                                            }
                                        }}
                                        disabled={
                                            !!selectedDocument
                                        }
                                    />

                                    <button
                                        type="button"
                                        className="btn-secondary"
                                        onClick={
                                            handleDocumentSearch
                                        }
                                        disabled={
                                            docSearchLoading ||
                                            !!selectedDocument
                                        }
                                    >
                                        {docSearchLoading
                                            ? "..."
                                            : "Rechercher"}
                                    </button>

                                </div>

                            </div>


                            {/* RESULTATS DE RECHERCHE */}

                            {!selectedDocument &&
                                docSearchLoading && (

                                    <div className="doc-search-hint">
                                        Recherche en cours...
                                    </div>

                                )}

                            {!selectedDocument &&
                                !docSearchLoading &&
                                docSearched &&
                                docSearchResults.length ===
                                    0 && (

                                    <div className="doc-search-empty">
                                        Aucun document trouvé.
                                    </div>

                                )}

                            {!selectedDocument &&
                                docSearchResults.length >
                                    0 && (

                                    <div className="doc-search-results">

                                        {docSearchResults.map(
                                            (document) => (

                                                <button
                                                    type="button"
                                                    key={
                                                        document.id
                                                    }
                                                    className="doc-search-result"
                                                    onClick={() =>
                                                        selectDocument(
                                                            document
                                                        )
                                                    }
                                                >

                                                    <strong>
                                                        {
                                                            document.reference_archive
                                                        }
                                                    </strong>

                                                    <span>
                                                        {
                                                            document.nom_document
                                                        }
                                                    </span>

                                                    <small>
                                                        {document.code_foncier
                                                            ? `Code: ${document.code_foncier}`
                                                            : ""}
                                                        {document.code_foncier &&
                                                        document.numero_ordre
                                                            ? " — "
                                                            : ""}
                                                        {document.numero_ordre
                                                            ? `N°: ${document.numero_ordre}`
                                                            : ""}
                                                    </small>

                                                </button>

                                            )
                                        )}

                                    </div>

                                )}


                            {/* DOCUMENT SELECTIONNE */}

                            {selectedDocument && (

                                <div className="doc-selected">

                                    <div className="doc-selected-info">

                                        <strong>
                                            {
                                                selectedDocument.reference_archive
                                            }
                                        </strong>

                                        <span>
                                            {
                                                selectedDocument.nom_document
                                            }
                                        </span>

                                        {selectedDocument.code_foncier && (

                                            <small>
                                                Code foncier: {
                                                    selectedDocument.code_foncier
                                                }
                                            </small>

                                        )}

                                        {selectedDocument.numero_ordre && (

                                            <small>
                                                N° d'ordre: {
                                                    selectedDocument.numero_ordre
                                                }
                                            </small>

                                        )}

                                        {getBureauName(
                                            selectedDocument.bureau_id
                                        ) && (

                                            <small>
                                                Bureau origine: {
                                                    getBureauName(
                                                        selectedDocument.bureau_id
                                                    )
                                                }
                                            </small>

                                        )}

                                    </div>

                                    <button
                                        type="button"
                                        className="btn-secondary"
                                        onClick={
                                            clearSelectedDocument
                                        }
                                    >
                                        Changer de document
                                    </button>

                                </div>

                            )}


                            {/* BUREAU DESTINATION */}

                            {selectedDocument && (

                                <div className="form-field">

                                    <label>
                                        Bureau destination *
                                    </label>

                                    {bureauxLoading ? (

                                        <div className="doc-search-hint">
                                            Chargement des bureaux...
                                        </div>

                                    ) : (() => {

                                        const availableBureaux =
                                            bureaux.filter(
                                                (bureau) =>
                                                    bureau.id !==
                                                    selectedDocument.bureau_id
                                            );

                                        if (
                                            availableBureaux.length ===
                                            0
                                        ) {

                                            return (

                                                <div className="doc-search-empty">
                                                    Aucun autre bureau disponible dans votre circonscription.
                                                </div>

                                            );

                                        }

                                        return (

                                            <select
                                                name="bureau_destination_id"
                                                value={
                                                    form.bureau_destination_id
                                                }
                                                onChange={
                                                    handleChange
                                                }
                                                required
                                            >

                                                <option value="">
                                                    Sélectionner un bureau destination
                                                </option>

                                                {availableBureaux.map(
                                                    (bureau) => (

                                                        <option
                                                            key={
                                                                bureau.id
                                                            }
                                                            value={
                                                                bureau.id
                                                            }
                                                        >
                                                            {
                                                                bureau.nom
                                                            }
                                                        </option>

                                                    )
                                                )}

                                            </select>

                                        );

                                    })()}

                                </div>

                            )}


                            <div className="form-field">

                                <label>
                                    Type de mouvement *
                                </label>

                                <select
                                    name="type_mouvement"
                                    value={
                                        form.type_mouvement
                                    }
                                    onChange={
                                        handleChange
                                    }
                                    required
                                >

                                    <option value="SORTIE">
                                        Sortie
                                    </option>

                                    <option value="CONSULTATION">
                                        Consultation
                                    </option>

                                </select>

                            </div>


                            <div className="form-field">

                                <label>
                                    Motif
                                </label>

                                <textarea
                                    name="motif"
                                    rows="4"
                                    placeholder="Ex. Consultation du dossier, demande administrative..."
                                    value={
                                        form.motif
                                    }
                                    onChange={
                                        handleChange
                                    }
                                />

                            </div>


                            <div className="modal-footer">

                                <button
                                    type="button"
                                    className="btn-secondary"
                                    onClick={
                                        closeCreateModal
                                    }
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
                                        : "Enregistrer le mouvement"}

                                </button>

                            </div>

                        </form>

                    </div>

                </div>

            )}

        </div>

    );

}