import React from 'react';
import type { Config } from '../types';

interface ConfigPanelProps {
    config: Config;
    onChange: (config: Config) => void;
}

export const ConfigPanel: React.FC<ConfigPanelProps> = ({ config, onChange }) => {
    const handleChange = (field: keyof Config, value: string) => {
        onChange({ ...config, [field]: value });
    };

    return (
        <div className="card sticky top-4">
            <h2 className="text-xl font-bold text-accent-yellow mb-6 flex items-center">
                <svg className="w-6 h-6 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 6V4m0 2a2 2 0 100 4m0-4a2 2 0 110 4m-6 8a2 2 0 100-4m0 4a2 2 0 110-4m0 4v2m0-6V4m6 6v10m6-2a2 2 0 100-4m0 4a2 2 0 110-4m0 4v2m0-6V4" />
                </svg>
                Configuration
            </h2>

            <div className="space-y-5">
                <div>
                    <label className="block text-sm font-medium text-gray-300 mb-2">
                        Instructor Name
                    </label>
                    <input
                        type="text"
                        value={config.instructor_name}
                        onChange={(e) => handleChange('instructor_name', e.target.value)}
                        className="input-field"
                        placeholder="Enter instructor name"
                    />
                </div>

                <div>
                    <label className="block text-sm font-medium text-gray-300 mb-2">
                        Subtitle
                    </label>
                    <input
                        type="text"
                        value={config.subtitle}
                        onChange={(e) => handleChange('subtitle', e.target.value)}
                        className="input-field"
                        placeholder="Enter subtitle"
                    />
                </div>

                <div>
                    <label className="block text-sm font-medium text-gray-300 mb-2">
                        Badge Text
                    </label>
                    <input
                        type="text"
                        value={config.badge_text}
                        onChange={(e) => handleChange('badge_text', e.target.value)}
                        className="input-field"
                        placeholder="Enter badge text"
                    />
                </div>
            </div>

            <div className="mt-6 p-4 bg-chalkboard-dark rounded-lg border border-accent-orange/30">
                <p className="text-xs text-gray-400 leading-relaxed">
                    These settings will appear on all generated slides. The instructor name appears in yellow,
                    subtitle in mint green, and badge in the top-right corner.
                </p>
            </div>
        </div>
    );
};
