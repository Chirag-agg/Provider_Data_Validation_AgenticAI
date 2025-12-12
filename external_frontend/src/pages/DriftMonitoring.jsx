import React, { useState } from 'react';
import axios from 'axios';
import { AlertCircle, TrendingUp, Clock, Shield, Activity } from 'lucide-react';

const DriftMonitoring = () => {
    const [providerName, setProviderName] = useState('');
    const [loading, setLoading] = useState(false);
    const [result, setResult] = useState(null);
    const [error, setError] = useState(null);

    const monitorDrift = async () => {
        if (!providerName.trim()) {
            setError('Please enter a provider name');
            return;
        }

        setLoading(true);
        setError(null);
        setResult(null);


        try {
            const response = await axios.post(`http://localhost:8000/drift-monitor?provider_name=${encodeURIComponent(providerName)}`);
            console.log('Full API Response:', response);
            console.log('Response Data:', response.data);
            console.log('Result Data:', response.data.data);
            setResult(response.data.data);
        } catch (err) {
            console.error('Error:', err);
            console.error('Error Response:', err.response);
            setError(err.response?.data?.detail || 'Failed to monitor drift. Please try again.');
        } finally {
            setLoading(false);
        }
    };

    const getRiskColor = (score) => {
        if (score >= 50) return 'text-red-500';
        if (score >= 30) return 'text-yellow-500';
        return 'text-green-500';
    };

    const getRiskBgColor = (score) => {
        if (score >= 50) return 'bg-red-500/10 border-red-500/30';
        if (score >= 30) return 'bg-yellow-500/10 border-yellow-500/30';
        return 'bg-green-500/10 border-green-500/30';
    };

    const getRiskLabel = (score) => {
        if (score >= 50) return 'HIGH RISK';
        if (score >= 30) return 'MEDIUM RISK';
        return 'LOW RISK';
    };

    return (
        <div className="max-w-6xl mx-auto space-y-6">
            {/* Header */}
            <div className="bg-gradient-to-r from-purple-900/40 to-indigo-900/40 backdrop-blur-md border border-purple-500/20 rounded-2xl p-8">
                <div className="flex items-center gap-4">
                    <div className="p-3 bg-purple-500/20 rounded-xl">
                        <Activity className="w-8 h-8 text-purple-400" />
                    </div>
                    <div>
                        <h1 className="text-3xl font-bold bg-gradient-to-r from-purple-400 to-indigo-400 bg-clip-text text-transparent">
                            Credential Drift Monitoring
                        </h1>
                        <p className="text-gray-400 mt-1">
                            Detect changes in provider credentials over time
                        </p>
                    </div>
                </div>
            </div>

            {/* Search Box */}
            <div className="bg-gray-900/60 backdrop-blur-md border border-gray-700/50 rounded-2xl p-6">
                <div className="flex gap-4">
                    <input
                        type="text"
                        value={providerName}
                        onChange={(e) => setProviderName(e.target.value)}
                        onKeyPress={(e) => e.key === 'Enter' && monitorDrift()}
                        placeholder="Enter provider name (e.g., Dr Shalini Rao)"
                        className="flex-1 px-6 py-4 bg-gray-800/50 border border-gray-700/50 rounded-xl text-white placeholder-gray-500 focus:outline-none focus:ring-2 focus:ring-purple-500/50 transition-all"
                    />
                    <button
                        onClick={monitorDrift}
                        disabled={loading}
                        className="px-8 py-4 bg-gradient-to-r from-purple-600 to-indigo-600 rounded-xl font-semibold hover:from-purple-500 hover:to-indigo-500 transition-all disabled:opacity-50"
                    >
                        {loading ? (
                            <div className="flex items-center gap-2">
                                <div className="w-5 h-5 border-2 border-white/30 border-t-white rounded-full animate-spin"></div>
                                Analyzing...
                            </div>
                        ) : (
                            'Monitor Drift'
                        )}
                    </button>
                </div>

                {error && (
                    <div className="mt-4 p-4 bg-red-500/10 border border-red-500/30 rounded-xl flex items-start gap-3">
                        <AlertCircle className="w-5 h-5 text-red-400 mt-0.5" />
                        <div className="text-red-400">{error}</div>
                    </div>
                )}
            </div>

            {/* Results */}
            {result && (
                <div className="space-y-6">
                    {/* Risk Score Card */}
                    <div className={`backdrop-blur-md border rounded-2xl p-8 ${getRiskBgColor(result.risk_increase)}`}>
                        <div className="flex items-center justify-between">
                            <div className="flex items-center gap-6">
                                <div className="p-4 bg-white/10 rounded-2xl">
                                    <Shield className={`w-12 h-12 ${getRiskColor(result.risk_increase)}`} />
                                </div>
                                <div>
                                    <div className="text-sm text-gray-400 mb-1">Provider: {result.provider}</div>
                                    <div className={`text-5xl font-bold ${getRiskColor(result.risk_increase)} mb-2`}>
                                        {result.risk_increase}%
                                    </div>
                                    <div className={`text-sm font-semibold ${getRiskColor(result.risk_increase)}`}>
                                        {getRiskLabel(result.risk_increase)}
                                    </div>
                                </div>
                            </div>
                            <div className="flex items-center gap-2 text-gray-400">
                                <Clock className="w-5 h-5" />
                                <span>Compared to historical data</span>
                            </div>
                        </div>
                    </div>

                    {/* Changes Detected */}
                    <div className="bg-gray-900/60 backdrop-blur-md border border-gray-700/50 rounded-2xl p-6">
                        <div className="flex items-center gap-3 mb-6">
                            <TrendingUp className="w-6 h-6 text-purple-400" />
                            <h2 className="text-2xl font-bold">Changes Detected</h2>
                            <span className="px-3 py-1 bg-purple-500/20 border border-purple-500/30 rounded-full text-sm text-purple-300">
                                {result.changes_detected?.length || 0} changes
                            </span>
                        </div>

                        {result.changes_detected && result.changes_detected.length > 0 ? (
                            <div className="space-y-3">
                                {result.changes_detected.map((change, index) => (
                                    <div
                                        key={index}
                                        className="p-4 bg-gray-800/50 border border-gray-700/50 rounded-xl flex items-start gap-3 hover:bg-gray-800/70 transition-colors"
                                    >
                                        <div className="p-2 bg-orange-500/20 rounded-lg mt-0.5">
                                            <AlertCircle className="w-5 h-5 text-orange-400" />
                                        </div>
                                        <div className="flex-1">
                                            <p className="text-white font-medium">{change}</p>
                                            {change.includes('→') && (
                                                <p className="text-sm text-gray-400 mt-1">
                                                    Historical value → Current value
                                                </p>
                                            )}
                                        </div>
                                    </div>
                                ))}
                            </div>
                        ) : (
                            <div className="p-8 text-center">
                                <div className="inline-block p-4 bg-green-500/20 rounded-2xl mb-4">
                                    <Shield className="w-12 h-12 text-green-400" />
                                </div>
                                <p className="text-xl font-semibold text-green-400">No Changes Detected</p>
                                <p className="text-gray-400 mt-2">
                                    Provider credentials match historical data
                                </p>
                            </div>
                        )}
                    </div>

                    {/* Info Box */}
                    <div className="bg-blue-500/10 border border-blue-500/30 rounded-xl p-4 flex items-start gap-3">
                        <div className="p-2 bg-blue-500/20 rounded-lg">
                            <AlertCircle className="w-5 h-5 text-blue-400" />
                        </div>
                        <div className="text-sm text-blue-300">
                            <p className="font-semibold mb-1">About Risk Scores</p>
                            <p className="text-blue-200/80">
                                Risk scores are calculated based on the severity of changes: License status changes (+30),
                                Hospital affiliation changes (+20), Contact updates (+15), and Specialty changes (+10).
                            </p>
                        </div>
                    </div>
                </div>
            )}

            {/* Sample Providers */}
            {!result && !loading && (
                <div className="bg-gray-900/60 backdrop-blur-md border border-gray-700/50 rounded-2xl p-6">
                    <h3 className="text-lg font-semibold mb-4 text-gray-300">Try with sample providers:</h3>
                    <div className="flex flex-wrap gap-3">
                        {['Dr Shalini Rao', 'Dr Aarav Mehta', 'Dr Ritu Sharma'].map((name) => (
                            <button
                                key={name}
                                onClick={() => setProviderName(name)}
                                className="px-4 py-2 bg-gray-800/50 border border-gray-700/50 rounded-lg hover:bg-gray-800 hover:border-purple-500/50 transition-all"
                            >
                                {name}
                            </button>
                        ))}
                    </div>
                </div>
            )}
        </div>
    );
};

export default DriftMonitoring;
