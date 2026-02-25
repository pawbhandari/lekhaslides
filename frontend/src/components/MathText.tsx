import React, { useEffect, useRef } from 'react';
import 'katex/dist/katex.min.css';
import katex from 'katex';

interface MathTextProps {
    text: string;
    className?: string;
    displayMode?: boolean;
}

export const MathText: React.FC<MathTextProps> = ({ text, className }) => {
    if (!text) return null;

    // Split text by $$...$$ and then by $...$
    const parts = text.split(/(\$\$[\s\S]+?\$\$|\$[\s\S]+?\$)/g);

    return (
        <span className={className}>
            {parts.map((part, index) => {
                if (part.startsWith('$$') && part.endsWith('$$')) {
                    const formula = part.slice(2, -2);
                    return <MathSpan key={index} formula={formula} displayMode={true} />;
                } else if (part.startsWith('$') && part.endsWith('$')) {
                    const formula = part.slice(1, -1);
                    return <MathSpan key={index} formula={formula} displayMode={false} />;
                }
                return <span key={index}>{part}</span>;
            })}
        </span>
    );
};

interface MathSpanProps {
    formula: string;
    displayMode: boolean;
}

const MathSpan: React.FC<MathSpanProps> = ({ formula, displayMode }) => {
    const spanRef = useRef<HTMLSpanElement>(null);

    useEffect(() => {
        if (spanRef.current) {
            try {
                katex.render(formula, spanRef.current, {
                    displayMode,
                    throwOnError: false,
                });
            } catch (err) {
                console.error('KaTeX error:', err);
                spanRef.current.textContent = formula;
            }
        }
    }, [formula, displayMode]);

    return <span ref={spanRef} />;
};
