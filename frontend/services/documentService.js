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

export const createDocumentWithAttachments = async (
    data,
    files
) => {
    const formData = new FormData();

    formData.append(
        "document_json",
        JSON.stringify(data)
    );

    files.forEach((file) => {
        formData.append(
            "file",
            file
        );
    });

    const response = await api.post(
        "/documents/with-attachment",
        formData
    );

    return response.data;
};

export const updateDocument = (id, data) => {
    return api.put(`/documents/${id}`, data);
};

export const deleteDocument = (id) => {
    return api.delete(`/documents/${id}`);
};

export const searchDocuments = async (params) => {
    const response = await api.get("/documents/search", { params });
    return response.data;
};