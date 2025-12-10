import React, { useState } from 'react';
import { Upload, Play, CheckCircle, AlertTriangle, FileText, Loader, Phone, MessageSquare, Download, X, Users } from 'lucide-react';
import { uploadFile, validateUploadedFile, getBatchStatus } from '../services/api';

const Validation = () => {
    const [file, setFile] = useState(null);
    const [uploading, setUploading] = useState(false);
    const [uploadResult, setUploadResult] = useState(null);
    const [validating, setValidating] = useState(false);
    const [validationResults, setValidationResults] = useState(null);
    const [error, setError] = useState(null);
    const [batchId, setBatchId] = useState(null);

    const handleFileSelect = (e) => {
        const selectedFile = e.target.files[0];
        if (selectedFile) {
            setFile(selectedFile);
            setError(null);
        }
    };

    const handleUpload = async () => {
        if (!file) {
            setError('Please select a file first');
            return;
        }

        setUploading(true);
        setError(null);

        try {
            const response = await uploadFile(file);

            if (response.data.extraction_status === 'success') {
                setUploadResult(response.data);
            } else {
                setError(response.data.extraction_status || 'Failed to extract providers from file');
            }
        } catch (err) {
            console.error("Upload failed", err);
            setError(err.response?.data?.error || err.message || 'Failed to upload file');
        } finally {
            setUploading(false);
        }
    };

    const handleValidate = async () => {
        if (!uploadResult || !uploadResult.file_id) {
            setError('No file uploaded');
            return;
        }

        setValidating(true);
        setError(null);

        try {
            // Start batch validation
            const response = await validateUploadedFile(uploadResult.file_id);
            const newBatchId = response.data.batch_id;
            setBatchId(newBatchId);

            // Poll for results
            let attempts = 0;
            const maxAttempts = 60; // 60 seconds max

            const pollResults = setInterval(async () => {
                attempts++;

                try {
                    const statusResponse = await getBatchStatus(newBatchId);
                    const batch = statusResponse.data;

                    if (batch.status === 'COMPLETED') {
                        clearInterval(pollResults);
                        setValidationResults(batch);
                        // Save results to localStorage for Directory page
                        if (batch.results && batch.results.length > 0) {
                            localStorage.setItem('validationResults', JSON.stringify(batch.results));
                        }
                        setValidating(false);
                    } else if (batch.status === 'FAILED' || attempts >= maxAttempts) {
                        clearInterval(pollResults);
                        setError('Validation failed or timed out');
                        setValidating(false);
                    }
                } catch (err) {
                    console.error('Error polling batch status:', err);
                }
            }, 1000);

        } catch (err) {
            console.error("Validation failed", err);
            setError(err.response?.data?.error || err.message || 'Failed to start validation');
            setValidating(false);
        }
    };

    const handleCallAll = () => {
        if (!validationResults || !validationResults.results) return;

        const phoneNumbers = validationResults.results
            .filter(r => r.verified_phone)
            .map(r => r.verified_phone);

        alert(`Initiating calls to ${phoneNumbers.length} providers:\n${phoneNumbers.join('\n')}`);
        // In production, this would integrate with a calling service
    };

    const handleSMSAll = () => {
        if (!validationResults || !validationResults.results) return;

        const phoneNumbers = validationResults.results
            .filter(r => r.verified_phone)
            .map(r => r.verified_phone);

        alert(`Sending SMS to ${phoneNumbers.length} providers:\n${phoneNumbers.join('\n')}`);
        // In production, this would integrate with an SMS service
    };

    const handleReset = () => {
        setFile(null);
        setUploadResult(null);
        setValidationResults(null);
        setError(null);
        setBatchId(null);
    };

    const getStatusColor = (status) => {
        switch (status) {
            case 'VERIFIED': return 'text-green-400 bg-green-500/20 border-green-500/30';
            case 'PARTIALLY_VERIFIED': return 'text-yellow-400 bg-yellow-500/20 border-yellow-500/30';
            case 'UNVERIFIED': return 'text-red-400 bg-red-500/20 border-red-500/30';
            case 'FLAGGED': return 'text-orange-400 bg-orange-500/20 border-orange-500/30';
            default: return 'text-slate-400 bg-slate-500/20 border-slate-500/30';
        }
    };

    return (
        <div className="max-w-6xl mx-auto space-y-8">
            <div className="text-center space-y-4">
                <h1 className="text-5xl font-poster text-white">Batch Provider Validation</h1>
                <p className="text-slate-400 max-w-2xl mx-auto text-lg">
                    Upload a PDF or Excel file with provider names. Our AI will validate them against multiple data sources and provide confidence scores.
                </p>
            </div>

            {/* Upload Section */}
            {!uploadResult && !validationResults && (
                <div className="glass-panel p-8 rounded-2xl border border-white/10">
                    <h2 className="text-2xl font-bold text-white mb-6">Upload Provider List</h2>

                    <div className="space-y-6">
                        <div className="border-2 border-dashed border-white/20 rounded-xl p-12 text-center hover:border-primary/50 transition-colors">
                            <Upload className="w-16 h-16 mx-auto mb-4 text-slate-400" />
                            <p className="text-lg text-white mb-2">Drop your file here or click to browse</p>
                            <p className="text-sm text-slate-400 mb-4">Supports PDF and Excel (.xlsx) files</p>
                            <input
                                type="file"
                                accept=".pdf,.xlsx,.xls"
                                onChange={handleFileSelect}
                                className="hidden"
                                id="file-upload"
                            />
                            <label
                                htmlFor="file-upload"
                                className="inline-block px-6 py-3 bg-white/10 hover:bg-white/20 border border-white/20 rounded-xl cursor-pointer transition-colors text-white font-medium"
                            >
                                Select File
                            </label>
                        </div>

                        {file && (
                            <div className="flex items-center justify-between p-4 bg-white/5 rounded-xl border border-white/10">
                                <div className="flex items-center gap-3">
                                    <FileText className="text-primary" size={24} />
                                    <div>
                                        <p className="text-white font-medium">{file.name}</p>
                                        <p className="text-sm text-slate-400">{(file.size / 1024).toFixed(2)} KB</p>
                                    </div>
                                </div>
                                <button
                                    onClick={() => setFile(null)}
                                    className="p-2 hover:bg-white/10 rounded-lg transition-colors"
                                >
                                    <X className="text-slate-400" size={20} />
                                </button>
                            </div>
                        )}

                        <button
                            onClick={handleUpload}
                            disabled={!file || uploading}
                            className="w-full px-8 py-4 bg-gradient-to-r from-primary to-neon-blue text-white rounded-xl font-bold text-lg hover:shadow-lg hover:shadow-primary/50 transition-all disabled:opacity-50 disabled:cursor-not-allowed flex items-center justify-center gap-2"
                        >
                            {uploading ? (
                                <>
                                    <Loader className="animate-spin" size={20} />
                                    Uploading & Extracting...
                                </>
                            ) : (
                                <>
                                    <Upload size={20} />
                                    Upload & Extract Providers
                                </>
                            )}
                        </button>
                    </div>
                </div>
            )}

            {/* Extracted Providers */}
            {uploadResult && !validationResults && (
                <div className="glass-panel p-8 rounded-2xl border border-white/10 space-y-6">
                    <div className="flex items-center justify-between">
                        <div>
                            <h2 className="text-2xl font-bold text-white">Providers Extracted</h2>
                            <p className="text-slate-400 mt-1">Found {uploadResult.providers_extracted} providers in {uploadResult.filename}</p>
                        </div>
                        <button
                            onClick={handleReset}
                            className="px-4 py-2 border border-white/20 rounded-lg hover:bg-white/5 transition-colors text-white"
                        >
                            Upload Different File
                        </button>
                    </div>

                    {/* Provider List Preview */}
                    <div className="max-h-64 overflow-y-auto space-y-2">
                        {uploadResult.extracted_providers && uploadResult.extracted_providers.slice(0, 10).map((provider, idx) => (
                            <div key={idx} className="p-3 bg-white/5 rounded-lg border border-white/10 flex items-center gap-3">
                                <Users className="text-primary flex-shrink-0" size={20} />
                                <div className="flex-1">
                                    <p className="text-white font-medium">{provider.provider_name || 'Unknown'}</p>
                                    <p className="text-sm text-slate-400">
                                        {provider.phone && `Phone: ${provider.phone}`}
                                        {provider.specialty && ` • ${provider.specialty}`}
                                    </p>
                                </div>
                            </div>
                        ))}
                        {uploadResult.providers_extracted > 10 && (
                            <p className="text-center text-slate-400 text-sm py-2">
                                ... and {uploadResult.providers_extracted - 10} more providers
                            </p>
                        )}
                    </div>

                    <button
                        onClick={handleValidate}
                        disabled={validating}
                        className="w-full px-8 py-4 bg-gradient-to-r from-primary to-neon-blue text-white rounded-xl font-bold text-lg hover:shadow-lg hover:shadow-primary/50 transition-all disabled:opacity-50 disabled:cursor-not-allowed flex items-center justify-center gap-2"
                    >
                        {validating ? (
                            <>
                                <Loader className="animate-spin" size={20} />
                                Validating with AI Agents...
                            </>
                        ) : (
                            <>
                                <Play size={20} />
                                Start AI Validation ({uploadResult.providers_extracted} providers)
                            </>
                        )}
                    </button>
                </div>
            )}

            {/* Error Display */}
            {error && (
                <div className="glass-panel p-6 rounded-2xl border border-red-500/30 bg-red-500/10">
                    <div className="flex items-start gap-3">
                        <AlertTriangle className="text-red-400 flex-shrink-0 mt-1" size={24} />
                        <div>
                            <h3 className="text-lg font-bold text-red-400 mb-1">Error</h3>
                            <p className="text-red-300">{error}</p>
                        </div>
                    </div>
                </div>
            )}

            {/* Validation Results */}
            {validationResults && (
                <div className="space-y-6">
                    {/* Summary Card */}
                    <div className="glass-panel p-8 rounded-2xl border border-white/10">
                        <div className="flex items-center justify-between mb-6">
                            <div>
                                <h2 className="text-3xl font-bold text-white flex items-center gap-3">
                                    <CheckCircle className="text-green-400" size={32} />
                                    Validation Complete
                                </h2>
                                <p className="text-slate-400 mt-1">
                                    Processed {validationResults.total_providers} providers •
                                    Completed {validationResults.completed_providers} •
                                    Status: {validationResults.status}
                                </p>
                            </div>
                            <button
                                onClick={handleReset}
                                className="px-4 py-2 border border-white/20 rounded-lg hover:bg-white/5 transition-colors text-white"
                            >
                                Start Over
                            </button>
                        </div>

                        {/* Bulk Actions */}
                        <div className="flex gap-4 mb-6">
                            <button
                                onClick={handleCallAll}
                                className="flex-1 px-6 py-3 bg-green-500/20 border border-green-500/30 rounded-xl text-green-400 font-semibold hover:bg-green-500/30 transition-colors flex items-center justify-center gap-2"
                            >
                                <Phone size={20} />
                                Call All Providers
                            </button>
                            <button
                                onClick={handleSMSAll}
                                className="flex-1 px-6 py-3 bg-blue-500/20 border border-blue-500/30 rounded-xl text-blue-400 font-semibold hover:bg-blue-500/30 transition-colors flex items-center justify-center gap-2"
                            >
                                <MessageSquare size={20} />
                                SMS All Providers
                            </button>
                            <button
                                className="flex-1 px-6 py-3 bg-white/10 border border-white/20 rounded-xl text-white font-semibold hover:bg-white/20 transition-colors flex items-center justify-center gap-2"
                            >
                                <Download size={20} />
                                Export Results
                            </button>
                        </div>

                        {/* Statistics */}
                        <div className="grid grid-cols-4 gap-4">
                            <div className="p-4 bg-white/5 rounded-xl border border-white/10 text-center">
                                <p className="text-slate-400 text-sm mb-1">Total</p>
                                <p className="text-3xl font-bold text-white">{validationResults.total_providers}</p>
                            </div>
                            <div className="p-4 bg-green-500/10 rounded-xl border border-green-500/20 text-center">
                                <p className="text-green-400 text-sm mb-1">Verified</p>
                                <p className="text-3xl font-bold text-green-400">
                                    {validationResults.results?.filter(r => r.validation_status === 'VERIFIED').length || 0}
                                </p>
                            </div>
                            <div className="p-4 bg-yellow-500/10 rounded-xl border border-yellow-500/20 text-center">
                                <p className="text-yellow-400 text-sm mb-1">Needs Review</p>
                                <p className="text-3xl font-bold text-yellow-400">
                                    {validationResults.results?.filter(r => r.validation_status === 'PARTIALLY_VERIFIED').length || 0}
                                </p>
                            </div>
                            <div className="p-4 bg-red-500/10 rounded-xl border border-red-500/20 text-center">
                                <p className="text-red-400 text-sm mb-1">Issues</p>
                                <p className="text-3xl font-bold text-red-400">
                                    {validationResults.results?.filter(r => r.validation_status === 'UNVERIFIED' || r.validation_status === 'FLAGGED').length || 0}
                                </p>
                            </div>
                        </div>
                    </div>

                    {/* Results Table */}
                    <div className="glass-panel rounded-2xl overflow-hidden">
                        <div className="overflow-x-auto">
                            <table className="w-full">
                                <thead className="bg-white/5 border-b border-white/10">
                                    <tr className="text-left text-slate-400 text-sm uppercase tracking-wider">
                                        <th className="p-4 font-medium">Provider</th>
                                        <th className="p-4 font-medium">Contact</th>
                                        <th className="p-4 font-medium">Confidence</th>
                                        <th className="p-4 font-medium">Status</th>
                                        <th className="p-4 font-medium">Issues</th>
                                    </tr>
                                </thead>
                                <tbody>
                                    {validationResults.results && validationResults.results.map((result, idx) => (
                                        <tr key={idx} className="border-b border-white/5 hover:bg-white/5 transition-colors">
                                            <td className="p-4">
                                                <div className="font-medium text-white">{result.provider_name || 'Unknown'}</div>
                                                {result.verified_specialty && (
                                                    <div className="text-sm text-slate-400">{result.verified_specialty}</div>
                                                )}
                                            </td>
                                            <td className="p-4">
                                                {result.verified_phone && (
                                                    <div className="text-sm text-slate-300 flex items-center gap-2">
                                                        <Phone size={14} className="text-green-400" />
                                                        {result.verified_phone}
                                                    </div>
                                                )}
                                                {result.verified_address && (
                                                    <div className="text-xs text-slate-400 mt-1">{result.verified_address}</div>
                                                )}
                                            </td>
                                            <td className="p-4">
                                                <div className="flex items-center gap-2">
                                                    <div className="w-20 h-2 bg-slate-700 rounded-full overflow-hidden">
                                                        <div
                                                            className={`h-full rounded-full ${result.confidence_scores.overall_confidence > 0.8 ? 'bg-green-500' :
                                                                result.confidence_scores.overall_confidence > 0.6 ? 'bg-yellow-500' :
                                                                    'bg-red-500'
                                                                }`}
                                                            style={{ width: `${result.confidence_scores.overall_confidence * 100}%` }}
                                                        />
                                                    </div>
                                                    <span className="text-sm font-medium text-white">
                                                        {Math.round(result.confidence_scores.overall_confidence * 100)}%
                                                    </span>
                                                </div>
                                            </td>
                                            <td className="p-4">
                                                <span className={`px-3 py-1 rounded-full text-xs font-medium border ${getStatusColor(result.validation_status)}`}>
                                                    {result.validation_status}
                                                </span>
                                            </td>
                                            <td className="p-4">
                                                {result.issues && result.issues.length > 0 ? (
                                                    <div className="text-sm text-slate-400">
                                                        {result.issues.length} issue{result.issues.length > 1 ? 's' : ''}
                                                    </div>
                                                ) : (
                                                    <div className="text-sm text-green-400">No issues</div>
                                                )}
                                            </td>
                                        </tr>
                                    ))}
                                </tbody>
                            </table>
                        </div>
                    </div>
                </div>
            )}
        </div>
    );
};

export default Validation;
