import { motion } from 'motion/react';
import { Card } from './ui/card';
import { Badge } from './ui/badge';
import { Phone, User, Clock, TrendingUp, FileText } from 'lucide-react';

interface CallLog {
    call_id: string;
    customer_id: string;
    customer_name: string;
    product_type: string;
    timestamp: string;
    call_duration: number;
    user_response: string;
    willingness_score: number;
    call_outcome: string;
}

interface CallLogCardProps {
    callLog: CallLog;
    onOpen: () => void;
}

export function CallLogCard({ callLog, onOpen }: CallLogCardProps) {
    const timeAgo = getTimeAgo(new Date(callLog.timestamp));
    const durationMinutes = Math.floor(callLog.call_duration / 60);

    const getResponseColor = (response: string) => {
        switch (response.toUpperCase()) {
            case 'HIGH':
                return 'default';
            case 'MEDIUM':
                return 'secondary';
            case 'LOW':
                return 'destructive';
            default:
                return 'outline';
        }
    };

    const getProductIcon = (product: string) => {
        const productLower = product.toLowerCase();
        if (productLower.includes('car')) return '';
        if (productLower.includes('mutual') || productLower.includes('fund')) return '';
        if (productLower.includes('nifty')) return '';
        return '💼';
    };

    return (
        <motion.div
            whileHover={{ scale: 1.02, y: -5 }}
            whileTap={{ scale: 0.98 }}
            transition={{ type: 'spring', stiffness: 300, damping: 20 }}
        >
            <Card
                className="p-6 cursor-pointer hover:shadow-2xl transition-all duration-300 border-l-4 border-l-primary bg-card group"
                onClick={onOpen}
            >
                {/* Header */}
                <div className="flex items-start justify-between mb-4">
                    <div className="flex items-center gap-3">
                        <div className="w-10 h-10 rounded-lg bg-primary/10 flex items-center justify-center group-hover:bg-primary/20 transition-colors">
                            <Phone className="w-5 h-5 text-primary" />
                        </div>
                        <div>
                            <h4 className="text-sm flex items-center gap-2">
                                <span>{getProductIcon(callLog.product_type)}</span>
                                <span className="capitalize">{callLog.product_type}</span>
                            </h4>
                            <p className="text-xs text-muted-foreground flex items-center gap-1">
                                <Clock className="w-3 h-3" />
                                {timeAgo}
                            </p>
                        </div>
                    </div>

                    <Badge
                        variant={getResponseColor(callLog.user_response)}
                        className="text-xs"
                    >
                        {callLog.user_response} Interest
                    </Badge>
                </div>

                {/* Customer Info */}
                <div className="mb-4 pb-4 border-b border-border">
                    <p className="text-xs text-muted-foreground mb-1 flex items-center gap-1">
                        <User className="w-3 h-3" />
                        Customer Details
                    </p>
                    <p className="text-sm font-medium">{callLog.customer_name}</p>
                    <p className="text-xs text-muted-foreground">ID: {callLog.customer_id}</p>
                </div>

                {/* Stats */}
                <div className="grid grid-cols-2 gap-4 mb-4">
                    <div>
                        <p className="text-xs text-muted-foreground mb-1">Call Duration</p>
                        <p className="text-lg">{durationMinutes} min</p>
                    </div>
                    <div>
                        <p className="text-xs text-muted-foreground mb-1">Willingness</p>
                        <p className="text-lg flex items-center gap-1">
                            {callLog.willingness_score}%
                            <TrendingUp className="w-4 h-4 text-green-500" />
                        </p>
                    </div>
                </div>

                {/* Outcome */}
                <div className="mb-2">
                    <Badge variant="outline" className="text-xs">
                        <FileText className="w-3 h-3 mr-1" />
                        {callLog.call_outcome.replace(/_/g, ' ')}
                    </Badge>
                </div>

                {/* Hover hint */}
                <motion.div
                    initial={{ opacity: 0 }}
                    whileHover={{ opacity: 1 }}
                    className="mt-4 pt-4 border-t border-border text-center"
                >
                    <p className="text-xs text-primary">Click to view call details & transcript</p>
                </motion.div>
            </Card>
        </motion.div>
    );
}

function getTimeAgo(date: Date): string {
    const seconds = Math.floor((Date.now() - date.getTime()) / 1000);

    const intervals = {
        year: 31536000,
        month: 2592000,
        week: 604800,
        day: 86400,
        hour: 3600,
        minute: 60,
    };

    for (const [unit, secondsInUnit] of Object.entries(intervals)) {
        const interval = Math.floor(seconds / secondsInUnit);
        if (interval >= 1) {
            return `${interval} ${unit}${interval > 1 ? 's' : ''} ago`;
        }
    }

    return 'Just now';
}
