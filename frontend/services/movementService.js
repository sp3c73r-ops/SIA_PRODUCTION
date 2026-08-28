import api from "../api/api";

// ============================================================
// LISTE DE TOUS LES MOUVEMENTS
// ============================================================

export const getMovements = async () => {
    return api.get("/movements/");
};


// ============================================================
// LISTE DES MOUVEMENTS EN COURS
// ============================================================

export const getActiveMovements = async () => {
    return api.get("/movements/active");
};


// ============================================================
// RECUPERER UN MOUVEMENT
// ============================================================

export const getMovement = async (movementId) => {
    return api.get(`/movements/${movementId}`);
};


// ============================================================
// MOUVEMENTS D'UN DOCUMENT
// ============================================================

export const getDocumentMovements = async (documentId) => {
    return api.get(
        `/movements/document/${documentId}`
    );
};


// ============================================================
// MOUVEMENTS D'UN UTILISATEUR
// ============================================================

export const getUserMovements = async (userId) => {
    return api.get(
        `/movements/user/${userId}`
    );
};


// ============================================================
// CREER UN MOUVEMENT
// ============================================================

export const createMovement = async (data) => {
    return api.post(
        "/movements/",
        data
    );
};


// ============================================================
// ENREGISTRER LE RETOUR D'UN DOCUMENT
// ============================================================

export const returnMovement = async (movementId) => {
    return api.put(
        `/movements/${movementId}/return`
    );
};