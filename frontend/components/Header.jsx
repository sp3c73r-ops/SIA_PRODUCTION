import { Bell, UserCircle } from "lucide-react";

export default function Header() {
    return (
        <header className="header">

            <div>
                <h2>Système Intégré des Archives Documentaires</h2>
            </div>

            <div className="header-right">

                <Bell size={22} />

                <UserCircle size={35} />

            </div>

        </header>
    );
}