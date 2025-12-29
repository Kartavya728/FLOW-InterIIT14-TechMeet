import { useEffect, useState } from 'react';
import { Shield } from 'lucide-react';

export function FraudDetection() {
    const [isLoading, setIsLoading] = useState(true);

    useEffect(() => {
        // Simulate loading
        const timer = setTimeout(() => {
            setIsLoading(false);
        }, 500);

        return () => clearTimeout(timer);
    }, []);

    if (isLoading) {
        return (
            <div className="flex items-center justify-center h-screen bg-background">
                <div className="text-center">
                    <Shield className="w-16 h-16 text-primary animate-pulse mx-auto mb-4" />
                    <p className="text-lg text-muted-foreground">Loading Fraud Detection System...</p>
                </div>
            </div>
        );
    }

    return (
        <div className="h-screen w-full bg-background">
            <iframe
                src="http://localhost:8000"
                className="w-full h-full border-0"
                title="Fraud Detection System"
                style={{ display: 'block' }}
            />
        </div>
    );
}
