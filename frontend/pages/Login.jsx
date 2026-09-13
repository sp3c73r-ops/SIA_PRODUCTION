import { useState } from "react";
import { useNavigate } from "react-router-dom";
import "../styles/login.css";
import { login } from "../services/authService";
import { useAuth } from "../contexts/AuthContext";

export default function Login() {
    const navigate = useNavigate();
    const { refreshUser } = useAuth();

    const [username, setUsername] = useState("");
    const [password, setPassword] = useState("");

    const [loading, setLoading] = useState(false);
    const [error, setError] = useState("");

    const handleSubmit = async (e) => {
        e.preventDefault();

        setError("");

        if (!username.trim() || !password) {
            setError("Veuillez renseigner le nom d'utilisateur et le mot de passe.");
            return;
        }

        try {
            setLoading(true);

            await login(
                username.trim(),
                password
            );

            await refreshUser({ isNewLogin: true });

            // Connexion réussie
            navigate("/", { replace: true });

        } catch (err) {
            console.error("Erreur de connexion :", err);

            if (err.response?.status === 401) {
                setError("Nom d'utilisateur ou mot de passe incorrect.");
            } else if (err.response?.data?.detail) {
                setError(err.response.data.detail);
            } else {
                setError(
                    "Impossible de contacter le serveur. Vérifiez que le backend est démarré."
                );
            }
        } finally {
            setLoading(false);
        }
    };

    return (
        <div className="login-page">

            <div className="login-container">

                {/* PARTIE GAUCHE */}
                <div className="login-brand">

                    <div className="brand-logo">
                        SIA
                    </div>

                    <div className="brand-content">

                        <h1>
                            Système Intégré
                            <br />
                            des Archives
                            <br />
                            Documentaires
                        </h1>

                        <p>
                            Système de gestion, de conservation et de
                            consultation des archives.
                        </p>

                        <div className="brand-line"></div>

                        <span>
                            Système Intégré des Archives Documentaires
                        </span>

                    </div>

                </div>

                {/* PARTIE DROITE */}
                <div className="login-form-container">

                    <div className="login-form-wrapper">

                        <div className="login-icon">
                            🔐
                        </div>

                        <h2>
                            Bienvenue
                        </h2>

                        <p className="login-subtitle">
                            Connectez-vous à votre espace de travail
                        </p>

                        <form onSubmit={handleSubmit}>

                            {/* USERNAME */}
                            <div className="form-group">

                                <label htmlFor="username">
                                    Nom d'utilisateur
                                </label>

                                <div className="input-wrapper">

                                    <span className="input-icon">
                                        👤
                                    </span>

                                    <input
                                        id="username"
                                        type="text"
                                        placeholder="Ex. chiru"
                                        value={username}
                                        onChange={(e) =>
                                            setUsername(e.target.value)
                                        }
                                        autoComplete="username"
                                        disabled={loading}
                                    />

                                </div>

                            </div>

                            {/* PASSWORD */}
                            <div className="form-group">

                                <label htmlFor="password">
                                    Mot de passe
                                </label>

                                <div className="input-wrapper">

                                    <span className="input-icon">
                                        🔒
                                    </span>

                                    <input
                                        id="password"
                                        type="password"
                                        placeholder="Votre mot de passe"
                                        value={password}
                                        onChange={(e) =>
                                            setPassword(e.target.value)
                                        }
                                        autoComplete="current-password"
                                        disabled={loading}
                                    />

                                </div>

                            </div>

                            {/* ERREUR */}
                            {error && (
                                <div className="login-error">
                                    {error}
                                </div>
                            )}

                            {/* OPTIONS */}
                            <div className="login-options">

                                <label className="remember-me">

                                    <input
                                        type="checkbox"
                                        disabled={loading}
                                    />

                                    <span>
                                        Se souvenir de moi
                                    </span>

                                </label>

                                <button
                                    type="button"
                                    className="forgot-password"
                                    onClick={() => {
                                        alert(
                                            "Veuillez contacter l'administrateur pour réinitialiser votre mot de passe."
                                        );
                                    }}
                                >
                                    Mot de passe oublié ?
                                </button>

                            </div>

                            {/* BOUTON */}
                            <button
                                type="submit"
                                className="login-button"
                                disabled={loading}
                            >
                                {loading ? (
                                    "Connexion..."
                                ) : (
                                    <>
                                        Se connecter
                                        <span>→</span>
                                    </>
                                )}
                            </button>

                        </form>

                        <div className="login-footer">
                            SIA
                            <span>•</span>
                            Accès sécurisé
                        </div>

                    </div>

                </div>

            </div>

        </div>
    );
}