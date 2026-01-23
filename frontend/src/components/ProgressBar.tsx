import React from 'react';

interface ProgressBarProps {
    current: number;
    total: number;
    label?: string;
}

export const ProgressBar: React.FC<ProgressBarProps> = ({ current, total, label }) => {
    const percentage = total > 0 ? Math.round((current / total) * 100) : 0;

    return (
        <div className="w-full">
            {label && (
                <div className="flex justify-between items-center mb-2">
                    <span className="text-sm font-medium text-gray-300">{label}</span>
                    <span className="text-sm font-medium text-accent-orange">
                        {current} / {total}
                    </span>
                </div>
            )}

            <div className="w-full bg-chalkboard-light rounded-full h-4 overflow-hidden border border-gray-600">
                <div
                    className="h-full bg-gradient-to-r from-accent-orange to-accent-yellow transition-all duration-300 ease-out flex items-center justify-end pr-2"
                    style={{ width: `${percentage}%` }}
                >
                    {percentage > 10 && (
                        <span className="text-xs font-bold text-chalkboard-dark">
                            {percentage}%
                        </span>
                    )}
                </div>
            </div>
        </div>
    );
};
