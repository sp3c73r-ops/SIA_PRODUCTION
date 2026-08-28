import { Outlet } from "react-router-dom";
import Sidebar from "./Sidebar";
import Header from "./Header";

import "../styles/layout.css";

export default function Layout() {
    return (
        <div className="app">

            <Sidebar />

            <div className="main-content">

                <Header />

                <main className="page-content">

                    <Outlet />

                </main>

            </div>

        </div>
    );
}