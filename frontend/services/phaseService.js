import api from "../api/api";

export const getPhases = () => {
    return api.get("/phases/");
};

export const createPhase = (data) => {
    return api.post("/phases/", data);
};

export const updatePhase = (id, data) => {
    return api.put(`/phases/${id}`, data);
};

export const deletePhase = (id) => {
    return api.delete(`/phases/${id}`);
};
