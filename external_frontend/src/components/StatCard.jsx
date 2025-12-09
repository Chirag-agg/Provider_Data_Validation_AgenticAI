import React from 'react';

const StatCard = ({ title, value, icon: Icon, trend, isAlert, className }) => {
    const bgColor = isAlert ? 'bg-red-500/10' : 'bg-blue-500/10';
    const borderColor = isAlert ? 'border-red-500/20' : 'border-blue-500/20';
    const iconColor = isAlert ? 'text-red-400' : 'text-blue-400';
    const trendColor = trend && trend.includes('-') ? 'text-red-400' : 'text-green-400';

    return (
        <div className={`${className} glass-card p-6 rounded-lg border ${borderColor} hover:border-white/30 transition-all`}>
            <div className="flex items-start justify-between">
                <div>
                    <p className="text-gray-400 text-sm mb-2">{title}</p>
                    <h3 className="text-3xl font-bold text-white">{value}</h3>
                </div>
                <div className={`p-3 rounded-lg ${bgColor}`}>
                    <Icon className={`w-6 h-6 ${iconColor}`} />
                </div>
            </div>
            {trend && (
                <p className={`text-xs mt-3 ${trendColor}`}>{trend}</p>
            )}
        </div>
    );
};

export default StatCard;
