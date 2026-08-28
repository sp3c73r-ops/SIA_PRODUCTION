import { useEffect, useMemo, useState } from "react";

import api from "../api/api";

import "../styles/piecesJointe.css";


export default function PiecesJointes() {

    const [attachments, setAttachments] = useState([]);
    const [documents, setDocuments] = useState([]);

    const [loading, setLoading] = useState(true);

    const [error, setError] = useState("");
    const [success, setSuccess] = useState("");

    const [search, setSearch] = useState("");
    const [typeFilter, setTypeFilter] = useState("TOUS");

    const [deletingId, setDeletingId] = useState(null);


    // ============================================================
    // CHARGER LES PIECES JOINTES
    // ============================================================

    const loadAttachments = async () => {

        try {

            setLoading(true);
            setError("");

            const response = await api.get(
                "/documents/attachments/all"
            );

            setAttachments(
                response.data || []
            );

        } catch (err) {

            console.error(
                "Erreur chargement pièces jointes :",
                err
            );

            setError(
                "Impossible de charger les pièces jointes."
            );

        } finally {

            setLoading(false);

        }

    };


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
    // CHARGEMENT INITIAL
    // ============================================================

    useEffect(() => {

        loadAttachments();
        loadDocuments();

    }, []);


    // ============================================================
    // DOCUMENT ASSOCIE
    // ============================================================

    const getDocument = (documentId) => {

        return documents.find(
            (document) =>
                document.id === documentId
        );

    };


    // ============================================================
    // FORMATAGE TAILLE
    // ============================================================

    const formatSize = (bytes) => {

        if (!bytes || bytes <= 0) {
            return "0 Ko";
        }

        if (bytes < 1024) {
            return `${bytes} octets`;
        }

        if (bytes < 1024 * 1024) {

            return `${(
                bytes / 1024
            ).toFixed(1)} Ko`;

        }

        if (bytes < 1024 * 1024 * 1024) {

            return `${(
                bytes /
                (1024 * 1024)
            ).toFixed(1)} Mo`;

        }

        return `${(
            bytes /
            (1024 * 1024 * 1024)
        ).toFixed(1)} Go`;

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
    // TYPE DE FICHIER
    // ============================================================

    const getFileCategory = (mime) => {

        if (!mime) {
            return "AUTRE";
        }

        if (
            mime === "application/pdf"
        ) {
            return "PDF";
        }

        if (
            mime.startsWith("image/")
        ) {
            return "IMAGE";
        }

        if (
            mime.includes("word") ||
            mime.includes("document")
        ) {
            return "WORD";
        }

        if (
            mime.includes("excel") ||
            mime.includes("spreadsheet")
        ) {
            return "EXCEL";
        }

        return "AUTRE";

    };


    // ============================================================
    // ICONE
    // ============================================================

    const getFileIcon = (mime) => {

        const category =
            getFileCategory(mime);

        switch (category) {

            case "PDF":
                return "📕";

            case "IMAGE":
                return "🖼️";

            case "WORD":
                return "📘";

            case "EXCEL":
                return "📗";

            default:
                return "📎";

        }

    };


    // ============================================================
    // FILTRAGE
    // ============================================================

    const filteredAttachments = useMemo(() => {

        const term =
            search
                .trim()
                .toLowerCase();

        return attachments.filter(
            (attachment) => {

                const document =
                    getDocument(
                        attachment.document_id
                    );

                const fileName =
                    attachment.nom_original
                    || "";

                const reference =
                    document?.reference_archive
                    || "";

                const documentName =
                    document?.nom_document
                    || "";

                const category =
                    getFileCategory(
                        attachment.type_mime
                    );


                const matchesSearch =
                    !term ||
                    fileName
                        .toLowerCase()
                        .includes(term) ||
                    reference
                        .toLowerCase()
                        .includes(term) ||
                    documentName
                        .toLowerCase()
                        .includes(term);


                const matchesType =
                    typeFilter === "TOUS" ||
                    category === typeFilter;


                return (
                    matchesSearch &&
                    matchesType
                );

            }
        );

    }, [
        attachments,
        documents,
        search,
        typeFilter,
    ]);


    // ============================================================
    // STATISTIQUES
    // ============================================================

    const totalAttachments =
        attachments.length;

    const totalPdf =
        attachments.filter(
            (attachment) =>
                getFileCategory(
                    attachment.type_mime
                ) === "PDF"
        ).length;

    const totalImages =
        attachments.filter(
            (attachment) =>
                getFileCategory(
                    attachment.type_mime
                ) === "IMAGE"
        ).length;

    const totalSize =
        attachments.reduce(
            (total, attachment) =>
                total +
                (
                    attachment.taille || 0
                ),
            0
        );


    // ============================================================
    // OUVRIR / TELECHARGER
    // ============================================================

    const handleOpen = async (
        attachment
    ) => {

        try {

            const response =
                await api.get(
                    `/documents/attachments/${attachment.id}/download`,
                    {
                        responseType: "blob",
                    }
                );


            const blob =
                new Blob(
                    [response.data],
                    {
                        type:
                            attachment.type_mime ||
                            "application/octet-stream",
                    }
                );


            const url =
                window.URL.createObjectURL(
                    blob
                );


            window.open(
                url,
                "_blank",
                "noopener,noreferrer"
            );


            setTimeout(() => {

                window.URL.revokeObjectURL(
                    url
                );

            }, 60000);

        } catch (err) {

            console.error(
                "Erreur ouverture fichier :",
                err
            );

            setError(
                "Impossible d'ouvrir cette pièce jointe."
            );

        }

    };


    // ============================================================
    // SUPPRIMER
    // ============================================================

    const handleDelete = async (
        attachment
    ) => {

        const confirmed =
            window.confirm(
                `Supprimer la pièce jointe "${attachment.nom_original}" ?`
            );

        if (!confirmed) {
            return;
        }


        try {

            setDeletingId(
                attachment.id
            );

            setError("");
            setSuccess("");


            await api.delete(
                `/documents/attachments/${attachment.id}`
            );


            setAttachments(
                (previous) =>
                    previous.filter(
                        (item) =>
                            item.id !==
                            attachment.id
                    )
            );


            setSuccess(
                "Pièce jointe supprimée avec succès."
            );

        } catch (err) {

            console.error(
                "Erreur suppression :",
                err
            );

            const detail =
                err?.response?.data?.detail;

            setError(
                detail ||
                "Impossible de supprimer la pièce jointe."
            );

        } finally {

            setDeletingId(null);

        }

    };


    // ============================================================
    // AFFICHAGE
    // ============================================================

    return (

        <div className="attachments-page">

            {/* ====================================================
                HEADER
            ===================================================== */}

            <div className="attachments-header">

                <div>

                    <h1>
                        Pièces jointes
                    </h1>

                    <p>
                        Gestion globale des fichiers associés aux documents.
                    </p>

                </div>

                <button
                    className="btn-refresh"
                    onClick={() => {

                        loadAttachments();
                        loadDocuments();

                    }}
                >
                    ↻ Actualiser
                </button>

            </div>


            {/* ====================================================
                ALERTES
            ===================================================== */}

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


            {/* ====================================================
                STATISTIQUES
            ===================================================== */}

            <div className="attachment-stats">

                <div className="attachment-stat-card">

                    <div className="stat-icon">
                        📎
                    </div>

                    <div>

                        <span>
                            Total pièces jointes
                        </span>

                        <strong>
                            {totalAttachments}
                        </strong>

                    </div>

                </div>


                <div className="attachment-stat-card">

                    <div className="stat-icon">
                        📕
                    </div>

                    <div>

                        <span>
                            Fichiers PDF
                        </span>

                        <strong>
                            {totalPdf}
                        </strong>

                    </div>

                </div>


                <div className="attachment-stat-card">

                    <div className="stat-icon">
                        🖼️
                    </div>

                    <div>

                        <span>
                            Images
                        </span>

                        <strong>
                            {totalImages}
                        </strong>

                    </div>

                </div>


                <div className="attachment-stat-card">

                    <div className="stat-icon">
                        💾
                    </div>

                    <div>

                        <span>
                            Volume total
                        </span>

                        <strong>
                            {formatSize(
                                totalSize
                            )}
                        </strong>

                    </div>

                </div>

            </div>


            {/* ====================================================
                FILTRES
            ===================================================== */}

            <div className="attachments-filters">

                <div className="attachment-search">

                    <span>
                        🔎
                    </span>

                    <input
                        type="text"
                        placeholder="Rechercher un fichier, document ou référence..."
                        value={search}
                        onChange={(event) =>
                            setSearch(
                                event.target.value
                            )
                        }
                    />

                </div>


                <select
                    value={typeFilter}
                    onChange={(event) =>
                        setTypeFilter(
                            event.target.value
                        )
                    }
                >

                    <option value="TOUS">
                        Tous les fichiers
                    </option>

                    <option value="PDF">
                        PDF
                    </option>

                    <option value="IMAGE">
                        Images
                    </option>

                    <option value="WORD">
                        Word
                    </option>

                    <option value="EXCEL">
                        Excel
                    </option>

                    <option value="AUTRE">
                        Autres
                    </option>

                </select>

            </div>


            {/* ====================================================
                REGISTRE
            ===================================================== */}

            <div className="attachments-card">

                <div className="attachments-card-header">

                    <div>

                        <h2>
                            Registre des pièces jointes
                        </h2>

                        <span>
                            {filteredAttachments.length}
                            {" "}
                            fichier(s) affiché(s)
                        </span>

                    </div>

                </div>


                {loading ? (

                    <div className="attachments-loading">

                        <div className="spinner"></div>

                        <p>
                            Chargement des pièces jointes...
                        </p>

                    </div>

                ) : filteredAttachments.length === 0 ? (

                    <div className="attachments-empty">

                        <div className="empty-icon">
                            📎
                        </div>

                        <h3>
                            Aucune pièce jointe
                        </h3>

                        <p>
                            Aucun fichier ne correspond aux critères actuels.
                        </p>

                    </div>

                ) : (

                    <div className="table-wrapper">

                        <table className="attachments-table">

                            <thead>

                                <tr>

                                    <th>
                                        Fichier
                                    </th>

                                    <th>
                                        Document
                                    </th>

                                    <th>
                                        Référence
                                    </th>

                                    <th>
                                        Type
                                    </th>

                                    <th>
                                        Taille
                                    </th>

                                    <th>
                                        Ajouté le
                                    </th>

                                    <th>
                                        Actions
                                    </th>

                                </tr>

                            </thead>


                            <tbody>

                                {filteredAttachments.map(
                                    (attachment) => {

                                        const document =
                                            getDocument(
                                                attachment.document_id
                                            );

                                        const category =
                                            getFileCategory(
                                                attachment.type_mime
                                            );


                                        return (

                                            <tr
                                                key={
                                                    attachment.id
                                                }
                                            >

                                                <td>

                                                    <div className="attachment-file">

                                                        <div className="file-icon">

                                                            {
                                                                getFileIcon(
                                                                    attachment.type_mime
                                                                )
                                                            }

                                                        </div>

                                                        <div>

                                                            <strong>
                                                                {
                                                                    attachment.nom_original
                                                                }
                                                            </strong>

                                                            <small>
                                                                {
                                                                    attachment.nom_stockage
                                                                }
                                                            </small>

                                                        </div>

                                                    </div>

                                                </td>


                                                <td>

                                                    <div className="attachment-document">

                                                        <strong>
                                                            {
                                                                document?.nom_document
                                                                ||
                                                                `Document #${attachment.document_id}`
                                                            }
                                                        </strong>

                                                        <small>
                                                            ID {
                                                                attachment.document_id
                                                            }
                                                        </small>

                                                    </div>

                                                </td>


                                                <td>

                                                    <span className="attachment-reference">

                                                        {
                                                            document?.reference_archive
                                                            ||
                                                            "—"
                                                        }

                                                    </span>

                                                </td>


                                                <td>

                                                    <span
                                                        className={
                                                            `file-type-badge file-type-${category.toLowerCase()}`
                                                        }
                                                    >
                                                        {
                                                            category
                                                        }
                                                    </span>

                                                </td>


                                                <td>

                                                    {
                                                        formatSize(
                                                            attachment.taille
                                                        )
                                                    }

                                                </td>


                                                <td>

                                                    {
                                                        formatDate(
                                                            attachment.created_at
                                                        )
                                                    }

                                                </td>


                                                <td>

                                                    <div className="attachment-actions">

                                                        <button
                                                            className="btn-attachment-open"
                                                            onClick={() =>
                                                                handleOpen(
                                                                    attachment
                                                                )
                                                            }
                                                            title="Ouvrir"
                                                        >
                                                            👁
                                                        </button>


                                                        <button
                                                            className="btn-attachment-delete"
                                                            disabled={
                                                                deletingId ===
                                                                attachment.id
                                                            }
                                                            onClick={() =>
                                                                handleDelete(
                                                                    attachment
                                                                )
                                                            }
                                                            title="Supprimer"
                                                        >
                                                            {
                                                                deletingId ===
                                                                attachment.id
                                                                    ? "..."
                                                                    : "🗑"
                                                            }
                                                        </button>

                                                    </div>

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

        </div>

    );

}