import { useState, useEffect } from 'react';
import { motion, AnimatePresence } from 'motion/react';
import { Card } from './ui/card';
import { Badge } from './ui/badge';
import { Button } from './ui/button';
import { X, FileText, User, Calendar, Clock, Loader2, TrendingUp, Target, MessageSquare, Lightbulb, Download, FileDown } from 'lucide-react';
import { PDFScroll } from './PDF-Scroll';
import { getReport, getReportFileUrl, generateIndividualReport, getIndividualReportUrl } from '../services/api';

// Customer Report Row Component
function CustomerReportRow({ userId }: { userId: string }) {
  const [generating, setGenerating] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const handleGenerateReport = async () => {
    setGenerating(true);
    setError(null);

    try {
      const result = await generateIndividualReport(userId);

      // Download the file automatically
      const downloadUrl = getIndividualReportUrl(result.filename);
      const link = document.createElement('a');
      link.href = downloadUrl;
      link.download = result.filename;
      document.body.appendChild(link);
      link.click();
      document.body.removeChild(link);

    } catch (err: any) {
      console.error('Failed to generate report:', err);
      setError(err.message || 'Failed to generate report');
    } finally {
      setGenerating(false);
    }
  };

  return (
    <Card className="p-3 bg-accent/30 hover:bg-accent/50 transition-colors">
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-3 flex-1">
          <Badge variant="outline" className="text-sm font-mono">
            {userId}
          </Badge>
          {error && (
            <span className="text-xs text-destructive">{error}</span>
          )}
        </div>

        <Button
          size="sm"
          variant="outline"
          onClick={handleGenerateReport}
          disabled={generating}
          className="gap-2"
        >
          {generating ? (
            <>
              <Loader2 className="w-4 h-4 animate-spin" />
              Generating...
            </>
          ) : (
            <>
              <FileDown className="w-4 h-4" />
              Generate Report
            </>
          )}
        </Button>
      </div>
    </Card>
  );
}

interface Report {
  id: string;
  batchId: string;
  category: string;
  userIds: string[];
  timestamp: Date;
  totalCalls: number;
  successfulCalls: number;
  reportFile?: string | null;
}

interface ReportModalProps {
  report: Report | null;
  onClose: () => void;
}

interface ClusterReportData {
  cluster_id: number;
  cluster_summary: string;
  avg_confidence: number;
  confidence_min: number;
  confidence_max: number;
  confidence_median: number;
  admin_summary: string;
  insights: {
    prediction_factors: string[];
    behavior_patterns: string[];
    exemplar_insights: string[];
    recommendations: string[];
  };
  userIds: string[];
}

export function ReportModal({ report, onClose }: ReportModalProps) {
  const [clusterData, setClusterData] = useState<ClusterReportData | null>(null);
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    if (report) {
      const fetchClusterData = async () => {
        setLoading(true);
        try {
          const data = await getReport(report.id);
          setClusterData(data as any);
        } catch (err) {
          console.error('Failed to fetch cluster data:', err);
        } finally {
          setLoading(false);
        }
      };
      fetchClusterData();
    }
  }, [report]);

  if (!report) return null;

  const pdfUrl = report.reportFile
    ? getReportFileUrl(report.reportFile)
    : '/Report_example.pdf';

  const getConfidenceColor = (confidence: number) => {
    if (confidence >= 1) return 'text-green-500';
    if (confidence >= 0) return 'text-yellow-500';
    return 'text-red-500';
  };

  const getConfidenceBadge = (confidence: number) => {
    if (confidence >= 1) return { variant: 'default' as const, text: 'High Confidence' };
    if (confidence >= 0) return { variant: 'secondary' as const, text: 'Medium Confidence' };
    return { variant: 'destructive' as const, text: 'Low Confidence' };
  };

  return (
    <AnimatePresence>
      {report && (
        <motion.div
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          exit={{ opacity: 0 }}
          className="fixed inset-0 bg-black/60 backdrop-blur-sm z-50 flex items-center justify-center p-4"
          onClick={onClose}
        >
          <motion.div
            initial={{ scale: 0.9, opacity: 0, y: 20 }}
            animate={{ scale: 1, opacity: 1, y: 0 }}
            exit={{ scale: 0.9, opacity: 0, y: 20 }}
            transition={{ type: 'spring', stiffness: 300, damping: 30 }}
            onClick={(e) => e.stopPropagation()}
            className="w-full max-w-6xl max-h-[90vh] overflow-auto"
          >
            <Card className="p-8 bg-card">
              {/* Header */}
              <div className="flex items-start justify-between mb-6 pb-6 border-b border-border">
                <div>
                  <h2 className="mb-2">{report.batchId}</h2>
                  <div className="flex items-center gap-4 text-sm text-muted-foreground">
                    <span className="flex items-center gap-1">
                      <Calendar className="w-4 h-4" />
                      {report.timestamp.toLocaleDateString()}
                    </span>
                    <span className="flex items-center gap-1">
                      <Clock className="w-4 h-4" />
                      {report.timestamp.toLocaleTimeString()}
                    </span>
                    {clusterData && (
                      <Badge {...getConfidenceBadge(clusterData.avg_confidence)}>
                        {getConfidenceBadge(clusterData.avg_confidence).text}
                      </Badge>
                    )}
                  </div>
                </div>

                <Button
                  variant="ghost"
                  size="icon"
                  onClick={onClose}
                  className="hover:bg-destructive/10 hover:text-destructive"
                >
                  <X className="w-5 h-5" />
                </Button>
              </div>

              {loading ? (
                <div className="flex items-center justify-center py-20">
                  <Loader2 className="w-12 h-12 animate-spin text-primary" />
                </div>
              ) : clusterData && (
                <>
                  {/* Cluster Summary Card */}
                  <Card className="p-6 mb-6 bg-gradient-to-br from-primary/5 to-primary/10 border-primary/20">
                    <h3 className="mb-3 flex items-center gap-2">
                      <MessageSquare className="w-5 h-5 text-primary" />
                      Cluster Summary
                    </h3>
                    <p className="text-muted-foreground leading-relaxed">
                      {clusterData.cluster_summary}
                    </p>
                  </Card>

                  {/* Confidence Metrics */}
                  <div className="grid grid-cols-1 md:grid-cols-4 gap-4 mb-6">
                    <Card className="p-4 bg-accent/50">
                      <div className="flex items-center gap-3">
                        <User className="w-8 h-8 text-blue-500" />
                        <div>
                          <p className="text-2xl font-bold">{report.userIds.length}</p>
                          <p className="text-xs text-muted-foreground">Total Customers</p>
                        </div>
                      </div>
                    </Card>

                    <Card className="p-4 bg-accent/50">
                      <div className="flex items-center gap-3">
                        <TrendingUp className={`w-8 h-8 ${getConfidenceColor(clusterData.avg_confidence)}`} />
                        <div>
                          <p className={`text-2xl font-bold ${getConfidenceColor(clusterData.avg_confidence)}`}>
                            {clusterData.avg_confidence.toFixed(2)}
                          </p>
                          <p className="text-xs text-muted-foreground">Avg Confidence</p>
                        </div>
                      </div>
                    </Card>

                    <Card className="p-4 bg-accent/50">
                      <div className="flex items-center gap-3">
                        <Target className="w-8 h-8 text-green-500" />
                        <div>
                          <p className="text-2xl font-bold">{clusterData.confidence_max.toFixed(2)}</p>
                          <p className="text-xs text-muted-foreground">Max Confidence</p>
                        </div>
                      </div>
                    </Card>

                    <Card className="p-4 bg-accent/50">
                      <div className="flex items-center gap-3">
                        <Target className="w-8 h-8 text-orange-500" />
                        <div>
                          <p className="text-2xl font-bold">{clusterData.confidence_min.toFixed(2)}</p>
                          <p className="text-xs text-muted-foreground">Min Confidence</p>
                        </div>
                      </div>
                    </Card>
                  </div>

                  {/* PDF Report Viewer */}
                  <div className="mb-6">
                    <div className="flex items-center justify-between mb-4">
                      <h3 className="flex items-center gap-2">
                        <FileText className="w-5 h-5" />
                        Cluster Report PDF
                      </h3>
                      <Button
                        variant="outline"
                        size="sm"
                        className="gap-2"
                        onClick={() => {
                          const link = document.createElement('a');
                          link.href = pdfUrl;
                          link.download = report.reportFile || 'cluster_report.pdf';
                          document.body.appendChild(link);
                          link.click();
                          document.body.removeChild(link);
                        }}
                      >
                        <Download className="w-4 h-4" />
                        Download Cluster Report
                      </Button>
                    </div>
                    <Card className="bg-accent/30 overflow-hidden">
                      <PDFScroll
                        file={pdfUrl}
                        height="40vh"
                        width={700}
                      />
                    </Card>
                  </div>

                  {/* Insights Grid */}
                  <div className="grid grid-cols-1 md:grid-cols-2 gap-6 mb-6">
                    {/* Prediction Factors */}
                    <Card className="p-6">
                      <h3 className="mb-4 flex items-center gap-2">
                        <Target className="w-5 h-5 text-primary" />
                        Prediction Factors
                      </h3>
                      <ul className="space-y-2">
                        {clusterData.insights.prediction_factors.map((factor, idx) => (
                          <motion.li
                            key={idx}
                            initial={{ opacity: 0, x: -10 }}
                            animate={{ opacity: 1, x: 0 }}
                            transition={{ delay: idx * 0.05 }}
                            className="flex items-start gap-2 p-2 bg-blue-500/5 rounded-lg"
                          >
                            <span className="text-blue-500 font-bold mt-0.5">•</span>
                            <span className="text-sm">{factor}</span>
                          </motion.li>
                        ))}
                      </ul>
                    </Card>

                    {/* Behavior Patterns */}
                    <Card className="p-6">
                      <h3 className="mb-4 flex items-center gap-2">
                        <TrendingUp className="w-5 h-5 text-primary" />
                        Customer Behavior Patterns
                      </h3>
                      <ul className="space-y-2">
                        {clusterData.insights.behavior_patterns.map((pattern, idx) => (
                          <motion.li
                            key={idx}
                            initial={{ opacity: 0, x: -10 }}
                            animate={{ opacity: 1, x: 0 }}
                            transition={{ delay: idx * 0.05 }}
                            className="flex items-start gap-2 p-2 bg-purple-500/5 rounded-lg"
                          >
                            <span className="text-purple-500 font-bold mt-0.5">•</span>
                            <span className="text-sm">{pattern}</span>
                          </motion.li>
                        ))}
                      </ul>
                    </Card>

                    {/* Exemplar Insights */}
                    <Card className="p-6">
                      <h3 className="mb-4 flex items-center gap-2">
                        <MessageSquare className="w-5 h-5 text-primary" />
                        Key Customer Insights
                      </h3>
                      <ul className="space-y-2">
                        {clusterData.insights.exemplar_insights.map((insight, idx) => (
                          <motion.li
                            key={idx}
                            initial={{ opacity: 0, x: -10 }}
                            animate={{ opacity: 1, x: 0 }}
                            transition={{ delay: idx * 0.05 }}
                            className="flex items-start gap-2 p-2 bg-green-500/5 rounded-lg"
                          >
                            <span className="text-green-500 font-bold mt-0.5">💡</span>
                            <span className="text-sm">{insight}</span>
                          </motion.li>
                        ))}
                      </ul>
                    </Card>

                    {/* Recommendations */}
                    <Card className="p-6">
                      <h3 className="mb-4 flex items-center gap-2">
                        <Lightbulb className="w-5 h-5 text-primary" />
                        Recommendations
                      </h3>
                      <ul className="space-y-2">
                        {clusterData.insights.recommendations.map((recommendation, idx) => (
                          <motion.li
                            key={idx}
                            initial={{ opacity: 0, x: -10 }}
                            animate={{ opacity: 1, x: 0 }}
                            transition={{ delay: idx * 0.05 }}
                            className="flex items-start gap-2 p-2 bg-orange-500/5 rounded-lg"
                          >
                            <span className="text-orange-500 font-bold mt-0.5">→</span>
                            <span className="text-sm">{recommendation}</span>
                          </motion.li>
                        ))}
                      </ul>
                    </Card>
                  </div>

                  {/* Customer List with Generate Report Buttons */}
                  <Card className="p-6 mb-6">
                    <h3 className="mb-4 flex items-center gap-2">
                      <User className="w-5 h-5 text-primary" />
                      Cluster Customers ({clusterData.userIds.length})
                    </h3>
                    <div className="space-y-2">
                      {clusterData.userIds.map((userId, idx) => (
                        <CustomerReportRow
                          key={idx}
                          userId={userId}
                        />
                      ))}
                    </div>
                  </Card>

                  {/* Admin Summary */}
                  <Card className="p-6 mb-6 bg-gradient-to-br from-amber-500/5 to-orange-500/10 border-amber-500/20">
                    <h3 className="mb-3 flex items-center gap-2">
                      <Lightbulb className="w-5 h-5 text-amber-500" />
                      Executive Summary
                    </h3>
                    <p className="text-muted-foreground leading-relaxed">
                      {clusterData.admin_summary}
                    </p>
                  </Card>
                </>
              )}

              {/* Footer Actions */}
              <div className="flex items-center justify-end gap-4 pt-6 border-t border-border">
                <Button onClick={onClose}>
                  Close
                </Button>
              </div>
            </Card>
          </motion.div>
        </motion.div>
      )}
    </AnimatePresence>
  );
}
