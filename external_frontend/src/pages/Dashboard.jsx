import React, { useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { Users, AlertTriangle, CheckCircle, Activity } from 'lucide-react';
import StatCard from '../components/StatCard';
import { checkHealth, getStats } from '../services/api';
import gsap from 'gsap';

const Dashboard = () => {
    const [stats, setStats] = useState({
        total: 1250,
        issues: 87,
        autoUpdated: 42,
        needsReview: 145,
        avgConfidence: 92
    });
    const [isLoading, setIsLoading] = useState(true);
    const [error, setError] = useState(null);
    const [apiConnected, setApiConnected] = useState(false);
    const navigate = useNavigate();

    useEffect(() => {
        const fetchData = async () => {
            try {
                setIsLoading(true);
                await checkHealth();
                setApiConnected(true);

                const statsRes = await getStats();
                if (statsRes.data) {
                    setStats(statsRes.data);
                }
                setError(null);
            } catch (err) {
                console.error('Error fetching data:', err);
                // Use mock data as fallback
                setStats({
                    total: 1250,
                    issues: 87,
                    autoUpdated: 42,
                    needsReview: 145,
                    avgConfidence: 92
                });
                setApiConnected(false);
            } finally {
                setIsLoading(false);
            }
        };

        fetchData();
    }, []);

    useEffect(() => {
        gsap.fromTo('.stat-card',
            { opacity: 0, y: 20 },
            { opacity: 1, y: 0, duration: 0.6, stagger: 0.1 }
        );
    }, [stats]);

    return (
        <div className="space-y-8">
            <div>
                <h1 className="text-4xl font-bold mb-2">Dashboard</h1>
                <p className="text-gray-400">Provider validation system overview</p>
                {!apiConnected && <p className="text-sm text-yellow-400 mt-2">Using demo data (backend not connected)</p>}
            </div>

            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-5 gap-4">
                <StatCard
                    className="stat-card"
                    title="Total Providers"
                    value={stats.total}
                    icon={Users}
                    trend={"+2.5%"}
                />
                <StatCard
                    className="stat-card"
                    title="Issues Found"
                    value={stats.issues}
                    icon={AlertTriangle}
                    trend={"-1.2%"}
                    isAlert
                />
                <StatCard
                    className="stat-card"
                    title="Auto Updated"
                    value={stats.autoUpdated}
                    icon={CheckCircle}
                    trend={"+5.3%"}
                />
                <StatCard
                    className="stat-card"
                    title="Needs Review"
                    value={stats.needsReview}
                    icon={Activity}
                    trend={"+3.1%"}
                />
                <StatCard
                    className="stat-card"
                    title="Avg Confidence"
                    value={`${stats.avgConfidence}%`}
                    icon={CheckCircle}
                    trend="+2.0%"
                />
            </div>

            <div className="glass-panel p-8 rounded-xl">
                <h2 className="text-2xl font-bold mb-4">Getting Started</h2>
                <p className="text-gray-300 mb-6">
                    Welcome to the Provider Data Validation System. Use the navigation menu to:
                </p>
                <ul className="space-y-3 text-gray-300">
                    <li>✓ <strong>Validation:</strong> Validate individual providers against multiple data sources</li>
                    <li>✓ <strong>Directory:</strong> View and manage your provider directory</li>
                    <li>✓ <strong>Review Queue:</strong> Process providers that need manual review</li>
                    <li>✓ <strong>Logs:</strong> View system activity and validation history</li>
                    <li>✓ <strong>Settings:</strong> Configure validation rules and thresholds</li>
                </ul>

                <div className="mt-8 pt-8 border-t border-white/20">
                    <h3 className="text-lg font-semibold mb-4">API Status</h3>
                    <p className="text-sm text-gray-400">
                        Backend running on: <code className="bg-slate-900 px-2 py-1 rounded">http://localhost:8000</code>
                    </p>
                    <p className="text-sm text-gray-400 mt-2">
                        API Documentation: <a href="http://localhost:8000/docs" target="_blank" rel="noopener noreferrer" className="text-blue-400 hover:underline">http://localhost:8000/docs</a>
                    </p>
                </div>
            </div>
        </div>
    );
};

export default Dashboard;
