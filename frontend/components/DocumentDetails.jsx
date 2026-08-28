import { useEffect, useState } from "react";

import api from "../api/api";

import "../styles/documentDetails.css";


export default function DocumentDetails({
    document,
    onClose,
}) {

    // ============================================================
    // ETAT
    // ============================================================

    const [attachments, setAttachments] = useState([]);

    const [loadingAttachments, setLoadingAttachments] =
        useState(false);

    const [downloadingId, setDownloadingId] =
        useState(null);

    const [error, setError] =
        useState("");


    // ============================================================
    // CHARGER LES PIECES JOINTES
    // ============================================================

    const loadAttachments = async () => {

        if (!document?.id) {
            return;
        }

        try {

            setLoadingAttachments(true);

            setError("");

            const response = await api.get(
                `/documents/${document.id}/attachments`
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

            setLoadingAttachments(false);

        }

    };


    // ============================================================
    // CHARGEMENT AUTOMATIQUE
    // ============================================================

    useEffect(() => {

        loadAttachments();

    }, [document?.id]);


    // ============================================================
    // TELECHARGER / OUVRIR UNE PIECE JOINTE
    // ============================================================

   const handleDownload = async (attachment) => {
    try {
        setDownloadingId(attachment.id);
        setError("");

        console.log(
            "Téléchargement de la pièce jointe :",
            attachment
        );

        const response = await api.get(
            `/documents/attachments/${attachment.id}/download`,
            {
                responseType: "blob",
            }
        );

        console.log(
            "Réponse téléchargement :",
            response.status,
            response.headers
        );

        // ========================================================
        // Vérification du contenu reçu
        // ========================================================

        const contentType =
            response.headers["content-type"] ||
            attachment.type_mime ||
            "application/octet-stream";

        // ========================================================
        // Création du Blob
        // ========================================================

        const blob = new Blob(
            [response.data],
            {
                type: contentType,
            }
        );

        // ========================================================
        // Création de l'URL temporaire
        // ========================================================

        const fileUrl =
            window.URL.createObjectURL(blob);

        // ========================================================
        // OUVERTURE DU FICHIER
        // ========================================================

        window.open(
            fileUrl,
            "_blank",
            "noopener,noreferrer"
        );

        // ========================================================
        // Nettoyage différé
        // ========================================================

        setTimeout(() => {
            window.URL.revokeObjectURL(fileUrl);
        }, 60000);

    } catch (err) {

        console.error(
            "ERREUR TELECHARGEMENT :",
            err
        );

        // ========================================================
        // Afficher l'erreur réelle du backend
        // ========================================================

        if (err.response) {

            console.error(
                "Status :",
                err.response.status
            );

            console.error(
                "Headers :",
                err.response.headers
            );

            // Avec responseType blob, FastAPI peut renvoyer
            // une erreur JSON sous forme de Blob.
            if (
                err.response.data instanceof Blob
            ) {

                try {

                    const errorText =
                        await err.response.data.text();

                    console.error(
                        "Réponse backend :",
                        errorText
                    );

                } catch (blobError) {

                    console.error(
                        "Impossible de lire l'erreur Blob :",
                        blobError
                    );

                }

            }

        }

        setError(
            "Impossible de télécharger la pièce jointe."
        );

    } finally {

        setDownloadingId(null);

    }
};


    // ============================================================
    // FORMAT TAILLE
    // ============================================================

    const formatSize = (
        size
    ) => {

        if (!size) {
            return "0 Ko";
        }

        if (size < 1024) {

            return `${size} octets`;

        }

        if (size < 1024 * 1024) {

            return `${(
                size / 1024
            ).toFixed(1)} Ko`;

        }

        return `${(
            size /
            (1024 * 1024)
        ).toFixed(1)} Mo`;

    };


    // ============================================================
    // FORMAT DATE
    // ============================================================

    const formatDate = (
        value
    ) => {

        if (!value) {
            return "—";
        }

        const date =
            new Date(value);

        if (
            Number.isNaN(
                date.getTime()
            )
        ) {
            return value;
        }

        return date.toLocaleDateString(
            "fr-FR"
        );

    };


    // ============================================================
    // FERMETURE
    // ============================================================

    const handleOverlayClick = (
        event
    ) => {

        if (
            event.target ===
            event.currentTarget
        ) {

            onClose();

        }

    };


    // ============================================================
    // AFFICHAGE
    // ============================================================

    if (!document) {
        return null;
    }


    return (

        <div
            className="modal-overlay"
            onClick={
                handleOverlayClick
            }
        >

            <div className="document-details-modal">


                {/* ==================================================
                    HEADER
                ================================================== */}

                <div className="document-details-header">

                    <div>

                        <h2>
                            Fiche du document
                        </h2>

                        <p>
                            Consultation des informations archivistiques
                        </p>

                    </div>


                    <button
                        type="button"
                        className="document-details-close"
                        onClick={
                            onClose
                        }
                    >
                        ×
                    </button>

                </div>


                {/* ==================================================
                    CONTENU
                ================================================== */}

                <div className="document-details-body">


                    {/* ==================================================
                        IDENTIFICATION
                    ================================================== */}

                    <div className="document-details-title">

                        <div>

                            <span>
                                Référence archive
                            </span>

                            <strong>
                                {
                                    document.reference_archive ||
                                    "—"
                                }
                            </strong>

                        </div>


                        <div>

                            <span>
                                Document
                            </span>

                            <strong>
                                {
                                    document.nom_document ||
                                    "—"
                                }
                            </strong>

                        </div>

                    </div>


                    {/* ==================================================
                        INFORMATIONS
                    ================================================== */}

                    <div className="document-details-grid">


                        <div className="document-detail-item">

                            <span>
                                Type de document
                            </span>

                            <strong>
                                {
                                    document.type_document ||
                                    "—"
                                }
                            </strong>

                        </div>


                        <div className="document-detail-item">

                            <span>
                                Nature
                            </span>

                            <strong>
                                {
                                    document.phase ||
                                    "—"
                                }
                            </strong>

                        </div>


                        <div className="document-detail-item">

                            <span>
                                Circonscription
                            </span>

                            <strong>
                                {
                                    document.circonscription ||
                                    "—"
                                }
                            </strong>

                        </div>


                        <div className="document-detail-item">

                            <span>
                                Date du document
                            </span>

                            <strong>
                                {
                                    formatDate(
                                        document.date_creation
                                    )
                                }
                            </strong>

                        </div>


                        <div className="document-detail-item">

                            <span>
                                Cote foncier
                            </span>

                            <strong>
                                {
                                    document.code_foncier ||
                                    "—"
                                }
                            </strong>

                        </div>


                        <div className="document-detail-item">

                            <span>
                                NumCad / Réf / Indice
                            </span>

                            <strong>
                                {
                                    document.numero_ordre ||
                                    "—"
                                }
                            </strong>

                        </div>

                    </div>


                    {/* ==================================================
                        REMARQUE
                    ================================================== */}

                    <div className="document-details-section">

                        <h3>
                            Remarque
                        </h3>

                        <div className="document-remarque">

                            {
                                document.remarque ||
                                "Aucune remarque."
                            }

                        </div>

                    </div>


                    {/* ==================================================
                        PIECES JOINTES
                    ================================================== */}

                    <div className="document-details-section">

                        <div className="attachments-title">

                            <div>

                                <h3>
                                    Pièces jointes
                                </h3>

                                <p>
                                    Documents associés à cette archive
                                </p>

                            </div>


                            <span className="attachments-count">

                                {
                                    attachments.length
                                }

                            </span>

                        </div>


                        {/* ERREUR */}

                        {error && (

                            <div className="attachments-error">

                                {error}

                            </div>

                        )}


                        {/* CHARGEMENT */}

                        {loadingAttachments ? (

                            <div className="attachments-loading">

                                Chargement des pièces jointes...

                            </div>

                        ) : attachments.length === 0 ? (

                            <div className="attachments-empty">

                                <span>
                                    📎
                                </span>

                                <p>
                                    Aucune pièce jointe pour ce document.
                                </p>

                            </div>

                        ) : (

                            <div className="attachments-list">

                                {attachments.map(
                                    attachment => (

                                        <div
                                            className="attachment-item"
                                            key={
                                                attachment.id
                                            }
                                        >


                                            <div className="attachment-icon">

                                                {
                                                    attachment.type_mime?.startsWith(
                                                        "image/"
                                                    )
                                                        ? "🖼️"
                                                        : attachment.type_mime ===
                                                          "application/pdf"
                                                        ? "📕"
                                                        : "📄"
                                                }

                                            </div>


                                            <div className="attachment-info">

                                                <strong>

                                                    {
                                                        attachment.nom_original
                                                    }

                                                </strong>

                                                <small>

                                                    {
                                                        formatSize(
                                                            attachment.taille
                                                        )
                                                    }

                                                    {" • "}

                                                    {
                                                        attachment.type_mime ||
                                                        "Type inconnu"
                                                    }

                                                </small>

                                            </div>


                                            <button
                                                type="button"
                                                className="attachment-open-button"
                                                disabled={
                                                    downloadingId ===
                                                    attachment.id
                                                }
                                                onClick={() =>
                                                    handleDownload(
                                                        attachment
                                                    )
                                                }
                                            >

                                                {downloadingId ===
                                                attachment.id
                                                    ? "..."
                                                    : "Ouvrir"}

                                            </button>


                                        </div>

                                    )
                                )}

                            </div>

                        )}

                    </div>

                </div>


                {/* ==================================================
                    FOOTER
                ================================================== */}

                <div className="document-details-footer">

                    <button
                        type="button"
                        className="btn-secondary"
                        onClick={
                            onClose
                        }
                    >
                        Fermer
                    </button>

                </div>

            </div>

        </div>

    );

}