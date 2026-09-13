import { useEffect, useState } from "react";
import {
    AlertCircle,
    CheckCircle,
    Clock,
    FileText,
    Loader2,
    MessageSquare,
    User,
    X,
} from "lucide-react";

import api from "../api/api";
import { getDocument } from "../services/documentService";
import {
    approvePermissionRequest,
    getPermissionRequests,
    rejectPermissionRequest,
} from "../services/permissionRequestService";

export default function PermissionRequestReviewModal({
    requestId,
    onClose,
    onSuccess,
}) {
    const [request, setRequest] = useState(null);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState(null);
    const [success, setSuccess] = useState(null);
    const [processing, setProcessing] = useState(false);
    const [durationMinutes, setDurationMinutes] = useState(1);

    const [applicantUser, setApplicantUser] = useState(null);
    const [targetDocument, setTargetDocument] = useState(null);
    const [applicantBureau, setApplicantBureau] = useState(null);
    const [circonscriptions, setCirconscriptions] = useState([]);

    useEffect(() => {
        let isMounted = true;

        const loadDetails = async () => {
            setLoading(true);
            setError(null);
            setSuccess(null);

            try {
                const res = await getPermissionRequests();
                const requests = res?.data || [];
                const found = requests.find((r) => r.id === requestId);

                if (!found) {
                    if (isMounted) {
                        setError("Demande introuvable ou vous n'avez pas accès à ce périmètre.");
                        setLoading(false);
                    }
                    return;
                }

                if (isMounted) {
                    setRequest(found);
                }

                const enrichPromises = [
                    api.get("/circonscriptions/")
                        .then((cRes) => { if (isMounted) setCirconscriptions(cRes.data || []); })
                        .catch(() => {})
                ];

                if (found.user_id) {
                    enrichPromises.push(
                        api.get(`/users/${found.user_id}`)
                            .then((uRes) => { if (isMounted) setApplicantUser(uRes.data); })
                            .catch(() => {})
                    );
                }

                if (found.document_id) {
                    enrichPromises.push(
                        getDocument(found.document_id)
                            .then((dRes) => { if (isMounted) setTargetDocument(dRes.data); })
                            .catch(() => {})
                    );
                }

                if (found.bureau_id) {
                    enrichPromises.push(
                        api.get(`/bureaux/${found.bureau_id}`)
                            .then((bRes) => { if (isMounted) setApplicantBureau(bRes.data); })
                            .catch(() => {})
                    );
                }

                await Promise.allSettled(enrichPromises);
            } catch (err) {
                if (isMounted) {
                    if (err?.response?.status === 403) {
                        setError("Accès refusé : vous n'avez pas les droits pour consulter cette demande.");
                    } else {
                        setError("Erreur lors du chargement des détails de la demande.");
                    }
                }
            } finally {
                if (isMounted) {
                    setLoading(false);
                }
            }
        };

        if (requestId) {
            loadDetails();
        }

        return () => {
            isMounted = false;
        };
    }, [requestId]);

    const handleApprove = async () => {
        setError(null);
        setSuccess(null);

        const minutes = parseInt(durationMinutes, 10);
        if (isNaN(minutes) || minutes < 1 || minutes > 1440) {
            setError("Veuillez indiquer une durée valide comprise entre 1 et 1440 minutes.");
            return;
        }

        setProcessing(true);

        try {
            const response = await approvePermissionRequest(requestId, minutes);
            setRequest(response.data);
            setSuccess(`La demande d'autorisation a été approuvée avec succès pour ${minutes} minute(s).`);
            if (onSuccess) {
                onSuccess(response.data);
            }
        } catch (err) {
            const status = err?.response?.status;
            const detail = err?.response?.data?.detail;

            if (status === 409) {
                setError("Cette demande a déjà été traitée par un autre administrateur.");
            } else if (status === 403) {
                setError("Accès refusé : vous n'avez pas les droits d'administration sur cette circonscription.");
            } else if (status === 404) {
                setError("Demande introuvable.");
            } else {
                setError(detail || "Erreur lors de l'approbation de la demande.");
            }
        } finally {
            setProcessing(false);
        }
    };

    const handleReject = async () => {
        setError(null);
        setSuccess(null);
        setProcessing(true);

        try {
            const response = await rejectPermissionRequest(requestId);
            setRequest(response.data);
            setSuccess("La demande d'autorisation a été rejetée.");
            if (onSuccess) {
                onSuccess(response.data);
            }
        } catch (err) {
            const status = err?.response?.status;
            const detail = err?.response?.data?.detail;

            if (status === 409) {
                setError("Cette demande a déjà été traitée par un autre administrateur.");
            } else if (status === 403) {
                setError("Accès refusé : vous n'avez pas les droits d'administration sur cette circonscription.");
            } else if (status === 404) {
                setError("Demande introuvable.");
            } else {
                setError(detail || "Erreur lors du rejet de la demande.");
            }
        } finally {
            setProcessing(false);
        }
    };

    const formatDate = (dateStr) => {
        if (!dateStr) return "Non spécifiée";
        try {
            const d = new Date(dateStr);
            return d.toLocaleString("fr-FR", {
                day: "2-digit",
                month: "2-digit",
                year: "numeric",
                hour: "2-digit",
                minute: "2-digit",
            });
        } catch {
            return dateStr;
        }
    };

    const renderStatusBadge = (status) => {
        switch (status) {
            case "PENDING":
                return <span className="permission-status-badge pending">EN ATTENTE</span>;
            case "APPROVED":
                return <span className="permission-status-badge approved">APPROUVÉE</span>;
            case "REJECTED":
                return <span className="permission-status-badge rejected">REJETÉE</span>;
            case "EXPIRED":
                return <span className="permission-status-badge expired">EXPIRÉE</span>;
            case "CANCELLED":
                return <span className="permission-status-badge cancelled">ANNULÉE</span>;
            default:
                return <span className="permission-status-badge">{status}</span>;
        }
    };

    const applicantName =
        [applicantUser?.prenom, applicantUser?.nom].filter(Boolean).join(" ") ||
        applicantUser?.username ||
        (request?.user_id ? `Utilisateur #${request.user_id}` : "Utilisateur");

    const applicantUsername = applicantUser?.username || "—";

    const bureauName =
        applicantBureau?.nom ||
        (request?.bureau_id ? `Bureau #${request.bureau_id}` : "Non spécifié");

    const targetCirconscriptionId =
        applicantBureau?.circonscription_id ||
        targetDocument?.circonscription_id;

    const matchedCirconscription = circonscriptions.find(
        (c) => Number(c.id) === Number(targetCirconscriptionId)
    );

    const circonscriptionName =
        matchedCirconscription?.nom ||
        applicantBureau?.circonscription?.nom ||
        "Circonscription non spécifiée";

    const documentTitle =
        targetDocument?.titre ||
        targetDocument?.title ||
        (targetDocument?.numero_ordre ? `N° ${targetDocument.numero_ordre}` : null) ||
        (request?.document_id ? `Document #${request.document_id}` : "Demande globale");

    return (
        <div className="modal-overlay" onClick={onClose}>
            <div
                className="permission-review-modal"
                onClick={(e) => e.stopPropagation()}
                role="dialog"
                aria-label="Demande d'autorisation de modification"
            >
                <div className="modal-header">
                    <div>
                        <h2>Demande d'autorisation de modification</h2>
                        <p>Examen administratif de la demande d'accès temporaire</p>
                    </div>
                    <button
                        type="button"
                        className="modal-close"
                        onClick={onClose}
                        aria-label="Fermer la modal"
                    >
                        <X size={20} />
                    </button>
                </div>

                <div className="permission-modal-body">
                    {loading && (
                        <div className="permission-review-loading">
                            <Loader2 size={32} className="notification-spinner" aria-hidden="true" />
                            <span>Chargement des détails de la demande...</span>
                        </div>
                    )}

                    {!loading && error && !request && (
                        <div className="permission-review-alert error">
                            <AlertCircle size={20} />
                            <span>{error}</span>
                        </div>
                    )}

                    {request && (
                        <div className="permission-review-content">
                            {error && (
                                <div className="permission-review-alert error">
                                    <AlertCircle size={18} />
                                    <span>{error}</span>
                                </div>
                            )}

                            {success && (
                                <div className="permission-review-alert success">
                                    <CheckCircle size={18} />
                                    <span>{success}</span>
                                </div>
                            )}

                            <div className="permission-review-grid">
                                <div className="review-section">
                                    <div className="review-section-header">
                                        <User size={16} />
                                        <span>Demandeur</span>
                                    </div>
                                    <div className="review-field">
                                        <label>Nom & Prénom :</label>
                                        <strong>{applicantName}</strong>
                                    </div>
                                    <div className="review-field">
                                        <label>Utilisateur :</label>
                                        <span>{applicantUsername}</span>
                                    </div>
                                    <div className="review-field">
                                        <label>Bureau :</label>
                                        <span>{bureauName}</span>
                                    </div>
                                    <div className="review-field">
                                        <label>Circonscription :</label>
                                        <span>{circonscriptionName}</span>
                                    </div>
                                </div>

                                <div className="review-section">
                                    <div className="review-section-header">
                                        <FileText size={16} />
                                        <span>Document & Permission</span>
                                    </div>
                                    <div className="review-field">
                                        <label>Document :</label>
                                        <strong>{documentTitle}</strong>
                                    </div>
                                    <div className="review-field">
                                        <label>Permission :</label>
                                        <span className="permission-code">{request.permission}</span>
                                    </div>
                                    <div className="review-field">
                                        <label>Demandée le :</label>
                                        <span>{formatDate(request.requested_at)}</span>
                                    </div>
                                    <div className="review-field">
                                        <label>Statut actuel :</label>
                                        <div>{renderStatusBadge(request.status)}</div>
                                    </div>
                                </div>
                            </div>

                            <div className="review-section full-width">
                                <div className="review-section-header">
                                    <MessageSquare size={16} />
                                    <span>Motif de la demande</span>
                                </div>
                                <div className="review-reason-box">
                                    {request.reason || "Aucun motif renseigné."}
                                </div>
                            </div>

                            {request.status === "PENDING" && !success && (
                                <div className="review-action-box">
                                    <div className="review-section-header">
                                        <Clock size={16} />
                                        <span>Durée d'autorisation temporaire</span>
                                    </div>
                                    <div className="duration-input-group">
                                        <label htmlFor="duration-input">
                                            Durée d'accès accordée :
                                        </label>
                                        <div className="duration-input-wrapper">
                                            <input
                                                id="duration-input"
                                                type="number"
                                                min="1"
                                                max="1440"
                                                value={durationMinutes}
                                                onChange={(e) => setDurationMinutes(e.target.value)}
                                                disabled={processing}
                                                className="duration-field"
                                            />
                                            <span className="duration-unit">minutes</span>
                                        </div>
                                    </div>
                                </div>
                            )}

                            {request.expires_at && (
                                <div className="review-info-box">
                                    <span>
                                        Expiration prévue / enregistrée :{" "}
                                        <strong>{formatDate(request.expires_at)}</strong>
                                    </span>
                                </div>
                            )}
                        </div>
                    )}
                </div>

                <div className="modal-footer">
                    <button
                        type="button"
                        className="btn-secondary"
                        onClick={onClose}
                        disabled={processing}
                    >
                        Fermer
                    </button>

                    {request && request.status === "PENDING" && !success && (
                        <div className="modal-actions-right">
                            <button
                                type="button"
                                className="btn-danger"
                                onClick={handleReject}
                                disabled={processing}
                            >
                                {processing ? "Traitement..." : "Rejeter"}
                            </button>
                            <button
                                type="button"
                                className="btn-primary"
                                onClick={handleApprove}
                                disabled={processing}
                            >
                                {processing ? "Traitement..." : "Approuver"}
                            </button>
                        </div>
                    )}
                </div>
            </div>
        </div>
    );
}
