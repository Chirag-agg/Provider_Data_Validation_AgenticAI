import React from 'react';
import { BrowserRouter as Router, Routes, Route } from 'react-router-dom';
import Layout from './components/Layout';
import Dashboard from './pages/Dashboard';
import Directory from './pages/Directory';
import ProviderDetail from './pages/ProviderDetail';
import Validation from './pages/Validation';
import ReviewQueue from './pages/ReviewQueue';
import Logs from './pages/Logs';
import Settings from './pages/Settings';
import MapPage from './pages/MapPage';
import DriftMonitoring from './pages/DriftMonitoring';
import BulkOutreach from './pages/BulkOutreach';

function App() {
    return (
        <Router>
            <Routes>
                <Route path="/map" element={<MapPage />} />
                <Route path="/" element={<Layout />}>
                    <Route index element={<Dashboard />} />
                    <Route path="directory" element={<Directory />} />
                    <Route path="provider/:id" element={<ProviderDetail />} />
                    <Route path="validation" element={<Validation />} />
                    <Route path="drift-monitoring" element={<DriftMonitoring />} />
                    <Route path="review" element={<ReviewQueue />} />
                    <Route path="bulk-outreach" element={<BulkOutreach />} />
                    <Route path="logs" element={<Logs />} />
                    <Route path="settings" element={<Settings />} />
                </Route>
            </Routes>
        </Router>
    );
}

export default App;
