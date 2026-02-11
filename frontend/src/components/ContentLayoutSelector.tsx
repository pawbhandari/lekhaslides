import { Minus, Plus } from 'lucide-react';

interface Props {
    region: string;
    scale: number;
    onRegionChange: (region: string) => void;
    onScaleChange: (scale: number) => void;
}

const REGIONS = [
    { id: 'full', label: 'Full', icon: '▰▰' },
    { id: 'left-half', label: 'Left', icon: '▰▱' },
    { id: 'right-half', label: 'Right', icon: '▱▰' },
    { id: 'left-third', label: 'L⅓', icon: '▰▱▱' },
    { id: 'center-third', label: 'C⅓', icon: '▱▰▱' },
    { id: 'right-third', label: 'R⅓', icon: '▱▱▰' },
];

export function ContentLayoutSelector({ region, scale, onRegionChange, onScaleChange }: Props) {
    return (
        <div className="space-y-4">
            {/* Region Selector */}
            <div>
                <label className="text-xs text-gray-400 uppercase tracking-wider mb-2 block font-medium">
                    Content Region
                </label>
                <div className="grid grid-cols-3 gap-1.5">
                    {REGIONS.map((r) => (
                        <button
                            key={r.id}
                            onClick={() => onRegionChange(r.id)}
                            className={`py-2 px-2 rounded-lg text-xs font-medium transition-all text-center
                ${region === r.id
                                    ? 'bg-accent-mint/20 text-accent-mint border border-accent-mint/30 shadow-sm shadow-accent-mint/10'
                                    : 'bg-white/5 text-gray-400 border border-white/5 hover:bg-white/10 hover:text-gray-300'
                                }`}
                        >
                            <span className="block text-base mb-0.5 tracking-wider font-mono">{r.icon}</span>
                            <span>{r.label}</span>
                        </button>
                    ))}
                </div>
            </div>

            {/* Content Scale */}
            <div>
                <div className="flex items-center justify-between mb-2">
                    <label className="text-xs text-gray-400 uppercase tracking-wider font-medium">
                        Content Scale
                    </label>
                    <span className="text-xs text-accent-mint font-mono font-bold">
                        {Math.round(scale * 100)}%
                    </span>
                </div>
                <div className="flex items-center gap-2">
                    <button
                        onClick={() => onScaleChange(Math.max(0.5, scale - 0.1))}
                        className="w-8 h-8 rounded-lg bg-white/5 border border-white/10 text-gray-400 hover:text-white 
                     hover:bg-white/10 flex items-center justify-center transition-all"
                    >
                        <Minus className="w-3.5 h-3.5" />
                    </button>
                    <input
                        type="range"
                        min={50}
                        max={200}
                        value={scale * 100}
                        onChange={(e) => onScaleChange(parseInt(e.target.value) / 100)}
                        className="flex-1 accent-[#64DCB4] h-1.5"
                    />
                    <button
                        onClick={() => onScaleChange(Math.min(2.0, scale + 0.1))}
                        className="w-8 h-8 rounded-lg bg-white/5 border border-white/10 text-gray-400 hover:text-white 
                     hover:bg-white/10 flex items-center justify-center transition-all"
                    >
                        <Plus className="w-3.5 h-3.5" />
                    </button>
                </div>
            </div>
        </div>
    );
}
