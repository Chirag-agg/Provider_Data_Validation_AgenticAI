import React, { useEffect, useState } from 'react';
import { Activity, Clock, CheckCircle, XCircle, AlertCircle } from 'lucide-react';

const Logs = () => {
    const [logs, setLogs] = useState([]);

    // Mock logs data
    const mockLogs = [
        { id: 1, action: 'Validation Started', status: 'Success', timestamp: new Date(Date.now() - 3600000), details: 'Started batch validation for 1250 providers' },
        { id: 2, action: 'Data Cross-Reference', status: 'Success', timestamp: new Date(Date.now() - 3300000), details: 'Checked 1250 providers against NPI Registry' },
        { id: 3, action: 'License Verification', status: 'Success', timestamp: new Date(Date.now() - 3000000), details: 'Verified licenses for 1125 providers' },
        { id: 4, action: 'Address Update', status: 'Success', timestamp: new Date(Date.now() - 2700000), details: 'Updated 87 provider addresses from Google Maps' },
        { id: 5, action: 'Insurance Network Check', status: 'Success', timestamp: new Date(Date.now() - 2400000), details: 'Validated provider networks with 5 insurers' },
        { id: 6, action: 'Conflict Resolution', status: 'Success', timestamp: new Date(Date.now() - 2100000), details: 'Resolved 42 data conflicts automatically' },
    ];

    useEffect(() => {
        setLogs(mockLogs);
    }, []);

    const getIcon = (status) => {
        switch (status) {
            case 'Success': return <CheckCircle size={18} className="text-green-400" />;
            case 'Failed': return <XCircle size={18} className="text-red-400" />;
            default: return <AlertCircle size={18} className="text-yellow-400" />;
        }
    };

    return (
        <div className="space-y-6">
            <h1 className="text-5xl font-poster text-white">Agent Activity Logs</h1>

            <div className="glass-panel p-6 rounded-2xl">
                <div className="space-y-6 relative before:absolute before:left-4 before:top-6 before:bottom-6 before:w-0.5 before:bg-white/10">
                    {logs.map((log) => (
                        <div key={log.id} className="relative pl-12">
                            <div className="absolute left-2 top-1 w-4 h-4 rounded-full bg-surface border-2 border-primary z-10"></div>
                            <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2 mb-1">
                                <h3 className="text-xl font-medium text-white flex items-center gap-2">
                                    {log.action}
                                    {getIcon(log.status)}
                                </h3>
                                <span className="text-sm text-slate-500 flex items-center gap-1">
                                    <Clock size={14} /> {log.timestamp.toLocaleString()}
                                </span>
                            </div>
                            <p className="text-slate-400 text-base bg-white/5 p-3 rounded-lg border border-white/5">
                                {log.details}
                            </p>
                        </div>
                    ))}
                </div>
            </div>
        </div>
    );
};

export default Logs;
