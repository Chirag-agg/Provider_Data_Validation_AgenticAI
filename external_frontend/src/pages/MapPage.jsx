import React, { useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { ArrowLeft, Activity } from 'lucide-react';
import WorldMap from '../components/WorldMap';

const MapPage = () => {
    const navigate = useNavigate();
    const [providers, setProviders] = useState([]);
    const [regionData, setRegionData] = useState({ east: 0, west: 0, central: 0, international: 0 });
    const [loading, setLoading] = useState(true);

    // Mock provider data
    const mockProviders = [
        { id: 1, name: 'Dr. Sarah Johnson', address: 'New York, NY', region: 'east' },
        { id: 2, name: 'Dr. Michael Chen', address: 'San Francisco, CA', region: 'west' },
        { id: 3, name: 'Dr. Emily Rodriguez', address: 'Chicago, IL', region: 'central' },
        { id: 4, name: 'Dr. James Wilson', address: 'London, UK', region: 'international' },
        { id: 5, name: 'Dr. Lisa Anderson', address: 'Boston, MA', region: 'east' },
        { id: 6, name: 'Dr. David Brown', address: 'Seattle, WA', region: 'west' },
        { id: 7, name: 'Dr. Jennifer Lee', address: 'Toronto, Canada', region: 'international' },
        { id: 8, name: 'Dr. Robert Taylor', address: 'Houston, TX', region: 'central' },
    ];

    useEffect(() => {
        const fetchProviders = async () => {
            try {
                setProviders(mockProviders);

                // Process regions
                const regions = { east: 0, west: 0, central: 0, international: 0 };
                mockProviders.forEach(p => {
                    const address = (p.address || '').toLowerCase();
                    if (address.includes('ny') || address.includes('ma') || address.includes('pa') ||
                        address.includes('nj') || address.includes('ct') || address.includes('vt') ||
                        address.includes('new york') || address.includes('boston') || address.includes('philadelphia')) {
                        regions.east++;
                    } else if (address.includes('ca') || address.includes('wa') || address.includes('or') ||
                        address.includes('az') || address.includes('nv') || address.includes('ut') ||
                        address.includes('california') || address.includes('seattle') || address.includes('portland')) {
                        regions.west++;
                    } else if (address.includes('india') || address.includes('mumbai') || address.includes('delhi') ||
                        address.includes('bangalore') || address.includes('hyderabad') || address.includes('chennai') ||
                        address.includes('uk') || address.includes('london') || address.includes('europe') ||
                        address.includes('canada') || address.includes('toronto') || address.includes('australia')) {
                        regions.international++;
                    } else {
                        regions.central++;
                    }
                });
                setRegionData(regions);
            } catch (error) {
                console.error("Failed to fetch map data", error);
            } finally {
                setLoading(false);
            }
        };

        fetchProviders();
    }, []);

    return (
        <div className="w-screen h-screen bg-slate-950 relative overflow-hidden flex flex-col">
            {/* Header / Nav */}
            <div className="absolute top-0 left-0 right-0 z-20 p-6 flex justify-between items-start pointer-events-none">
                <button
                    onClick={() => navigate('/')}
                    className="pointer-events-auto flex items-center gap-2 px-4 py-2 bg-slate-900/50 hover:bg-slate-800/80 backdrop-blur-md border border-white/10 rounded-full text-white transition-all group"
                >
                    <ArrowLeft size={18} className="group-hover:-translate-x-1 transition-transform" />
                    Back to Dashboard
                </button>

                <div className="glass-panel px-6 py-3 rounded-xl flex items-center gap-3">
                    <Activity className="text-neon-blue animate-pulse" size={24} />
                    <div>
                        <h1 className="text-xl font-poster text-white tracking-wide">Global Network</h1>
                        <p className="text-xs text-slate-400 font-mono">LIVE MONITORING</p>
                    </div>
                </div>
            </div>

            {/* Main Map Area */}
            <div className="flex-1 w-full h-full relative">
                {loading ? (
                    <div className="absolute inset-0 flex items-center justify-center">
                        <div className="animate-spin rounded-full h-12 w-12 border-t-2 border-b-2 border-primary"></div>
                    </div>
                ) : (
                    <WorldMap regionData={regionData} />
                )}
            </div>

            {/* Floating Stats Footer */}
            <div className="absolute bottom-8 left-1/2 -translate-x-1/2 z-20 pointer-events-none w-full max-w-4xl px-4">
                <div className="glass-panel p-6 rounded-2xl flex flex-wrap justify-between items-center gap-8 pointer-events-auto border border-white/10 shadow-2xl bg-slate-900/80 backdrop-blur-xl">
                    <div className="text-center min-w-[100px]">
                        <p className="text-slate-400 text-sm mb-1 uppercase tracking-wider font-semibold">Total Nodes</p>
                        <p className="text-4xl font-display font-bold text-white">{providers.length}</p>
                    </div>
                    <div className="w-px h-12 bg-white/10 hidden md:block"></div>
                    <div className="text-center min-w-[100px]">
                        <p className="text-slate-400 text-sm mb-1 uppercase tracking-wider font-semibold">North America</p>
                        <p className="text-4xl font-display font-bold text-neon-blue">{regionData.east + regionData.west + regionData.central}</p>
                    </div>
                    <div className="w-px h-12 bg-white/10 hidden md:block"></div>
                    <div className="text-center min-w-[100px]">
                        <p className="text-slate-400 text-sm mb-1 uppercase tracking-wider font-semibold">International</p>
                        <p className="text-4xl font-display font-bold text-amber-400">{regionData.international}</p>
                    </div>
                </div>
            </div>
        </div>
    );
};

export default MapPage;
