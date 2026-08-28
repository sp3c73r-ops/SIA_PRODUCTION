import { Routes, Route } from "react-router-dom";

import Layout from "./components/Layout";

import Dashboard from "./pages/Dashboard";
import Documents from "./pages/Documents";
import Recherche from "./pages/Recherche";
import Mouvements from "./pages/Mouvements";
import PiecesJointes from "./pages/PiecesJointes";
import Parametres from "./pages/Parametres";
import Login from "./pages/Login";


export default function RoutesApp() {

    return (

        <Routes>

            {/* PAGE DE CONNEXION */}

            <Route
                path="/login"
                element={<Login />}
            />


            {/* APPLICATION */}

            <Route element={<Layout />}>

                <Route
                    path="/"
                    element={<Dashboard />}
                />

                <Route
                    path="/documents"
                    element={<Documents />}
                />

                <Route
                    path="/recherche"
                    element={<Recherche />}
                />

                <Route
                    path="/mouvements"
                    element={<Mouvements />}
                />

                <Route
                    path="/pieces-jointes"
                    element={<PiecesJointes />}
                />

                <Route
                    path="/parametres"
                    element={<Parametres />}
                />

            </Route>

        </Routes>

    );

}