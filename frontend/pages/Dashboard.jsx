import { useEffect, useState } from "react";
import api from "../api/api";

import "../styles/dashboard.css";


export default function Dashboard() {

    const [stats, setStats] = useState(null);

    const [loading, setLoading] = useState(true);

    const [error, setError] = useState("");


    // ============================================================
    // CHARGEMENT DES STATISTIQUES
    // ============================================================

    const loadDashboard = async () => {

        try {

            setLoading(true);

            setError("");

            const response = await api.get(
                "/dashboard/stats"
            );

            setStats(
                response.data
            );

        } catch (err) {

            console.error(
                "Erreur chargement dashboard :",
                err
            );

            setError(
                err.response?.data?.detail ||
                "Impossible de charger les statistiques du dashboard."
            );

        } finally {

            setLoading(false);

        }

    };


    useEffect(() => {

        loadDashboard();

    }, []);


    // ============================================================
    // CHARGEMENT
    // ============================================================

    if (loading) {

        return (

            <div className="dashboard-page">

                <div className="dashboard-loading">

                    <div className="dashboard-spinner"></div>

                    <p>
                        Chargement du tableau de bord...
                    </p>

                </div>

            </div>

        );

    }


    // ============================================================
    // ERREUR
    // ============================================================

    if (error) {

        return (

            <div className="dashboard-page">

                <div className="dashboard-header">

                    <div>

                        <h1>
                            Tableau de bord
                        </h1>

                        <p>
                            Vue d'ensemble de la gestion
                            des archives documentaires.
                        </p>

                    </div>

                </div>


                <div className="dashboard-alert">

                    <div className="dashboard-alert-icon">
                        ⚠️
                    </div>

                    <div>

                        <strong>
                            Impossible de charger le dashboard
                        </strong>

                        <p>
                            {error}
                        </p>

                    </div>

                    <button
                        className="dashboard-retry"
                        onClick={loadDashboard}
                    >
                        Réessayer
                    </button>

                </div>

            </div>

        );

    }


    if (!stats) {
        return null;
    }


    // ============================================================
    // DONNEES
    // ============================================================

    const summary =
        stats.summary || {};

    const documentsByType =
        stats.documents_by_type || [];

    const documentsByNature =
        stats.documents_by_nature || [];

    const documentsByCirconscription =
        stats.documents_by_circonscription || [];

    const recentDocuments =
        stats.recent_documents || [];


    // ============================================================
    // MAX POUR BARRES
    // ============================================================

    const maxType =
        Math.max(
            ...documentsByType.map(
                item => item.total
            ),
            1
        );

    const maxNature =
        Math.max(
            ...documentsByNature.map(
                item => item.total
            ),
            1
        );

    const maxCirconscription =
        Math.max(
            ...documentsByCirconscription.map(
                item => item.total
            ),
            1
        );


    // ============================================================
    // FORMAT DATE
    // ============================================================

    const formatDate = (value) => {

        if (!value) {
            return "—";
        }

        try {

            return new Date(
                value
            ).toLocaleDateString(
                "fr-FR"
            );

        } catch {

            return value;

        }

    };


    // ============================================================
    // NOM TYPE
    // ============================================================

    const getTypeName = (id) => {

        const item =
            documentsByType.find(
                type =>
                    type.id === id
            );

        return item?.libelle || "—";

    };


    // ============================================================
    // NOM NATURE
    // ============================================================

    const getNatureName = (id) => {

        const item =
            documentsByNature.find(
                nature =>
                    nature.id === id
            );

        return item?.libelle || "—";

    };


    // ============================================================
    // NOM CIRCONSCRIPTION
    // ============================================================

    const getCirconscriptionName = (id) => {

        const item =
            documentsByCirconscription.find(
                circo =>
                    circo.id === id
            );

        return item?.nom || "—";

    };


    // ============================================================
    // RENDU
    // ============================================================

    return (

        <div className="dashboard-page">

            {/* ==================================================
                HEADER
            ================================================== */}

            <div className="dashboard-header">

                <div>

                    <h1>
                        Tableau de bord
                    </h1>

                    <p>
                        Vue d'ensemble de la gestion
                        des archives documentaires.
                    </p>

                </div>


                <button
                    className="dashboard-refresh"
                    onClick={loadDashboard}
                    disabled={loading}
                >

                    ↻

                    <span>
                        Actualiser
                    </span>

                </button>

            </div>


            {/* ==================================================
                KPI
            ================================================== */}

            <div className="dashboard-kpis">

                {/* DOCUMENTS */}

                <div className="dashboard-kpi-card">

                    <div className="dashboard-kpi-icon blue">
                        📄
                    </div>

                    <div>

                        <span>
                            Documents actifs
                        </span>

                        <strong>
                            {summary.total_documents ?? 0}
                        </strong>

                    </div>

                </div>


                {/* PIECES JOINTES */}

                <div className="dashboard-kpi-card">

                    <div className="dashboard-kpi-icon green">
                        📎
                    </div>

                    <div>

                        <span>
                            Pièces jointes
                        </span>

                        <strong>
                            {summary.total_attachments ?? 0}
                        </strong>

                    </div>

                </div>


                {/* TYPES */}

                <div className="dashboard-kpi-card">

                    <div className="dashboard-kpi-icon purple">
                        🗂️
                    </div>

                    <div>

                        <span>
                            Types de documents
                        </span>

                        <strong>
                            {summary.total_types ?? 0}
                        </strong>

                    </div>

                </div>


                {/* NATURES */}

                <div className="dashboard-kpi-card">

                    <div className="dashboard-kpi-icon orange">
                        📑
                    </div>

                    <div>

                        <span>
                            Natures
                        </span>

                        <strong>
                            {summary.total_natures ?? 0}
                        </strong>

                    </div>

                </div>


                {/* CIRCONSCRIPTIONS */}

                <div className="dashboard-kpi-card">

                    <div className="dashboard-kpi-icon teal">
                        🏛️
                    </div>

                    <div>

                        <span>
                            Circonscriptions
                        </span>

                        <strong>
                            {
                                summary.total_circonscriptions
                                ?? 0
                            }
                        </strong>

                    </div>

                </div>

            </div>


            {/* ==================================================
                PREMIERE LIGNE : TYPES / NATURES
            ================================================== */}

            <div className="dashboard-grid-two">


                {/* ==================================================
                    DOCUMENTS PAR TYPE
                ================================================== */}

                <div className="dashboard-card">

                    <div className="dashboard-card-header">

                        <div>

                            <h2>
                                Documents par type
                            </h2>

                            <p>
                                Répartition des documents
                                selon leur type.
                            </p>

                        </div>

                        <span className="dashboard-card-icon">
                            🗂️
                        </span>

                    </div>


                    <div className="dashboard-bars">

                        {documentsByType.map(
                            item => (

                                <div
                                    className="dashboard-bar-row"
                                    key={item.id}
                                >

                                    <div className="dashboard-bar-label">

                                        <span>
                                            {item.libelle}
                                        </span>

                                        <strong>
                                            {item.total}
                                        </strong>

                                    </div>


                                    <div className="dashboard-bar-track">

                                        <div
                                            className="dashboard-bar-fill type-bar"
                                            style={{
                                                width:
                                                    `${(
                                                        item.total /
                                                        maxType
                                                    ) * 100}%`
                                            }}
                                        ></div>

                                    </div>

                                </div>

                            )
                        )}

                    </div>

                </div>


                {/* ==================================================
                    DOCUMENTS PAR NATURE
                ================================================== */}

                <div className="dashboard-card">

                    <div className="dashboard-card-header">

                        <div>

                            <h2>
                                Documents par nature
                            </h2>

                            <p>
                                Répartition selon la nature
                                de l'acte foncier.
                            </p>

                        </div>

                        <span className="dashboard-card-icon">
                            📑
                        </span>

                    </div>


                    <div className="dashboard-bars">

                        {documentsByNature.map(
                            item => (

                                <div
                                    className="dashboard-bar-row"
                                    key={item.id}
                                >

                                    <div className="dashboard-bar-label">

                                        <span>
                                            {item.libelle}
                                        </span>

                                        <strong>
                                            {item.total}
                                        </strong>

                                    </div>


                                    <div className="dashboard-bar-track">

                                        <div
                                            className="dashboard-bar-fill nature-bar"
                                            style={{
                                                width:
                                                    `${(
                                                        item.total /
                                                        maxNature
                                                    ) * 100}%`
                                            }}
                                        ></div>

                                    </div>

                                </div>

                            )
                        )}

                    </div>

                </div>

            </div>


            {/* ==================================================
                CIRCONSCRIPTIONS
            ================================================== */}

            <div className="dashboard-card dashboard-circo-card">

                <div className="dashboard-card-header">

                    <div>

                        <h2>
                            Documents par circonscription
                        </h2>

                        <p>
                            Répartition géographique
                            des archives enregistrées.
                        </p>

                    </div>

                    <span className="dashboard-card-icon">
                        🏛️
                    </span>

                </div>


                <div className="dashboard-circo-grid">

                    {documentsByCirconscription.map(
                        item => (

                            <div
                                className="dashboard-circo-item"
                                key={item.id}
                            >

                                <div className="dashboard-circo-top">

                                    <span>
                                        {item.nom}
                                    </span>

                                    <strong>
                                        {item.total}
                                    </strong>

                                </div>


                                <div className="dashboard-bar-track">

                                    <div
                                        className="dashboard-bar-fill circo-bar"
                                        style={{
                                            width:
                                                `${(
                                                    item.total /
                                                    maxCirconscription
                                                ) * 100}%`
                                        }}
                                    ></div>

                                </div>

                            </div>

                        )
                    )}

                </div>

            </div>


            {/* ==================================================
                DERNIERS DOCUMENTS
            ================================================== */}

            <div className="dashboard-card recent-documents-card">

                <div className="dashboard-card-header">

                    <div>

                        <h2>
                            Documents récemment enregistrés
                        </h2>

                        <p>
                            Les cinq derniers documents
                            ajoutés au SIA.
                        </p>

                    </div>

                    <span className="dashboard-card-icon">
                        🕐
                    </span>

                </div>


                {recentDocuments.length === 0 ? (

                    <div className="dashboard-empty">

                        <div>
                            📂
                        </div>

                        <p>
                            Aucun document récent.
                        </p>

                    </div>

                ) : (

                    <div className="dashboard-table-wrapper">

                        <table className="dashboard-table">

                            <thead>

                                <tr>

                                    <th>
                                        Référence
                                    </th>

                                    <th>
                                        Document
                                    </th>

                                    <th>
                                        Type
                                    </th>

                                    <th>
                                        Nature
                                    </th>

                                    <th>
                                        Circonscription
                                    </th>

                                    <th>
                                        Date
                                    </th>

                                </tr>

                            </thead>


                            <tbody>

                                {recentDocuments.map(
                                    document => (

                                        <tr
                                            key={
                                                document.id
                                            }
                                        >

                                            <td>

                                                <span className="dashboard-reference">

                                                    {
                                                        document.reference_archive
                                                    }

                                                </span>

                                            </td>


                                            <td>

                                                <strong className="dashboard-document-name">

                                                    {
                                                        document.nom_document
                                                    }

                                                </strong>

                                            </td>


                                            <td>

                                                <span className="dashboard-badge blue">

                                                    {
                                                        getTypeName(
                                                            document.type_document_id
                                                        )
                                                    }

                                                </span>

                                            </td>


                                            <td>

                                                <span className="dashboard-badge green">

                                                    {
                                                        getNatureName(
                                                            document.phase_id
                                                        )
                                                    }

                                                </span>

                                            </td>


                                            <td>

                                                {
                                                    getCirconscriptionName(
                                                        document.circonscription_id
                                                    )
                                                }

                                            </td>


                                            <td>

                                                {
                                                    formatDate(
                                                        document.date_creation
                                                    )
                                                }

                                            </td>

                                        </tr>

                                    )
                                )}

                            </tbody>

                        </table>

                    </div>

                )}

            </div>

        </div>

    );

}