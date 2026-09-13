import RoutesApp from "./routes";
import { AuthProvider } from "./contexts/AuthContext";
import WelcomePopup from "./components/WelcomePopup";

function App() {
    return (
        <AuthProvider>
            <RoutesApp />
            <WelcomePopup />
        </AuthProvider>
    );
}

export default App;