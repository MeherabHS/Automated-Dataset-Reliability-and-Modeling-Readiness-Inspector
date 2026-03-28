import React from 'react';
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from './ui/card';
import { Badge } from './ui/badge';
import { Alert, AlertDescription } from './ui/alert';
import { Skeleton } from './ui/skeleton';
import { TableIcon, TriangleAlert } from 'lucide-react';

export default function PreviewSection({
  isLocked,
  isUploading,
  isParsed,
  isAuditing,
  isComplete,
  previewData,
  parseWarnings,
}) {
  const preview = previewData?.preview || [];
  const meta = previewData?.meta || {};
  const columns = preview.length > 0 ? Object.keys(preview[0]) : [];
  const hasData = preview.length > 0;

  // Show skeleton during upload (parse) OR during audit
  const showSkeleton = isUploading || isAuditing;

  return (
    <Card
      data-testid="dataset-preview-section"
      className={isLocked ? 'section-locked' : ''}
    >
      <CardHeader className="pb-3">
        <div className="flex items-start justify-between gap-4">
          <div className="space-y-1">
            <CardTitle className="font-heading text-base font-semibold flex items-center gap-2">
              <TableIcon className="w-4 h-4 text-muted-foreground" />
              Dataset Preview
            </CardTitle>
            <CardDescription className="text-xs">
              {hasData
                ? 'First rows of the uploaded dataset. Verify columns and values before running the audit.'
                : 'Upload a CSV file to preview the first rows here.'}
            </CardDescription>
          </div>
          {hasData && (
            <div className="flex items-center gap-1.5 shrink-0">
              {meta.encoding && meta.encoding !== 'utf-8' && meta.encoding !== 'utf-8-sig' && (
                <Badge variant="secondary" className="text-xs font-mono-text" title="Encoding used for parsing">
                  {meta.encoding}
                </Badge>
              )}
              {meta.delimiter && meta.delimiter !== ',' && (
                <Badge variant="secondary" className="text-xs font-mono-text" title="Delimiter detected">
                  delim: {JSON.stringify(meta.delimiter)}
                </Badge>
              )}
              <Badge variant="secondary" className="text-xs font-mono-text">
                {meta.rows?.toLocaleString()} rows
              </Badge>
              <Badge variant="secondary" className="text-xs font-mono-text">
                {meta.cols} cols
              </Badge>
            </div>
          )}
        </div>
      </CardHeader>

      <CardContent className="p-0">
        {/* Parse warnings banner */}
        {hasData && parseWarnings?.length > 0 && (
          <div className="px-4 py-2 border-b border-[hsl(var(--warning-border))] bg-[hsl(var(--warning-bg))]">
            {parseWarnings.map((w, i) => (
              <div key={i} className="flex items-start gap-2 text-xs text-[hsl(var(--warning-fg))]">
                <TriangleAlert className="w-3.5 h-3.5 mt-0.5 shrink-0" />
                <span>{w}</span>
              </div>
            ))}
          </div>
        )}

        {/* Locked / empty state */}
        {isLocked && (
          <div
            className="flex flex-col items-center justify-center py-14 text-center px-6"
            data-testid="dataset-preview-empty-state"
          >
            <div className="w-12 h-12 rounded-xl border-2 border-dashed border-border flex items-center justify-center mb-4">
              <TableIcon className="w-5 h-5 text-muted-foreground/40" />
            </div>
            <p className="text-sm font-medium text-muted-foreground">No dataset loaded</p>
            <p className="text-xs text-muted-foreground/60 mt-1 max-w-xs">
              Upload a CSV file and click <strong>Upload &amp; Preview</strong> to see the first rows here.
            </p>
          </div>
        )}

        {/* Skeleton loading */}
        {showSkeleton && !isLocked && (
          <div className="p-4 space-y-2" data-testid="preview-skeleton">
            {[...Array(6)].map((_, i) => (
              <Skeleton key={i} className={`h-7 w-full ${i === 0 ? 'bg-muted/80' : ''}`} />
            ))}
          </div>
        )}

        {/* Preview table */}
        {!showSkeleton && hasData && (
          <>
            <div className="table-scroll-wrapper" data-testid="dataset-preview-table">
              <table
                className="w-full text-sm audit-table"
                style={{ minWidth: `${Math.max(columns.length * 130, 400)}px` }}
              >
                <thead>
                  <tr>
                    <th className="py-2.5 px-3 text-left text-xs uppercase tracking-wide text-muted-foreground w-10">#</th>
                    {columns.map((col) => (
                      <th
                        key={col}
                        className="py-2.5 px-3 text-left text-xs uppercase tracking-wide text-muted-foreground whitespace-nowrap"
                      >
                        {col}
                      </th>
                    ))}
                  </tr>
                </thead>
                <tbody>
                  {preview.map((row, idx) => (
                    <tr key={idx} className="border-t border-border/50 hover:bg-muted/40">
                      <td className="py-2 px-3 text-xs text-muted-foreground tabular-nums">{idx + 1}</td>
                      {columns.map((col) => {
                        const val = row[col];
                        return (
                          <td key={col} className="py-2 px-3 text-sm max-w-[200px]">
                            {val === null || val === undefined ? (
                              <span className="text-muted-foreground/40 italic text-xs">null</span>
                            ) : (
                              <span
                                className="truncate block"
                                title={String(val)}
                              >
                                {String(val)}
                              </span>
                            )}
                          </td>
                        );
                      })}
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
            <div className="px-4 py-2 border-t border-border bg-muted/30">
              <p className="text-xs text-muted-foreground">
                Showing first {preview.length} of {meta.rows?.toLocaleString()} rows
                &nbsp;&bull;&nbsp;{columns.length} columns
                {meta.encoding && meta.encoding !== 'utf-8' && (
                  <span className="ml-2 text-muted-foreground/60">
                    Encoding: {meta.encoding}
                  </span>
                )}
                {meta.delimiter && meta.delimiter !== ',' && (
                  <span className="ml-2 text-muted-foreground/60">
                    Delimiter: {JSON.stringify(meta.delimiter)}
                  </span>
                )}
              </p>
            </div>
          </>
        )}
      </CardContent>
    </Card>
  );
}
