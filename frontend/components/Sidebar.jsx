import { NavLink } from "react-router-dom";

import {
    LayoutDashboard,
    FolderOpen,
    Search,
    Archive,
    Paperclip,
    Settings
} from "lucide-react";

export default function Sidebar() {

    return (

        <aside className="sidebar">

            <div className="logo">

                <h2>SIA</h2>

                <span>Archives</span>

            </div>

            <nav>

                <NavLink to="/">

                    <LayoutDashboard size={20} />

                    Dashboard

                </NavLink>

                <NavLink to="/documents">

                    <FolderOpen size={20} />

                    Documents

                </NavLink>

                <NavLink to="/recherche">

                    <Search size={20} />

                    Recherche

                </NavLink>

                <NavLink to="/mouvements">

                    <Archive size={20} />

                    Mouvements

                </NavLink>

                <NavLink to="/pieces-jointes">

                    <Paperclip size={20} />

                    Pièces jointes

                </NavLink>

                <NavLink to="/parametres">

                    <Settings size={20} />

                    Paramètres

                </NavLink>

            </nav>

        </aside>

    );

}