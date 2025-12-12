import React, { useState, useEffect } from 'react';
import { Check, X, AlertOctagon, ExternalLink } from 'lucide-react';
import { useNavigate } from 'react-router-dom';

const ReviewQueue = () => {
    const [reviews, setReviews] = useState([]);
    const navigate = useNavigate();

    useEffect(() => {
        fetchReviews();
    }, []);

    const fetchReviews = async () => {
        try {
            // Get validated providers from localStorage
            const storedResults = localStorage.getItem('validationResults');

            if (!storedResults) {
                setReviews([]);
                return;
            }

            const results = JSON.parse(storedResults);

            // Filter only FLAGGED or providers requiring manual review
            const flaggedProviders = results
                .filter(result =>
                    result.validation_status === 'FLAGGED' ||
                    result.requires_manual_review === true ||
                    (result.issues && result.issues.some(issue => issue.severity === 'HIGH' || issue.severity === 'CRITICAL'))
                )
                .map(result => ({
                    id: result.provider_id,
                    name: result.provider_name,
                    specialty: result.verified_specialty || 'Unknown',
                    issues: result.issues?.map(i => i.issue) || ['Requires review'],
                    phone: result.verified_phone || 'N/A',
                    confidenceScore: Math.round((result.confidence_scores?.overall_confidence || 0) * 100)
                }));

            setReviews(flaggedProviders);
        } catch (error) {
            console.error("Error fetching reviews", error);
            setReviews([]);
        }
    };

    const handleReview = async (id, action) => {
        try {
            // Simulate review action
            await new Promise(resolve => setTimeout(resolve, 500));
            setReviews(prev => prev.filter(p => p.id !== id));
        } catch (error) {
            console.error("Review failed", error);
        }
    };

    return (
        <div className="space-y-6">
            <h1 className="text-3xl font-poster text-white">Manual Review Queue</h1>
            <p className="text-slate-400">Review flagged providers that require human intervention.</p>

            <div className="grid grid-cols-1 gap-4">
                {reviews.map(provider => (
                    <div key={provider.id} className="glass-panel p-6 rounded-xl flex flex-col md:flex-row justify-between items-start md:items-center gap-6 group hover:border-primary/30 transition-all">
                        <div className="flex-1">
                            <div className="flex items-center gap-3 mb-2">
                                <h3 className="text-xl font-bold text-white">{provider.name}</h3>
                                <span className="px-2 py-0.5 bg-red-500/20 text-red-400 text-xs rounded border border-red-500/30">
                                    {provider.issues.join(', ')}
                                </span>
                            </div>
                            <div className="grid grid-cols-2 gap-x-8 gap-y-2 text-sm text-slate-400">
                                <p>ID: <span className="text-slate-300">{provider.id.slice(0, 8)}</span></p>
                                <p>Specialty: <span className="text-slate-300">{provider.specialty}</span></p>
                                <p>Confidence: <span className="text-yellow-400 font-medium">{provider.confidenceScore}%</span></p>
                                <p className="flex items-center gap-1 hover:text-primary cursor-pointer">
                                    Source Evidence <ExternalLink size={12} />
                                </p>
                            </div>
                        </div>

                        <div className="flex gap-3 w-full md:w-auto">
                            <button
                                onClick={() => navigate(`/provider/${provider.id}`)}
                                className="flex-1 md:flex-none px-4 py-2 rounded-lg border border-white/10 hover:bg-white/5 transition-colors text-sm"
                            >
                                View Details
                            </button>
                            <button
                                onClick={() => handleReview(provider.id, 'reject')}
                                className="flex-1 md:flex-none px-4 py-2 rounded-lg bg-red-500/10 hover:bg-red-500/20 text-red-400 border border-red-500/20 transition-colors flex items-center justify-center gap-2"
                            >
                                <X size={18} /> Reject
                            </button>
                            <button
                                onClick={() => handleReview(provider.id, 'approve')}
                                className="flex-1 md:flex-none px-4 py-2 rounded-lg bg-green-500/10 hover:bg-green-500/20 text-green-400 border border-green-500/20 transition-colors flex items-center justify-center gap-2"
                            >
                                <Check size={18} /> Approve
                            </button>
                        </div>
                    </div>
                ))}

                {reviews.length === 0 && (
                    <div className="text-center py-12 glass-panel rounded-2xl">
                        <div className="w-16 h-16 bg-green-500/20 rounded-full flex items-center justify-center mx-auto text-green-400 mb-4">
                            <Check size={32} />
                        </div>
                        <h3 className="text-xl font-bold text-white">All Caught Up!</h3>
                        <p className="text-slate-400 mt-2">No providers currently require manual review.</p>
                    </div>
                )}
            </div>
        </div>
    );
};

export default ReviewQueue;
