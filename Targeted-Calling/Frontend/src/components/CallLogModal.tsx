import { useEffect, useState } from 'react';
import { motion, AnimatePresence } from 'motion/react';
import { X, Phone, User, Clock, TrendingUp, FileText, MessageSquare, HelpCircle, Target, ArrowRight, Loader2 } from 'lucide-react';
import { Button } from './ui/button';
import { Badge } from './ui/badge';
import { Card } from './ui/card';
import { getTranscript } from '../services/api';

interface CallLog {
    call_id: string;
    customer_id: string;
    customer_name: string;
    product_type: string;
    timestamp: string;
    call_duration: number;
    user_response: string;
    willingness_score: number;
    main_points: string[];
    customer_doubts: string[];
    agent_notes: string;
    call_outcome: string;
    next_action: string;
    transcript_file: string;
}

interface CallLogModalProps {
    callLog: CallLog | null;
    onClose: () => void;
}

export function CallLogModal({ callLog, onClose }: CallLogModalProps) {
    const [transcript, setTranscript] = useState<string>('');
    const [loadingTranscript, setLoadingTranscript] = useState(false);
    const [showTranscript, setShowTranscript] = useState(false);

    useEffect(() => {
        if (callLog && showTranscript && !transcript) {
            loadTranscript();
        }
    }, [callLog, showTranscript]);

    const loadTranscript = async () => {
        if (!callLog) return;

        setLoadingTranscript(true);
        try {
            const content = await getTranscript(callLog.transcript_file);
            setTranscript(content);
        } catch (error) {
            console.error('Failed to load transcript:', error);
            setTranscript('Failed to load transcript. Please try again.');
        } finally {
            setLoadingTranscript(false);
        }
    };

    const handleViewTranscript = () => {
        setShowTranscript(!showTranscript);
    };

    if (!callLog) return null;

    const durationMinutes = Math.floor(callLog.call_duration / 60);
    const durationSeconds = callLog.call_duration % 60;

    const getResponseColor = (response: string) => {
        switch (response.toUpperCase()) {
            case 'HIGH':
                return 'bg-green-500/10 text-green-500 border-green-500';
            case 'MEDIUM':
                return 'bg-yellow-500/10 text-yellow-500 border-yellow-500';
            case 'LOW':
                return 'bg-red-500/10 text-red-500 border-red-500';
            default:
                return 'bg-gray-500/10 text-gray-500 border-gray-500';
        }
    };

    const getProductIcon = (product: string) => {
        const productLower = product.toLowerCase();
        if (productLower.includes('car')) return '';
        if (productLower.includes('mutual') || productLower.includes('fund')) return '';
        if (productLower.includes('nifty')) return '*';
        return '';
    };

    return (
        <AnimatePresence>
            <motion.div
                initial={{ opacity: 0 }}
                animate={{ opacity: 1 }}
                exit={{ opacity: 0 }}
                className="fixed inset-0 bg-black/50 backdrop-blur-sm z-50 flex items-center justify-center p-4"
                onClick={onClose}
            >
                <motion.div
                    initial={{ scale: 0.9, opacity: 0 }}
                    animate={{ scale: 1, opacity: 1 }}
                    exit={{ scale: 0.9, opacity: 0 }}
                    transition={{ type: 'spring', stiffness: 300, damping: 30 }}
                    className="bg-background rounded-2xl shadow-2xl max-w-4xl w-full max-h-[90vh] flex flex-col"
                    onClick={(e) => e.stopPropagation()}
                >
                    {/* Header */}
                    <div className="p-6 border-b border-border bg-card/50 flex-shrink-0">
                        <div className="flex items-start justify-between">
                            <div className="flex items-center gap-4">
                                <div className="w-12 h-12 rounded-lg bg-primary/10 flex items-center justify-center">
                                    <Phone className="w-6 h-6 text-primary" />
                                </div>
                                <div>
                                    <h2 className="text-2xl font-bold flex items-center gap-2">
                                        <span>{getProductIcon(callLog.product_type)}</span>
                                        <span className="capitalize">{callLog.product_type}</span>
                                    </h2>
                                    <p className="text-sm text-muted-foreground">Call ID: {callLog.call_id}</p>
                                </div>
                            </div>
                            <Button variant="ghost" size="icon" onClick={onClose}>
                                <X className="w-5 h-5" />
                            </Button>
                        </div>
                    </div>

                    {/* Content - Scrollable */}
                    <div className="p-6 overflow-y-auto flex-1">
                        {/* Customer Info Card */}
                        <Card className="p-6 mb-6 bg-gradient-to-br from-primary/5 to-primary/10 border-primary/20">
                            <div className="flex items-center gap-3 mb-4">
                                <User className="w-5 h-5 text-primary" />
                                <h3 className="text-lg font-semibold">Customer Information</h3>
                            </div>
                            <div className="grid grid-cols-2 gap-4">
                                <div>
                                    <p className="text-sm text-muted-foreground">Name</p>
                                    <p className="text-lg font-medium">{callLog.customer_name}</p>
                                </div>
                                <div>
                                    <p className="text-sm text-muted-foreground">Customer ID</p>
                                    <p className="text-lg font-medium">{callLog.customer_id}</p>
                                </div>
                                <div>
                                    <p className="text-sm text-muted-foreground">Call Date</p>
                                    <p className="text-lg font-medium">
                                        {new Date(callLog.timestamp).toLocaleDateString('en-IN', {
                                            year: 'numeric',
                                            month: 'long',
                                            day: 'numeric',
                                            hour: '2-digit',
                                            minute: '2-digit'
                                        })}
                                    </p>
                                </div>
                                <div>
                                    <p className="text-sm text-muted-foreground">Duration</p>
                                    <p className="text-lg font-medium flex items-center gap-1">
                                        <Clock className="w-4 h-4" />
                                        {durationMinutes}m {durationSeconds}s
                                    </p>
                                </div>
                            </div>
                        </Card>

                        {/* User Response & Willingness */}
                        <div className="grid grid-cols-2 gap-4 mb-6">
                            <Card className="p-6">
                                <div className="flex items-center gap-2 mb-3">
                                    <TrendingUp className="w-5 h-5 text-primary" />
                                    <h3 className="font-semibold">User Response</h3>
                                </div>
                                <div className={`inline-flex items-center px-4 py-2 rounded-lg border-2 ${getResponseColor(callLog.user_response)}`}>
                                    <span className="text-lg font-bold">{callLog.user_response} Interest</span>
                                </div>
                            </Card>

                            <Card className="p-6">
                                <div className="flex items-center gap-2 mb-3">
                                    <Target className="w-5 h-5 text-primary" />
                                    <h3 className="font-semibold">Willingness Score</h3>
                                </div>
                                <div className="flex items-center gap-3">
                                    <div className="flex-1 bg-muted rounded-full h-3 overflow-hidden">
                                        <motion.div
                                            initial={{ width: 0 }}
                                            animate={{ width: `${callLog.willingness_score}%` }}
                                            transition={{ duration: 1, ease: 'easeOut' }}
                                            className={`h-full ${callLog.willingness_score >= 75 ? 'bg-green-500' :
                                                callLog.willingness_score >= 50 ? 'bg-yellow-500' :
                                                    'bg-red-500'
                                                }`}
                                        />
                                    </div>
                                    <span className="text-2xl font-bold">{callLog.willingness_score}%</span>
                                </div>
                            </Card>
                        </div>

                        {/* Main Points */}
                        <Card className="p-6 mb-6">
                            <div className="flex items-center gap-2 mb-4">
                                <MessageSquare className="w-5 h-5 text-primary" />
                                <h3 className="text-lg font-semibold">Main Points Discussed</h3>
                            </div>
                            <ul className="space-y-2">
                                {callLog.main_points.map((point, index) => (
                                    <motion.li
                                        key={index}
                                        initial={{ opacity: 0, x: -20 }}
                                        animate={{ opacity: 1, x: 0 }}
                                        transition={{ delay: index * 0.1 }}
                                        className="flex items-start gap-3 p-3 bg-muted/50 rounded-lg"
                                    >
                                        <span className="text-primary font-bold mt-0.5">•</span>
                                        <span className="flex-1">{point}</span>
                                    </motion.li>
                                ))}
                            </ul>
                        </Card>

                        {/* Customer Doubts */}
                        <Card className="p-6 mb-6">
                            <div className="flex items-center gap-2 mb-4">
                                <HelpCircle className="w-5 h-5 text-primary" />
                                <h3 className="text-lg font-semibold">Customer Doubts & Questions</h3>
                            </div>
                            <ul className="space-y-2">
                                {callLog.customer_doubts.map((doubt, index) => (
                                    <motion.li
                                        key={index}
                                        initial={{ opacity: 0, x: -20 }}
                                        animate={{ opacity: 1, x: 0 }}
                                        transition={{ delay: index * 0.1 }}
                                        className="flex items-start gap-3 p-3 bg-orange-500/5 border border-orange-500/20 rounded-lg"
                                    >
                                        <span className="text-orange-500 font-bold mt-0.5">?</span>
                                        <span className="flex-1">{doubt}</span>
                                    </motion.li>
                                ))}
                            </ul>
                        </Card>

                        {/* Agent Notes & Next Action */}
                        <div className="grid grid-cols-1 md:grid-cols-2 gap-4 mb-6">
                            <Card className="p-6">
                                <div className="flex items-center gap-2 mb-3">
                                    <FileText className="w-5 h-5 text-primary" />
                                    <h3 className="font-semibold">Agent Notes</h3>
                                </div>
                                <p className="text-muted-foreground italic">{callLog.agent_notes}</p>
                            </Card>

                            <Card className="p-6 bg-gradient-to-br from-blue-500/5 to-blue-500/10 border-blue-500/20">
                                <div className="flex items-center gap-2 mb-3">
                                    <ArrowRight className="w-5 h-5 text-blue-500" />
                                    <h3 className="font-semibold">Next Action</h3>
                                </div>
                                <p className="text-blue-600 dark:text-blue-400 font-medium">{callLog.next_action}</p>
                            </Card>
                        </div>

                        {/* Call Outcome */}
                        <Card className="p-6 mb-6">
                            <div className="flex items-center gap-2 mb-3">
                                <Target className="w-5 h-5 text-primary" />
                                <h3 className="font-semibold">Call Outcome</h3>
                            </div>
                            <Badge variant="outline" className="text-sm px-4 py-2">
                                {callLog.call_outcome.replace(/_/g, ' ')}
                            </Badge>
                        </Card>

                        {/* Transcript Section */}
                        <Card className="p-6">
                            <div className="flex items-center justify-between mb-4">
                                <div className="flex items-center gap-2">
                                    <FileText className="w-5 h-5 text-primary" />
                                    <h3 className="text-lg font-semibold">Call Transcript</h3>
                                </div>
                                <Button onClick={handleViewTranscript} variant="outline">
                                    {showTranscript ? 'Hide Transcript' : 'View Transcript'}
                                </Button>
                            </div>

                            <AnimatePresence>
                                {showTranscript && (
                                    <motion.div
                                        initial={{ height: 0, opacity: 0 }}
                                        animate={{ height: 'auto', opacity: 1 }}
                                        exit={{ height: 0, opacity: 0 }}
                                        transition={{ duration: 0.3 }}
                                        className="overflow-hidden"
                                    >
                                        {loadingTranscript ? (
                                            <div className="flex items-center justify-center py-12">
                                                <Loader2 className="w-8 h-8 animate-spin text-primary" />
                                            </div>
                                        ) : (
                                            <div className="bg-muted/50 rounded-lg p-6 mt-4">
                                                <pre className="whitespace-pre-wrap font-mono text-sm leading-relaxed">
                                                    {transcript}
                                                </pre>
                                            </div>
                                        )}
                                    </motion.div>
                                )}
                            </AnimatePresence>
                        </Card>
                    </div>
                </motion.div>
            </motion.div>
        </AnimatePresence>
    );
}
