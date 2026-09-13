import api from "../api/api";

// ============================================================
// LISTER LES NOTIFICATIONS (UTILISATEUR CONNECTE)
// ============================================================

export const getNotifications = async ({
    limit = 50,
    offset = 0,
    unreadOnly = false,
} = {}) => {
    const response = await api.get("/notifications", {
        params: {
            limit,
            offset,
            unread_only: unreadOnly,
        },
    });
    return response.data;
};

// ============================================================
// COMPTEUR DE NOTIFICATIONS NON LUES
// ============================================================

export const getUnreadCount = async () => {
    const response = await api.get("/notifications/unread-count");
    return response.data;
};

// ============================================================
// MARQUER UNE NOTIFICATION COMME LUE
// ============================================================

export const markNotificationAsRead = async (notificationId) => {
    const response = await api.patch(`/notifications/${notificationId}/read`);
    return response.data;
};

// ============================================================
// MARQUER TOUTES LES NOTIFICATIONS COMME LUES
// ============================================================

export const markAllNotificationsAsRead = async () => {
    const response = await api.patch("/notifications/read-all");
    return response.data;
};
