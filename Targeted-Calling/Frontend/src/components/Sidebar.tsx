import { useState } from 'react';
import { useLocation, Link } from 'react-router-dom';
import { Home, FileText, BarChart3, LogOut, Moon, Sun, Phone, Shield } from 'lucide-react';
import { motion } from 'motion/react';
import { Button } from './ui/button';

interface SidebarProps {
    isDark: boolean;
    toggleTheme: () => void;
}

interface MenuItem {
    path: string;
    label: string;
    icon: typeof Home;
}

export function Sidebar({ isDark, toggleTheme }: SidebarProps) {
    const [isExpanded, setIsExpanded] = useState(false);
    const location = useLocation();

    const menuItems: MenuItem[] = [
        { path: '/', label: 'Home', icon: Home },
        { path: '/reports', label: 'Reports', icon: FileText },
        { path: '/call-logs', label: 'AI Call Logs', icon: Phone },
        { path: '/fraud-detection', label: 'Fraud Detection', icon: Shield }
    ];

    const isActive = (path: string) => {
        if (path === '/') {
            return location.pathname === '/';
        }
        return location.pathname.startsWith(path);
    };

    return (
        <motion.div
            className="relative h-screen bg-sidebar border-r border-sidebar-border flex flex-col"
            initial={{ width: 80 }}
            animate={{ width: isExpanded ? 280 : 80 }}
            transition={{ duration: 0.3, ease: 'easeInOut' }}
            onMouseEnter={() => setIsExpanded(true)}
            onMouseLeave={() => setIsExpanded(false)}
        >
            {/* Employee Info */}
            <div className="p-6 border-b border-sidebar-border">
                <motion.div
                    className="flex items-center gap-3"
                    initial={{ opacity: 0 }}
                    animate={{ opacity: isExpanded ? 1 : 0 }}
                    transition={{ duration: 0.2 }}
                >
                    <div className="w-10 h-10 rounded-full bg-primary flex items-center justify-center text-primary-foreground">
                        <span className="text-sm">AB</span>
                    </div>
                    {isExpanded && (
                        <div className="overflow-hidden">
                            <p className="text-sm text-sidebar-foreground whitespace-nowrap">Employee</p>
                            <p className="text-xs text-muted-foreground whitespace-nowrap">Bank Agent</p>
                        </div>
                    )}
                </motion.div>
                {!isExpanded && (
                    <div className="flex justify-center mt-2">
                        <div className="w-10 h-10 rounded-full bg-primary flex items-center justify-center text-primary-foreground">
                            <span className="text-sm">AB</span>
                        </div>
                    </div>
                )}
            </div>

            {/* Navigation Menu */}
            <nav className="flex-1 p-4">
                <ul className="space-y-2">
                    {menuItems.map((item) => {
                        const Icon = item.icon;
                        const active = isActive(item.path);

                        return (
                            <li key={item.path}>
                                <Link
                                    to={item.path}
                                    className={`
                    w-full flex items-center gap-3 px-4 py-3 rounded-lg transition-all duration-200
                    ${active
                                            ? 'bg-primary text-primary-foreground shadow-lg shadow-primary/20'
                                            : 'text-sidebar-foreground hover:bg-sidebar-accent hover:text-sidebar-accent-foreground'
                                        }
                  `}
                                >
                                    <Icon className="w-5 h-5 flex-shrink-0" />
                                    {isExpanded && (
                                        <motion.span
                                            initial={{ opacity: 0, x: -10 }}
                                            animate={{ opacity: 1, x: 0 }}
                                            transition={{ duration: 0.2 }}
                                            className="whitespace-nowrap"
                                        >
                                            {item.label}
                                        </motion.span>
                                    )}
                                </Link>
                            </li>
                        );
                    })}
                </ul>
            </nav>

            {/* Theme Toggle and Logout */}
            <div className="p-4 border-t border-sidebar-border space-y-2">
                <button
                    onClick={toggleTheme}
                    className="w-full flex items-center gap-3 px-4 py-3 rounded-lg text-sidebar-foreground hover:bg-sidebar-accent hover:text-sidebar-accent-foreground transition-all duration-200"
                >
                    {isDark ? <Sun className="w-5 h-5 flex-shrink-0" /> : <Moon className="w-5 h-5 flex-shrink-0" />}
                    {isExpanded && (
                        <motion.span
                            initial={{ opacity: 0, x: -10 }}
                            animate={{ opacity: 1, x: 0 }}
                            transition={{ duration: 0.2 }}
                            className="whitespace-nowrap"
                        >
                            {isDark ? 'Light Mode' : 'Dark Mode'}
                        </motion.span>
                    )}
                </button>

                <Button
                    variant="destructive"
                    className="w-full flex items-center gap-3 justify-start px-4 py-3"
                    onClick={() => alert('Logging out...')}
                >
                    <LogOut className="w-5 h-5 flex-shrink-0" />
                    {isExpanded && (
                        <motion.span
                            initial={{ opacity: 0, x: -10 }}
                            animate={{ opacity: 1, x: 0 }}
                            transition={{ duration: 0.2 }}
                            className="whitespace-nowrap"
                        >
                            Logout
                        </motion.span>
                    )}
                </Button>
            </div>
        </motion.div>
    );
}
