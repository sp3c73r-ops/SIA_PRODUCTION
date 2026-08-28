import api from "../api/api";

export const getDocumentFields = () => {
    return api.get("/document-fields/");
};

export const getDocumentField = (id) => {
    return api.get(`/document-fields/${id}`);
};

export const createDocumentField = (data) => {
    return api.post("/document-fields/", data);
};

export const updateDocumentField = (id, data) => {
    return api.put(`/document-fields/${id}`, data);
};

export const toggleDocumentFieldActive = (id, active) => {
    return api.patch(`/document-fields/${id}/toggle-active?active=${active}`);
};

export const deleteDocumentField = (id) => {
    return api.delete(`/document-fields/${id}`);
};
