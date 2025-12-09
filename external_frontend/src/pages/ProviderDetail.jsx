import React, { useEffect, useState } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { ArrowLeft, Phone, MessageSquare, CheckCircle, AlertTriangle, Clock, Shield } from 'lucide-react';
import gsap from 'gsap';

const ProviderDetail = () => {
    const { id } = useParams();
    const navigate = useNavigate();
    const [provider, setProvider] = useState(null);
    const [loading, setLoading] = useState(true);
    const [verifying, setVerifying] = useState(false);

    // Mock provider detail data
    const mockProviders = {
        '1': { id: 1, name: 'Dr. Sarah Johnson', specialty: 'Cardiology', phone: '(555) 123-4567', email: 'sarah@clinic.com', address: '123 Medical Blvd, New York, NY 10001', verified: true, status: 'Verified', confidence: 98, matchedSources: 5 },
        '2': { id: 2, name: 'Dr. Michael Chen', specialty: 'Neurology', phone: '(555) 234-5678', email: 'michael@clinic.com', address: '456 Health Ave, Boston, MA 02101', verified: false, status: 'Needs Review', confidence: 85, matchedSources: 3 },
    };

    useEffect(() => {
        fetchProvider();
    }, [id]);

    const fetchProvider = async () => {
        try {
            // Simulate API call
            await new Promise(resolve => setTimeout(resolve, 500));
            const providerData = mockProviders[id] || { id, name: 'Unknown Provider', specialty: 'N/A', verified: false, status: 'Not Found' };
            setProvider(providerData);
            setLoading(false);
        } catch (error) {
            console.error("Error fetching provider", error);
            setLoading(false);
        }
    };

    const handleVerify = async (method) => {
        setVerifying(true);
        try {
            // Simulate verification
            await new Promise(resolve => setTimeout(resolve, 1000));
            setProvider({ ...provider, verified: true, status: 'Verified' });
            alert(`Verification via ${method.toUpperCase()} sent successfully!`);
        } catch (error) {
            console.error("Verification failed", error);
        } finally {
            setVerifying(false);
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
                        </div>
                    </div>

                    <div className="glass-panel p-6 rounded-2xl">
                        <h3 className="text-lg font-semibold mb-4">Source Evidence</h3>
                        <div className="flex gap-3">
                            <span className="px-3 py-1 bg-indigo-500/20 text-indigo-300 border border-indigo-500/30 rounded-lg text-xs">
                                Source: {provider.source}
                            </span>
                            <span className="px-3 py-1 bg-slate-700/30 text-slate-400 border border-slate-600/30 rounded-lg text-xs">
                                Last Checked: {new Date(provider.lastUpdated).toLocaleDateString()}
                            </span>
                        </div>
                    </div>
                </div>

                {/* Right Column: Actions */}
                <div className="space-y-6">
                    <div className="glass-panel p-6 rounded-2xl">
                        <h3 className="text-lg font-semibold mb-4">Verification Actions</h3>
                        <div className="space-y-3">
                            <button
                                onClick={() => handleVerify('sms')}
                                disabled={verifying}
                                className="w-full py-3 px-4 bg-primary/10 hover:bg-primary/20 border border-primary/30 text-primary rounded-xl flex items-center justify-center gap-2 transition-all disabled:opacity-50"
                            >
                                <MessageSquare size={18} />
                                {verifying ? 'Sending...' : 'Trigger SMS Verification'}
                            </button>
                            <button
                                onClick={() => handleVerify('call')}
                                disabled={verifying}
                                className="w-full py-3 px-4 bg-secondary/10 hover:bg-secondary/20 border border-secondary/30 text-secondary rounded-xl flex items-center justify-center gap-2 transition-all disabled:opacity-50"
                            >
                                <Phone size={18} />
                                {verifying ? 'Calling...' : 'Simulate Voice Call'}
                            </button>
                        </div>
                    </div>

                    <div className="glass-panel p-6 rounded-2xl">
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
        </div>
    );
};

export default ProviderDetail;
