import React, { useEffect, useState } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import axios from 'axios';
import { ArrowLeft, CheckCircle, AlertTriangle, Clock, Shield, Send, MessageSquare, PhoneCall } from 'lucide-react';
import gsap from 'gsap';
import { startVerification, getVerificationStatus, getProviderVerifications } from '../services/api';
import CompliancePanel from '../components/CompliancePanel';

const ProviderDetail = () => {
    const { id } = useParams();
    const navigate = useNavigate();
    // Persistent state with localStorage
    const [provider, setProvider] = useState(() => {
        const cached = sessionStorage.getItem(`provider_${id}`);
        return cached ? JSON.parse(cached) : null;
    });
    const [loading, setLoading] = useState(true);
    const [verificationLoading, setVerificationLoading] = useState(false);
    const [verificationHistory, setVerificationHistory] = useState(() => {
        const cached = sessionStorage.getItem(`verification_history_${id}`);
        return cached ? JSON.parse(cached) : [];
    });
    const [currentSession, setCurrentSession] = useState(() => {
        const cached = sessionStorage.getItem(`current_session_${id}`);
        return cached ? JSON.parse(cached) : null;
    });

    useEffect(() => {
        fetchProvider();
        fetchVerificationHistory();
    }, [id]);

    const fetchVerificationHistory = async () => {
        try {
            const response = await getProviderVerifications(id);
            setVerificationHistory(response.data.sessions || []);
        } catch (error) {
            console.error('Error fetching verification history:', error);
        }
    };

    const [conversation, setConversation] = useState(() => {
        const cached = sessionStorage.getItem(`conversation_${id}`);
        return cached ? JSON.parse(cached) : [];
    });

    // Call verification data from Omni Dimension webhook
    const [callVerification, setCallVerification] = useState(() => {
        const cached = sessionStorage.getItem(`call_verification_${id}`);
        return cached ? JSON.parse(cached) : null;
    });
    const [callLoading, setCallLoading] = useState(false);
    const [callPollingEnabled, setCallPollingEnabled] = useState(false);

    // Fetch call verification data - only when polling is enabled
    useEffect(() => {
        if (!callPollingEnabled) return;

        const fetchCallData = async () => {
            if (!id) return;

            try {
                setCallLoading(true);
                const response = await axios.get(`http://localhost:8000/verify/call-data/${id}`);

                if (response.data.success && response.data.call_verification) {
                    setCallVerification(response.data.call_verification);
                }
            } catch (error) {
                console.error('Error fetching call verification:', error);
            } finally {
                setCallLoading(false);
            }
        };

        fetchCallData();
        // Poll for updates every 10 seconds
        const interval = setInterval(fetchCallData, 10000);
        return () => clearInterval(interval);
    }, [id, callPollingEnabled]);

    // Save state to sessionStorage when it changes
    useEffect(() => {
        if (provider) sessionStorage.setItem(`provider_${id}`, JSON.stringify(provider));
    }, [provider, id]);

    useEffect(() => {
        sessionStorage.setItem(`verification_history_${id}`, JSON.stringify(verificationHistory));
    }, [verificationHistory, id]);

    useEffect(() => {
        if (currentSession) sessionStorage.setItem(`current_session_${id}`, JSON.stringify(currentSession));
    }, [currentSession, id]);

    useEffect(() => {
        sessionStorage.setItem(`conversation_${id}`, JSON.stringify(conversation));
    }, [conversation, id]);

    useEffect(() => {
        if (callVerification) sessionStorage.setItem(`call_verification_${id}`, JSON.stringify(callVerification));
    }, [callVerification, id]);

    const handleStartVerification = async () => {
        if (!provider.phone || provider.phone === 'N/A') {
            alert('No phone number available for this provider');
            return;
        }

        setVerificationLoading(true);
        setConversation([]);  // Clear previous conversation

        try {
            const verificationRequest = {
                provider_id: provider.id,
                provider_name: provider.name,
                phone: provider.phone,
                specialty: provider.specialty !== 'N/A' ? provider.specialty : undefined,
                address: provider.address !== 'N/A' ? provider.address : undefined,
                license_number: provider.licenseInfo?.license_number,
                hospital: provider.hospitalAffiliation?.hospital_name
            };

            const response = await startVerification(verificationRequest);

            if (response.data.success) {
                setCurrentSession(response.data);

                // Start conversation simulation
                simulateSmartConversation();
            } else {
                alert('Failed to send verification: ' + response.data.message);
            }
        } catch (error) {
            console.error('Verification error:', error);
            alert('Error sending verification SMS');
        } finally {
            setVerificationLoading(false);
        }
    };

    // Simulate intelligent conversation based on validation issues
    const simulateSmartConversation = () => {
        // ONLY ask about MUTABLE fields (address, hospital) 
        // SKIP: phone (delivery proves it), specialty (doesn't change)
        const issues = [];

        // Address - practices relocate
        if (provider.address) {
            issues.push({
                field: 'address',
                question: 'Is your practice still at: MG Road, Bangalore 560001?',
                correction: '456 New Medical Plaza, MG Road, Bangalore 560001'
            });
        }

        // Hospital affiliation - doctors switch hospitals
        if (provider.hospitalAffiliation) {
            issues.push({
                field: 'hospital',
                question: 'Are you still affiliated with Apollo Hospital?',
                correction: 'Fortis Hospital, Bangalore'
            });
        }

        // Initial SMS
        setTimeout(() => {
            setConversation([{
                sender: 'system',
                message: `Hi ${provider.name}, we're verifying your provider information.`,
                time: new Date()
            }]);

            // Ask about first issue
            setTimeout(() => {
                if (issues.length > 0) {
                    setConversation(prev => [...prev, {
                        sender: 'system',
                        message: issues[0].question,
                        time: new Date()
                    }]);

                    // Provider responds NO
                    setTimeout(() => {
                        setConversation(prev => [...prev, {
                            sender: 'provider',
                            message: 'NO, that needs updating',
                            time: new Date()
                        }]);

                        setCurrentSession(prev => ({
                            ...prev,
                            status: 'CORRECTIONS_NEEDED',
                            provider_response: 'NO'
                        }));

                        // Request correction
                        setTimeout(() => {
                            setConversation(prev => [...prev, {
                                sender: 'system',
                                message: 'Please reply with the correct information.',
                                time: new Date()
                            }]);

                            // Provider provides correction
                            setTimeout(() => {
                                const corrections = {};
                                issues.forEach(issue => {
                                    corrections[issue.field] = issue.correction;
                                });

                                setConversation(prev => [...prev, {
                                    sender: 'provider',
                                    message: Object.entries(corrections).map(([k, v]) => `${k}: ${v}`).join('\n'),
                                    time: new Date()
                                }]);

                                setCurrentSession(prev => ({
                                    ...prev,
                                    status: 'COMPLETED',
                                    corrections,
                                    completed_at: new Date().toISOString()
                                }));
                            }, 3000);
                        }, 2000);
                    }, 2000);
                }
            }, 1500);
        }, 500);
    };

    const pollVerificationStatus = (sessionId) => {
        const interval = setInterval(async () => {
            try {
                const response = await getVerificationStatus(sessionId);
                const session = response.data;

                setCurrentSession(session);

                // Stop polling if completed
                if (['CONFIRMED', 'COMPLETED', 'FAILED', 'TIMEOUT'].includes(session.status)) {
                    clearInterval(interval);
                    fetchVerificationHistory(); // Refresh history
                }
            } catch (error) {
                console.error('Error polling status:', error);
                clearInterval(interval);
            }
        }, 5000); // Poll every 5 seconds

        // Stop polling after 5 minutes
        setTimeout(() => clearInterval(interval), 300000);
    };

    const fetchProvider = async () => {
        try {
            // Check sessionStorage first - if we have cached data, use it
            const cachedProvider = sessionStorage.getItem(`provider_${id}`);
            if (cachedProvider) {
                setProvider(JSON.parse(cachedProvider));
                setLoading(false);
                return;
            }

            // Load validation results from localStorage only if no cache
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

            {/* Compliance Intelligence Panel */}
            <CompliancePanel providerId={provider.id} providerData={provider} />

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
                                            <p className="text-sm mt-1 font-medium">Provider should NOT be practicing with revoked license</p>
                                        )}
                                        {provider.licenseInfo.status === 'Suspended' && (
                                            <p className="text-sm mt-1 font-medium">License suspended - requires immediate review</p>
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
                                            <p className="font-medium">{flag.flag}</p>
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

            {/* SMS Verification Section */}
            <div className="glass-panel p-6 rounded-2xl mb-8">
                <div className="flex items-center justify-between mb-4">
                    <h3 className="text-lg font-semibold flex items-center gap-2">
                        <MessageSquare size={20} />
                        SMS Verification
                    </h3>
                    <button
                        onClick={handleStartVerification}
                        disabled={verificationLoading || !provider.phone || provider.phone === 'N/A'}
                        className="flex items-center gap-2 px-4 py-2 bg-blue-500 hover:bg-blue-600 disabled:bg-gray-600 disabled:cursor-not-allowed text-white rounded-lg transition-colors"
                    >
                        <Send size={16} />
                        {verificationLoading ? 'Sending...' : 'Send Verification SMS'}
                    </button>
                </div>

                {/* Conversation Display */}
                {conversation.length > 0 && (
                    <div className="mb-4 p-4 bg-slate-900/50 rounded-xl border border-purple-500/20 max-h-96 overflow-y-auto">
                        <h4 className="text-sm font-semibold text-purple-300 mb-3">Conversation</h4>
                        <div className="space-y-2">
                            {conversation.map((msg, idx) => {
                                const isSystem = (msg.sender === 'system' || msg.from === 'system');
                                return (
                                    <div key={idx} className={`p-2 rounded ${isSystem ? 'bg-blue-500/10 text-blue-200' : 'bg-green-500/10 text-green-200'}`}>
                                        <p className="text-xs text-slate-400 mb-1">{isSystem ? 'AI Agent' : 'Provider'}</p>
                                        <p className="text-sm">{msg.message}</p>
                                    </div>
                                );
                            })}
                        </div>
                    </div>
                )}

                {/* Current Session Status */}
                {currentSession && (
                    <div className="p-4 bg-white/5 rounded-xl border border-white/10 mb-4">
                        <div className="flex items-center justify-between mb-2">
                            <span className="text-xs text-slate-500">Status</span>
                            <span className={`text-xs px-2 py-1 rounded ${currentSession.status === 'CONFIRMED' ? 'bg-green-500/20 text-green-400' :
                                currentSession.status === 'COMPLETED' ? 'bg-blue-500/20 text-blue-400' :
                                    currentSession.status === 'PENDING_RESPONSE' ? 'bg-yellow-500/20 text-yellow-400' :
                                        'bg-gray-500/20 text-gray-400'
                                }`}>
                                {currentSession.status.replace(/_/g, ' ')}
                            </span>
                        </div>
                        {currentSession.initial_response && (
                            <p className="text-sm text-slate-300">Response: {currentSession.initial_response}</p>
                        )}
                        {currentSession.correction_text && (
                            <p className="text-xs text-slate-400 mt-2">Corrections: {currentSession.correction_text}</p>
                        )}
                    </div>
                )}

                {/* Verification History */}
                {verificationHistory.length > 0 && (
                    <div className="mt-4">
                        <h4 className="text-sm font-semibold text-slate-300 mb-3">Verification History</h4>
                        <div className="space-y-2 max-h-64 overflow-y-auto">
                            {verificationHistory.map((session, idx) => (
                                <div key={idx} className="p-3 bg-white/5 rounded-lg border border-white/10">
                                    <div className="flex items-center justify-between mb-1">
                                        <span className="text-xs text-slate-400">
                                            {new Date(session.created_at).toLocaleString()}
                                        </span>
                                        <span className={`text-xs px-2 py-0.5 rounded ${session.status === 'CONFIRMED' ? 'bg-green-500/20 text-green-400' :
                                            session.status === 'COMPLETED' ? 'bg-blue-500/20 text-blue-400' :
                                                session.status === 'PENDING_RESPONSE' ? 'bg-yellow-500/20 text-yellow-400' :
                                                    'bg-gray-500/20 text-gray-400'
                                            }`}>
                                            {session.status.replace(/_/g, ' ')}
                                        </span>
                                    </div>
                                    {session.initial_response && (
                                        <p className="text-sm text-slate-300">Response: {session.initial_response}</p>
                                    )}
                                    {session.correction_text && (
                                        <p className="text-xs text-slate-400 mt-1">Corrections: {session.correction_text.substring(0, 100)}{session.correction_text.length > 100 ? '...' : ''}</p>
                                    )}
                                </div>
                            ))}
                        </div>
                    </div>
                )}

                {verificationHistory.length === 0 && !currentSession && (
                    <p className="text-sm text-slate-400 text-center py-4">No verification history. Click the button above to send a verification SMS.</p>
                )}
            </div>

            {/* Call Verification Section - Separate Block */}
            <div className="glass-panel p-6 rounded-2xl mb-8 border-2 border-purple-500/30">
                <div className="flex items-center justify-between mb-4">
                    <h3 className="text-lg font-semibold flex items-center gap-2 text-purple-400">
                        <PhoneCall size={20} />
                        Call Verification
                    </h3>
                    <button
                        onClick={() => {
                            setCallPollingEnabled(true);
                            alert('Call verification webhook is now active!\n\nWebhook URL:\n' +
                                window.location.origin.replace('5173', '8000') + '/verify/omni-webhook\n\n' +
                                'Initiate the call through Omni Dimension dashboard.\nData will appear here automatically when received.');
                        }}
                        disabled={!provider.phone || provider.phone === 'N/A'}
                        className="flex items-center gap-2 px-4 py-2 bg-purple-500 hover:bg-purple-600 disabled:bg-gray-600 disabled:cursor-not-allowed text-white rounded-lg transition-colors"
                    >
                        <PhoneCall size={16} />
                        Start Call Verification
                    </button>
                </div>

                {callLoading && (
                    <div className="p-4 bg-purple-500/10 rounded-xl border border-purple-500/30 mb-4">
                        <p className="text-sm text-purple-300">Waiting for call webhook data...</p>
                        <p className="text-xs text-slate-400 mt-1">Polling every 10 seconds</p>
                    </div>
                )}

                {!callVerification && !callLoading && (
                    <div className="p-4 bg-slate-900/50 rounded-xl border border-white/10">
                        <p className="text-sm text-slate-400 text-center">
                            No call verification data yet. Click "Start Call Verification" to begin.
                        </p>
                    </div>
                )}
            </div>

            {/* Call Verification Data Display - Only when webhook data exists */}
            {callVerification && (
                <div className="glass-panel p-6 rounded-2xl mb-8">
                    <div className="flex items-center justify-between mb-6">
                        <h3 className="text-lg font-semibold flex items-center gap-2">
                            <PhoneCall size={20} />
                            Call Verification
                        </h3>
                        <div className="flex items-center gap-2">
                            <span className={`text-xs px-3 py-1 rounded-full ${callVerification.status === 'completed'
                                ? 'bg-green-500/20 text-green-400 border border-green-500/30'
                                : 'bg-yellow-500/20 text-yellow-400 border border-yellow-500/30'
                                }`}>
                                {callVerification.status.toUpperCase()}
                            </span>
                            <span className="text-xs text-slate-400">
                                Duration: {callVerification.duration}
                            </span>
                        </div>
                    </div>

                    {/* Call Summary */}
                    <div className="mb-6 p-4 bg-blue-500/10 rounded-xl border border-blue-500/30">
                        <h4 className="text-sm font-semibold text-blue-300 mb-2 flex items-center gap-2">
                            Call Summary
                        </h4>
                        <p className="text-sm text-slate-300 leading-relaxed">
                            {callVerification.callSummary}
                        </p>
                        <p className="text-xs text-slate-500 mt-2">
                            Call ID: {callVerification.callId} • {new Date(callVerification.timestamp).toLocaleString()}
                        </p>
                    </div>

                    {/* Full Conversation Transcript */}
                    <div className="mb-6 p-4 bg-slate-900/50 rounded-xl border border-purple-500/20 max-h-80 overflow-y-auto">
                        <h4 className="text-sm font-semibold text-purple-300 mb-3 flex items-center gap-2">
                            Full Conversation
                        </h4>
                        <div className="space-y-2">
                            {callVerification.fullConversation.map((msg, idx) => (
                                <div key={idx} className="flex gap-3">
                                    <span className="text-xs text-slate-500 w-12 flex-shrink-0">{msg.time}</span>
                                    <div className="flex-1">
                                        <span className={`text-xs font-semibold ${msg.sender === 'system' ? 'text-blue-400' : 'text-green-400'}`}>
                                            {msg.sender === 'system' ? 'AI Agent' : 'Provider'}:
                                        </span>
                                        <p className="text-sm text-slate-300 mt-0.5">{msg.message}</p>
                                    </div>
                                </div>
                            ))}
                        </div>
                    </div>

                    {/* Sentiment Analysis */}
                    <div className="mb-6 p-4 bg-purple-500/10 rounded-xl border border-purple-500/30">
                        <h4 className="text-sm font-semibold text-purple-300 mb-3 flex items-center gap-2">
                            Sentiment Analysis
                        </h4>
                        <div className="grid grid-cols-2 gap-4">
                            <div>
                                <p className="text-xs text-slate-500 mb-1">Overall Sentiment</p>
                                <p className="text-lg font-bold text-green-400">{callVerification.sentimentAnalysis.overall}</p>
                            </div>
                            <div>
                                <p className="text-xs text-slate-500 mb-1">Confidence</p>
                                <p className="text-lg font-bold text-blue-400">{callVerification.sentimentAnalysis.confidence}%</p>
                            </div>
                            <div className="col-span-2">
                                <p className="text-xs text-slate-500 mb-1">Mood</p>
                                <p className="text-sm text-slate-300">{callVerification.sentimentAnalysis.mood}</p>
                            </div>
                            <div className="col-span-2">
                                <p className="text-xs text-slate-500 mb-1">Key Emotions</p>
                                <div className="flex flex-wrap gap-2 mt-1">
                                    {callVerification.sentimentAnalysis.keyEmotions.map((emotion, idx) => (
                                        <span key={idx} className="text-xs px-2 py-1 bg-purple-500/20 text-purple-300 rounded-full border border-purple-500/30">
                                            {emotion}
                                        </span>
                                    ))}
                                </div>
                            </div>
                        </div>
                    </div>

                    {/* Extracted Information */}
                    <div className="p-4 bg-green-500/10 rounded-xl border border-green-500/30">
                        <h4 className="text-sm font-semibold text-green-300 mb-3 flex items-center gap-2">
                            Extracted Information
                        </h4>
                        <div className="space-y-2">
                            <div className="flex justify-between items-start">
                                <span className="text-xs text-slate-500">Address Confirmed:</span>
                                <span className="text-sm text-slate-300 text-right max-w-[60%]">
                                    {callVerification.extractedInformation.addressConfirmed}
                                </span>
                            </div>
                            <div className="flex justify-between items-start">
                                <span className="text-xs text-slate-500">Hospital Updated:</span>
                                <span className="text-sm text-green-400 text-right max-w-[60%]">
                                    {callVerification.extractedInformation.hospitalUpdated}
                                </span>
                            </div>
                            <div className="grid grid-cols-2 gap-4 mt-3 pt-3 border-t border-white/10">
                                <div>
                                    <p className="text-xs text-slate-500 mb-1">Verifications Completed</p>
                                    <p className="text-lg font-bold text-green-400">
                                        {callVerification.extractedInformation.verificationsCompleted}
                                    </p>
                                </div>
                                <div>
                                    <p className="text-xs text-slate-500 mb-1">Corrections Provided</p>
                                    <p className="text-lg font-bold text-orange-400">
                                        {callVerification.extractedInformation.correctionsProvided}
                                    </p>
                                </div>
                            </div>
                        </div>
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
        </div >
    );
};

export default ProviderDetail;
