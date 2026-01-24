import React, { type ChangeEvent } from 'react';
import type { Config } from '../types';
import { ChevronDown, Type, Layout, Palette, PenTool } from 'lucide-react';

interface ConfigPanelProps {
    config: Config;
    onChange: (config: Config) => void;
}


const Section = ({ title, icon: Icon, children, defaultOpen = false }: any) => (
    <details className="group mb-4" open={defaultOpen}>
        <summary className="flex items-center justify-between cursor-pointer p-4 bg-chalkboard-light rounded-lg hover:bg-gray-700 transition-colors list-none">
            <div className="flex items-center space-x-3">
                <Icon className="w-5 h-5 text-accent-yellow" />
                <span className="font-semibold text-gray-200">{title}</span>
            </div>
            <ChevronDown className="w-4 h-4 text-gray-400 transform group-open:rotate-180 transition-transform" />
        </summary>
        <div className="p-4 space-y-4 border-l-2 border-gray-700 ml-4 mt-2">
            {children}
        </div>
    </details>
);

export const ConfigPanel: React.FC<ConfigPanelProps> = ({ config, onChange }) => {
    const handleChange = (field: keyof Config, value: string | number) => {
        onChange({ ...config, [field]: value });
    };

    const handleTextChange = (field: keyof Config) => (e: ChangeEvent<HTMLInputElement>) => {
        handleChange(field, e.target.value);
    };

    const handleNumberChange = (field: keyof Config) => (e: ChangeEvent<HTMLInputElement>) => {
        handleChange(field, Number(e.target.value));
    };

    return (
        <div className="space-y-2 pb-20">
            <h2 className="text-xl font-bold text-accent-yellow mb-6 px-2 flex items-center">
                <PenTool className="w-6 h-6 mr-3" />
                Slide Studio
            </h2>

            <Section title="Content" icon={Type} defaultOpen={true}>
                <div>
                    <label className="text-xs text-gray-400 uppercase font-semibold">Instructor Name</label>
                    <input
                        type="text"
                        value={config.instructor_name}
                        onChange={handleTextChange('instructor_name')}
                        className="input-field mt-1"
                        placeholder="Enter instructor name"
                    />
                </div>
                <div>
                    <label className="text-xs text-gray-400 uppercase font-semibold">Subtitle</label>
                    <input
                        type="text"
                        value={config.subtitle}
                        onChange={handleTextChange('subtitle')}
                        className="input-field mt-1"
                        placeholder="Enter subtitle"
                    />
                </div>
                <div>
                    <label className="text-xs text-gray-400 uppercase font-semibold">Badge Text</label>
                    <input
                        type="text"
                        value={config.badge_text}
                        onChange={handleTextChange('badge_text')}
                        className="input-field mt-1"
                        placeholder="Enter badge text"
                    />
                </div>
                <div>
                    <label className="text-xs text-gray-400 uppercase font-semibold">Watermark (Bottom Right)</label>
                    <input
                        type="text"
                        value={config.watermark_text || ''}
                        onChange={handleTextChange('watermark_text')}
                        className="input-field mt-1"
                        placeholder="Enter watermark text"
                    />
                </div>
            </Section>

            <Section title="Typography & Color" icon={Palette} defaultOpen={true}>
                <div className="mb-4">
                    <label className="text-xs text-gray-400 uppercase font-semibold block mb-2">Font Style</label>
                    <div className="grid grid-cols-2 gap-2">
                        {['Chalk', 'Casual', 'Playful', 'Natural'].map((font) => (
                            <button
                                key={font}
                                onClick={() => handleChange('font_family', font)}
                                className={`px-3 py-2 text-xs font-medium rounded-lg transition-all border ${config.font_family === font || (!config.font_family && font === 'Chalk')
                                    ? 'bg-accent-yellow text-black border-accent-yellow'
                                    : 'bg-white/5 text-gray-400 border-white/10 hover:border-white/30'
                                    }`}
                            >
                                {font}
                            </button>
                        ))}
                    </div>
                </div>

                <div>
                    <div className="flex justify-between mb-1">
                        <label className="text-xs text-gray-400 uppercase font-semibold">Heading Size</label>
                        <span className="text-xs text-accent-yellow">{config.font_size_heading || 60}px</span>
                    </div>
                    <input
                        type="range"
                        min="30"
                        max="100"
                        value={config.font_size_heading || 60}
                        onChange={handleNumberChange('font_size_heading')}
                        className="w-full h-1.5 bg-gray-700 rounded-lg appearance-none cursor-pointer accent-accent-yellow"
                    />
                </div>
                <div>
                    <div className="flex justify-between mb-1">
                        <label className="text-xs text-gray-400 uppercase font-semibold">Body Size</label>
                        <span className="text-xs text-accent-mint">{config.font_size_body || 28}px</span>
                    </div>
                    <input
                        type="range"
                        min="14"
                        max="60"
                        value={config.font_size_body || 28}
                        onChange={handleNumberChange('font_size_body')}
                        className="w-full h-1.5 bg-gray-700 rounded-lg appearance-none cursor-pointer accent-accent-mint"
                    />
                </div>
                <div>
                    <label className="text-xs text-gray-400 uppercase font-semibold block mb-2">Text Color</label>
                    <div className="flex items-center space-x-3 bg-chalkboard-light p-2 rounded-lg border border-gray-600">
                        <input
                            type="color"
                            value={config.font_text_color || '#F0C83C'}
                            onChange={handleTextChange('font_text_color')}
                            className="h-8 w-12 bg-transparent cursor-pointer rounded"
                        />
                        <span className="text-sm font-mono text-gray-300 uppercase">{config.font_text_color || '#F0C83C'}</span>
                    </div>
                </div>
            </Section>

            <Section title="Layout & Positioning" icon={Layout}>
                <div className="grid grid-cols-2 gap-4">
                    <div>
                        <label className="text-xs text-gray-400 uppercase font-semibold">X Offset</label>
                        <input
                            type="number"
                            value={config.pos_x || 0}
                            onChange={handleNumberChange('pos_x')}
                            className="input-field mt-1"
                        />
                    </div>
                    <div>
                        <label className="text-xs text-gray-400 uppercase font-semibold">Y Offset</label>
                        <input
                            type="number"
                            value={config.pos_y || 0}
                            onChange={handleNumberChange('pos_y')}
                            className="input-field mt-1"
                        />
                    </div>
                </div>

                <div className="mt-4">
                    <div className="flex justify-between mb-1">
                        <label className="text-xs text-gray-400 uppercase font-semibold">Pointer Spacing</label>
                        <span className="text-xs text-gray-400">{config.pointer_spacing || 0}px</span>
                    </div>
                    <input
                        type="range"
                        min="-50"
                        max="100"
                        value={config.pointer_spacing || 0}
                        onChange={handleNumberChange('pointer_spacing')}
                        className="w-full h-1.5 bg-gray-700 rounded-lg appearance-none cursor-pointer accent-accent-mint"
                    />
                </div>
            </Section>
        </div>
    );
};
