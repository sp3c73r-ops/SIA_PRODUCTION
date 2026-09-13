import { useEffect, useRef, useState } from "react";
import {
    Bell,
    Check,
    CheckCheck,
    Inbox,
    Loader2,
} from "lucide-react";

import { useAuth } from "../contexts/AuthContext";
import {
    getNotifications,
    getUnreadCount,
    markAllNotificationsAsRead,
    markNotificationAsRead,
} from "../services/notificationService";

export default function NotificationBell() {
    const { currentUser } = useAuth();
    const [unreadCount, setUnreadCount] = useState(0);
    const [notifications, setNotifications] = useState([]);
    const [isOpen, setIsOpen] = useState(false);
    const [loading, setLoading] = useState(false);
    const [error, setError] = useState(null);
    const [markingAll, setMarkingAll] = useState(false);
    const [markingIds, setMarkingIds] = useState(new Set());

    const bellRef = useRef(null);

    // ============================================================
    // RAFRAÎCHISSEMENT PÉRIODIQUE DU COMPTEUR (POLLING 30s)
    // ============================================================
    useEffect(() => {
        if (!currentUser) {
            setUnreadCount(0);
            setNotifications([]);
            setIsOpen(false);
            return;
        }

        let isMounted = true;

        const fetchCount = async () => {
            try {
                const data = await getUnreadCount();
                if (isMounted && typeof data?.unread_count === "number") {
                    setUnreadCount(data.unread_count);
                }
            } catch (err) {
                // Silencieusement ignoré pour ne pas altérer le Header
                if (err?.response?.status === 403) {
                    // Utilisateur sans permission notification.read
                }
            }
        };

        fetchCount();

        const intervalId = setInterval(fetchCount, 30000);

        return () => {
            isMounted = false;
            clearInterval(intervalId);
        };
    }, [currentUser]);

    // ============================================================
    // CHARGEMENT DU FLUX DE NOTIFICATIONS A L'OUVERTURE
    // ============================================================
    const fetchNotifications = async () => {
        setLoading(true);
        setError(null);
        try {
            const [listData, countData] = await Promise.all([
                getNotifications({ limit: 20, offset: 0, unreadOnly: false }),
                getUnreadCount(),
            ]);
            setNotifications(Array.isArray(listData) ? listData : []);
            if (typeof countData?.unread_count === "number") {
                setUnreadCount(countData.unread_count);
            }
        } catch (err) {
            if (err?.response?.status === 403) {
                setError("Accès refuse aux notifications.");
            } else {
                setError("Impossible de charger les notifications.");
            }
        } finally {
            setLoading(false);
        }
    };

    const handleToggle = () => {
        if (!isOpen) {
            fetchNotifications();
        }
        setIsOpen((prev) => !prev);
    };

    // ============================================================
    // FERMETURE SUR CLIC EXTERIEUR OU ECHAP
    // ============================================================
    useEffect(() => {
        if (!isOpen) return;

        const handleDocumentClick = (event) => {
            if (
                bellRef.current &&
                !bellRef.current.contains(event.target)
            ) {
                setIsOpen(false);
            }
        };

        const handleKeyDown = (event) => {
            if (event.key === "Escape") {
                setIsOpen(false);
            }
        };

        document.addEventListener("mousedown", handleDocumentClick);
        document.addEventListener("keydown", handleKeyDown);

        return () => {
            document.removeEventListener("mousedown", handleDocumentClick);
            document.removeEventListener("keydown", handleKeyDown);
        };
    }, [isOpen]);

    // ============================================================
    // MARQUER UNE NOTIFICATION COMME LUE
    // ============================================================
    const handleMarkAsRead = async (notif) => {
        if (!notif || notif.read_at || markingIds.has(notif.id)) {
            return;
        }

        setMarkingIds((prev) => new Set(prev).add(notif.id));

        try {
            const updated = await markNotificationAsRead(notif.id);
            setNotifications((prev) =>
                prev.map((item) => (item.id === notif.id ? updated : item))
            );
            setUnreadCount((prev) => Math.max(0, prev - 1));
        } catch {
            // Erreur ignorée sans crash UI
        } finally {
            setMarkingIds((prev) => {
                const next = new Set(prev);
                next.delete(notif.id);
                return next;
            });
        }
    };

    // ============================================================
    // MARQUER TOUTES LES NOTIFICATIONS COMME LUES
    // ============================================================
    const handleMarkAllAsRead = async () => {
        if (markingAll || unreadCount === 0) {
            return;
        }

        setMarkingAll(true);
        try {
            await markAllNotificationsAsRead();
            const now = new Date().toISOString();
            setNotifications((prev) =>
                prev.map((item) => ({
                    ...item,
                    read_at: item.read_at || now,
                }))
            );
            setUnreadCount(0);
        } catch {
            // Erreur ignorée sans crash UI
        } finally {
            setMarkingAll(false);
        }
    };

    // Formate la date en français
    const formatDate = (dateString) => {
        if (!dateString) return "";
        try {
            const date = new Date(dateString);
            return date.toLocaleString("fr-FR", {
                day: "2-digit",
                month: "2-digit",
                year: "numeric",
                hour: "2-digit",
                minute: "2-digit",
            });
        } catch {
            return dateString;
        }
    };

    const ariaLabel =
        unreadCount > 0
            ? `Notifications (${unreadCount} non lue${unreadCount > 1 ? "s" : ""})`
            : "Notifications";

    return (
        <div className="notification-bell-container" ref={bellRef}>
            <button
                type="button"
                className="notification-bell-trigger"
                aria-expanded={isOpen}
                aria-haspopup="dialog"
                aria-label={ariaLabel}
                onClick={handleToggle}
            >
                <Bell size={22} aria-hidden="true" />
                {unreadCount > 0 && (
                    <span className="notification-badge" aria-hidden="true">
                        {unreadCount > 99 ? "99+" : unreadCount}
                    </span>
                )}
            </button>

            {isOpen && (
                <div
                    className="notification-dropdown"
                    role="dialog"
                    aria-label="Panneau de notifications"
                >
                    <div className="notification-dropdown-header">
                        <div className="notification-header-title">
                            <strong>Notifications</strong>
                            {unreadCount > 0 && (
                                <span className="notification-header-badge">
                                    {unreadCount} non lue{unreadCount > 1 ? "s" : ""}
                                </span>
                            )}
                        </div>

                        {unreadCount > 0 && (
                            <button
                                type="button"
                                className="notification-mark-all-btn"
                                onClick={handleMarkAllAsRead}
                                disabled={markingAll}
                                title="Tout marquer comme lu"
                            >
                                <CheckCheck size={16} aria-hidden="true" />
                                <span>{markingAll ? "Traitement..." : "Tout marquer lu"}</span>
                            </button>
                        )}
                    </div>

                    <div className="notification-dropdown-body">
                        {loading && (
                            <div className="notification-status-box">
                                <Loader2 size={24} className="notification-spinner" aria-hidden="true" />
                                <span>Chargement des notifications...</span>
                            </div>
                        )}

                        {!loading && error && (
                            <div className="notification-status-box notification-error">
                                <span>{error}</span>
                            </div>
                        )}

                        {!loading && !error && notifications.length === 0 && (
                            <div className="notification-status-box">
                                <Inbox size={32} className="notification-empty-icon" aria-hidden="true" />
                                <span>Aucune notification</span>
                            </div>
                        )}

                        {!loading && !error && notifications.length > 0 && (
                            <ul className="notification-list" role="list">
                                {notifications.map((notif) => {
                                    const isUnread = !notif.read_at;
                                    const isMarking = markingIds.has(notif.id);

                                    return (
                                        <li
                                            key={notif.id}
                                            className={`notification-item ${
                                                isUnread ? "is-unread" : "is-read"
                                            }`}
                                            onClick={() => isUnread && handleMarkAsRead(notif)}
                                            role={isUnread ? "button" : "listitem"}
                                            tabIndex={isUnread ? 0 : -1}
                                            onKeyDown={(e) => {
                                                if (isUnread && (e.key === "Enter" || e.key === " ")) {
                                                    e.preventDefault();
                                                    handleMarkAsRead(notif);
                                                }
                                            }}
                                            aria-label={`${notif.title}, ${
                                                isUnread ? "non lue" : "lue"
                                            }`}
                                        >
                                            <div className="notification-item-content">
                                                <div className="notification-item-top">
                                                    <strong className="notification-item-title">
                                                        {notif.title}
                                                    </strong>
                                                    <span className="notification-item-date">
                                                        {formatDate(notif.created_at)}
                                                    </span>
                                                </div>

                                                <p className="notification-item-message">
                                                    {notif.message}
                                                </p>

                                                <div className="notification-item-footer">
                                                    {isUnread ? (
                                                        <span className="notification-status-indicator unread">
                                                            <span className="notification-dot" aria-hidden="true" />
                                                            <span>Non lue</span>
                                                        </span>
                                                    ) : (
                                                        <span className="notification-status-indicator read">
                                                            <Check size={14} aria-hidden="true" />
                                                            <span>Lue</span>
                                                        </span>
                                                    )}

                                                    {isUnread && (
                                                        <button
                                                            type="button"
                                                            className="notification-read-action"
                                                            disabled={isMarking}
                                                            onClick={(e) => {
                                                                e.stopPropagation();
                                                                handleMarkAsRead(notif);
                                                            }}
                                                        >
                                                            {isMarking ? "Mise à jour..." : "Marquer comme lue"}
                                                        </button>
                                                    )}
                                                </div>
                                            </div>
                                        </li>
                                    );
                                })}
                            </ul>
                        )}
                    </div>
                </div>
            )}
        </div>
    );
}
