import { useEffect, useState } from "react";
import { Clock } from "lucide-react";

/**
 * Composant de décompte d'autorisation temporaire.
 *
 * Source de vérité : `expiresAt` transmis par le backend.
 * Calcule le temps restant = Math.max(0, Math.floor((expiresAt - Date.now()) / 1000)).
 * Se met à jour en temps réel (1s) et s'arrête automatiquement à 00:00.
 */
export default function AuthorizationTimer({
    expiresAt,
    onExpire,
    compact = false,
    showLabel = true,
}) {
    const calculateRemaining = () => {
        if (!expiresAt) return 0;
        const targetTime = new Date(expiresAt).getTime();
        const now = Date.now();
        return Math.max(0, Math.floor((targetTime - now) / 1000));
    };

    const [secondsLeft, setSecondsLeft] = useState(calculateRemaining);

    useEffect(() => {
        setSecondsLeft(calculateRemaining());

        const intervalId = setInterval(() => {
            const remaining = calculateRemaining();
            setSecondsLeft(remaining);

            if (remaining <= 0) {
                clearInterval(intervalId);
                if (onExpire) {
                    onExpire();
                }
            }
        }, 1000);

        return () => {
            clearInterval(intervalId);
        };
    }, [expiresAt]);

    const minutes = Math.floor(secondsLeft / 60);
    const seconds = secondsLeft % 60;
    const formattedTime = `${String(minutes).padStart(2, "0")}:${String(seconds).padStart(2, "0")}`;

    const isExpired = secondsLeft <= 0;

    if (isExpired) {
        return (
            <span
                className={`authorization-timer expired ${
                    compact ? "is-compact" : ""
                }`}
                title="L'autorisation temporaire est expirée"
            >
                <Clock size={compact ? 13 : 15} aria-hidden="true" />
                <span>00:00 (Expiré)</span>
            </span>
        );
    }

    return (
        <span
            className={`authorization-timer active ${
                compact ? "is-compact" : ""
            }`}
            title={`Autorisation temporaire active jusqu'à ${new Date(
                expiresAt
            ).toLocaleTimeString()}`}
        >
            <Clock
                size={compact ? 13 : 15}
                aria-hidden="true"
                className="timer-clock-icon"
            />
            {showLabel && !compact && <span>Autorisation de modification active — </span>}
            <strong className="timer-countdown">{formattedTime}</strong>
        </span>
    );
}
