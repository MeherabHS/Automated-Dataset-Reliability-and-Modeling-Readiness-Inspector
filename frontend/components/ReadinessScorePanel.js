import React from 'react';
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from './ui/card';
import { Badge } from './ui/badge';
import { Separator } from './ui/separator';
import { Skeleton } from './ui/skeleton';
import { Progress } from './ui/progress';
import { Gauge, Info, CheckCircle2 } from 'lucide-react';

// ── Score band → semantic style ─────────────────────────────────
const BAND_STYLES = {
  'Ready':                       { badge: 'severity-low',      bar: 'hsl(173, 80%, 28%)' },
  'Acceptable with preprocessing': { badge: 'severity-info',     bar: 'hsl(199, 84%, 45%)' },
  'Needs preprocessing':         { badge: 'severity-moderate', bar: 'hsl(30, 90%, 40%)' },
  'High risk':                   { badge: 'severity-high',     bar: 'hsl(0, 72%, 51%)' },
};

function getBandStyle(band) {
  return BAND_STYLES[band] || { badge: 'severity-moderate', bar: 'hsl(30, 90%, 40%)' };
}

// ── Penalty table row ──────────────────────────────────────────────────
function PenaltyRow({ penalty }) {
  const check = penalty.check || penalty.factor || '?';
  const rule  = penalty.rule  || penalty.detail  || '';
  const pts   = penalty.penalty ?? 0;
  return (
    <div className="flex items-start justify-between gap-3 rounded-md border border-border bg-muted/30 px-3 py-2.5">
      <div className="flex-1 min-w-0">
        <p className="text-sm font-medium text-foreground">{check}</p>
        {rule && <p className="text-xs text-muted-foreground mt-0.5">{rule}</p>}
      </div>
      <span className="shrink-0 font-heading font-semibold text-sm tabular-nums text-[hsl(var(--danger-fg))]">
        −{pts}
      </span>
    </div>
  );
}

// ── Not-applicable row ─────────────────────────────────────────────────────
function NotApplicableRow({ item }) {
  return (
    <div className="flex items-start gap-2 rounded-md border border-border/50 bg-muted/20 px-3 py-2">
      <Info className="w-3.5 h-3.5 text-muted-foreground shrink-0 mt-0.5" />
      <div className="flex-1 min-w-0">
        <span className="text-sm text-muted-foreground font-medium">{item.check}</span>
        {item.reason && (
          <span className="text-xs text-muted-foreground/70"> — {item.reason}</span>
        )}
      </div>
      <span className="shrink-0 text-xs text-muted-foreground/50 font-mono-text">N/A</span>
    </div>
  );
}

// ── Main component ─────────────────────────────────────────────────────
export default function ReadinessScorePanel({ isLocked, isAuditing, isComplete, readiness }) {
  const score      = readiness?.score ?? null;
  const band       = readiness?.score_band ?? readiness?.category ?? null;
  const penalties  = readiness?.penalties  ?? [];
  const naList     = readiness?.not_applicable ?? [];
  const explanation = readiness?.explanation ?? '';

  const totalDeducted = penalties.reduce((s, p) => s + (p.penalty ?? 0), 0);
  const style = band ? getBandStyle(band) : { badge: 'severity-moderate', bar: 'hsl(30,90%,40%)' };

  return (
    <Card
      data-testid="modeling-readiness-section"
      className={isLocked ? 'section-locked' : ''}
    >
      <CardHeader className="pb-3">
        <div className="flex items-start justify-between gap-4">
          <div className="space-y-1">
            <CardTitle className="font-heading text-base font-semibold flex items-center gap-2">
              <Gauge className="w-4 h-4 text-muted-foreground" />
              Modeling Readiness Score
            </CardTitle>
            <CardDescription className="text-xs">
              Rule-based score (0–100). Starts at 100 and subtracts penalties for detected issues.
            </CardDescription>
          </div>
          {isComplete && band && (
            <Badge
              className={`text-xs border shrink-0 ${style.badge}`}
              data-testid="readiness-category-badge"
            >
              {band}
            </Badge>
          )}
        </div>
      </CardHeader>
      <Separator />
      <CardContent className="pt-5">
        <div className="grid grid-cols-1 lg:grid-cols-5 gap-6">
          {/* Left: numeric score + progress */}
          <div className="lg:col-span-2 flex flex-col gap-4">
            <div>
              <p className="text-xs text-muted-foreground uppercase tracking-wide font-medium mb-2">Score</p>
              {isAuditing ? (
                <Skeleton className="h-16 w-28" />
              ) : (
                <p
                  className="font-heading font-semibold tabular-nums"
                  style={{
                    fontSize: '4rem',
                    lineHeight: 1,
                    color: isComplete && score !== null ? style.bar : 'hsl(215, 16%, 70%)',
                  }}
                  data-testid="modeling-readiness-score"
                >
                  {isComplete && score !== null ? score : '--'}
                </p>
              )}
              <p className="text-xs text-muted-foreground mt-1">out of 100</p>
            </div>

            {/* Score bar */}
            <div className="space-y-1.5">
              <div className="flex justify-between text-xs text-muted-foreground">
                <span>Score</span>
                <span className="tabular-nums font-medium">
                  {isComplete && score !== null ? `${score}/100` : '--'}
                </span>
              </div>
              <Progress
                value={isComplete ? (score ?? 0) : 0}
                className="h-2"
                data-testid="readiness-score-progress"
              />
            </div>

            {/* Score band thresholds reference */}
            {isComplete && (
              <div className="rounded-lg border border-border bg-muted/20 px-3 py-2.5">
                <p className="text-xs text-muted-foreground font-medium mb-1.5">Score bands</p>
                <div className="space-y-0.5">
                  {[
                    { label: 'Ready',                       range: '≥85' },
                    { label: 'Acceptable with preprocessing', range: '70–84' },
                    { label: 'Needs preprocessing',          range: '50–69' },
                    { label: 'High risk',                   range: '<50' },
                  ].map(({ label, range }) => (
                    <div key={label} className="flex justify-between text-xs">
                      <span className={band === label ? 'font-semibold text-foreground' : 'text-muted-foreground'}>
                        {label}
                      </span>
                      <span className="text-muted-foreground/60 font-mono-text">{range}</span>
                    </div>
                  ))}
                </div>
              </div>
            )}
          </div>

          {/* Right: explanation + penalties + not-applicable */}
          <div className="lg:col-span-3 space-y-4">
            {/* Explanation */}
            {isComplete && explanation ? (
              <div
                className="rounded-lg border border-border bg-muted/20 px-4 py-3"
                data-testid="modeling-readiness-explanation"
              >
                <p className="text-sm text-foreground leading-relaxed">{explanation}</p>
              </div>
            ) : !isComplete ? (
              <div className="rounded-lg border border-border bg-muted/20 px-4 py-3">
                <p className="text-sm text-muted-foreground">
                  The readiness score starts at 100 and deducts penalties for detected issues: 
                  missingness, duplicates, type anomalies, outliers, class imbalance, and leakage risk.
                  Every deduction is explained.
                </p>
              </div>
            ) : null}

            <Separator />

            {/* Penalty breakdown */}
            <div>
              <div className="flex items-center justify-between mb-2">
                <p className="text-xs text-muted-foreground uppercase tracking-wide font-medium">
                  Penalty breakdown
                </p>
                {isComplete && totalDeducted > 0 && (
                  <span className="text-xs text-muted-foreground font-mono-text">
                    Total deducted: −{totalDeducted}
                  </span>
                )}
              </div>

              {isAuditing ? (
                <div className="space-y-2">
                  {[...Array(3)].map((_, i) => <Skeleton key={i} className="h-10 w-full" />)}
                </div>
              ) : isComplete && penalties.length > 0 ? (
                <div className="space-y-1.5" data-testid="readiness-penalty-list">
                  {penalties.map((p, i) => <PenaltyRow key={i} penalty={p} />)}
                </div>
              ) : isComplete ? (
                <div className="flex items-center gap-2 rounded-md border border-[hsl(var(--success-border))] bg-[hsl(var(--success-bg))] px-3 py-2.5">
                  <CheckCircle2 className="w-4 h-4 text-[hsl(var(--success-fg))] shrink-0" />
                  <p className="text-sm text-[hsl(var(--success-fg))] font-medium">
                    No penalties applied — dataset is ready for modeling.
                  </p>
                </div>
              ) : (
                <div className="space-y-1.5" data-testid="readiness-penalty-list">
                  {['Missingness','Duplicates','Datatype anomalies','Outliers','Class imbalance','Leakage risk','Basic schema quality'].map(check => (
                    <div key={check} className="flex items-center justify-between rounded-md border border-border/50 bg-muted/20 px-3 py-2 opacity-40">
                      <span className="text-sm text-muted-foreground">{check}</span>
                      <span className="text-sm font-mono-text text-muted-foreground/50">—</span>
                    </div>
                  ))}
                </div>
              )}
            </div>

            {/* Not-applicable checks */}
            {isComplete && naList.length > 0 && (
              <div>
                <p className="text-xs text-muted-foreground uppercase tracking-wide font-medium mb-2">
                  Not-applicable checks
                </p>
                <div className="space-y-1">
                  {naList.map((item, i) => <NotApplicableRow key={i} item={item} />)}
                </div>
              </div>
            )}
          </div>
        </div>
      </CardContent>
    </Card>
  );
}
