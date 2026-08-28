import { useEffect, useState } from "react";

import api from "../api/api";

import DocumentDetails from "../components/DocumentDetails";

import "../styles/recherche.css";


export default function Recherche() {

    // ============================================================
    // REFERENTIELS
    // ============================================================

    const [types, setTypes] = useState([]);

    const [natures, setNatures] = useState([]);

    const [circonscriptions, setCirconscriptions] = useState([]);


    // ============================================================
    // RESULTATS
    // ============================================================

    const [results, setResults] = useState([]);

    const [searched, setSearched] = useState(false);

    const [loading, setLoading] = useState(false);

    const [error, setError] = useState("");


    // ============================================================
    // DOCUMENT SELECTIONNE
    // ============================================================

    const [selectedDocument, setSelectedDocument] = useState(null);


    // ============================================================
    // FORMULAIRE
    // ============================================================

    const [filters, setFilters] = useState({

        reference_archive: "",

        nom_document: "",

        code_foncier: "",

        numero_ordre: "",

        type_document_id: "",

        phase_id: "",

        circonscription_id: "",

        date_debut: "",

        date_fin: "",

    });


    // ============================================================
    // CHARGEMENT DES REFERENTIELS
    // ============================================================

    const loadReferences = async () => {

        try {

            setError("");

            const [
                typesResponse,
                naturesResponse,
                circonscriptionsResponse,
            ] = await Promise.all([

                api.get(
                    "/document-types/"
                ),

                api.get(
                    "/phases/"
                ),

                api.get(
                    "/circonscriptions/"
                ),

            ]);


            setTypes(
                typesResponse.data
            );

            setNatures(
                naturesResponse.data
            );

            setCirconscriptions(
                circonscriptionsResponse.data
            );

        } catch (err) {

            console.error(
                "Erreur chargement référentiels :",
                err
            );

            setError(
                "Impossible de charger les critères de recherche."
            );

        }

    };


    useEffect(() => {

        loadReferences();

    }, []);


    // ============================================================
    // CHANGEMENT FILTRE
    // ============================================================

    const handleChange = (event) => {

        const {
            name,
            value,
        } = event.target;

        setFilters(
            previous => ({
                ...previous,
                [name]: value,
            })
        );

    };


    // ============================================================
    // RECHERCHE
    // ============================================================

    const handleSearch = async (
        event
    ) => {

        event.preventDefault();

        try {

            setLoading(true);

            setError("");

            const params = {};


            Object.entries(
                filters
            ).forEach(
                ([key, value]) => {

                    if (
                        value !== "" &&
                        value !== null &&
                        value !== undefined
                    ) {

                        params[key] = value;

                    }

                }
            );


            const response = await api.get(
                "/documents/search",
                {
                    params,
                }
            );


            setResults(
                response.data
            );

            setSearched(true);

        } catch (err) {

            console.error(
                "Erreur recherche :",
                err
            );

            setError(
                err.response?.data?.detail ||
                "Impossible d'effectuer la recherche."
            );

            setResults([]);

        } finally {

            setLoading(false);

        }

    };


    // ============================================================
    // REINITIALISER
    // ============================================================

    const handleReset = () => {

        setFilters({

            reference_archive: "",

            nom_document: "",

            code_foncier: "",

            numero_ordre: "",

            type_document_id: "",

            phase_id: "",

            circonscription_id: "",

            date_debut: "",

            date_fin: "",

        });

        setResults([]);

        setSearched(false);

        setError("");

        setSelectedDocument(null);

    };


    // ============================================================
    // DATE
    // ============================================================

    const formatDate = (
        value
    ) => {

        if (!value) {
            return "—";
        }

        const date = new Date(
            value
        );

        if (
            Number.isNaN(
                date.getTime()
            )
        ) {
            return value;
        }

        return date.toLocaleDateString(
            "fr-FR"
        );

    };


    // ============================================================
    // TYPE
    // ============================================================

    const getTypeName = (
        id
    ) => {

        const type =
            types.find(
                item =>
                    item.id === id
            );

        return type?.libelle || "—";

    };


    // ============================================================
    // NATURE
    // ============================================================

    const getNatureName = (
        id
    ) => {

        const nature =
            natures.find(
                item =>
                    item.id === id
            );

        return nature?.libelle || "—";

    };


    // ============================================================
    // CIRCONSCRIPTION
    // ============================================================

    const getCirconscriptionName = (
        id
    ) => {

        const circonscription =
            circonscriptions.find(
                item =>
                    item.id === id
            );

        return circonscription?.nom || "—";

    };


    // ============================================================
    // PREPARER LE DOCUMENT POUR LA FICHE
    // ============================================================

    const prepareDocumentDetails = (
        document
    ) => {

        return {

            ...document,

            type_document:
                getTypeName(
                    document.type_document_id
                ),

            phase:
                getNatureName(
                    document.phase_id
                ),

            circonscription:
                getCirconscriptionName(
                    document.circonscription_id
                ),

        };

    };


    // ============================================================
    // OUVRIR LA FICHE
    // ============================================================

    const handleViewDocument = (
        document
    ) => {

        setSelectedDocument(
            prepareDocumentDetails(
                document
            )
        );

    };


    // ============================================================
    // RENDU
    // ============================================================

    return (

        <div className="recherche-page">


            {/* ==================================================
                HEADER
            ================================================== */}

            <div className="recherche-header">

                <div>

                    <h1>
                        Recherche des archives
                    </h1>

                    <p>
                        Recherchez rapidement un document
                        dans les archives foncières.
                    </p>

                </div>

            </div>


            {/* ==================================================
                ERREUR
            ================================================== */}

            {error && (

                <div className="recherche-alert">

                    {error}

                </div>

            )}


            {/* ==================================================
                FORMULAIRE
            ================================================== */}

            <div className="recherche-card">

                <div className="recherche-card-header">

                    <div>

                        <h2>
                            Recherche avancée
                        </h2>

                        <p>
                            Combinez plusieurs critères
                            pour affiner les résultats.
                        </p>

                    </div>

                    <span className="recherche-icon">
                        🔎
                    </span>

                </div>


                <form
                    className="recherche-form"
                    onSubmit={
                        handleSearch
                    }
                >


                    {/* REFERENCE */}

                    <div className="recherche-field">

                        <label>
                            Référence archive
                        </label>

                        <input
                            type="text"
                            name="reference_archive"
                            value={
                                filters.reference_archive
                            }
                            onChange={
                                handleChange
                            }
                            placeholder="Ex. KN-GOM-B2-R2-C100-012"
                        />

                    </div>


                    {/* NOM */}

                    <div className="recherche-field">

                        <label>
                            Nom du document
                        </label>

                        <input
                            type="text"
                            name="nom_document"
                            value={
                                filters.nom_document
                            }
                            onChange={
                                handleChange
                            }
                            placeholder="Ex. Dossier immobilier"
                        />

                    </div>


                    {/* COTE */}

                    <div className="recherche-field">

                        <label>
                            Cote foncier
                        </label>

                        <input
                            type="text"
                            name="code_foncier"
                            value={
                                filters.code_foncier
                            }
                            onChange={
                                handleChange
                            }
                            placeholder="Ex. KN-GOM-B2-R2-C100"
                        />

                    </div>


                    {/* NUMCAD */}

                    <div className="recherche-field">

                        <label>
                            NumCad / Réf / Indice
                        </label>

                        <input
                            type="text"
                            name="numero_ordre"
                            value={
                                filters.numero_ordre
                            }
                            onChange={
                                handleChange
                            }
                            placeholder="Ex. JA/56/GOMBE"
                        />

                    </div>


                    {/* TYPE */}

                    <div className="recherche-field">

                        <label>
                            Type de document
                        </label>

                        <select
                            name="type_document_id"
                            value={
                                filters.type_document_id
                            }
                            onChange={
                                handleChange
                            }
                        >

                            <option value="">
                                Tous les types
                            </option>

                            {types.map(
                                type => (

                                    <option
                                        key={
                                            type.id
                                        }
                                        value={
                                            type.id
                                        }
                                    >
                                        {
                                            type.libelle
                                        }
                                    </option>

                                )
                            )}

                        </select>

                    </div>


                    {/* NATURE */}

                    <div className="recherche-field">

                        <label>
                            Nature du document
                        </label>

                        <select
                            name="phase_id"
                            value={
                                filters.phase_id
                            }
                            onChange={
                                handleChange
                            }
                        >

                            <option value="">
                                Toutes les natures
                            </option>

                            {natures.map(
                                nature => (

                                    <option
                                        key={
                                            nature.id
                                        }
                                        value={
                                            nature.id
                                        }
                                    >
                                        {
                                            nature.libelle
                                        }
                                    </option>

                                )
                            )}

                        </select>

                    </div>


                    {/* CIRCONSCRIPTION */}

                    <div className="recherche-field">

                        <label>
                            Circonscription
                        </label>

                        <select
                            name="circonscription_id"
                            value={
                                filters.circonscription_id
                            }
                            onChange={
                                handleChange
                            }
                        >

                            <option value="">
                                Toutes les circonscriptions
                            </option>

                            {circonscriptions.map(
                                circonscription => (

                                    <option
                                        key={
                                            circonscription.id
                                        }
                                        value={
                                            circonscription.id
                                        }
                                    >
                                        {
                                            circonscription.nom
                                        }
                                    </option>

                                )
                            )}

                        </select>

                    </div>


                    {/* DATE DEBUT */}

                    <div className="recherche-field">

                        <label>
                            Date début
                        </label>

                        <input
                            type="date"
                            name="date_debut"
                            value={
                                filters.date_debut
                            }
                            onChange={
                                handleChange
                            }
                        />

                    </div>


                    {/* DATE FIN */}

                    <div className="recherche-field">

                        <label>
                            Date fin
                        </label>

                        <input
                            type="date"
                            name="date_fin"
                            value={
                                filters.date_fin
                            }
                            onChange={
                                handleChange
                            }
                        />

                    </div>


                    {/* ACTIONS */}

                    <div className="recherche-actions">

                        <button
                            type="button"
                            className="recherche-reset"
                            onClick={
                                handleReset
                            }
                        >
                            Réinitialiser
                        </button>


                        <button
                            type="submit"
                            className="recherche-submit"
                            disabled={
                                loading
                            }
                        >

                            {loading
                                ? "Recherche..."
                                : "🔎 Rechercher"
                            }

                        </button>

                    </div>

                </form>

            </div>


            {/* ==================================================
                RESULTATS
            ================================================== */}

            {searched && (

                <div className="recherche-card results-card">

                    <div className="recherche-card-header">

                        <div>

                            <h2>
                                Résultats de recherche
                            </h2>

                            <p>

                                {results.length}

                                {" "}

                                document
                                {
                                    results.length !== 1
                                        ? "s"
                                        : ""
                                }

                                {" trouvé"}
                                {
                                    results.length !== 1
                                        ? "s"
                                        : ""
                                }

                            </p>

                        </div>

                    </div>


                    {results.length === 0 ? (

                        <div className="recherche-empty">

                            <div className="recherche-empty-icon">
                                🔎
                            </div>

                            <h3>
                                Aucun document trouvé
                            </h3>

                            <p>
                                Aucun document ne correspond
                                aux critères sélectionnés.
                            </p>

                        </div>

                    ) : (

                        <div className="recherche-table-wrapper">

                            <table className="recherche-table">

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

                                        <th>
                                            Actions
                                        </th>

                                    </tr>

                                </thead>


                                <tbody>

                                    {results.map(
                                        document => (

                                            <tr
                                                key={
                                                    document.id
                                                }
                                            >

                                                <td>

                                                    <span className="recherche-reference">

                                                        {
                                                            document.reference_archive
                                                        }

                                                    </span>

                                                </td>


                                                <td>

                                                    <strong>

                                                        {
                                                            document.nom_document
                                                        }

                                                    </strong>

                                                    <small>

                                                        {
                                                            document.code_foncier ||
                                                            "Cote non renseignée"
                                                        }

                                                    </small>

                                                </td>


                                                <td>

                                                    <span className="recherche-badge blue">

                                                        {
                                                            getTypeName(
                                                                document.type_document_id
                                                            )
                                                        }

                                                    </span>

                                                </td>


                                                <td>

                                                    <span className="recherche-badge green">

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


                                                {/* ACTION */}

                                                <td>

                                                    <button
                                                        type="button"
                                                        className="recherche-view-button"
                                                        title="Consulter le document"
                                                        onClick={() =>
                                                            handleViewDocument(
                                                                document
                                                            )
                                                        }
                                                    >
                                                        👁️
                                                    </button>

                                                </td>

                                            </tr>

                                        )
                                    )}

                                </tbody>

                            </table>

                        </div>

                    )}

                </div>

            )}


            {/* ==================================================
                FICHE DOCUMENT
            ================================================== */}

            {selectedDocument && (

                <DocumentDetails
                    document={
                        selectedDocument
                    }
                    onClose={() =>
                        setSelectedDocument(
                            null
                        )
                    }
                />

            )}

        </div>

    );

}