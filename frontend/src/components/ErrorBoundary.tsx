import { Component, type ErrorInfo, type ReactNode } from 'react';
import { AlertTriangle, RefreshCw } from 'lucide-react';

interface Props {
    children: ReactNode;
    name: string;
}

interface State {
    hasError: boolean;
    error: Error | null;
    errorInfo: ErrorInfo | null;
}

export class ErrorBoundary extends Component<Props, State> {
    public state: State = {
        hasError: false,
        error: null,
        errorInfo: null
    };

    public static getDerivedStateFromError(error: Error): State {
        return { hasError: true, error, errorInfo: null };
    }

    public componentDidCatch(error: Error, errorInfo: ErrorInfo) {
        console.error(`🔴 [ErrorBoundary: ${this.props.name}] Error caught:`, error, errorInfo);
        this.setState({ errorInfo });
    }

    private handleReset = () => {
        this.setState({ hasError: false, error: null, errorInfo: null });
        window.location.reload();
    };

    public render() {
        if (this.state.hasError) {
            return (
                <div className="flex flex-col items-center justify-center p-12 bg-red-500/5 rounded-3xl border-2 border-dashed border-red-500/20 m-4 text-center">
                    <div className="bg-red-500/10 p-4 rounded-full mb-6">
                        <AlertTriangle className="w-12 h-12 text-red-500" />
                    </div>
                    <h2 className="text-2xl font-bold text-white mb-2">Something went wrong in {this.props.name}</h2>
                    <p className="text-red-400/80 mb-6 max-w-md font-mono text-sm overflow-hidden text-ellipsis">
                        {this.state.error?.message || "Unknown error occurred"}
                    </p>
                    <div className="bg-black/40 p-4 rounded-xl mb-8 text-left text-xs font-mono text-gray-400 w-full max-w-2xl overflow-auto max-h-48 custom-scrollbar border border-white/5">
                        <p className="text-red-300 mb-2 font-bold uppercase tracking-widest text-[10px]">Stack Trace:</p>
                        {this.state.error?.stack}
                    </div>
                    <button
                        onClick={this.handleReset}
                        className="flex items-center space-x-2 bg-red-500 hover:bg-red-600 text-white px-8 py-3 rounded-xl font-bold transition-all shadow-lg shadow-red-500/20"
                    >
                        <RefreshCw className="w-5 h-5" />
                        <span>Reload Application</span>
                    </button>
                </div>
            );
        }

        return this.props.children;
    }
}
