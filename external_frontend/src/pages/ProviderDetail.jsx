import React, { useEffect, useState } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { ArrowLeft, CheckCircle, AlertTriangle, Clock, Shield } from 'lucide-react';
import gsap from 'gsap';

const ProviderDetail = () => {
    const { id } = useParams();
    const navigate = useNavigate();
    const [provider, setProvider] = useState(null);
    const [loading, setLoading] = useState(true);

    useEffect(() => {
        fetchProvider();
    }, [id]);

    const fetchProvider = async () => {
        try {
            // Load validation results from localStorage
            const storedResults = localStorage.getItem('validationResults');

            if (!storedResults) {
                setProvider({ id, name: 'Unknown Provider', specialty: 'N/A', verified: false, status: 'Not Found' });
                setLoading(false);
                return;
            }

            const results = JSON.parse(storedResults);
            // Find the provider by ID
            const validationResult = results.find(r => r.provider_id === id);

            if (!validationResult) {
                setProvider({ id, name: 'Unknown Provider', specialty: 'N/A', verified: false, status: 'Not Found' });
                setLoading(false);
                return;
            }

            // Map validation result to provider detail format
            const providerData = {
                id: validationResult.provider_id,
                name: validationResult.provider_name,
                specialty: validationResult.verified_specialty || 'Unknown',
                phone: validationResult.verified_phone || 'N/A',
                address: validationResult.verified_address || 'N/A',
                email: validationResult.verified_email || 'N/A',
                npi: validationResult.npi_number || 'N/A',

                // Get old values from discrepancies
                oldPhone: validationResult.discrepancies?.phone?.current_value || validationResult.verified_phone,
                oldAddress: validationResult.discrepancies?.address?.current_value || validationResult.verified_address,
                oldSpecialty: validationResult.discrepancies?.specialty?.current_value,

                // All discrepancies for comprehensive display
                discrepancies: validationResult.discrepancies || {},

                // Status mapping
                status: validationResult.validation_status === 'VERIFIED' ? 'Verified' :
                    validationResult.validation_status === 'PARTIALLY_VERIFIED' ? 'Needs Review' :
                        validationResult.validation_status === 'FLAGGED' ? 'Needs Review' : 'Auto-Updated',
                verified: validationResult.validation_status === 'VERIFIED',
                validationStatus: validationResult.validation_status,

                // Confidence scores
                confidence: Math.round(validationResult.confidence_scores.overall_confidence * 100),
                confidenceScore: Math.round(validationResult.confidence_scores.overall_confidence * 100),
                confidenceScores: validationResult.confidence_scores,

                // Source information - store ALL matched sources
                sourcesMatched: validationResult.sources_matched || [],
                sourcesChecked: validationResult.sources_checked || [],
                lastUpdated: validationResult.validation_timestamp || new Date().toISOString(),

                // Additional metadata
                matchedSources: validationResult.sources_matched?.length || 0,

                // License and hospital info
                licenseInfo: validationResult.license_info,
                hospitalAffiliation: validationResult.hospital_affiliation,

                // VALIDATION ISSUES & FLAGS
                issues: validationResult.issues || [],
                riskFlags: validationResult.risk_flags || [],
                requiresManualReview: validationResult.requires_manual_review || false,
                requiresContactVerification: validationResult.requires_contact_verification || false,
                nextSteps: validationResult.next_steps || []
            };

            setProvider(providerData);
            setLoading(false);
        } catch (error) {
            console.error("Error fetching provider", error);
            setProvider({ id, name: 'Unknown Provider', specialty: 'N/A', verified: false, status: 'Not Found' });
            setLoading(false);
        }
    };

    if (loading) return <div className="p-8 text-center">Loading...</div>;
    if (!provider) return <div className="p-8 text-center">Provider not found</div>;

    return (
        <div className="space-y-6 animate-fade-in">
            <button onClick={() => navigate(-1)} className="flex items-center gap-2 text-slate-400 hover:text-white transition-colors">
                <ArrowLeft size={18} /> Back to Directory
            </button>

            <div className="flex justify-between items-start">
                <div>
                    <h1 className="text-3xl font-poster text-white">{provider.name}</h1>
                    <div className="flex items-center gap-4 mt-2 text-sm text-slate-400">
                        <span className="bg-white/5 px-2 py-1 rounded border border-white/10">ID: {provider.id}</span>
                        <span>{provider.specialty}</span>
                    </div>
                </div>
                <div className={`px-4 py-2 rounded-full border ${provider.status === 'Verified' ? 'bg-green-500/20 border-green-500/30 text-green-400' :
                    provider.status === 'Needs Review' ? 'bg-red-500/20 border-red-500/30 text-red-400' :
                        'bg-blue-500/20 border-blue-500/30 text-blue-400'
                    }`}>
                    <span className="font-bold uppercase tracking-wider text-xs flex items-center gap-2">
                        {provider.status === 'Verified' ? <CheckCircle size={14} /> :
                            provider.status === 'Needs Review' ? <AlertTriangle size={14} /> :
                                <Clock size={14} />}
                        {provider.status}
                    </span>
                </div>
            </div>

            {/* Manual Review Banner */}
            {provider.requiresManualReview && (
                <div className="glass-panel p-4 rounded-xl border-2 border-yellow-500/50 bg-yellow-500/10">
                    <div className="flex items-center gap-3">
                        <AlertTriangle size={24} className="text-yellow-400" />
                        <div>
                            <h4 className="font-semibold text-yellow-400">Requires Manual Review</h4>
                            <p className="text-sm text-slate-300">This provider has been flagged for manual verification</p>
                        </div>
                    </div>
                </div>
            )}

            {/* Issues & Risk Flags */}
            {(provider.issues?.length > 0 || provider.riskFlags?.length > 0 || (provider.licenseInfo?.status && provider.licenseInfo.status !== 'Active')) && (
                <div className="glass-panel p-6 rounded-2xl border-2 border-red-500/30">
                    <h3 className="text-lg font-semibold mb-4 flex items-center gap-2 text-red-400">
                        <AlertTriangle size={20} />
                        Issues Detected
                    </h3>
                    <div className="space-y-3">
                        {/* License Status Issues */}
                        {provider.licenseInfo?.status && provider.licenseInfo.status !== 'Active' && (
                            <div className={`p-4 rounded-xl border-2 ${provider.licenseInfo.status === 'Revoked' ? 'bg-red-500/20 border-red-500 text-red-300' :
                                provider.licenseInfo.status === 'Suspended' ? 'bg-orange-500/20 border-orange-500 text-orange-300' :
                                    'bg-yellow-500/20 border-yellow-500 text-yellow-300'
                                }`}>
                                <div className="flex items-start gap-3">
                                    <Shield size={20} className="mt-0.5" />
                                    <div>
                                        <p className="font-semibold">License Status: {provider.licenseInfo.status}</p>
                                        {provider.licenseInfo.license_number && (
                                            <p className="text-sm opacity-90">License: {provider.licenseInfo.license_number}</p>
                                        )}
                                        {provider.licenseInfo.status === 'Revoked' && (
                                            <p className="text-sm mt-1 font-medium">⚠️ Provider should NOT be practicing with revoked license</p>
                                        )}
                                        {provider.licenseInfo.status === 'Suspended' && (
                                            <p className="text-sm mt-1 font-medium">⚠️ License suspended - requires immediate review</p>
                                        )}
                                    </div>
                                </div>
                            </div>
                        )}

                        {/* Validation Issues */}
                        {provider.issues?.map((issue, idx) => {
                            const severityColors = {
                                'CRITICAL': 'bg-red-500/20 border-red-500/50 text-red-300',
                                'HIGH': 'bg-orange-500/20 border-orange-500/50 text-orange-300',
                                'MEDIUM': 'bg-yellow-500/20 border-yellow-500/50 text-yellow-300',
                                'LOW': 'bg-blue-500/20 border-blue-500/50 text-blue-300'
                            };
                            return (
                                <div key={idx} className={`p-3 rounded-lg border ${severityColors[issue.severity] || severityColors['LOW']}`}>
                                    <div className="flex items-start justify-between gap-2">
                                        <div className="flex-1">
                                            <p className="font-medium">{issue.issue}</p>
                                            {issue.source && <p className="text-xs mt-1 opacity-75">Source: {issue.source}</p>}
                                            {issue.recommendation && (
                                                <p className="text-sm mt-2 italic">→ {issue.recommendation}</p>
                                            )}
                                        </div>
                                        <span className="text-xs px-2 py-0.5 bg-white/10 rounded">{issue.severity}</span>
                                    </div>
                                </div>
                            );
                        })}

                        {/* Risk Flags */}
                        {provider.riskFlags?.map((flag, idx) => {
                            const severityColors = {
                                'CRITICAL': 'bg-red-500/20 border-red-500/50 text-red-300',
                                'HIGH': 'bg-orange-500/20 border-orange-500/50 text-orange-300',
                                'MEDIUM': 'bg-yellow-500/20 border-yellow-500/50 text-yellow-300',
                                'LOW': 'bg-blue-500/20 border-blue-500/50 text-blue-300'
                            };
                            return (
                                <div key={idx} className={`p-3 rounded-lg border ${severityColors[flag.severity] || severityColors['LOW']}`}>
                                    <div className="flex items-start justify-between gap-2">
                                        <div className="flex-1">
                                            <p className="font-medium">🚩 {flag.flag}</p>
                                            {flag.description && <p className="text-sm mt-1">{flag.description}</p>}
                                        </div>
                                        <span className="text-xs px-2 py-0.5 bg-white/10 rounded">{flag.severity}</span>
                                    </div>
                                </div>
                            );
                        })}
                    </div>
                </div>
            )}

            <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
                {/* Left Column: Comparison */}
                <div className="lg:col-span-2 space-y-6">
                    <div className="glass-panel p-6 rounded-2xl">
                        <h3 className="text-lg font-semibold mb-4 flex items-center gap-2">
                            <Shield size={18} className="text-primary" /> Record Comparison
                        </h3>

                        <div className="space-y-4">
                            {/* Phone Comparison */}
                            <div className="grid grid-cols-2 gap-4 p-4 bg-white/5 rounded-xl border border-white/5">
                                <div>
                                    <p className="text-xs text-slate-500 uppercase mb-1">Current Value</p>
                                    <p className="text-slate-300">{provider.oldPhone || provider.phone}</p>
                                </div>
                                <div className="relative">
                                    <p className="text-xs text-primary uppercase mb-1">New / Detected</p>
                                    <p className="text-white font-medium">{provider.phone}</p>
                                    {provider.oldPhone && provider.oldPhone !== provider.phone && (
                                        <span className="absolute top-0 right-0 text-[10px] bg-yellow-500/20 text-yellow-400 px-2 py-0.5 rounded">CHANGED</span>
                                    )}
                                </div>
                            </div>

                            {/* Address Comparison */}
                            <div className="grid grid-cols-2 gap-4 p-4 bg-white/5 rounded-xl border border-white/5">
                                <div>
                                    <p className="text-xs text-slate-500 uppercase mb-1">Current Address</p>
                                    <p className="text-slate-300">{provider.oldAddress || provider.address}</p>
                                </div>
                                <div className="relative">
                                    <p className="text-xs text-primary uppercase mb-1">New / Detected</p>
                                    <p className="text-white font-medium">{provider.address}</p>
                                    {provider.oldAddress && provider.oldAddress !== provider.address && (
                                        <span className="absolute top-0 right-0 text-[10px] bg-yellow-500/20 text-yellow-400 px-2 py-0.5 rounded">CHANGED</span>
                                    )}
                                </div>
                            </div>

                            {/* Specialty Comparison */}
                            {provider.oldSpecialty && provider.oldSpecialty !== provider.specialty && (
                                <div className="grid grid-cols-2 gap-4 p-4 bg-white/5 rounded-xl border border-yellow-500/30">
                                    <div>
                                        <p className="text-xs text-slate-500 uppercase mb-1">Current Specialty</p>
                                        <p className="text-slate-300">{provider.oldSpecialty}</p>
                                    </div>
                                    <div className="relative">
                                        <p className="text-xs text-primary uppercase mb-1">New / Detected</p>
                                        <p className="text-white font-medium">{provider.specialty}</p>
                                        <span className="absolute top-0 right-0 text-[10px] bg-yellow-500/20 text-yellow-400 px-2 py-0.5 rounded">MISMATCH</span>
                                    </div>
                                </div>
                            )}
                        </div>
                    </div>

                    {/* Next Steps */}
                    {provider.nextSteps && provider.nextSteps.length > 0 && (
                        <div className="glass-panel p-6 rounded-2xl border border-primary/30">
                            <h3 className="text-lg font-semibold mb-4 text-primary">📋 Recommended Next Steps</h3>
                            <ul className="space-y-2">
                                {provider.nextSteps.map((step, idx) => (
                                    <li key={idx} className="flex items-start gap-3 text-slate-300">
                                        <span className="text-primary mt-0.5">→</span>
                                        <span>{step}</span>
                                    </li>
                                ))}
                            </ul>
                        </div>
                    )}

                    <div className="glass-panel p-6 rounded-2xl">
                        <h3 className="text-lg font-semibold mb-4">Source Evidence</h3>
                        <div className="space-y-3">
                            <div>
                                <p className="text-xs text-slate-500 uppercase mb-2">Matched Sources ({provider.sourcesMatched?.length || 0})</p>
                                <div className="flex flex-wrap gap-2">
                                    {provider.sourcesMatched && provider.sourcesMatched.length > 0 ? (
                                        provider.sourcesMatched.map((source, index) => {
                                            const sourceNames = {
                                                'npi': 'NPI Registry',
                                                'license': 'License Registry',
                                                'hospital': 'Hospital Roster',
                                                'maps': 'Maps Listing',
                                                'clinic': 'Clinic Website',
                                                'telemedicine': 'Telemedicine Directory'
                                            };
                                            return (
                                                <span key={index} className="px-3 py-1.5 bg-neon-mint/20 text-neon-mint border border-neon-mint/30 rounded-lg text-xs font-medium">
                                                    ✓ {sourceNames[source] || source.toUpperCase()}
                                                </span>
                                            );
                                        })
                                    ) : (
                                        <span className="px-3 py-1 bg-slate-700/30 text-slate-400 border border-slate-600/30 rounded-lg text-xs">
                                            No sources matched
                                        </span>
                                    )}
                                </div>
                            </div>
                            <div>
                                <span className="px-3 py-1 bg-slate-700/30 text-slate-400 border border-slate-600/30 rounded-lg text-xs">
                                    Last Checked: {new Date(provider.lastUpdated).toLocaleDateString()}
                                </span>
                            </div>
                            {provider.npi && provider.npi !== 'N/A' && (
                                <div>
                                    <p className="text-xs text-slate-500 uppercase mb-1">NPI Number</p>
                                    <p className="text-white font-mono text-sm">{provider.npi}</p>
                                </div>
                            )}
                            {provider.licenseInfo && (
                                <div>
                                    <p className="text-xs text-slate-500 uppercase mb-1">License Information</p>
                                    <div className="text-sm space-y-1">
                                        {provider.licenseInfo.license_number && (
                                            <p className="text-slate-300">Number: <span className="text-white font-mono">{provider.licenseInfo.license_number}</span></p>
                                        )}
                                        {provider.licenseInfo.status && (
                                            <p className="text-slate-300">Status: <span className="text-white">{provider.licenseInfo.status}</span></p>
                                        )}
                                    </div>
                                </div>
                            )}
                            {provider.hospitalAffiliation && (
                                <div>
                                    <p className="text-xs text-slate-500 uppercase mb-1">Hospital Affiliation</p>
                                    <div className="text-sm space-y-1">
                                        {provider.hospitalAffiliation.hospital_name && (
                                            <p className="text-white font-medium">{provider.hospitalAffiliation.hospital_name}</p>
                                        )}
                                        {provider.hospitalAffiliation.department && (
                                            <p className="text-slate-300">Department: {provider.hospitalAffiliation.department}</p>
                                        )}
                                    </div>
                                </div>
                            )}
                        </div>
                    </div>
                </div>

                {/* Right Column: Confidence Score */}
                <div className="space-y-6">
                    <h3 className="text-lg font-semibold mb-4">Confidence Score</h3>
                    <div className="flex flex-col items-center justify-center py-4">
                        <div className="relative w-32 h-32 flex items-center justify-center">
                            <svg className="w-full h-full" viewBox="0 0 36 36">
                                <path
                                    d="M18 2.0845 a 15.9155 15.9155 0 0 1 0 31.831 a 15.9155 15.9155 0 0 1 0 -31.831"
                                    fill="none"
                                    stroke="#1e293b"
                                    strokeWidth="3"
                                />
                                <path
                                    d="M18 2.0845 a 15.9155 15.9155 0 0 1 0 31.831 a 15.9155 15.9155 0 0 1 0 -31.831"
                                    fill="none"
                                    stroke={provider.confidenceScore > 80 ? '#4ade80' : '#fbbf24'}
                                    strokeWidth="3"
                                    strokeDasharray={`${provider.confidenceScore}, 100`}
                                    className="animate-[spin_1s_ease-out_reverse]"
                                />
                            </svg>
                            <span className="absolute text-2xl font-bold text-white">{provider.confidenceScore}%</span>
                        </div>
                        <p className="text-xs text-slate-400 mt-2 text-center">Based on multi-source validation</p>
                    </div>
                </div>
            </div>
        </div>
    );
};

export default ProviderDetail;
