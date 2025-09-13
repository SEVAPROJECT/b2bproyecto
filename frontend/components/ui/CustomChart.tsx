import React from 'react';

interface ChartDataPoint {
    name: string;
    value: number;
}

interface CustomChartProps {
    data: ChartDataPoint[];
    dataKey: string;
    chartType: 'line' | 'bar';
}

const CustomChart: React.FC<CustomChartProps> = ({ data, dataKey, chartType }) => {
    // Datos mock para los gráficos
    const mockData = [
        { name: 'Ene', value: 65 },
        { name: 'Feb', value: 78 },
        { name: 'Mar', value: 90 },
        { name: 'Abr', value: 85 },
        { name: 'May', value: 95 },
        { name: 'Jun', value: 110 }
    ];

    const chartData = data.length > 0 ? data : mockData;
    const maxValue = Math.max(...chartData.map(d => d.value));

    return (
        <div className="h-64 w-full">
            <div className="h-full flex items-end justify-between space-x-2">
                {chartData.map((item, index) => {
                    const height = (item.value / maxValue) * 100;
                    return (
                        <div key={index} className="flex flex-col items-center flex-1">
                            <div 
                                className={`w-full bg-primary-500 rounded-t ${
                                    chartType === 'line' ? 'h-1' : ''
                                }`}
                                style={{ 
                                    height: chartType === 'bar' ? `${height}%` : '4px',
                                    minHeight: chartType === 'bar' ? '20px' : '4px'
                                }}
                            />
                            <span className="text-xs text-slate-500 mt-2">{item.name}</span>
                        </div>
                    );
                })}
            </div>
        </div>
    );
};

export default CustomChart;
