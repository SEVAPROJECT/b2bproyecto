import React from 'react';
import { HashRouter } from 'react-router-dom';
import { AuthProvider } from './contexts/AuthContext';
import AppRoutes from './routes/AppRoutes';
import './index.css';

const App: React.FC = () => {
    return (
        <HashRouter>
            <AuthProvider>
                <AppRoutes />
            </AuthProvider>
        </HashRouter>
    );
};

export default App;
