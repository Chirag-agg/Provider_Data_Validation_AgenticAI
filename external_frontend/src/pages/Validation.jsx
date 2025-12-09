import React, { useState } from 'react';
import { Play, CheckCircle, AlertTriangle, FileText, Loader } from 'lucide-react';
import gsap from 'gsap';

const Validation = () => {
    const [running, setRunning] = useState(false);
    const [result, setResult] = useState(null);
    const [progress, setProgress] = useState(0);

    const handleRun = async () => {
        setRunning(true);
        setResult(null);
        setProgress(0);

        // Simulate progress
        const interval = setInterval(() => {
            setProgress(prev => {
                if (prev >= 90) return prev;
                return prev + 10;
            });
        }, 200);

        try {
            // Simulate validation by showing a mock result
            await new Promise(resolve => setTimeout(resolve, 3000));
            clearInterval(interval);
            setProgress(100);
            setTimeout(() => {
                setResult({
                    processed: 1250,
                    issuesFound: 87,
                    autoUpdated: 42
                });
                setRunning(false);
            }, 500);
        } catch (error) {
            console.error("Validation failed", error);
            setRunning(false);
            clearInterval(interval);
        }
    };

    return (
        <div className="max-w-4xl mx-auto space-y-8">
            <div className="text-center space-y-4">
                <h1 className="text-4xl font-poster text-white">Run Validation Pipeline</h1>
                <p className="text-slate-400 max-w-lg mx-auto">
                    Trigger the AI-powered validation engine to cross-reference provider data against external registries, websites, and insurance databases.
                </p>
            </div>

            <div className="glass-panel p-12 rounded-3xl text-center border border-white/10 relative overflow-hidden">
                {/* Background Animation */}
                {running && (
                    <div className="absolute inset-0 bg-primary/5 animate-pulse pointer-events-none"></div>
                )}

                {!running && !result && (
                    <button
                        onClick={handleRun}
                        className="group relative inline-flex items-center justify-center px-8 py-4 font-bold text-white transition-all duration-200 bg-primary font-lg rounded-full hover:bg-primary/90 hover:scale-105 focus:outline-none ring-offset-2 focus:ring-2 ring-primary/50"
                    >
                        <Play className="mr-2 group-hover:translate-x-1 transition-transform" />
                        Start Full Validation
                    </button>
                )}

                {running && (
                    <div className="space-y-6">
                        <div className="w-24 h-24 mx-auto relative">
                            <Loader className="w-full h-full text-primary animate-spin" />
                            <span className="absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 font-bold text-white">{progress}%</span>
                        </div>
                        <p className="text-lg text-slate-300 animate-pulse">Analyzing provider records...</p>
                    </div>
                )}

                {result && (
                    <div className="space-y-6 animate-fade-in-up">
                        <div className="w-20 h-20 bg-green-500/20 rounded-full flex items-center justify-center mx-auto text-green-400 mb-6">
                            <CheckCircle size={40} />
                        </div>
                        <h2 className="text-2xl font-bold text-white">Validation Complete</h2>

                        <div className="grid grid-cols-3 gap-6 mt-8">
                            <div className="p-4 bg-white/5 rounded-xl border border-white/10">
                                <p className="text-slate-400 text-sm uppercase">Processed</p>
                                <p className="text-3xl font-bold text-white">{result.processed}</p>
                            </div>
                            <div className="p-4 bg-red-500/10 rounded-xl border border-red-500/20">
                                <p className="text-red-400 text-sm uppercase">Issues Found</p>
                                <p className="text-3xl font-bold text-red-400">{result.issuesFound}</p>
                            </div>
                            <div className="p-4 bg-blue-500/10 rounded-xl border border-blue-500/20">
                                <p className="text-blue-400 text-sm uppercase">Auto-Updated</p>
                                <p className="text-3xl font-bold text-blue-400">{result.autoUpdated}</p>
                            </div>
                        </div>

                        <div className="flex justify-center gap-4 mt-8">
                            <button onClick={() => setResult(null)} className="px-6 py-2 rounded-lg border border-white/10 hover:bg-white/5 transition-colors">
                                Run Again
                            </button>
                            <button className="px-6 py-2 rounded-lg bg-white/10 hover:bg-white/20 transition-colors flex items-center gap-2">
                                <FileText size={18} /> Download Report
                            </button>
                        </div>
                    </div>
                )}
            </div>
        </div>
    );
};

export default Validation;
