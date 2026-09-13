import {
    createContext,
    useContext,
    useEffect,
    useState,
} from "react";

import {
    getCurrentUser,
    getMe,
    isAuthenticated,
    logout as logoutService,
} from "../services/authService";

const AuthContext = createContext(null);

export function AuthProvider({ children }) {
    const [currentUser, setCurrentUser] = useState(null);
    const [loading, setLoading] = useState(true);
    const [initializationError, setInitializationError] = useState(false);
    const [welcomeUser, setWelcomeUser] = useState(null);

    const refreshUser = async ({ isNewLogin = false } = {}) => {
        const user = await getMe();
        setCurrentUser(user);
        setInitializationError(false);

        if (isNewLogin) {
            setWelcomeUser(user);
        }

        return user;
    };

    const logout = () => {
        logoutService();
        setCurrentUser(null);
        setInitializationError(false);
        setWelcomeUser(null);
    };

    useEffect(() => {
        let isMounted = true;

        const initialize = async () => {
            if (!isAuthenticated()) {
                if (isMounted) {
                    setCurrentUser(null);
                    setLoading(false);
                }
                return;
            }

            try {
                const user = await getMe();

                if (isMounted) {
                    setCurrentUser(user);
                    setInitializationError(false);
                }
            } catch (error) {
                if (!isMounted) {
                    return;
                }

                if (error?.response?.status === 401) {
                    setCurrentUser(null);
                } else {
                    setCurrentUser(getCurrentUser());
                    setInitializationError(true);
                }
            } finally {
                if (isMounted) {
                    setLoading(false);
                }
            }
        };

        initialize();

        return () => {
            isMounted = false;
        };
    }, []);

    return (
        <AuthContext.Provider
            value={{
                currentUser,
                loading,
                initializationError,
                welcomeUser,
                refreshUser,
                logout,
            }}
        >
            {children}
        </AuthContext.Provider>
    );
}

export function useAuth() {
    const context = useContext(AuthContext);

    if (!context) {
        throw new Error(
            "useAuth doit être utilisé dans AuthProvider."
        );
    }

    return context;
}
