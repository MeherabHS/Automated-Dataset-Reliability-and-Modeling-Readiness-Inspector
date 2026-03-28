import React, { useRef } from 'react';
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from './ui/card';
import { Button } from './ui/button';
import { Label } from './ui/label';
import { Alert, AlertDescription, AlertTitle } from './ui/alert';
import { Separator } from './ui/separator';
import { Badge } from './ui/badge';
import {
  Upload, FileText, AlertCircle, CheckCircle2, X,
  Loader2, Play, TriangleAlert, Info
} from 'lucide-react';

// ── Error code → user-facing guidance mapping ──────────────────────
const ERROR_GUIDANCE = {
  unsupported_file_type: {
    title: 'Unsupported file type',
    hint: 'Only .csv files are accepted. Excel (.xlsx, .xls) and other formats are not supported.',
  },
  too_large: {
    title: 'File too large',
    hint: 'Maximum file size is 50 MB. Split the dataset or reduce the number of rows.',
  },
  empty_file: {
    title: 'Empty file',
    hint: 'The file contains no data. Ensure there is a header row and at least one data row.',
  },
  encoding_error: {
    title: 'Encoding error',
    hint: 'Re-save the file as UTF-8 in your spreadsheet application. Try: File → Save As → CSV UTF-8.',
  },
  malformed_csv: {
    title: 'Malformed CSV',
    hint: 'Open the file in a text editor. Check for: unescaped commas in quoted fields, inconsistent column counts, or mixed line endings.',
  },
  no_columns: {
    title: 'No columns detected',
    hint: 'Check that the first row is a valid comma-separated header. Make sure the delimiter matches throughout the file.',
  },
  no_data_rows: {
    title: 'No data rows',
    hint: 'The file only has a header row. Add at least one data row below the header and re-upload.',
  },
  network_error: {
    title: 'Network error',
    hint: 'Check your internet connection and try again.',
  },
  server_error: {
    title: 'Server error',
    hint: 'An unexpected error occurred on the server. Try uploading the file again.',
  },
};

function getGuidance(code, fallbackHint) {
  const g = ERROR_GUIDANCE[code] || {};
  return {
    title: g.title || 'Upload error',
    hint: fallbackHint || g.hint || 'Check the file and try again.',
  };
}

export default function UploadSection({
  appState,
  selectedFile,
  parseResult,
  parseError,
  auditError,
  onFileSelect,
  onUploadAndParse,
  onRunAudit,
  onReset,
}) {
  const inputRef = useRef(null);

  const handleInputChange = (e) => {
    const file = e.target.files[0];
    if (file) onFileSelect(file);
  };

  const handleClear = () => {
    if (inputRef.current) inputRef.current.value = '';
    onReset();
  };

  const isUploading = appState === 'uploading';
  const isFileSelected = appState === 'file_selected';
  const isParsed = appState === 'parsed' || appState === 'audit_error';
  const isAuditing = appState === 'auditing';
  const isComplete = appState === 'complete';
  const isError = appState === 'parse_error';
  const canClear = appState !== 'empty';

  return (
    <Card data-testid="upload-section">
      <CardHeader className="pb-4">
        <div className="flex items-start justify-between gap-4">
          <div className="space-y-1">
            <CardTitle className="font-heading text-base font-semibold">CSV Upload</CardTitle>
            <CardDescription className="text-sm">
              Select a CSV file to begin dataset inspection.
            </CardDescription>
          </div>
          {canClear && (
            <Button
              variant="ghost"
              size="sm"
              onClick={handleClear}
              className="shrink-0 text-muted-foreground hover:text-foreground"
              data-testid="reset-button"
            >
              <X className="w-4 h-4 mr-1" />
              Clear
            </Button>
          )}
        </div>
      </CardHeader>

      <CardContent className="space-y-5">
        <div className="grid grid-cols-1 lg:grid-cols-5 gap-6">
          {/* Left: instructions */}
          <div className="lg:col-span-3 space-y-3">
            <div>
              <p className="text-sm font-medium text-foreground mb-2">How to use</p>
              <ol className="text-sm text-muted-foreground space-y-1.5 list-decimal list-inside">
                <li>
                  Select a <span className="font-mono-text text-xs bg-muted px-1.5 py-0.5 rounded">.csv</span> file using the input.
                </li>
                <li>
                  Click <strong>Upload &amp; Preview</strong> — the file is parsed and the first rows are shown.
                </li>
                <li>
                  Review the preview, then click <strong>Run Full Audit</strong> to analyse the dataset.
                </li>
                <li>
                  Inspect each panel and download the text report when ready.
                </li>
              </ol>
            </div>
            <Separator />
            <div className="text-xs text-muted-foreground space-y-0.5">
              <p>Accepted format: CSV &mdash; comma, semicolon, tab, or pipe-delimited</p>
              <p>Accepted encodings: UTF-8, UTF-8 BOM, Latin-1, CP-1252</p>
              <p>Maximum file size: 50 MB</p>
            </div>
          </div>

          {/* Right: controls + status */}
          <div className="lg:col-span-2 space-y-3">
            {/* File input */}
            <div className="space-y-1.5 upload-input-wrapper">
              <Label htmlFor="csv-upload-input" className="text-sm font-medium">
                Select file
              </Label>
              <input
                id="csv-upload-input"
                ref={inputRef}
                type="file"
                accept=".csv,text/csv"
                onChange={handleInputChange}
                disabled={isUploading || isAuditing}
                className="flex w-full rounded-md border border-input bg-background px-3 py-2 text-sm text-foreground file:border-0 file:bg-transparent file:text-sm file:font-medium placeholder:text-muted-foreground focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2 disabled:cursor-not-allowed disabled:opacity-50 cursor-pointer"
                data-testid="csv-upload-input"
                aria-describedby="upload-status"
              />
              {selectedFile && (
                <p className="text-xs text-muted-foreground font-mono-text">
                  {selectedFile.name}
                  <span className="ml-1.5 text-muted-foreground/60">
                    &bull; {selectedFile.size < 1024
                      ? `${selectedFile.size} B`
                      : selectedFile.size < 1024 * 1024
                      ? `${(selectedFile.size / 1024).toFixed(1)} KB`
                      : `${(selectedFile.size / 1024 / 1024).toFixed(1)} MB`}
                  </span>
                </p>
              )}
            </div>

            {/* Action buttons */}
            <div className="space-y-2">
              {/* Upload & Preview button */}
              <Button
                onClick={onUploadAndParse}
                disabled={!isFileSelected}
                className="w-full btn-press"
                variant="default"
                data-testid="upload-parse-button"
              >
                {isUploading ? (
                  <><Loader2 className="w-4 h-4 mr-2 animate-spin" />Parsing file&hellip;</>
                ) : (
                  <><Upload className="w-4 h-4 mr-2" />Upload &amp; Preview</>
                )}
              </Button>

              {/* Run Full Audit button — only enabled after successful parse */}
              <Button
                onClick={onRunAudit}
                disabled={!isParsed}
                className="w-full btn-press"
                variant={isParsed ? 'default' : 'outline'}
                data-testid="run-audit-button"
              >
                {isAuditing ? (
                  <><Loader2 className="w-4 h-4 mr-2 animate-spin" />Running audit&hellip;</>
                ) : (
                  <><Play className="w-4 h-4 mr-2" />Run Full Audit</>
                )}
              </Button>
            </div>

            {/* Status alert */}
            <div id="upload-status" data-testid="upload-status-alert">
              {appState === 'empty' && (
                <Alert>
                  <FileText className="h-4 w-4" />
                  <AlertTitle className="text-sm">No file selected</AlertTitle>
                  <AlertDescription className="text-xs">Choose a CSV file to begin.</AlertDescription>
                </Alert>
              )}

              {isFileSelected && (
                <Alert className="border-[hsl(var(--info-border))] bg-[hsl(var(--info-bg))]">
                  <Info className="h-4 w-4 text-[hsl(var(--info-fg))]" />
                  <AlertTitle className="text-sm text-[hsl(var(--info-fg))]">File ready</AlertTitle>
                  <AlertDescription className="text-xs text-[hsl(var(--info-fg))]/80">
                    Click <strong>Upload &amp; Preview</strong> to parse the file.
                  </AlertDescription>
                </Alert>
              )}

              {isUploading && (
                <Alert className="border-[hsl(var(--info-border))] bg-[hsl(var(--info-bg))]">
                  <Loader2 className="h-4 w-4 animate-spin text-[hsl(var(--info-fg))]" />
                  <AlertTitle className="text-sm text-[hsl(var(--info-fg))]">Parsing&hellip;</AlertTitle>
                  <AlertDescription className="text-xs text-[hsl(var(--info-fg))]/80">
                    Reading and validating the CSV file.
                  </AlertDescription>
                </Alert>
              )}

              {isError && parseError && (
                <Alert variant="destructive" data-testid="parsing-error-message">
                  <AlertCircle className="h-4 w-4" />
                  <AlertTitle className="text-sm">
                    {getGuidance(parseError.code, parseError.hint).title}
                  </AlertTitle>
                  <AlertDescription className="text-xs space-y-1">
                    <p>{parseError.message}</p>
                    <p className="opacity-75">{getGuidance(parseError.code, parseError.hint).hint}</p>
                  </AlertDescription>
                </Alert>
              )}

              {isParsed && parseResult && !auditError && (
                <Alert className="border-[hsl(var(--success-border))] bg-[hsl(var(--success-bg))]">
                  <CheckCircle2 className="h-4 w-4 text-[hsl(var(--success-fg))]" />
                  <AlertTitle className="text-sm text-[hsl(var(--success-fg))]">Parsed successfully</AlertTitle>
                  <AlertDescription className="text-xs text-[hsl(var(--success-fg))]/80">
                    {parseResult.meta.rows.toLocaleString()} rows detected.
                    {parseResult.warnings?.length > 0 && (
                      <span className="block mt-0.5 text-[hsl(var(--warning-fg))]">
                        {parseResult.warnings.length} warning{parseResult.warnings.length > 1 ? 's' : ''} &mdash; see preview below.
                      </span>
                    )}
                    Click <strong>Run Full Audit</strong> to continue.
                  </AlertDescription>
                </Alert>
              )}

              {appState === 'audit_error' && auditError && (
                <Alert variant="destructive" data-testid="audit-error-message">
                  <AlertCircle className="h-4 w-4" />
                  <AlertTitle className="text-sm">Audit failed</AlertTitle>
                  <AlertDescription className="text-xs">
                    {auditError}
                    <span className="block mt-0.5 opacity-75">The file was parsed successfully — try running the audit again.</span>
                  </AlertDescription>
                </Alert>
              )}

              {isAuditing && (
                <Alert className="border-[hsl(var(--info-border))] bg-[hsl(var(--info-bg))]">
                  <Loader2 className="h-4 w-4 animate-spin text-[hsl(var(--info-fg))]" />
                  <AlertTitle className="text-sm text-[hsl(var(--info-fg))]">Running audit&hellip;</AlertTitle>
                  <AlertDescription className="text-xs text-[hsl(var(--info-fg))]/80">
                    Running all inspection checks.
                  </AlertDescription>
                </Alert>
              )}

              {isComplete && (
                <Alert className="border-[hsl(var(--success-border))] bg-[hsl(var(--success-bg))]">
                  <CheckCircle2 className="h-4 w-4 text-[hsl(var(--success-fg))]" />
                  <AlertTitle className="text-sm text-[hsl(var(--success-fg))]">Audit complete</AlertTitle>
                  <AlertDescription className="text-xs text-[hsl(var(--success-fg))]/80">
                    All panels populated. Review results below.
                  </AlertDescription>
                </Alert>
              )}
            </div>
          </div>
        </div>
      </CardContent>
    </Card>
  );
}
