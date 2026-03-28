import React from 'react';
import { Badge } from './ui/badge';
import { Separator } from './ui/separator';

export default function AppHeader() {
  return (
    <header className="pt-10 pb-8">
      <div>
        <h1
          className="font-heading font-semibold tracking-tight text-3xl sm:text-4xl text-foreground"
          data-testid="app-title"
        >
          Automated Dataset Reliability and Modeling Readiness Inspector
        </h1>
        <p
          className="mt-3 text-base text-muted-foreground max-w-3xl leading-relaxed"
          data-testid="app-subtitle"
        >
          Upload a CSV dataset to receive a structured audit report covering schema validity, missingness, duplicates, numeric outliers, class imbalance, leakage risk, and overall modeling readiness.
        </p>
        <div className="mt-4 flex flex-wrap items-center gap-2">
          <Badge variant="secondary" className="text-xs font-medium">Single-page audit</Badge>
          <Badge variant="secondary" className="text-xs font-medium">CSV only</Badge>
          <Badge variant="secondary" className="text-xs font-medium">Rule-based checks</Badge>
          <Badge variant="secondary" className="text-xs font-medium">No model training</Badge>
        </div>
      </div>
      <Separator className="mt-8" />
    </header>
  );
}
