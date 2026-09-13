import { Navigate, Outlet } from "react-router-dom";

import { useAuth } from "../contexts/AuthContext";
import { isAuthenticated } from "../services/authService";

function InitializingView() {
    return (
        <main aria-busy="true" aria-live="polite">
            Initialisation de la session...
        </main>
    );
}

function InitializationErrorView() {
    return (
        <main role="alert">
            Impossible de vérifier la session. Réessayez plus tard.
        </main>
    );
}

export default function RequireAuth({ children }) {
    const {
        currentUser,
        loading,
        initializationError,
    } = useAuth();

    if (!isAuthenticated()) {
        return <Navigate to="/login" replace />;
    }

    if (initializationError) {
        return <InitializationErrorView />;
    }

    if (loading || !currentUser) {
        return <InitializingView />;
    }

    return children || <Outlet />;
}
