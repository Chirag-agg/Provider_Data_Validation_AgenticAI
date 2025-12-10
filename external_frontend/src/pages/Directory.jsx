import React, { useState, useEffect, useRef } from 'react';
import { Search, Filter, ChevronRight, Phone, MapPin, AlertCircle, CheckCircle, Plus, X } from 'lucide-react';
import { useNavigate } from 'react-router-dom';
import gsap from 'gsap';

const Directory = () => {
    const [providers, setProviders] = useState([]);
    const [search, setSearch] = useState('');
    const [statusFilter, setStatusFilter] = useState('');
    const [showModal, setShowModal] = useState(false);
    const [formData, setFormData] = useState({ name: '', specialty: '', phone: '', address: '' });
    const [isSubmitting, setIsSubmitting] = useState(false);
    const tableRef = useRef(null);
    const modalRef = useRef(null);
    const navigate = useNavigate();

    const specialties = ['Cardiology', 'Dermatology', 'Neurology', 'Pediatrics', 'Oncology', 'General Practice'];

    useEffect(() => {
        fetchProviders();
    }, [search, statusFilter]);

    const fetchProviders = async () => {
        try {
            // Load validated providers from localStorage
            const storedResults = localStorage.getItem('validationResults');
            let allProviders = [];

            if (storedResults) {
                const results = JSON.parse(storedResults);
                // Convert validation results to provider format
                allProviders = results.map((result, index) => ({
                    id: result.provider_id || `provider-${index + 1}`,
                    name: result.provider_name,
                    specialty: result.verified_specialty || 'Unknown',
                    phone: result.verified_phone || 'N/A',
                    address: result.verified_address || 'N/A',
                    confidence: Math.round(result.confidence_scores.overall_confidence * 100),
                    status: result.validation_status === 'VERIFIED' ? 'Verified' :
                        result.validation_status === 'PARTIALLY_VERIFIED' ? 'Needs Review' :
                            result.validation_status === 'FLAGGED' ? 'Needs Review' :
                                'Auto-Updated'
                }));
            }

            let filtered = allProviders;

            if (search) {
                filtered = filtered.filter(p =>
                    p.name.toLowerCase().includes(search.toLowerCase()) ||
                    p.specialty.toLowerCase().includes(search.toLowerCase())
                );
            }

            if (statusFilter) {
                filtered = filtered.filter(p => p.status === statusFilter);
            }

            setProviders(filtered);

            // Animate rows in
            if (tableRef.current && filtered.length > 0) {
                gsap.fromTo(tableRef.current.children,
                    { y: 20, opacity: 0 },
                    { y: 0, opacity: 1, duration: 0.4, stagger: 0.05, ease: 'power2.out', clearProps: 'all' }
                );
            }
        } catch (error) {
            console.error("Error fetching providers", error);
        }
    };

    const getStatusColor = (status) => {
        switch (status) {
            case 'Verified': return 'bg-neon-mint/20 text-neon-mint border-neon-mint/30 shadow-none';
            case 'Needs Review': return 'bg-accent/20 text-accent border-accent/30 shadow-none';
            case 'Auto-Updated': return 'bg-neon-blue/20 text-neon-blue border-neon-blue/30 shadow-none';
            default: return 'bg-surface text-slate-400 border-white/10';
        }
    };

    const handleOpenModal = () => {
        setShowModal(true);
        if (modalRef.current) {
            gsap.fromTo(modalRef.current,
                { opacity: 0, scale: 0.9 },
                { opacity: 1, scale: 1, duration: 0.3, ease: 'back.out(1.7)' }
            );
        }
    };

    const handleCloseModal = () => {
        if (modalRef.current) {
            gsap.to(modalRef.current, {
                opacity: 0,
                scale: 0.9,
                duration: 0.2,
                onComplete: () => {
                    setShowModal(false);
                    setFormData({ name: '', specialty: '', phone: '', address: '' });
                }
            });
        }
    };

    const handleInputChange = (e) => {
        setFormData({ ...formData, [e.target.name]: e.target.value });
    };

    const handleSubmit = async (e) => {
        e.preventDefault();
        setIsSubmitting(true);

        try {
            // Add new provider to mock data
            const newProvider = {
                id: providers.length + 1,
                ...formData,
                confidence: 75,
                status: 'Needs Review'
            };
            setProviders([...providers, newProvider]);
            handleCloseModal();
        } catch (error) {
            console.error('Error creating provider:', error);
            alert('Failed to create provider. Please try again.');
        } finally {
            setIsSubmitting(false);
        }
    };

    return (
        <div className="space-y-6">
            <div className="flex justify-between items-center">
                <h1 className="text-5xl font-poster text-white">Provider Directory</h1>
                <div className="flex gap-4 items-center">
                    <button
                        onClick={handleOpenModal}
                        className="px-5 py-3 bg-gradient-to-r from-primary to-neon-blue text-white rounded-xl font-semibold text-base flex items-center gap-2 hover:shadow-lg hover:shadow-primary/50 transition-all hover:scale-105 active:scale-95"
                    >
                        <Plus size={20} /> Add Provider
                    </button>
                    <div className="relative group">
                        <Search className="absolute left-3 top-1/2 -translate-y-1/2 text-slate-400 group-focus-within:text-primary transition-colors" size={18} />
                        <input
                            type="text"
                            placeholder="Search providers..."
                            className="bg-surface/50 border border-white/10 rounded-xl pl-10 pr-4 py-3 text-base focus:outline-none focus:border-primary/50 focus:bg-surface transition-all w-64"
                            value={search}
                            onChange={(e) => setSearch(e.target.value)}
                        />
                    </div>
                    <div className="relative">
                        <Filter className="absolute left-3 top-1/2 -translate-y-1/2 text-slate-400" size={18} />
                        <select
                            className="bg-surface/50 border border-white/10 rounded-xl pl-10 pr-8 py-3 text-base focus:outline-none focus:border-primary/50 appearance-none cursor-pointer"
                            value={statusFilter}
                            onChange={(e) => setStatusFilter(e.target.value)}
                        >
                            <option value="">All Statuses</option>
                            <option value="Verified">Verified</option>
                            <option value="Needs Review">Needs Review</option>
                            <option value="Auto-Updated">Auto-Updated</option>
                        </select>
                    </div>
                </div>
            </div>

            <div className="glass-panel rounded-2xl overflow-hidden">
                <table className="w-full text-left border-collapse">
                    <thead>
                        <tr className="border-b border-white/10 text-slate-400 text-sm uppercase tracking-wider">
                            <th className="p-4 font-medium">Provider</th>
                            <th className="p-4 font-medium">Specialty</th>
                            <th className="p-4 font-medium">Contact Info</th>
                            <th className="p-4 font-medium">Confidence</th>
                            <th className="p-4 font-medium">Status</th>
                            <th className="p-4 font-medium"></th>
                        </tr>
                    </thead>
                    <tbody ref={tableRef} className="text-base">
                        {providers.map((provider) => (
                            <tr
                                key={provider.id}
                                onClick={() => navigate(`/provider/${provider.id}`)}
                                className="border-b border-white/5 hover:bg-white/5 transition-colors cursor-pointer group"
                            >
                                <td className="p-4">
                                    <div className="flex items-center gap-3">
                                        <img src="/provider-icon.png" alt="" className="w-10 h-10 rounded-full border border-white/10 bg-white/5 p-1" />
                                        <div>
                                            <div className="font-medium text-white text-lg">{provider.name}</div>
                                            <div className="text-sm text-slate-500">ID: {String(provider.id).padStart(8, '0')}</div>
                                        </div>
                                    </div>
                                </td>
                                <td className="p-4 text-slate-300 text-base">{provider.specialty}</td>
                                <td className="p-4">
                                    <div className="flex items-center gap-2 text-slate-400 text-sm mb-1">
                                        <Phone size={14} /> {provider.phone}
                                    </div>
                                    <div className="flex items-center gap-2 text-slate-400 text-sm">
                                        <MapPin size={14} /> {provider.address}
                                    </div>
                                </td>
                                <td className="p-4">
                                    <div className="flex items-center gap-2">
                                        <div className="w-16 h-1.5 bg-slate-700 rounded-full overflow-hidden">
                                            <div
                                                className={`h-full rounded-full ${provider.confidence > 80 ? 'bg-green-500' : provider.confidence > 60 ? 'bg-yellow-500' : 'bg-red-500'}`}
                                                style={{ width: `${provider.confidence}%` }}
                                            />
                                        </div>
                                        <span className="text-sm font-medium">{provider.confidence}%</span>
                                    </div>
                                </td>
                                <td className="p-4">
                                    <span className={`px-3 py-1.5 rounded-full text-sm font-medium border ${getStatusColor(provider.status)}`}>
                                        {provider.status}
                                    </span>
                                </td>
                                <td className="p-4 text-right">
                                    <ChevronRight className="text-slate-600 group-hover:text-white group-hover:translate-x-1 transition-all" size={18} />
                                </td>
                            </tr>
                        ))}
                    </tbody>
                </table>
                {providers.length === 0 && (
                    <div className="p-8 text-center text-slate-500">No providers found matching your criteria.</div>
                )}
            </div>

            {/* Add Provider Modal */}
            {showModal && (
                <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/60 backdrop-blur-sm" onClick={handleCloseModal}>
                    <div
                        ref={modalRef}
                        className="glass-panel p-8 rounded-3xl w-full max-w-lg mx-4 border-2 border-white/20 shadow-2xl"
                        onClick={(e) => e.stopPropagation()}
                    >
                        <div className="flex justify-between items-center mb-6">
                            <h2 className="text-3xl font-poster text-white">Add New Provider</h2>
                            <button
                                onClick={handleCloseModal}
                                className="p-2 hover:bg-white/10 rounded-lg transition-colors"
                            >
                                <X size={24} className="text-slate-400" />
                            </button>
                        </div>

                        <form onSubmit={handleSubmit} className="space-y-5">
                            <div>
                                <label className="block text-sm font-medium text-slate-300 mb-2">Provider Name</label>
                                <input
                                    type="text"
                                    name="name"
                                    value={formData.name}
                                    onChange={handleInputChange}
                                    required
                                    className="w-full bg-surface/50 border border-white/10 rounded-xl px-4 py-3 text-base text-white focus:outline-none focus:border-primary/50 transition-all"
                                    placeholder="Dr. John Smith"
                                />
                            </div>

                            <div>
                                <label className="block text-sm font-medium text-slate-300 mb-2">Specialty</label>
                                <select
                                    name="specialty"
                                    value={formData.specialty}
                                    onChange={handleInputChange}
                                    required
                                    className="w-full bg-surface/50 border border-white/10 rounded-xl px-4 py-3 text-base text-white focus:outline-none focus:border-primary/50 transition-all appearance-none cursor-pointer"
                                >
                                    <option value="">Select a specialty</option>
                                    {specialties.map((spec) => (
                                        <option key={spec} value={spec}>{spec}</option>
                                    ))}
                                </select>
                            </div>

                            <div>
                                <label className="block text-sm font-medium text-slate-300 mb-2">Phone Number</label>
                                <input
                                    type="tel"
                                    name="phone"
                                    value={formData.phone}
                                    onChange={handleInputChange}
                                    required
                                    className="w-full bg-surface/50 border border-white/10 rounded-xl px-4 py-3 text-base text-white focus:outline-none focus:border-primary/50 transition-all"
                                    placeholder="555-123-4567"
                                />
                            </div>

                            <div>
                                <label className="block text-sm font-medium text-slate-300 mb-2">Address</label>
                                <input
                                    type="text"
                                    name="address"
                                    value={formData.address}
                                    onChange={handleInputChange}
                                    required
                                    className="w-full bg-surface/50 border border-white/10 rounded-xl px-4 py-3 text-base text-white focus:outline-none focus:border-primary/50 transition-all"
                                    placeholder="123 Main Street, City, State"
                                />
                            </div>

                            <div className="flex gap-3 pt-4">
                                <button
                                    type="button"
                                    onClick={handleCloseModal}
                                    className="flex-1 px-5 py-3 bg-white/5 hover:bg-white/10 border border-white/10 rounded-xl text-base font-medium text-white transition-all"
                                >
                                    Cancel
                                </button>
                                <button
                                    type="submit"
                                    disabled={isSubmitting}
                                    className="flex-1 px-5 py-3 bg-gradient-to-r from-primary to-neon-blue text-white rounded-xl font-semibold text-base hover:shadow-lg hover:shadow-primary/50 transition-all disabled:opacity-50 disabled:cursor-not-allowed"
                                >
                                    {isSubmitting ? 'Adding...' : 'Add Provider'}
                                </button>
                            </div>
                        </form>
                    </div>
                </div>
            )}
        </div>
    );
};

export default Directory;
