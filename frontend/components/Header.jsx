import { useEffect, useRef, useState } from "react";
import {
    ChevronDown,
    LogOut,
    UserCircle,
} from "lucide-react";

import { useAuth } from "../contexts/AuthContext";
import NotificationBell from "./NotificationBell";

export default function Header() {
    const { currentUser, logout } = useAuth();
    const [isMenuOpen, setIsMenuOpen] = useState(false);
    const profileRef = useRef(null);

    useEffect(() => {
        const handleDocumentClick = (event) => {
            if (
                profileRef.current
                && !profileRef.current.contains(event.target)
            ) {
                setIsMenuOpen(false);
            }
        };

        const handleKeyDown = (event) => {
            if (event.key === "Escape") {
                setIsMenuOpen(false);
            }
        };

        document.addEventListener("mousedown", handleDocumentClick);
        document.addEventListener("keydown", handleKeyDown);

        return () => {
            document.removeEventListener("mousedown", handleDocumentClick);
            document.removeEventListener("keydown", handleKeyDown);
        };
    }, []);

    const displayName = [
        currentUser?.prenom,
        currentUser?.nom,
    ]
        .filter(Boolean)
        .join(" ")
        || currentUser?.username
        || "Utilisateur";

    const bureauName =
        currentUser?.bureau?.nom
        || "Bureau non attribué";

    const circonscriptionName =
        currentUser?.circonscription?.nom
        || "Circonscription non attribuée";

    const handleLogout = () => {
        setIsMenuOpen(false);
        logout();
    };

    return (
        <header className="header">

            <div>
                <h2>Système Intégré des Archives Documentaires</h2>
            </div>

            <div className="header-right">

                <NotificationBell />

                <div
                    className="header-profile"
                    ref={profileRef}
                >
                    <button
                        type="button"
                        className="header-profile-trigger"
                        aria-expanded={isMenuOpen}
                        aria-haspopup="menu"
                        aria-label={`Ouvrir le profil de ${displayName}`}
                        onClick={() => setIsMenuOpen((isOpen) => !isOpen)}
                    >
                        <span className="header-profile-summary">
                            <strong>{displayName}</strong>
                            <span>{bureauName}</span>
                        </span>
                        <UserCircle size={35} aria-hidden="true" />
                        <ChevronDown
                            size={16}
                            aria-hidden="true"
                            className={isMenuOpen ? "is-open" : ""}
                        />
                    </button>

                    {isMenuOpen && (
                        <div
                            className="header-profile-menu"
                            role="menu"
                            aria-label="Profil utilisateur"
                        >
                            <div className="header-profile-details">
                                <strong>{displayName}</strong>
                                {currentUser?.username && (
                                    <span>{currentUser.username}</span>
                                )}
                                <span>{bureauName}</span>
                                <span>{circonscriptionName}</span>
                            </div>

                            <button
                                type="button"
                                className="header-profile-logout"
                                role="menuitem"
                                onClick={handleLogout}
                            >
                                <LogOut size={16} aria-hidden="true" />
                                Se déconnecter
                            </button>
                        </div>
                    )}
                </div>

            </div>

        </header>
    );
}