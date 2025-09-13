import React from 'react';

interface DashboardStatCardProps {
    title: string;
    value: string;
    icon: React.ReactNode;
    change?: string;
    changeColor?: string;
}

const DashboardStatCard: React.FC<DashboardStatCardProps> = ({ 
    title, 
    value, 
    icon, 
    change, 
    changeColor = 'text-green-500' 
}) => (
    <div className="bg-white p-5 rounded-xl shadow-md border border-slate-200/80">
        <div className="flex items-center justify-between">
            <p className="text-sm font-medium text-slate-500">{title}</p>
            <div className="text-slate-400">{icon}</div>
        </div>
        <div className="mt-2 flex items-baseline">
            <p className="text-2xl font-bold text-slate-900">{value}</p>
            {change && <span className={`ml-2 text-sm font-semibold ${changeColor}`}>{change}</span>}
        </div>
    </div>
);

export default DashboardStatCard;
