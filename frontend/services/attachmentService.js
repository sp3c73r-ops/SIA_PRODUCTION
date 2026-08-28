import api from "../api/api";

// ============================================================
// AJOUTER UNE PIECE JOINTE
// ============================================================

export const uploadAttachment = async (
    documentId,
    file
) => {

    const formData = new FormData();

    formData.append(
        "file",
        file
    );

    return api.post(
        `/documents/${documentId}/attachments`,
        formData
    );
};


// ============================================================
// LISTE DES PIECES JOINTES
// ============================================================

export const getAttachments = async (
    documentId
) => {

    return api.get(
        `/documents/${documentId}/attachments`
    );
};


// ============================================================
// SUPPRIMER UNE PIECE JOINTE
// ============================================================

export const deleteAttachment = async (
    attachmentId
) => {

    return api.delete(
        `/documents/attachments/${attachmentId}`
    );
};


// ============================================================
// OUVRIR / TELECHARGER UNE PIECE JOINTE
// ============================================================

export const downloadAttachment = async (
    attachmentId
) => {

    const response = await api.get(
        `/documents/attachments/${attachmentId}/download`,
        {
            responseType: "blob",
        }
    );

    const blobUrl = window.URL.createObjectURL(
        new Blob(
            [response.data],
            {
                type:
                    response.headers[
                        "content-type"
                    ] || "application/octet-stream",
            }
        )
    );

    const link =
        document.createElement("a");

    link.href = blobUrl;

    link.target = "_blank";

    link.rel = "noopener noreferrer";

    document.body.appendChild(link);

    link.click();

    link.remove();

    setTimeout(() => {
        window.URL.revokeObjectURL(
            blobUrl
        );
    }, 1000);

    return response;
};