import axios from "axios";
import { logout } from "../services/authService";

let sessionInvalidationInProgress = false;
let sessionInvalidationPromise = null;

const SESSION_INVALIDATION_TRANSITION_MS = 250;

const waitForSessionInvalidationTransition = () => (
    new Promise((resolve) => {
        setTimeout(resolve, SESSION_INVALIDATION_TRANSITION_MS);
    })
);

const isLoginRequest = (config) => {
    const requestUrl = config?.url || "";

    return (
        requestUrl === "/auth/login"
        || requestUrl.endsWith("/auth/login")
    );
};

const api = axios.create({
    baseURL: "",
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

api.interceptors.response.use(
    (response) => {
        if (isLoginRequest(response.config)) {
            sessionInvalidationInProgress = false;
            sessionInvalidationPromise = null;
        }

        return response;
    },
    async (error) => {
        const response = error?.response;
        const config = response?.config || error?.config;

        if (response?.status === 401 && !isLoginRequest(config)) {
            if (!sessionInvalidationInProgress) {
                sessionInvalidationInProgress = true;
                sessionInvalidationPromise = (async () => {
                    logout();

                    if (window.location.pathname !== "/login") {
                        window.location.replace("/login");
                    }

                    await waitForSessionInvalidationTransition();
                })();
            }

            await sessionInvalidationPromise;
        }

        return Promise.reject(error);
    }
);

export default api;