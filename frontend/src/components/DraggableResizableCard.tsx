import React, { useRef, useState, useEffect } from 'react';
import { ColorPickerToolbar } from './ColorPickerToolbar';
interface DraggableResizableCardProps {
    id: string;
    text: string;
    x: number;
    y: number;
    fontSize: number;
    color: string;
    rotation: number;
    fontFamily: string;
    backgroundColor?: string;
    containerScale: number;
    isSelected: boolean;
    onSelect: () => void;
    onChange: (attrs: { x: number; y: number; fontSize: number; rotation: number }) => void;
    onColorChange: (color: string) => void;
}

export const DraggableResizableCard: React.FC<DraggableResizableCardProps> = ({
    id,
    text,
    x,
    y,
    fontSize,
    color,
    rotation,
    fontFamily,
    backgroundColor,
    containerScale,
    isSelected,
    onSelect,
    onChange,
    onColorChange
}) => {
    const [isDragging, setIsDragging] = useState(false);
    const [isResizing, setIsResizing] = useState(false);
    const [isRotating, setIsRotating] = useState(false);

    const [dragStart, setDragStart] = useState({ x: 0, y: 0 });
    const [initialAttrs, setInitialAttrs] = useState({ x, y, fontSize, rotation });
    const [centerPos, setCenterPos] = useState({ x: 0, y: 0 }); // For rotation

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
        e.preventDefault();
        onSelect();

        setIsDragging(true);
        setDragStart({ x: e.clientX, y: e.clientY });
        setInitialAttrs({ x, y, fontSize, rotation });
    };

    const handleResizeStart = (e: React.MouseEvent) => {
        e.stopPropagation();
        e.preventDefault();
        onSelect();

        setIsResizing(true);
        setDragStart({ x: e.clientX, y: e.clientY });
        setInitialAttrs({ x, y, fontSize, rotation });
    };

    const handleRotateStart = (e: React.MouseEvent) => {
        e.stopPropagation();
        e.preventDefault();
        onSelect();

        // Calculate center for atan2
        if (cardRef.current) {
            const rect = cardRef.current.getBoundingClientRect();
            setCenterPos({
                x: rect.left + rect.width / 2,
                y: rect.top + rect.height / 2
            });
            const startAngle = Math.atan2(e.clientY - (rect.top + rect.height / 2), e.clientX - (rect.left + rect.width / 2));

            setIsRotating(true);
            setDragStart({ x: startAngle, y: 0 }); // Store angle in x
            setInitialAttrs({ x, y, fontSize, rotation });
        }
    };

    // Global Listeners
    useEffect(() => {
        if (!isDragging && !isResizing && !isRotating) return;

        const handleMove = (e: MouseEvent) => {
            if (isDragging) {
                const dx = (e.clientX - dragStart.x) / containerScale;
                const dy = (e.clientY - dragStart.y) / containerScale;

                onChange({
                    x: Math.round(initialAttrs.x + dx),
                    y: Math.round(initialAttrs.y + dy),
                    fontSize: initialAttrs.fontSize,
                    rotation: initialAttrs.rotation
                });
            } else if (isResizing) {
                const dx = (e.clientX - dragStart.x) / containerScale;
                const dy = (e.clientY - dragStart.y) / containerScale;
                const sensitivity = 0.5;
                const sizeDelta = (dx + dy) * sensitivity;
                const newSize = Math.max(10, initialAttrs.fontSize + sizeDelta);

                onChange({
                    x: initialAttrs.x,
                    y: initialAttrs.y,
                    fontSize: Math.round(newSize),
                    rotation: initialAttrs.rotation
                });
            } else if (isRotating) {
                const currentAngle = Math.atan2(e.clientY - centerPos.y, e.clientX - centerPos.x);
                const startAngle = dragStart.x;
                const angleDiff = currentAngle - startAngle;
                const degDiff = angleDiff * (180 / Math.PI);

                const newRotation = (initialAttrs.rotation + degDiff) % 360;

                onChange({
                    x: initialAttrs.x,
                    y: initialAttrs.y,
                    fontSize: initialAttrs.fontSize,
                    rotation: Math.round(newRotation)
                });
            }
        };

        const handleUp = () => {
            setIsDragging(false);
            setIsResizing(false);
            setIsRotating(false);
        };

        window.addEventListener('mousemove', handleMove);
        window.addEventListener('mouseup', handleUp);

        return () => {
            window.removeEventListener('mousemove', handleMove);
            window.removeEventListener('mouseup', handleUp);
        };
    }, [isDragging, isResizing, isRotating, dragStart, initialAttrs, centerPos, containerScale, onChange]);

    return (
        <div
            ref={cardRef}
            id={id}
            className={`absolute group select-none ${isSelected ? 'z-50' : 'z-30'}`}
            style={{
                left: displayX,
                top: displayY,
                // Apply rotation to the wrapper or content?
                // Applying to wrapper affects drag axis interpretation usually.
                // Standard: Transform wrapper.
                transform: `rotate(${rotation}deg)`,
                cursor: isDragging ? 'grabbing' : 'grab',
            }}
            onMouseDown={handleMouseDown}
            onClick={(e) => e.stopPropagation()}
        >
            <div
                className={`relative px-2 py-1 transition-colors duration-200 
                           ${isSelected ? 'ring-2 ring-accent-mint ring-offset-2 ring-offset-[#0f111a]' : 'hover:bg-white/5 border border-transparent hover:border-white/10 rounded-lg'}
                           ${backgroundColor ? 'rounded-md shadow-lg' : ''}`}
                style={{
                    backgroundColor: backgroundColor || 'transparent',
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

                {/* Overlays */}
                {isSelected && (
                    <>
                        {/* Size Indicator */}
                        <div className="absolute -top-5 -left-3 px-1 py-0.5 bg-accent-mint text-[10px] text-black font-bold rounded shadow-md pointer-events-none whitespace-nowrap">
                            {Math.round(fontSize)}px
                        </div>

                        {/* Resize Handle (Bottom Right) */}
                        <div
                            className="absolute -bottom-3 -right-3 w-10 h-10 flex items-center justify-center cursor-nwse-resize z-50 group/handle"
                            onMouseDown={handleResizeStart}
                        >
                            <div className="w-4 h-4 bg-white border-2 border-accent-mint rounded-full shadow-sm group-hover/handle:scale-125 transition-transform" />
                        </div>

                        {/* Rotate Handle (Bottom Left) */}
                        <div
                            className="absolute -bottom-3 -left-3 w-10 h-10 flex items-center justify-center cursor-ew-resize z-50 group/rotate"
                            onMouseDown={handleRotateStart}
                            title="Rotate"
                        >
                            <div className="w-4 h-4 bg-accent-yellow border-2 border-white rounded-full shadow-sm group-hover/rotate:scale-125 transition-transform flex items-center justify-center">
                                {/* Optional: Icon inside */}
                            </div>
                        </div>

                        {/* Color Picker (Top Right) */}
                        <div className="absolute -top-16 -right-2 z-50 pointer-events-auto" onMouseDown={(e) => e.stopPropagation()}>
                            <ColorPickerToolbar
                                color={color}
                                onChange={onColorChange}
                                position={{ x: 0, y: 0 }}
                            />
                        </div>
                    </>
                )}
            </div>
        </div>
    );
};
