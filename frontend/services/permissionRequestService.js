import api from "../api/api";

// ============================================================
// CREER UNE DEMANDE DE PERMISSION
// ============================================================

export const createPermissionRequest = async (data) => {
    return api.post(
        "/permission-requests",
        data
    );
};

// ============================================================
// MES DEMANDES (UTILISATEUR CONNECTE)
// ============================================================

export const getMyPermissionRequests = async () => {
    return api.get("/permission-requests/me");
};

// ============================================================
// ANNULER UNE DEMANDE
// ============================================================

export const cancelPermissionRequest = async (requestId) => {
    return api.delete(
        `/permission-requests/${requestId}`
    );
};

// ============================================================
// TOUTES LES DEMANDES (ADMIN, SCOPE CIRCONSCRIPTION)
// ============================================================

export const getPermissionRequests = async () => {
    return api.get("/permission-requests");
};

// ============================================================
// DEMANDES EN ATTENTE (ADMIN, SCOPE CIRCONSCRIPTION)
// ============================================================

export const getPendingPermissionRequests = async () => {
    return api.get("/permission-requests/pending");
};

// ============================================================
// APPROUVER UNE DEMANDE (ADMIN)
// ============================================================

export const approvePermissionRequest = async (
    requestId,
    durationMinutes
) => {
    return api.post(
        `/permission-requests/${requestId}/approve`,
        {
            duration_minutes: durationMinutes,
        }
    );
};

// ============================================================
// REFUSER UNE DEMANDE (ADMIN)
// ============================================================

export const rejectPermissionRequest = async (requestId) => {
    return api.post(
        `/permission-requests/${requestId}/reject`
    );
};
