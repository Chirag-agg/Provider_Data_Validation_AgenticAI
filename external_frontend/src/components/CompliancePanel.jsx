import { useState, useEffect } from 'react';
import { AlertTriangle, Shield, TrendingUp, CheckCircle, XCircle } from 'lucide-react';

export default function CompliancePanel({ providerId, providerData }) {
    const [compliance, setCompliance] = useState(null);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState(null);

    useEffect(() => {
        if (providerId) {
            fetchCompliance();
        }
    }, [providerId]);

    const fetchCompliance = async () => {
        try {
            setLoading(true);
            setError(null);
            console.log('Fetching compliance for provider:', providerId);

            const response = await fetch(`http://localhost:8000/compliance/check/${providerId}`);
            console.log('Response status:', response.status);

            const data = await response.json();
            console.log('Compliance data received:', data);

            if (data.success && data.data) {
                setCompliance(data.data);
            } else {
                console.error('Compliance response not successful:', data);
                setError('Failed to load compliance data');
            }
        } catch (err) {
            console.error('Compliance fetch error:', err);
            setError('Failed to load compliance data: ' + err.message);
        } finally {
            setLoading(false);
        }
    };

    const recalculate = async () => {
        try {
            setLoading(true);
            setError(null);
            console.log('Recalculating compliance for provider:', providerId);

            // Prepare provider data for compliance calculation
            const requestData = providerData ? {
                id: providerId,
                full_name: providerData.name || providerData.provider_name || 'Unknown',
                first_name: providerData.first_name || '',
                last_name: providerData.last_name || '',
                npi: providerData.npi || '',
                license: providerData.license_number || providerData.license || '',
                board_certified: providerData.board_certified || false,
                updated_at: providerData.updated_at || new Date().toISOString()
            } : { id: providerId };

            console.log('Sending request data:', requestData);

            const response = await fetch(`http://localhost:8000/compliance/recalculate/${providerId}`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(requestData)
            });

            console.log('Recalculate response status:', response.status);
            const data = await response.json();
            console.log('Recalculate response:', data);

            if (data.success && data.data) {
                setCompliance(data.data);
                console.log('Compliance updated:', data.data);
            } else {
                const errorMsg = data.error || 'Failed to recalculate compliance';
                console.error('Recalculate error:', errorMsg);
                setError(errorMsg);
            }
        } catch (err) {
            console.error('Recalculate exception:', err);
            setError('Failed to recalculate compliance: ' + err.message);
        } finally {
            setLoading(false);
        }
    };

    if (loading) {
        return (
            <div className="bg-gray-900 rounded-lg shadow-lg p-6">
                <div className="animate-pulse">
                    <div className="h-8 bg-gray-700 rounded w-1/3 mb-4"></div>
                    <div className="h-4 bg-gray-700 rounded w-2/3"></div>
                </div>
            </div>
        );
    }

    if (error) {
        return (
            <div className="bg-gray-900 rounded-lg shadow-lg p-6">
                <div className="flex items-center text-red-400">
                    <XCircle className="w-5 h-5 mr-2" />
                    <span>{error}</span>
                </div>
            </div>
        );
    }

    if (!compliance) {
        return null;
    }

    const getRiskColor = (color) => {
        const colors = {
            green: 'bg-green-900/30 text-green-300 border-green-700 shadow-green-500/20',
            yellow: 'bg-yellow-900/30 text-yellow-300 border-yellow-700 shadow-yellow-500/20',
            orange: 'bg-orange-900/30 text-orange-300 border-orange-700 shadow-orange-500/20',
            red: 'bg-red-900/30 text-red-300 border-red-700 shadow-red-500/20',
            gray: 'bg-gray-800 text-gray-300 border-gray-700'
        };
        return colors[color] || colors.gray;
    };

    // Show initial calculation prompt if not calculated
    if (compliance.risk_level === 'UNKNOWN' || !compliance.calculated_at) {
        return (
            <div className="bg-gray-900 rounded-lg shadow-lg p-6">
                <div className="flex items-center justify-between border-b border-gray-700 pb-4 mb-4">
                    <div className="flex items-center">
                        <Shield className="w-6 h-6 mr-2 text-blue-400" />
                        <h2 className="text-2xl font-bold text-white">Compliance Intelligence</h2>
                    </div>
                </div>

                <div className="bg-gray-800 rounded-lg p-8 text-center">
                    <Shield className="w-16 h-16 mx-auto mb-4 text-gray-500" />
                    <h3 className="text-lg font-semibold text-gray-200 mb-2">
                        Compliance Status Not Calculated
                    </h3>
                    <p className="text-gray-400 mb-6">
                        Run compliance analysis to check this provider against sanction registries and calculate their Compliance Risk Index (CRI).
                    </p>
                    <button
                        onClick={recalculate}
                        className="px-6 py-3 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition font-semibold shadow-lg"
                    >
                        Calculate Compliance Status
                    </button>
                </div>
            </div>
        );
    }

    return (
        <div className="bg-gray-900 rounded-lg shadow-lg p-6 space-y-6">
            {/* Header */}
            <div className="flex items-center justify-between border-b border-gray-700 pb-4">
                <div className="flex items-center">
                    <Shield className="w-6 h-6 mr-2 text-blue-400" />
                    <h2 className="text-2xl font-bold text-white">Compliance Intelligence</h2>
                </div>
                <button
                    onClick={recalculate}
                    className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition shadow-lg font-semibold"
                >
                    Recalculate
                </button>
            </div>

            {/* CRI Score */}
            <div className={`border-2 rounded-lg p-6 shadow-lg ${getRiskColor(compliance.risk_color)}`}>
                <div className="flex items-center justify-between">
                    <div>
                        <div className="text-sm font-semibold uppercase tracking-wide mb-2 opacity-90">
                            COMPLIANCE RISK INDEX
                        </div>
                        <div className="text-6xl font-bold mb-2">
                            {compliance.cri_score}
                        </div>
                        <div className="text-xl font-bold uppercase tracking-wide">
                            {compliance.risk_level} RISK
                        </div>
                    </div>
                    <div className="text-right opacity-80">
                        <TrendingUp className="w-16 h-16" />
                    </div>
                </div>
            </div>

            {/* Risk Factors */}
            {compliance.factors && compliance.factors.length > 0 && (
                <div className="bg-orange-900/20 border border-orange-800/50 rounded-lg p-4">
                    <h3 className="text-lg font-semibold mb-3 flex items-center text-orange-400">
                        <AlertTriangle className="w-5 h-5 mr-2" />
                        Risk Factors
                    </h3>
                    <ul className="space-y-2">
                        {compliance.factors.map((factor, idx) => (
                            <li key={idx} className="flex items-start">
                                <span className="text-orange-400 mr-2">•</span>
                                <span className="text-gray-300">{factor}</span>
                            </li>
                        ))}
                    </ul>
                </div>
            )}

            {/* Sanction Matches */}
            {compliance.sanction_matches && compliance.sanction_matches.length > 0 && (
                <div className="bg-red-900/20 border-2 border-red-800/50 rounded-lg p-4">
                    <h3 className="text-lg font-semibold mb-3 flex items-center text-red-400">
                        <XCircle className="w-5 h-5 mr-2" />
                        Sanction Matches ({compliance.sanction_matches.length})
                    </h3>
                    <div className="space-y-3">
                        {compliance.sanction_matches.map((match, idx) => (
                            <div key={idx} className="bg-gray-800 rounded p-3 border border-red-700/50">
                                <div className="flex justify-between items-start mb-2">
                                    <span className="font-semibold text-white">{match.matched_name}</span>
                                    <span className="text-sm px-2 py-1 bg-red-600 text-white rounded">
                                        {match.similarity_score}% match
                                    </span>
                                </div>
                                <div className="text-sm text-gray-400">
                                    <div><strong className="text-gray-300">Source:</strong> {match.source}</div>
                                    <div><strong className="text-gray-300">Effective:</strong> {match.effective_date}</div>
                                    <div><strong className="text-gray-300">Reason:</strong> {match.reason}</div>
                                </div>
                            </div>
                        ))}
                    </div>
                </div>
            )}

            {/* No Issues */}
            {(!compliance.sanction_matches || compliance.sanction_matches.length === 0) &&
                compliance.cri_score === 0 && (
                    <div className="bg-green-900/20 border-2 border-green-700/50 rounded-lg p-4 flex items-center">
                        <CheckCircle className="w-6 h-6 mr-3 text-green-400" />
                        <span className="text-green-300 font-semibold">
                            No compliance issues detected
                        </span>
                    </div>
                )}

            {/* Timestamp */}
            <div className="text-sm text-gray-400 text-right pt-2 border-t border-gray-800">
                Last calculated: {new Date(compliance.calculated_at).toLocaleString()}
            </div>
        </div>
    );
}
