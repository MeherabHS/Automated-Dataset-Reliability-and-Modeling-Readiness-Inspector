import React from 'react';
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from './ui/card';
import { Badge } from './ui/badge';
import { Separator } from './ui/separator';
import { Skeleton } from './ui/skeleton';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from './ui/select';
import {
  LayoutList, Columns3, Copy, TrendingUp, PieChart, ShieldAlert,
  AlertTriangle, Info
} from 'lucide-react';

// ────────────────────────────────────────────────────────────────
// Shared sub-components
// ────────────────────────────────────────────────────────────────
function SkeletonRows({ rows = 3, cols = 4 }) {
  return (
    <>
      {Array.from({ length: rows }).map((_, i) => (
        <tr key={i}>
          {Array.from({ length: cols }).map((_, j) => (
            <td key={j} className="py-2 px-3">
              <Skeleton className="h-4 w-full" />
            </td>
          ))}
        </tr>
      ))}
    </>
  );
}

function PlaceholderRows({ rows = 3, cols = 4, colLabels }) {
  return (
    <>
      {Array.from({ length: rows }).map((_, i) => (
        <tr key={i} className="border-t border-border/30">
          {colLabels
            ? colLabels.map((lbl, j) => (
                <td key={j} className={`py-2 px-3 text-xs text-muted-foreground/40 ${j > 0 ? 'text-right' : ''}`}>
                  {j === 0 ? `column_${i + 1}` : '--'}
                </td>
              ))
            : Array.from({ length: cols }).map((_, j) => (
                <td key={j} className="py-2 px-3 text-xs text-muted-foreground/40">--</td>
              ))}
        </tr>
      ))}
    </>
  );
}

function NotApplicable({ reason }) {
  return (
    <div className="flex items-start gap-2 py-5 px-2 text-muted-foreground">
      <Info className="w-4 h-4 shrink-0 mt-0.5" />
      <p className="text-sm">
        <span className="font-medium">Not applicable</span>
        {reason && <span className="text-muted-foreground/70"> — {reason}</span>}
      </p>
    </div>
  );
}

function PanelShell({ icon: Icon, title, description, badge, testId, locked, children }) {
  return (
    <Card data-testid={testId} className={locked ? 'section-locked' : ''}>
      <CardHeader className="pb-3">
        <div className="flex items-start justify-between gap-4">
          <div className="space-y-1">
            <CardTitle className="font-heading text-base font-semibold flex items-center gap-2">
              <Icon className="w-4 h-4 text-muted-foreground" />
              {title}
            </CardTitle>
            <CardDescription className="text-xs">{description}</CardDescription>
          </div>
          {badge}
        </div>
      </CardHeader>
      <Separator />
      <CardContent className="pt-4 pb-5">
        {children}
      </CardContent>
    </Card>
  );
}

// ────────────────────────────────────────────────────────────────
// 1. Schema Summary Panel
// ────────────────────────────────────────────────────────────────
function SchemaPanel({ isLocked, isAuditing, isComplete, data }) {
  const schema = data?.schema;
  const columns = schema?.columns || [];
  const mismatches = schema?.mismatch_columns || [];

  let badge;
  if (!isComplete) {
    badge = <Badge variant="secondary" className="text-xs shrink-0">Pending</Badge>;
  } else if (!schema?.applicable) {
    badge = <Badge variant="secondary" className="text-xs shrink-0">N/A</Badge>;
  } else if (mismatches.length > 0) {
    badge = <Badge className="text-xs border severity-moderate shrink-0">{mismatches.length} mismatch{mismatches.length !== 1 ? 'es' : ''}</Badge>;
  } else {
    badge = <Badge className="text-xs border severity-low shrink-0">Clean</Badge>;
  }

  return (
    <PanelShell
      icon={LayoutList}
      title="Schema Summary"
      description="Inferred column types, unique value counts, null rates, and type-mismatch warnings."
      testId="audit-panel-schema"
      locked={isLocked}
      badge={badge}
    >
      {isComplete && schema?.applicable === false ? (
        <NotApplicable reason={schema.reason} />
      ) : (
        <>
          <div className="table-scroll-wrapper">
            <table className="w-full text-sm audit-table">
              <thead>
                <tr>
                  <th className="py-2 px-3 text-left text-xs uppercase tracking-wide text-muted-foreground">Column</th>
                  <th className="py-2 px-3 text-left text-xs uppercase tracking-wide text-muted-foreground">Inferred type</th>
                  <th className="py-2 px-3 text-right text-xs uppercase tracking-wide text-muted-foreground">Nulls</th>
                  <th className="py-2 px-3 text-right text-xs uppercase tracking-wide text-muted-foreground">Null %</th>
                  <th className="py-2 px-3 text-right text-xs uppercase tracking-wide text-muted-foreground">Unique</th>
                  <th className="py-2 px-3 text-center text-xs uppercase tracking-wide text-muted-foreground">Mismatch</th>
                </tr>
              </thead>
              <tbody>
                {isAuditing ? <SkeletonRows rows={4} cols={6} /> :
                isComplete && columns.length > 0 ? (
                  columns.map((col, i) => (
                    <tr key={i} className="border-t border-border/50 hover:bg-muted/40">
                      <td className="py-2 px-3 font-medium">{col.name}</td>
                      <td className="py-2 px-3">
                        <span className="font-mono-text text-xs bg-muted px-1.5 py-0.5 rounded">{col.inferred_type}</span>
                        {col.all_missing && (
                          <span className="ml-1.5 text-xs text-muted-foreground/60 italic">all null</span>
                        )}
                      </td>
                      <td className="py-2 px-3 text-right tabular-nums">{col.null_count.toLocaleString()}</td>
                      <td className="py-2 px-3 text-right tabular-nums">
                        <span className={col.null_pct > 20 ? 'text-[hsl(var(--warning-fg))] font-medium' : ''}>
                          {col.null_pct}%
                        </span>
                      </td>
                      <td className="py-2 px-3 text-right tabular-nums">{col.unique_count.toLocaleString()}</td>
                      <td className="py-2 px-3 text-center">
                        {col.mismatch_warning ? (
                          <span className="inline-flex items-center gap-1 text-xs font-medium text-[hsl(var(--warning-fg))]">
                            <AlertTriangle className="w-3 h-3" /> Yes
                          </span>
                        ) : (
                          <span className="text-xs text-muted-foreground">No</span>
                        )}
                      </td>
                    </tr>
                  ))
                ) : (
                  <PlaceholderRows rows={3} cols={6} colLabels={['col','type','nulls','null%','unique','mismatch']} />
                )}
              </tbody>
            </table>
          </div>
          {isComplete && mismatches.length > 0 && (
            <p className="text-xs text-[hsl(var(--warning-fg))] mt-3">
              Type coercions detected in: {mismatches.join(', ')}
            </p>
          )}
          {!isComplete && (
            <p className="text-xs text-muted-foreground/50 italic mt-3">
              Column schema details will appear here after the audit completes.
            </p>
          )}
        </>
      )}
    </PanelShell>
  );
}

// ────────────────────────────────────────────────────────────────
// 2. Missingness Panel
// ────────────────────────────────────────────────────────────────
function MissingnessPanel({ isLocked, isAuditing, isComplete, data }) {
  const miss = data?.missingness;
  const perColumn = miss?.per_column || [];

  const pct = miss?.missing_pct_overall;
  let badge;
  if (!isComplete) {
    badge = <Badge variant="secondary" className="text-xs shrink-0">Pending</Badge>;
  } else if (pct > 20) {
    badge = <Badge className="text-xs border severity-high shrink-0">{pct}% missing</Badge>;
  } else if (pct > 5) {
    badge = <Badge className="text-xs border severity-moderate shrink-0">{pct}% missing</Badge>;
  } else {
    badge = <Badge className="text-xs border severity-low shrink-0">{pct}% missing</Badge>;
  }

  return (
    <PanelShell
      icon={Columns3}
      title="Missingness Analysis"
      description="Per-column null counts, missing percentages, and overall dataset completeness."
      testId="audit-panel-missingness"
      locked={isLocked}
      badge={badge}
    >
      <div className="mb-4">
        <span className="text-sm text-muted-foreground">Overall missingness: </span>
        <span className="font-heading font-semibold tabular-nums text-foreground">
          {isComplete
            ? `${pct}% (${Number(miss?.total_missing).toLocaleString()} of ${Number(miss?.total_cells).toLocaleString()} cells)`
            : '--'}
        </span>
      </div>
      <div className="table-scroll-wrapper">
        <table className="w-full text-sm audit-table">
          <thead>
            <tr>
              <th className="py-2 px-3 text-left text-xs uppercase tracking-wide text-muted-foreground">Column</th>
              <th className="py-2 px-3 text-right text-xs uppercase tracking-wide text-muted-foreground">Null count</th>
              <th className="py-2 px-3 text-right text-xs uppercase tracking-wide text-muted-foreground">Null %</th>
              <th className="py-2 px-3 text-left text-xs uppercase tracking-wide text-muted-foreground">Suggested action</th>
            </tr>
          </thead>
          <tbody>
            {isAuditing ? <SkeletonRows rows={3} cols={4} /> :
            isComplete && perColumn.length > 0 ? (
              perColumn.map((col, i) => (
                <tr key={i} className="border-t border-border/50 hover:bg-muted/40">
                  <td className="py-2 px-3 font-medium">{col.column}</td>
                  <td className="py-2 px-3 text-right tabular-nums">{col.null_count.toLocaleString()}</td>
                  <td className="py-2 px-3 text-right tabular-nums">{col.null_pct}%</td>
                  <td className="py-2 px-3 text-xs text-muted-foreground">{col.suggested_action}</td>
                </tr>
              ))
            ) : isComplete ? (
              <tr className="border-t border-border/50">
                <td colSpan={4} className="py-4 px-3 text-sm text-center text-muted-foreground">
                  No missing values detected — dataset is complete.
                </td>
              </tr>
            ) : (
              <PlaceholderRows rows={3} cols={4} colLabels={['col','count','%','action']} />
            )}
          </tbody>
        </table>
      </div>
      {!isComplete && (
        <p className="text-xs text-muted-foreground/50 italic mt-3">
          Per-column missingness breakdown will appear here after the audit completes.
        </p>
      )}
    </PanelShell>
  );
}

// ────────────────────────────────────────────────────────────────
// 3. Duplicate Analysis Panel
// ────────────────────────────────────────────────────────────────
function DuplicatesPanel({ isLocked, isAuditing, isComplete, data }) {
  const dup = data?.duplicates;

  let badge;
  if (!isComplete) {
    badge = <Badge variant="secondary" className="text-xs shrink-0">Pending</Badge>;
  } else if (dup?.applicable === false) {
    badge = <Badge variant="secondary" className="text-xs shrink-0">N/A</Badge>;
  } else {
    const r = dup?.risk_label;
    badge = r === 'Low'
      ? <Badge className="text-xs border severity-low shrink-0">Low risk</Badge>
      : r === 'Moderate'
      ? <Badge className="text-xs border severity-moderate shrink-0">Moderate risk</Badge>
      : <Badge className="text-xs border severity-high shrink-0">High risk</Badge>;
  }

  const rows = [
    { label: 'Duplicate rows', value: isComplete ? (dup?.applicable === false ? 'N/A' : (dup?.duplicate_row_count?.toLocaleString() ?? '--')) : '--' },
    { label: 'Duplicate %', value: isComplete ? (dup?.applicable === false ? 'N/A' : `${dup?.duplicate_pct ?? '--'}%`) : '--' },
    { label: 'Risk classification', value: isComplete ? (dup?.applicable === false ? 'N/A' : (dup?.risk_label ?? '--')) : '--' },
  ];

  return (
    <PanelShell
      icon={Copy}
      title="Duplicate Analysis"
      description="Exact duplicate row detection with risk classification."
      testId="audit-panel-duplicates"
      locked={isLocked}
      badge={badge}
    >
      {isComplete && dup?.applicable === false ? (
        <NotApplicable reason={dup.reason} />
      ) : (
        <>
          <div className="table-scroll-wrapper">
            <table className="w-full text-sm audit-table">
              <thead>
                <tr>
                  <th className="py-2 px-3 text-left text-xs uppercase tracking-wide text-muted-foreground">Metric</th>
                  <th className="py-2 px-3 text-right text-xs uppercase tracking-wide text-muted-foreground">Value</th>
                </tr>
              </thead>
              <tbody>
                {isAuditing ? <SkeletonRows rows={3} cols={2} /> :
                rows.map(({ label, value }, i) => (
                  <tr key={i} className="border-t border-border/50 hover:bg-muted/40">
                    <td className="py-2.5 px-3 text-muted-foreground">{label}</td>
                    <td className="py-2.5 px-3 text-right font-medium tabular-nums">{value}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
          {!isComplete && (
            <p className="text-xs text-muted-foreground/50 italic mt-3">
              Duplicate row count and risk label will appear here after the audit completes.
            </p>
          )}
        </>
      )}
    </PanelShell>
  );
}

// ────────────────────────────────────────────────────────────────
// 4. Numeric Outlier Analysis Panel
// ────────────────────────────────────────────────────────────────
function OutliersPanel({ isLocked, isAuditing, isComplete, data }) {
  const out = data?.outliers;
  const numericCols = out?.numeric_columns || [];
  const applicableCols = numericCols.filter(c => c.applicable !== false);
  const totalOutliers = applicableCols.reduce((s, c) => s + (c.outlier_count || 0), 0);

  let badge;
  if (!isComplete) {
    badge = <Badge variant="secondary" className="text-xs shrink-0">Pending</Badge>;
  } else if (out?.applicable === false) {
    badge = <Badge variant="secondary" className="text-xs shrink-0">N/A</Badge>;
  } else if (totalOutliers === 0) {
    badge = <Badge className="text-xs border severity-low shrink-0">No outliers</Badge>;
  } else if (totalOutliers > 50) {
    badge = <Badge className="text-xs border severity-high shrink-0">{totalOutliers.toLocaleString()} outliers</Badge>;
  } else {
    badge = <Badge className="text-xs border severity-moderate shrink-0">{totalOutliers} outliers</Badge>;
  }

  return (
    <PanelShell
      icon={TrendingUp}
      title="Numeric Outlier Analysis"
      description="IQR-based outlier detection: Q1, Q3, IQR, bounds, and outlier count per numeric column."
      testId="audit-panel-outliers"
      locked={isLocked}
      badge={badge}
    >
      {isComplete && out?.applicable === false ? (
        <NotApplicable reason={out.reason} />
      ) : (
        <>
          <div className="table-scroll-wrapper" data-testid="outliers-table">
            <table className="w-full text-sm audit-table" style={{ minWidth: '600px' }}>
              <thead>
                <tr>
                  <th className="py-2 px-3 text-left text-xs uppercase tracking-wide text-muted-foreground">Column</th>
                  <th className="py-2 px-3 text-right text-xs uppercase tracking-wide text-muted-foreground">Method</th>
                  <th className="py-2 px-3 text-right text-xs uppercase tracking-wide text-muted-foreground">Q1</th>
                  <th className="py-2 px-3 text-right text-xs uppercase tracking-wide text-muted-foreground">Q3</th>
                  <th className="py-2 px-3 text-right text-xs uppercase tracking-wide text-muted-foreground">Lower</th>
                  <th className="py-2 px-3 text-right text-xs uppercase tracking-wide text-muted-foreground">Upper</th>
                  <th className="py-2 px-3 text-right text-xs uppercase tracking-wide text-muted-foreground">Outliers</th>
                  <th className="py-2 px-3 text-right text-xs uppercase tracking-wide text-muted-foreground">%</th>
                </tr>
              </thead>
              <tbody>
                {isAuditing ? <SkeletonRows rows={3} cols={8} /> :
                isComplete && applicableCols.length > 0 ? (
                  applicableCols.map((col, i) => (
                    <tr key={i} className="border-t border-border/50 hover:bg-muted/40">
                      <td className="py-2 px-3 font-medium">{col.column}</td>
                      <td className="py-2 px-3 text-right">
                        <span className="font-mono-text text-xs bg-muted px-1.5 py-0.5 rounded">IQR</span>
                      </td>
                      <td className="py-2 px-3 text-right tabular-nums font-mono-text text-xs">{col.q1}</td>
                      <td className="py-2 px-3 text-right tabular-nums font-mono-text text-xs">{col.q3}</td>
                      <td className="py-2 px-3 text-right tabular-nums font-mono-text text-xs">{col.lower_bound}</td>
                      <td className="py-2 px-3 text-right tabular-nums font-mono-text text-xs">{col.upper_bound}</td>
                      <td className="py-2 px-3 text-right tabular-nums">
                        <span className={col.outlier_count > 0 ? 'text-[hsl(var(--warning-fg))] font-medium' : ''}>
                          {col.outlier_count.toLocaleString()}
                        </span>
                      </td>
                      <td className="py-2 px-3 text-right tabular-nums">{col.outlier_pct}%</td>
                    </tr>
                  ))
                ) : isComplete ? (
                  <tr className="border-t border-border/50">
                    <td colSpan={8} className="py-4 px-3 text-sm text-center text-muted-foreground">
                      No numeric columns with sufficient data for IQR analysis.
                    </td>
                  </tr>
                ) : (
                  <>
                    {[...Array(3)].map((_, i) => (
                      <tr key={i} className="border-t border-border/30">
                        <td className="py-2 px-3 text-xs text-muted-foreground/40">col_{i + 1}</td>
                        <td className="py-2 px-3 text-right"><span className="font-mono-text text-xs bg-muted px-1.5 py-0.5 rounded text-muted-foreground/40">IQR</span></td>
                        {[...Array(6)].map((_, j) => <td key={j} className="py-2 px-3 text-right text-xs text-muted-foreground/40">--</td>)}
                      </tr>
                    ))}
                  </>
                )}
              </tbody>
            </table>
          </div>
          {!isComplete && (
            <p className="text-xs text-muted-foreground/50 italic mt-3">
              IQR outlier statistics per numeric column will appear here after the audit completes.
            </p>
          )}
        </>
      )}
    </PanelShell>
  );
}

// ────────────────────────────────────────────────────────────────
// 5. Class Imbalance Panel
// ────────────────────────────────────────────────────────────────
function ClassImbalancePanel({ isLocked, isAuditing, isComplete, data, targetCol, onTargetColChange, columnNames }) {
  const imb = data?.imbalance;
  const dist = imb?.class_distribution || [];

  let badge;
  if (!isComplete) {
    badge = <Badge variant="secondary" className="text-xs shrink-0">Pending</Badge>;
  } else if (!imb?.applicable) {
    badge = <Badge variant="secondary" className="text-xs shrink-0">N/A</Badge>;
  } else {
    const label = imb.imbalance_label || '';
    if (label === 'Balanced')           badge = <Badge className="text-xs border severity-low shrink-0">Balanced</Badge>;
    else if (label === 'Moderate imbalance') badge = <Badge className="text-xs border severity-moderate shrink-0">Moderate</Badge>;
    else if (label === 'Severe imbalance')   badge = <Badge className="text-xs border severity-high shrink-0">Severe</Badge>;
    else badge = <Badge variant="secondary" className="text-xs shrink-0">{label}</Badge>;
  }

  return (
    <PanelShell
      icon={PieChart}
      title="Class Imbalance"
      description="Class distribution for the selected target column. Majority-to-minority ratio and imbalance classification."
      testId="audit-panel-class-imbalance"
      locked={isLocked}
      badge={badge}
    >
      {isComplete && !imb?.applicable ? (
        <NotApplicable reason={imb?.reason} />
      ) : (
        <>
          {/* Target column selector */}
          {isComplete && (
            <div className="mb-4 space-y-1.5">
              <label className="text-xs font-medium text-muted-foreground block">
                Target column <span className="text-muted-foreground/60">(for class imbalance analysis)</span>
              </label>
              <Select
                value={targetCol || ''}
                onValueChange={onTargetColChange}
                data-testid="target-column-select"
              >
                <SelectTrigger className="w-64 h-8 text-sm" data-testid="target-column-select">
                  <SelectValue placeholder="Select target column…" />
                </SelectTrigger>
                <SelectContent>
                  {columnNames.map((col) => (
                    <SelectItem key={col} value={col}>{col}</SelectItem>
                  ))}
                </SelectContent>
              </Select>
              {!targetCol && (
                <p className="text-xs text-muted-foreground/60">
                  Select the column you intend to predict to see class distribution.
                </p>
              )}
            </div>
          )}

          {/* Target column + key metrics */}
          <div className="flex flex-wrap gap-4 mb-4">
            <div>
              <p className="text-xs text-muted-foreground mb-0.5">Target column</p>
              <p className="text-sm font-medium">
                {isComplete
                  ? imb?.target_col
                    ? <span className="font-mono-text text-xs bg-muted px-1.5 py-0.5 rounded">{imb.target_col}</span>
                    : <span className="text-muted-foreground italic text-xs">Not selected</span>
                  : '--'}
              </p>
            </div>
            {isComplete && imb?.applicable && (
              <>
                <div>
                  <p className="text-xs text-muted-foreground mb-0.5">Imbalance label</p>
                  <p className="text-sm font-medium">{imb.imbalance_label || '--'}</p>
                </div>
                <div>
                  <p className="text-xs text-muted-foreground mb-0.5">Majority / minority ratio</p>
                  <p className="text-sm font-heading font-semibold tabular-nums">
                    {imb.majority_to_minority_ratio != null
                      ? `${imb.majority_to_minority_ratio}x`
                      : 'N/A'}
                  </p>
                </div>
              </>
            )}
          </div>

          {/* Class distribution table */}
          <div className="table-scroll-wrapper">
            <table className="w-full text-sm audit-table">
              <thead>
                <tr>
                  <th className="py-2 px-3 text-left text-xs uppercase tracking-wide text-muted-foreground">Class</th>
                  <th className="py-2 px-3 text-right text-xs uppercase tracking-wide text-muted-foreground">Count</th>
                  <th className="py-2 px-3 text-right text-xs uppercase tracking-wide text-muted-foreground">Distribution %</th>
                  <th className="py-2 px-3 text-left text-xs uppercase tracking-wide text-muted-foreground">Role</th>
                </tr>
              </thead>
              <tbody>
                {isAuditing ? <SkeletonRows rows={3} cols={4} /> :
                isComplete && dist.length > 0 ? (
                  dist.map((cls, i) => (
                    <tr key={i} className="border-t border-border/50 hover:bg-muted/40">
                      <td className="py-2 px-3 font-medium font-mono-text text-xs">{cls.class}</td>
                      <td className="py-2 px-3 text-right tabular-nums">{cls.count.toLocaleString()}</td>
                      <td className="py-2 px-3 text-right tabular-nums">{cls.pct}%</td>
                      <td className="py-2 px-3 text-xs text-muted-foreground">
                        {i === 0 ? 'Majority' : i === dist.length - 1 ? 'Minority' : ''}
                      </td>
                    </tr>
                  ))
                ) : isComplete ? (
                  <tr className="border-t border-border/50">
                    <td colSpan={4} className="py-4 px-3 text-sm text-center text-muted-foreground">
                      Select a target column to see class distribution.
                    </td>
                  </tr>
                ) : (
                  <PlaceholderRows rows={3} cols={4} colLabels={['class','count','%','role']} />
                )}
              </tbody>
            </table>
          </div>
          {!isComplete && (
            <p className="text-xs text-muted-foreground/50 italic mt-3">
              Class distribution will appear here after selecting a target column and running the audit.
            </p>
          )}
        </>
      )}
    </PanelShell>
  );
}

// ────────────────────────────────────────────────────────────────
// 6. Leakage Risk Panel
// ────────────────────────────────────────────────────────────────
function LeakagePanel({ isLocked, isAuditing, isComplete, data }) {
  const lk = data?.leakage;
  const flagged = lk?.flagged_columns || [];
  const flagCount = lk?.flag_count ?? 0;
  const keywords = lk?.keywords_checked || [];

  let badge;
  if (!isComplete) {
    badge = <Badge variant="secondary" className="text-xs shrink-0">Pending</Badge>;
  } else if (flagCount === 0) {
    badge = <Badge className="text-xs border severity-low shrink-0">No flags</Badge>;
  } else if (flagCount < 3) {
    badge = <Badge className="text-xs border severity-moderate shrink-0">{flagCount} flagged</Badge>;
  } else {
    badge = <Badge className="text-xs border severity-high shrink-0">{flagCount} flagged</Badge>;
  }

  return (
    <PanelShell
      icon={ShieldAlert}
      title="Leakage Risk"
      description="Columns whose names contain leakage-risk keywords (case-insensitive substring match)."
      testId="audit-panel-leakage"
      locked={isLocked}
      badge={badge}
    >
      <div className="table-scroll-wrapper">
        <table className="w-full text-sm audit-table">
          <thead>
            <tr>
              <th className="py-2 px-3 text-left text-xs uppercase tracking-wide text-muted-foreground">Column</th>
              <th className="py-2 px-3 text-left text-xs uppercase tracking-wide text-muted-foreground">Matched keyword(s)</th>
              <th className="py-2 px-3 text-left text-xs uppercase tracking-wide text-muted-foreground">Action</th>
            </tr>
          </thead>
          <tbody>
            {isAuditing ? <SkeletonRows rows={2} cols={3} /> :
            isComplete && flagged.length > 0 ? (
              flagged.map((col, i) => (
                <tr key={i} className="border-t border-border/50 hover:bg-muted/40">
                  <td className="py-2 px-3 font-medium">{col.column}</td>
                  <td className="py-2 px-3">
                    <div className="flex flex-wrap gap-1">
                      {col.matched_keywords.map((kw) => (
                        <span
                          key={kw}
                          className="font-mono-text text-xs bg-[hsl(var(--warning-bg))] border border-[hsl(var(--warning-border))] text-[hsl(var(--warning-fg))] px-1.5 py-0.5 rounded"
                        >
                          {kw}
                        </span>
                      ))}
                    </div>
                  </td>
                  <td className="py-2 px-3">
                    <Badge className="text-xs border severity-moderate">Review before modelling</Badge>
                  </td>
                </tr>
              ))
            ) : isComplete ? (
              <tr className="border-t border-border/50">
                <td colSpan={3} className="py-4 px-3 text-sm text-center text-muted-foreground">
                  No leakage-risk columns detected.
                </td>
              </tr>
            ) : (
              <PlaceholderRows rows={2} cols={3} colLabels={['col','keywords','action']} />
            )}
          </tbody>
        </table>
      </div>
      <p className="text-xs text-muted-foreground mt-3">
        {isComplete && keywords.length > 0
          ? `Keywords checked: ${keywords.join(', ')}`
          : 'Keywords checked: id, target, label, outcome, status, result, final, prediction, future, post, completed, discharge'}
      </p>
      {!isComplete && (
        <p className="text-xs text-muted-foreground/50 italic mt-1">
          Leakage-risk flags will appear here after the audit completes.
        </p>
      )}
    </PanelShell>
  );
}

// ────────────────────────────────────────────────────────────────
// Main export
// ────────────────────────────────────────────────────────────────
export default function AuditPanels({ isLocked, isAuditing, isComplete, auditData, targetCol, onTargetColChange, columnNames }) {
  return (
    <div
      data-testid="audit-panels-section"
      className={`space-y-5 ${isLocked ? 'section-locked' : ''}`}
    >
      <div>
        <h2 className="font-heading text-base font-semibold text-foreground">Detailed Audit Panels</h2>
        <p className="text-xs text-muted-foreground mt-0.5">
          {isLocked
            ? 'Upload and audit a CSV file to see detailed results.'
            : isComplete
            ? 'Full inspection results for each of the six audit checks.'
            : 'Running audit…'}
        </p>
      </div>

      <SchemaPanel         isLocked={isLocked} isAuditing={isAuditing} isComplete={isComplete} data={auditData} />
      <MissingnessPanel   isLocked={isLocked} isAuditing={isAuditing} isComplete={isComplete} data={auditData} />
      <DuplicatesPanel    isLocked={isLocked} isAuditing={isAuditing} isComplete={isComplete} data={auditData} />
      <OutliersPanel      isLocked={isLocked} isAuditing={isAuditing} isComplete={isComplete} data={auditData} />
      <ClassImbalancePanel
        isLocked={isLocked}
        isAuditing={isAuditing}
        isComplete={isComplete}
        data={auditData}
        targetCol={targetCol || ''}
        onTargetColChange={onTargetColChange}
        columnNames={columnNames || []}
      />
      <LeakagePanel       isLocked={isLocked} isAuditing={isAuditing} isComplete={isComplete} data={auditData} />
    </div>
  );
}
