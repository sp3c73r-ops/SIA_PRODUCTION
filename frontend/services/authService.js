import api from "../api/api";

const ACCESS_TOKEN_KEY = "access_token";
const CURRENT_USER_KEY = "current_user";

export const login = async (username, password) => {
    const response = await api.post(
        "/auth/login",
        {
            username: username,
            password: password,
        }
    );

    if (response.data.access_token) {
        localStorage.setItem(
            ACCESS_TOKEN_KEY,
            response.data.access_token
        );
    }

    return response.data;
};

export const getMe = async () => {
    const response = await api.get("/auth/me");

    if (response.data) {
        localStorage.setItem(
            CURRENT_USER_KEY,
            JSON.stringify(response.data)
        );
    }

    return response.data;
};

export const getCurrentUser = () => {
    const raw = localStorage.getItem(CURRENT_USER_KEY);

    if (!raw) {
        return null;
    }

    try {
        return JSON.parse(raw);
    } catch {
        localStorage.removeItem(CURRENT_USER_KEY);
        return null;
    }
};

export const logout = () => {
    localStorage.removeItem(ACCESS_TOKEN_KEY);
    localStorage.removeItem(CURRENT_USER_KEY);
};

export const getToken = () => {
    return localStorage.getItem(ACCESS_TOKEN_KEY);
};

export const isAuthenticated = () => {
    return !!localStorage.getItem(ACCESS_TOKEN_KEY);
};