import api from "../api/api";

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
            "access_token",
            response.data.access_token
        );
    }

    return response.data;
};

export const logout = () => {
    localStorage.removeItem("access_token");
};

export const getToken = () => {
    return localStorage.getItem("access_token");
};

export const isAuthenticated = () => {
    return !!localStorage.getItem("access_token");
};