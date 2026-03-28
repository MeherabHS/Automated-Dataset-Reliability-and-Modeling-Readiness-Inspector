import React from 'react';
import { Card, CardContent } from './ui/card';
import { Badge } from './ui/badge';
import { Skeleton } from './ui/skeleton';

// ────────────────────────────────────────────────────────────────
// Summary card definitions — maps to new audit_engine.py field names
// ────────────────────────────────────────────────────────────────
const SUMMARY_CARDS = [
  {
    key: 'schema',
    title: 'Schema Summary',
    testId: 'audit-summary-card-schema',
    placeholder: [
      { label: 'Total columns', value: '--' },
      { label: 'Type mismatches', value: '--' },
    ],
    getData: (d) => [
      { label: 'Total columns', value: d.schema?.column_count ?? '--' },
      { label: 'Type mismatches', value: d.schema?.mismatch_columns?.length ?? '--' },
    ],
  },
  {
    key: 'missingness',
    title: 'Missingness',
    testId: 'audit-summary-card-missingness',
    placeholder: [
      { label: 'Missing cells', value: '--' },
      { label: 'Missing %', value: '--' },
    ],
    getData: (d) => [
      { label: 'Missing cells', value: d.missingness?.total_missing?.toLocaleString() ?? '--' },
      {
        label: 'Missing %',
        value: d.missingness?.missing_pct_overall != null
          ? `${d.missingness.missing_pct_overall}%`
          : '--',
      },
    ],
  },
  {
    key: 'duplicates',
    title: 'Duplicates',
    testId: 'audit-summary-card-duplicates',
    placeholder: [
      { label: 'Duplicate rows', value: '--' },
      { label: 'Duplicate %', value: '--' },
    ],
    getData: (d) => [
      {
        label: 'Duplicate rows',
        value: d.duplicates?.applicable === false
          ? 'N/A'
          : d.duplicates?.duplicate_row_count?.toLocaleString() ?? '--',
      },
      {
        label: 'Duplicate %',
        value: d.duplicates?.applicable === false
          ? 'N/A'
          : d.duplicates?.duplicate_pct != null ? `${d.duplicates.duplicate_pct}%` : '--',
      },
    ],
  },
  {
    key: 'outliers',
    title: 'Numeric Outliers',
    testId: 'audit-summary-card-outliers',
    placeholder: [
      { label: 'Numeric columns', value: '--' },
      { label: 'With outliers', value: '--' },
    ],
    getData: (d) => {
      if (d.outliers?.applicable === false) {
        return [
          { label: 'Numeric columns', value: '0' },
          { label: 'With outliers', value: 'N/A' },
        ];
      }
      const cols = d.outliers?.numeric_columns || [];
      const applicable = cols.filter(c => c.applicable !== false);
      const withOutliers = applicable.filter(c => c.outlier_count > 0).length;
      return [
        { label: 'Numeric columns', value: applicable.length },
        { label: 'With outliers', value: withOutliers },
      ];
    },
  },
  {
    key: 'class-imbalance',
    title: 'Class Imbalance',
    testId: 'audit-summary-card-class-imbalance',
    placeholder: [
      { label: 'Target column', value: '--' },
      { label: 'Imbalance', value: '--' },
    ],
    getData: (d) => {
      const imb = d.imbalance || {};
      return [
        {
          label: 'Target column',
          value: imb.target_col || (imb.not_selected ? 'Not set' : 'N/A'),
        },
        {
          label: 'Imbalance',
          value: imb.applicable ? (imb.imbalance_label || '--') : 'N/A',
        },
      ];
    },
  },
  {
    key: 'leakage',
    title: 'Leakage Risk',
    testId: 'audit-summary-card-leakage',
    placeholder: [
      { label: 'Flagged columns', value: '--' },
      { label: 'Risk', value: '--' },
    ],
    getData: (d) => {
      const count = d.leakage?.flag_count ?? 0;
      const risk = count === 0 ? 'None' : count < 3 ? 'Moderate' : 'High';
      return [
        { label: 'Flagged columns', value: count },
        { label: 'Risk', value: risk },
      ];
    },
  },
];

// ── Severity badge per card ──────────────────────────────────────
function SummaryBadge({ cardKey, data }) {
  if (!data) return <Badge variant="secondary" className="text-xs">Pending</Badge>;

  switch (cardKey) {
    case 'schema': {
      const count = data.schema?.mismatch_columns?.length || 0;
      return count > 0
        ? <Badge className="text-xs border severity-moderate">{count} mismatch{count !== 1 ? 'es' : ''}</Badge>
        : <Badge className="text-xs border severity-low">Clean</Badge>;
    }
    case 'missingness': {
      const pct = data.missingness?.missing_pct_overall || 0;
      if (pct > 20) return <Badge className="text-xs border severity-high">{pct}% missing</Badge>;
      if (pct > 5)  return <Badge className="text-xs border severity-moderate">{pct}% missing</Badge>;
      return <Badge className="text-xs border severity-low">Low</Badge>;
    }
    case 'duplicates': {
      if (data.duplicates?.applicable === false) return <Badge variant="secondary" className="text-xs">N/A</Badge>;
      const r = data.duplicates?.risk_label;
      if (r === 'Low')      return <Badge className="text-xs border severity-low">Low risk</Badge>;
      if (r === 'Moderate') return <Badge className="text-xs border severity-moderate">Moderate risk</Badge>;
      if (r === 'High')     return <Badge className="text-xs border severity-high">High risk</Badge>;
      return <Badge variant="secondary" className="text-xs">--</Badge>;
    }
    case 'outliers': {
      if (data.outliers?.applicable === false) return <Badge variant="secondary" className="text-xs">N/A</Badge>;
      const cols = data.outliers?.numeric_columns || [];
      const applicable = cols.filter(c => c.applicable !== false);
      const total = applicable.reduce((s, c) => s + (c.outlier_count || 0), 0);
      if (total === 0)   return <Badge className="text-xs border severity-low">None</Badge>;
      if (total > 50)    return <Badge className="text-xs border severity-high">{total} outliers</Badge>;
      return <Badge className="text-xs border severity-moderate">{total} outliers</Badge>;
    }
    case 'class-imbalance': {
      const imb = data.imbalance;
      if (!imb?.applicable) return <Badge variant="secondary" className="text-xs">N/A</Badge>;
      const label = imb.imbalance_label || '';
      if (label === 'Balanced')          return <Badge className="text-xs border severity-low">Balanced</Badge>;
      if (label === 'Moderate imbalance') return <Badge className="text-xs border severity-moderate">Moderate</Badge>;
      if (label === 'Severe imbalance')   return <Badge className="text-xs border severity-high">Severe</Badge>;
      return <Badge variant="secondary" className="text-xs">{label}</Badge>;
    }
    case 'leakage': {
      const count = data.leakage?.flag_count ?? 0;
      if (count === 0) return <Badge className="text-xs border severity-low">Clean</Badge>;
      if (count < 3)   return <Badge className="text-xs border severity-moderate">{count} flagged</Badge>;
      return <Badge className="text-xs border severity-high">{count} flagged</Badge>;
    }
    default:
      return <Badge variant="secondary" className="text-xs">--</Badge>;
  }
}

// ── Main component ───────────────────────────────────────────────
export default function AuditSummaryCards({ isLocked, isAuditing, isComplete, auditData }) {
  return (
    <div
      data-testid="audit-summary-cards"
      className={isLocked ? 'section-locked' : ''}
    >
      <div className="mb-3">
        <h2 className="font-heading text-base font-semibold text-foreground">Audit Summary</h2>
        <p className="text-xs text-muted-foreground mt-0.5">
          {isLocked
            ? 'Upload and audit a CSV file to see summary metrics.'
            : isComplete
            ? 'Overview of all six audit checks.'
            : 'Running audit checks…'}
        </p>
      </div>

      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-3">
        {SUMMARY_CARDS.map((card) => {
          const metrics = isComplete && auditData ? card.getData(auditData) : null;
          const rows = metrics || card.placeholder;

          return (
            <Card key={card.key} data-testid={card.testId} className="p-0">
              <CardContent className="p-4">
                <div className="flex items-start justify-between gap-2 mb-3">
                  <span className="text-sm font-heading font-semibold text-foreground">{card.title}</span>
                  {isAuditing
                    ? <Skeleton className="h-5 w-14 rounded-full" />
                    : <SummaryBadge cardKey={card.key} data={isComplete ? auditData : null} />}
                </div>
                <div className="space-y-2">
                  {rows.map((row, i) => (
                    <div key={i} className="flex items-center justify-between gap-2">
                      <span className="text-xs text-muted-foreground">{row.label}</span>
                      {isAuditing
                        ? <Skeleton className="h-4 w-12" />
                        : <span className="text-sm font-heading font-semibold tabular-nums text-foreground">
                            {String(row.value)}
                          </span>}
                    </div>
                  ))}
                </div>
              </CardContent>
            </Card>
          );
        })}
      </div>
    </div>
  );
}
