import React from 'react';

interface ColorPickerToolbarProps {
    color: string;
    onChange: (color: string) => void;
    position: { x: number; y: number };
}

const PRESET_COLORS = [
    '#F0C83C', // Yellow (Default)
    '#64DCB4', // Mint
    '#FFB450', // Orange
    '#F0F5FA', // White
    '#F28B82', // Red/Pink
    '#81C995', // Green
    '#8AB4F8', // Blue
    '#C58AF9', // Purple
];

export const ColorPickerToolbar: React.FC<ColorPickerToolbarProps> = ({
    color,
    onChange,
    position
}) => {
    return (
        <div
            className="absolute z-50 flex items-center space-x-1 p-2 bg-[#1e293b] border border-white/10 rounded-full shadow-2xl animate-in fade-in zoom-in duration-200"
            style={{
                left: position.x,
                top: position.y - 60, // Float above
                transform: 'translateX(-50%)'
            }}
            onMouseDown={(e) => e.stopPropagation()} // Prevent deselection
        >
            {PRESET_COLORS.map((c) => (
                <button
                    key={c}
                    onClick={() => onChange(c)}
                    className={`w-6 h-6 rounded-full border-2 transition-transform hover:scale-125 ${color === c ? 'border-white scale-110' : 'border-transparent hover:border-white/50'}`}
                    style={{ backgroundColor: c }}
                />
            ))}

            <div className="w-px h-6 bg-white/10 mx-1"></div>

            <div className="relative group">
                <div className="w-6 h-6 rounded-full bg-gradient-to-tr from-blue-500 to-pink-500 border-2 border-transparent group-hover:border-white/50 cursor-pointer overflow-hidden">
                    <input
                        type="color"
                        value={color}
                        onChange={(e) => onChange(e.target.value)}
                        className="opacity-0 w-full h-full cursor-pointer"
                    />
                </div>
            </div>
        </div>
    );
};
