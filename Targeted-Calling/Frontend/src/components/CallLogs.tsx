import { useState, useEffect } from 'react';
import { motion, AnimatePresence } from 'motion/react';
import { Card } from './ui/card';
import { Input } from './ui/input';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from './ui/select';
import { CallLogCard } from './CallLogCard';
import { CallLogModal } from './CallLogModal';
import { Search, TrendingUp, Wallet, LineChart, MoreHorizontal, Loader2, Phone } from 'lucide-react';
import { getCallLogs, CallLog as ApiCallLog } from '../services/api';

type ProductType = 'car loan' | 'mutual funds' | 'nifty' | 'others' | 'all';

interface CallLog extends ApiCallLog { }

export function CallLogs() {
    const [selectedProduct, setSelectedProduct] = useState<ProductType>('all');
    const [searchQuery, setSearchQuery] = useState('');
    const [timeFilter, setTimeFilter] = useState('all');
    const [selectedCallLog, setSelectedCallLog] = useState<CallLog | null>(null);
    const [callLogs, setCallLogs] = useState<CallLog[]>([]);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState<string | null>(null);

    const productTypes = [
        { id: 'all' as ProductType, label: 'All Products', icon: <Phone className="w-4 h-4" /> },
        { id: 'car loan' as ProductType, label: 'Car Loans', icon: <TrendingUp className="w-4 h-4" /> },
        { id: 'mutual funds' as ProductType, label: 'Mutual Funds', icon: <Wallet className="w-4 h-4" /> },
        { id: 'nifty' as ProductType, label: 'Nifty', icon: <LineChart className="w-4 h-4" /> },
        { id: 'others' as ProductType, label: 'Others', icon: <MoreHorizontal className="w-4 h-4" /> },
    ];

    // Fetch call logs when product type changes and poll every 5 seconds
    useEffect(() => {
        const fetchCallLogs = async () => {
            // Don't show loading spinner for polling updates (only for initial load)
            if (callLogs.length === 0) {
                setLoading(true);
            }
            setError(null);
            try {
                const productParam = selectedProduct === 'all' ? undefined : selectedProduct;
                const data = await getCallLogs(productParam);

                // Update call logs smoothly - only if there are actual changes
                setCallLogs(prevLogs => {
                    if (JSON.stringify(prevLogs) !== JSON.stringify(data)) {
                        console.log('📞 Call logs updated:', data.length, 'calls');
                        return data;
                    }
                    return prevLogs;
                });
            } catch (err) {
                console.error('Failed to fetch call logs:', err);
                // Only show error on initial load, not during polling
                if (callLogs.length === 0) {
                    setError('Failed to load call logs. Make sure the backend is running.');
                }
            } finally {
                setLoading(false);
            }
        };

        // Initial fetch
        fetchCallLogs();

        // Set up polling every 5 seconds
        const pollInterval = setInterval(() => {
            console.log('🔄 Polling for call log updates...');
            fetchCallLogs();
        }, 5000);

        // Cleanup interval on unmount or product change
        return () => {
            console.log('🛑 Stopping call log polling');
            clearInterval(pollInterval);
        };
    }, [selectedProduct, callLogs.length]);

    const filteredCallLogs = callLogs.filter(callLog => {
        // Search filter
        const matchesSearch = searchQuery === '' ||
            callLog.customer_name.toLowerCase().includes(searchQuery.toLowerCase()) ||
            callLog.customer_id.toLowerCase().includes(searchQuery.toLowerCase()) ||
            callLog.call_id.toLowerCase().includes(searchQuery.toLowerCase());

        // Time filter
        const now = Date.now();
        const callTime = new Date(callLog.timestamp).getTime();
        let matchesTime = true;

        if (timeFilter === '1hour') {
            matchesTime = now - callTime <= 60 * 60 * 1000;
        } else if (timeFilter === '1day') {
            matchesTime = now - callTime <= 24 * 60 * 60 * 1000;
        } else if (timeFilter === '3days') {
            matchesTime = now - callTime <= 3 * 24 * 60 * 60 * 1000;
        } else if (timeFilter === '7days') {
            matchesTime = now - callTime <= 7 * 24 * 60 * 60 * 1000;
        }

        return matchesSearch && matchesTime;
    });

    return (
        <div className="min-h-screen p-8 overflow-auto">
            <motion.div
                initial={{ opacity: 0 }}
                animate={{ opacity: 1 }}
                transition={{ duration: 0.5 }}
            >
                <div className="max-w-7xl mx-auto">
                    {/* Header */}
                    <motion.div
                        initial={{ opacity: 0, y: -20 }}
                        animate={{ opacity: 1, y: 0 }}
                        transition={{ duration: 0.5 }}
                        className="mb-8"
                    >
                        <div className="flex items-start justify-between">
                            <div>
                                <h1 className="mb-2">AI Call Logs</h1>
                                <p className="text-muted-foreground">
                                    AI-powered call analytics with detailed customer insights and conversation transcripts
                                </p>
                            </div>

                            {/* Stats Card */}
                            <div className="flex items-center gap-2 px-4 py-2 rounded-lg border bg-card">
                                <Phone className="w-4 h-4 text-primary" />
                                <div className="flex flex-col">
                                    <span className="text-xs font-medium">Total Calls</span>
                                    <span className="text-lg font-bold">{callLogs.length}</span>
                                </div>
                            </div>
                        </div>
                    </motion.div>

                    {/* Floating Product Type Navbar */}
                    <motion.div
                        initial={{ opacity: 0, y: -10 }}
                        animate={{ opacity: 1, y: 0 }}
                        transition={{ delay: 0.1, duration: 0.5 }}
                        className="sticky top-0 z-10 mb-8"
                    >
                        <Card className="p-2 bg-card/95 backdrop-blur-lg shadow-lg border-2">
                            <div className="flex items-center gap-2 relative">
                                {productTypes.map((product) => (
                                    <motion.button
                                        key={product.id}
                                        onClick={() => setSelectedProduct(product.id)}
                                        className={`
                      flex-1 px-6 py-3 rounded-lg transition-all duration-300 relative
                      ${selectedProduct === product.id
                                                ? 'text-primary-foreground'
                                                : 'text-foreground hover:bg-accent'
                                            }
                    `}
                                        whileHover={{ scale: 1.02 }}
                                        whileTap={{ scale: 0.98 }}
                                    >
                                        {selectedProduct === product.id && (
                                            <motion.div
                                                layoutId="activeProduct"
                                                className="absolute inset-0 bg-primary rounded-lg shadow-lg"
                                                transition={{ type: 'spring', stiffness: 300, damping: 30 }}
                                            />
                                        )}
                                        <span className="relative z-10 flex items-center justify-center gap-2">
                                            <span>{product.icon}</span>
                                            <span>{product.label}</span>
                                        </span>
                                    </motion.button>
                                ))}
                            </div>
                        </Card>
                    </motion.div>

                    {/* Filters */}
                    <motion.div
                        initial={{ opacity: 0, y: 20 }}
                        animate={{ opacity: 1, y: 0 }}
                        transition={{ delay: 0.2, duration: 0.5 }}
                        className="mb-6"
                    >
                        <Card className="p-6">
                            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                                <div className="relative">
                                    <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-muted-foreground" />
                                    <Input
                                        placeholder="Search by Customer Name, ID, or Call ID..."
                                        value={searchQuery}
                                        onChange={(e) => setSearchQuery(e.target.value)}
                                        className="pl-10"
                                    />
                                </div>

                                <Select value={timeFilter} onValueChange={setTimeFilter}>
                                    <SelectTrigger>
                                        <SelectValue placeholder="Filter by time" />
                                    </SelectTrigger>
                                    <SelectContent>
                                        <SelectItem value="all">All Time</SelectItem>
                                        <SelectItem value="1hour">Last 1 Hour</SelectItem>
                                        <SelectItem value="1day">Last 1 Day</SelectItem>
                                        <SelectItem value="3days">Last 3 Days</SelectItem>
                                        <SelectItem value="7days">Last 7 Days</SelectItem>
                                    </SelectContent>
                                </Select>
                            </div>
                        </Card>
                    </motion.div>

                    {/* Loading State */}
                    {loading && (
                        <div className="flex items-center justify-center py-20">
                            <div className="text-center">
                                <Loader2 className="w-12 h-12 animate-spin text-primary mx-auto mb-4" />
                                <p className="text-muted-foreground">Loading call logs...</p>
                            </div>
                        </div>
                    )}

                    {/* Error State */}
                    {error && !loading && (
                        <div className="text-center py-12">
                            <p className="text-destructive mb-2">{error}</p>
                            <p className="text-sm text-muted-foreground">
                                Run <code className="bg-accent px-2 py-1 rounded">python app.py</code> in the Backend folder
                            </p>
                        </div>
                    )}

                    {/* Call Logs Grid */}
                    {!loading && !error && (
                        <motion.div
                            initial={{ opacity: 0 }}
                            animate={{ opacity: 1 }}
                            transition={{ delay: 0.3, duration: 0.5 }}
                        >
                            <AnimatePresence mode="wait">
                                <motion.div
                                    key={selectedProduct}
                                    initial={{ opacity: 0, x: 20 }}
                                    animate={{ opacity: 1, x: 0 }}
                                    exit={{ opacity: 0, x: -20 }}
                                    transition={{ duration: 0.3 }}
                                    className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6"
                                >
                                    {filteredCallLogs.map((callLog, index) => (
                                        <motion.div
                                            key={callLog.call_id}
                                            initial={{ opacity: 0, y: 20 }}
                                            animate={{ opacity: 1, y: 0 }}
                                            transition={{ delay: index * 0.05, duration: 0.3 }}
                                        >
                                            <CallLogCard
                                                callLog={callLog}
                                                onOpen={() => setSelectedCallLog(callLog)}
                                            />
                                        </motion.div>
                                    ))}
                                </motion.div>
                            </AnimatePresence>

                            {filteredCallLogs.length === 0 && (
                                <motion.div
                                    initial={{ opacity: 0 }}
                                    animate={{ opacity: 1 }}
                                    className="text-center py-12"
                                >
                                    <p className="text-muted-foreground">No call logs found matching your filters</p>
                                </motion.div>
                            )}
                        </motion.div>
                    )}
                </div>
            </motion.div>
            <div className='border-red-500 border-2'>
                {/* Call Log Modal */}
                <CallLogModal
                    callLog={selectedCallLog}
                    onClose={() => setSelectedCallLog(null)}
                />
            </div>
        </div>
    );
}
