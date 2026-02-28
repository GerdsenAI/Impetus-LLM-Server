import { Component, ErrorInfo, ReactNode } from 'react';
import { RefreshCw, Home } from 'lucide-react';

interface Props {
  children: ReactNode;
  fallback?: ReactNode;
}

interface State {
  hasError: boolean;
  error: Error | null;
  errorInfo: ErrorInfo | null;
}

class ErrorBoundary extends Component<Props, State> {
  public state: State = {
    hasError: false,
    error: null,
    errorInfo: null,
  };

  public static getDerivedStateFromError(error: Error): State {
    return { hasError: true, error, errorInfo: null };
  }

  public componentDidCatch(error: Error, errorInfo: ErrorInfo) {
    console.error('Uncaught error:', error, errorInfo);
    this.setState({
      error,
      errorInfo,
    });
  }

  private handleReset = () => {
    this.setState({
      hasError: false,
      error: null,
      errorInfo: null,
    });
    window.location.reload();
  };

  private handleHome = () => {
    this.setState({
      hasError: false,
      error: null,
      errorInfo: null,
    });
    window.location.href = '/';
  };

  public render() {
    if (this.state.hasError) {
      if (this.props.fallback) {
        return this.props.fallback;
      }

      return (
        <div style={{
          height: '100vh',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
          padding: '20px',
          flexDirection: 'column',
          gap: '16px',
        }}>
          <h2 style={{ color: '#ff4d4f' }}>Something went wrong</h2>
          <p>The application encountered an unexpected error.</p>
          {this.state.error && (
            <details style={{ marginTop: '16px', textAlign: 'left', maxWidth: '600px', width: '100%' }}>
              <summary style={{ cursor: 'pointer', marginBottom: '8px' }}>
                Error details
              </summary>
              <pre style={{
                fontSize: '12px',
                background: '#f5f5f5',
                padding: '12px',
                borderRadius: '4px',
                overflow: 'auto',
                maxHeight: '200px'
              }}>
                {this.state.error.toString()}
                {this.state.errorInfo && this.state.errorInfo.componentStack}
              </pre>
            </details>
          )}
          <div style={{ display: 'flex', gap: '8px' }}>
            <button
              onClick={this.handleReset}
              style={{
                display: 'inline-flex', alignItems: 'center', gap: '6px',
                padding: '8px 16px', borderRadius: '6px', border: 'none',
                background: '#1677ff', color: '#fff', cursor: 'pointer',
              }}
            >
              <RefreshCw size={14} /> Reload Page
            </button>
            <button
              onClick={this.handleHome}
              style={{
                display: 'inline-flex', alignItems: 'center', gap: '6px',
                padding: '8px 16px', borderRadius: '6px', border: '1px solid #d9d9d9',
                background: '#fff', cursor: 'pointer',
              }}
            >
              <Home size={14} /> Go Home
            </button>
          </div>
        </div>
      );
    }

    return this.props.children;
  }
}

export default ErrorBoundary;
