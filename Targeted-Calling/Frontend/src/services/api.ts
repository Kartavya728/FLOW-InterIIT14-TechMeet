/**
 * API service for communicating with the Python backend.
 */

const API_BASE_URL = 'http://localhost:5001/api';

export interface Category {
    id: string;
    label: string;
    prefix: string;
}

export interface Report {
    id: string;
    batch_id: string;
    category_id: string;
    timestamp: string;
    total_calls: number;
    successful_calls: number;
    report_file: string | null;
    userIds: string[];
    category_label?: string;
    category_prefix?: string;
}

export interface User {
    id: string;
    user_id: string;
    report_id: string;
    name: string;
    agreed: number;
    call_duration: number;
    call_date: string;
    loan_amount: number;
    credit_score: number;
    risk_level: string;
    audio_file: string | null;
}

export interface ReportWithUsers extends Report {
    users: User[];
}

// Health check
export async function checkHealth(): Promise<boolean> {
    try {
        const response = await fetch(`${API_BASE_URL}/health`);
        return response.ok;
    } catch {
        return false;
    }
}

// Get all categories
export async function getCategories(): Promise<Category[]> {
    const response = await fetch(`${API_BASE_URL}/categories`);
    if (!response.ok) throw new Error('Failed to fetch categories');
    return response.json();
}

// Get reports by category
export async function getReports(category?: string): Promise<Report[]> {
    const url = category
        ? `${API_BASE_URL}/reports?category=${category}`
        : `${API_BASE_URL}/reports`;

    const response = await fetch(url);
    if (!response.ok) throw new Error('Failed to fetch reports');
    return response.json();
}

// Get single report with users
export async function getReport(reportId: string): Promise<ReportWithUsers> {
    const response = await fetch(`${API_BASE_URL}/reports/${reportId}`);
    if (!response.ok) throw new Error('Failed to fetch report');
    return response.json();
}

// Get users for a report
export async function getReportUsers(reportId: string): Promise<User[]> {
    const response = await fetch(`${API_BASE_URL}/reports/${reportId}/users`);
    if (!response.ok) throw new Error('Failed to fetch users');
    return response.json();
}

// Get single user
export async function getUser(userId: string): Promise<User> {
    const response = await fetch(`${API_BASE_URL}/users/${userId}`);
    if (!response.ok) throw new Error('Failed to fetch user');
    return response.json();
}

// Get audio file URL
export function getAudioUrl(filename: string): string {
    return `${API_BASE_URL}/audio/${filename}`;
}

// Get report PDF file URL
export function getReportFileUrl(filename: string): string {
    return `${API_BASE_URL}/reports/file/${filename}`;
}

// Get stats
export async function getStats(): Promise<{
    totalReports: number;
    totalUsers: number;
    totalAgreed: number;
    totalDeclined: number;
    categoryStats: Array<{
        id: string;
        label: string;
        report_count: number;
        total_calls: number;
        successful_calls: number;
    }>;
}> {
    const response = await fetch(`${API_BASE_URL}/stats`);
    if (!response.ok) throw new Error('Failed to fetch stats');
    return response.json();
}

// AI Call Logs interfaces and functions
export interface CallLog {
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

export interface CallLogsStats {
    total_calls: number;
    high_interest: number;
    medium_interest: number;
    low_interest: number;
    product_stats: {
        'car loan': number;
        'mutual funds': number;
        'nifty': number;
        'others': number;
    };
}

// Get all call logs, optionally filtered by product type
export async function getCallLogs(productType?: string): Promise<CallLog[]> {
    const url = productType
        ? `${API_BASE_URL}/call-logs?product_type=${productType}`
        : `${API_BASE_URL}/call-logs`;

    const response = await fetch(url);
    if (!response.ok) throw new Error('Failed to fetch call logs');
    return response.json();
}

// Get single call log
export async function getCallLog(callId: string): Promise<CallLog> {
    const response = await fetch(`${API_BASE_URL}/call-logs/${callId}`);
    if (!response.ok) throw new Error('Failed to fetch call log');
    return response.json();
}

// Get transcript content
export async function getTranscript(transcriptFile: string): Promise<string> {
    const response = await fetch(`${API_BASE_URL}/transcripts/${transcriptFile}`);
    if (!response.ok) throw new Error('Failed to fetch transcript');
    const data = await response.json();
    return data.content;
}

// Get call logs statistics
export async function getCallLogsStats(): Promise<CallLogsStats> {
    const response = await fetch(`${API_BASE_URL}/call-logs/stats`);
    if (!response.ok) throw new Error('Failed to fetch call logs stats');
    return response.json();
}

// Individual Report Generation
export async function generateIndividualReport(customerId: string): Promise<{
    success: boolean;
    filename: string;
    customer_id: string;
}> {
    const response = await fetch(`${API_BASE_URL}/generate-individual-report/${customerId}`, {
        method: 'POST'
    });
    if (!response.ok) {
        const error = await response.json();
        throw new Error(error.error || 'Failed to generate report');
    }
    return response.json();
}

// Get individual report file URL
export function getIndividualReportUrl(filename: string): string {
    return `${API_BASE_URL}/individual-reports/${filename}`;
}

