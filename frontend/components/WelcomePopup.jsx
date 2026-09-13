import { useEffect, useState } from "react";
import { CheckCircle2, X } from "lucide-react";

import { useAuth } from "../contexts/AuthContext";
import "../styles/welcomePopup.css";

const DISPLAY_DURATION_MS = 8000;

export default function WelcomePopup() {
    const { welcomeUser } = useAuth();
    const [isVisible, setIsVisible] = useState(false);

    useEffect(() => {
        if (!welcomeUser) {
            setIsVisible(false);
            return undefined;
        }

        setIsVisible(true);

        const timeoutId = window.setTimeout(() => {
            setIsVisible(false);
        }, DISPLAY_DURATION_MS);

        return () => {
            window.clearTimeout(timeoutId);
        };
    }, [welcomeUser]);

    useEffect(() => {
        if (!isVisible) {
            return undefined;
        }

        const handleKeyDown = (event) => {
            if (event.key === "Escape") {
                setIsVisible(false);
            }
        };

        document.addEventListener("keydown", handleKeyDown);

        return () => {
            document.removeEventListener("keydown", handleKeyDown);
        };
    }, [isVisible]);

    if (!isVisible || !welcomeUser) {
        return null;
    }

    const bureauName =
        welcomeUser.bureau?.nom
        || "Bureau non attribué";

    const circonscriptionName =
        welcomeUser.circonscription?.nom
        || "Circonscription non attribuée";

    const firstName =
        welcomeUser.prenom
        || welcomeUser.username
        || "Utilisateur";

    return (
        <aside
            className="welcome-popup"
            role="status"
            aria-live="polite"
            aria-atomic="true"
        >
            <CheckCircle2
                className="welcome-popup-icon"
                size={22}
                aria-hidden="true"
            />

            <div className="welcome-popup-content">
                <strong>Bienvenue dans SIA, {firstName} !</strong>
                <span>
                    Vous êtes connecté à la circonscription de {circonscriptionName}, au bureau {bureauName}.
                </span>
            </div>

            <button
                type="button"
                className="welcome-popup-close"
                aria-label="Fermer le message de bienvenue"
                onClick={() => setIsVisible(false)}
            >
                <X size={18} aria-hidden="true" />
            </button>
        </aside>
    );
}