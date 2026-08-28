import api from "../api/api";

export const getDocuments = () => {
    return api.get("/documents/");
};

export const getDocument = (id) => {
    return api.get(`/documents/${id}`);
};

export const createDocument = (data) => {
    return api.post("/documents/", data);
};

export const updateDocument = (id, data) => {
    return api.put(`/documents/${id}`, data);
};

export const deleteDocument = (id) => {
    return api.delete(`/documents/${id}`);
};