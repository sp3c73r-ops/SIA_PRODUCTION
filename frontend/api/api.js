import axios from "axios";

const api = axios.create({
    baseURL: "http://127.0.0.1:8001",
});

api.interceptors.request.use(
    (config) => {
        const token = localStorage.getItem("access_token");

        if (token) {
            config.headers.Authorization = `Bearer ${token}`;
        }

        // Si on envoie un fichier, Axios doit laisser
        // le navigateur définir automatiquement :
        // multipart/form-data; boundary=...
        if (config.data instanceof FormData) {
            delete config.headers["Content-Type"];
        }

        return config;
    },
    (error) => {
        return Promise.reject(error);
    }
);

export default api;