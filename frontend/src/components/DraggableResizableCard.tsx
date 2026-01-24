import React, { useRef, useState, useEffect } from 'react';
import { Move } from 'lucide-react';

interface DraggableResizableCardProps {
    id: string;
    text: string;
    x: number;
    y: number;
    fontSize: number;
    color: string;
    fontFamily: string;
    backgroundColor?: string;
    isBadge?: boolean;

    // Canvas context
    containerScale: number; // e.g. 0.5 for 960px preview of 1920px slide
    isSelected: boolean;

    onSelect: () => void;
    onChange: (attrs: { x: number; y: number; fontSize: number }) => void;
}

export const DraggableResizableCard: React.FC<DraggableResizableCardProps> = ({
    id,
    text,
    x,
    y,
    fontSize,
    color,
    fontFamily,
    backgroundColor,
    isBadge,
    containerScale,
    isSelected,
    onSelect,
    onChange
}) => {
    const [isDragging, setIsDragging] = useState(false);
    const [isResizing, setIsResizing] = useState(false);
    const [dragStart, setDragStart] = useState({ x: 0, y: 0 });
    const [initialAttrs, setInitialAttrs] = useState({ x, y, fontSize });

    const cardRef = useRef<HTMLDivElement>(null);

    // Font mapping
    const getFontFamily = (name: string) => {
        switch (name) {
            case 'Chalk': return 'Patrick Hand';
            case 'Casual': return 'Caveat';
            case 'Playful': return 'Indie Flower';
            case 'Natural': return 'Kalam';
            default: return 'Patrick Hand';
        }
    };

    // Calculate display values
    const displayX = x * containerScale;
    const displayY = y * containerScale;
    const displayFontSize = fontSize * containerScale;

    // Handlers
    const handleMouseDown = (e: React.MouseEvent) => {
        e.stopPropagation();
        e.preventDefault(); // Prevent text selection
        onSelect();

        setIsDragging(true);
        setDragStart({ x: e.clientX, y: e.clientY });
        setInitialAttrs({ x, y, fontSize });
    };

    const handleResizeStart = (e: React.MouseEvent) => {
        e.stopPropagation();
        e.preventDefault();
        onSelect();

        setIsResizing(true);
        setDragStart({ x: e.clientX, y: e.clientY });
        setInitialAttrs({ x, y, fontSize });
    };

    // Global Listeners for dragging/resizing
    useEffect(() => {
        if (!isDragging && !isResizing) return;

        const handleMove = (e: MouseEvent) => {
            const dx = (e.clientX - dragStart.x) / containerScale;
            const dy = (e.clientY - dragStart.y) / containerScale;

            if (isDragging) {
                onChange({
                    x: Math.round(initialAttrs.x + dx),
                    y: Math.round(initialAttrs.y + dy),
                    fontSize: initialAttrs.fontSize
                });
            } else if (isResizing) {
                // Resize logic: 
                // Scaling font based on horizontal drag (dragging Right increases size)
                // Or diagonal. Let's start with drag Right/Down = Increase.
                // Simple scalar: 1px movement = 0.5 pt font change?
                // Better: Percentage increase.

                const sensitivity = 0.5;
                const sizeDelta = (dx + dy) * sensitivity;
                const newSize = Math.max(10, initialAttrs.fontSize + sizeDelta);

                onChange({
                    x: initialAttrs.x,
                    y: initialAttrs.y,
                    fontSize: Math.round(newSize)
                });
            }
        };

        const handleUp = () => {
            setIsDragging(false);
            setIsResizing(false);
        };

        window.addEventListener('mousemove', handleMove);
        window.addEventListener('mouseup', handleUp);

        return () => {
            window.removeEventListener('mousemove', handleMove);
            window.removeEventListener('mouseup', handleUp);
        };
    }, [isDragging, isResizing, dragStart, initialAttrs, containerScale, onChange]);

    return (
        <div
            ref={cardRef}
            className={`absolute group select-none ${isSelected ? 'z-50' : 'z-30'}`}
            style={{
                left: displayX,
                top: displayY,
                cursor: isDragging ? 'grabbing' : 'grab',
            }}
            onMouseDown={handleMouseDown}
        >
            {/* The Content */}
            <div
                className={`relative px-2 py-1 transition-colors duration-200 
                           ${isSelected ? 'ring-2 ring-accent-mint ring-offset-2 ring-offset-[#0f111a]' : 'hover:bg-white/5 border border-transparent hover:border-white/10 rounded-lg'}
                           ${backgroundColor ? 'rounded-md shadow-lg' : ''}`}
                style={{
                    backgroundColor: backgroundColor || 'transparent',
                    transform: isBadge ? 'rotate(-2deg)' : 'none'
                }}
            >
                <span
                    style={{
                        fontFamily: getFontFamily(fontFamily),
                        fontSize: `${displayFontSize}px`,
                        color: color,
                        display: 'block',
                        lineHeight: '1.2'
                    }}
                    className="whitespace-nowrap font-bold"
                >
                    {text}
                </span>

                {/* Resize Handles (Only show when selected) */}
                {isSelected && (
                    <>
                        <div className="absolute -top-3 -left-3 px-1 py-0.5 bg-accent-mint text-[10px] text-black font-bold rounded shadow-md pointer-events-none whitespace-nowrap">
                            {Math.round(fontSize)}px
                        </div>

                        {/* Corner Handle (Bottom Right) - Larger Hitbox */}
                        <div
                            className="absolute -bottom-3 -right-3 w-10 h-10 flex items-center justify-center cursor-nwse-resize z-50 group/handle"
                            onMouseDown={handleResizeStart}
                        >
                            <div className="w-4 h-4 bg-white border-2 border-accent-mint rounded-full shadow-sm group-hover/handle:scale-125 transition-transform" />
                        </div>
                    </>
                )}
            </div>

        </div>
    );
};
