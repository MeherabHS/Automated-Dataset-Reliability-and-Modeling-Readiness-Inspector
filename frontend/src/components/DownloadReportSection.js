import React, { useState } from 'react';
import { Card, CardContent } from './ui/card';
import { Button } from './ui/button';
import { Separator } from './ui/separator';
import { Download, FileText, Loader2 } from 'lucide-react';

const REPORT_SECTIONS = [
  'Dataset Overview',
  'Schema Diagnostics',
  'Missingness Summary',
  'Duplicate Analysis',
  'Numeric Outlier Summary',
  'Class Imbalance Summary',
  'Leakage-Risk Indicators',
  'Modeling Readiness Score',
  'Recommendations',
];

export default function DownloadReportSection({ isComplete, onDownload }) {
  const [downloading, setDownloading] = useState(false);

  const handleClick = async () => {
    if (!isComplete || downloading) return;
    setDownloading(true);
    try {
      await onDownload();
    } finally {
      setDownloading(false);
    }
  };

  return (
    <Card data-testid="download-report-section">
      <CardContent className="p-5">
        <div className="grid grid-cols-1 lg:grid-cols-5 gap-5 items-start">
          {/* Left: description */}
          <div className="lg:col-span-3 space-y-3">
            <div className="flex items-center gap-2">
              <FileText className="w-4 h-4 text-muted-foreground shrink-0" />
              <p className="text-sm font-heading font-semibold text-foreground">
                Download Audit Report
              </p>
            </div>
            <p className="text-xs text-muted-foreground">
              {isComplete
                ? 'Plain-text audit report covering all inspection results and recommendations.'
                : 'Run an audit to enable the report download.'}
            </p>

            {/* Section list */}
            <div className="grid grid-cols-1 sm:grid-cols-2 gap-x-4 gap-y-0.5">
              {REPORT_SECTIONS.map((section, i) => (
                <div key={section} className="flex items-center gap-1.5">
                  <span className={`text-xs font-mono-text ${isComplete ? 'text-primary' : 'text-muted-foreground/40'}`}>
                    {String(i + 1).padStart(2, '0')}
                  </span>
                  <span className={`text-xs ${isComplete ? 'text-foreground' : 'text-muted-foreground/50'}`}>
                    {section}
                  </span>
                </div>
              ))}
            </div>
          </div>

          {/* Right: download button */}
          <div className="lg:col-span-2 flex flex-col items-stretch gap-3">
            <Button
              onClick={handleClick}
              disabled={!isComplete || downloading}
              className="w-full btn-press gap-2"
              data-testid="download-report-button"
            >
              {downloading ? (
                <><Loader2 className="w-4 h-4 animate-spin" /> Generating&hellip;</>
              ) : isComplete ? (
                <><Download className="w-4 h-4" /> Download Report (.txt)</>
              ) : (
                <><Download className="w-4 h-4" /> Report unavailable</>
              )}
            </Button>
            {isComplete && (
              <p className="text-xs text-muted-foreground text-center">
                Plain-text &bull; UTF-8 &bull; Timestamped
              </p>
            )}
          </div>
        </div>
      </CardContent>
    </Card>
  );
}
