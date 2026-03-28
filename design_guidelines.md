{
  "design_system_name": "Automated Dataset Reliability and Modeling Readiness Inspector — Minimal Data Tool UI",
  "product_goals": {
    "app_type": "single-page SaaS data tool",
    "target_audience": ["Data scientists", "ML engineers", "Data analysts"],
    "primary_user_tasks": [
      "Upload a CSV",
      "Confirm parsing succeeded (or understand parsing errors)",
      "Scan dataset preview",
      "Scan 6 audit summaries",
      "Read 6 detailed audit panels",
      "Understand modeling readiness score",
      "Download report after audit completes"
    ],
    "success_actions": [
      "User can upload a CSV and see a clear status",
      "User can quickly locate issues via summary cards",
      "User can read dense tables without visual noise",
      "User can download report only when audit is complete"
    ],
    "hard_constraints": [
      "No sidebar navigation",
      "No tabs",
      "No routing",
      "No charts",
      "No animations (avoid motion libraries; keep only minimal state transitions like focus/hover)",
      "Strictly vertical single-page layout",
      "Cards + sections (not tabs)",
      "Minimal color usage (status only)",
      "Use shadcn/ui components from /src/components/ui",
      "All interactive + key informational elements must include data-testid"
    ]
  },
  "visual_personality": {
    "keywords": [
      "quiet",
      "clinical",
      "information-dense",
      "pandas/Jupyter-like",
      "enterprise-neutral",
      "high-contrast typography",
      "structured panels"
    ],
    "inspiration_notes": [
      "Aim for a report-like flow similar to pandas profiling / ydata-profiling outputs: overview → table preview → module summaries → deep dives.",
      "Use bento-like metric cards but keep them flat and readable (no decorative gradients, no illustrations)."
    ]
  },
  "typography": {
    "font_pairing": {
      "heading": {
        "name": "Space Grotesk",
        "usage": "App title, section titles, card titles",
        "css": "font-heading"
      },
      "body": {
        "name": "Manrope",
        "usage": "Body text, helper text, labels",
        "css": "font-sans (default body)"
      },
      "mono": {
        "name": "System mono stack",
        "usage": "Column names, code-like values, file names, row/col counts",
        "css": "font-mono"
      }
    },
    "type_scale_tailwind": {
      "page_title_h1": "text-4xl sm:text-5xl lg:text-6xl font-heading font-semibold tracking-tight",
      "page_subtitle_h2": "text-base md:text-lg text-muted-foreground leading-relaxed",
      "section_title": "text-lg sm:text-xl font-heading font-semibold",
      "section_description": "text-sm text-muted-foreground",
      "table_text": "text-sm",
      "table_header": "text-xs uppercase tracking-wide text-muted-foreground",
      "metric_value": "text-2xl sm:text-3xl font-heading font-semibold tabular-nums",
      "metric_label": "text-xs text-muted-foreground",
      "helper": "text-xs text-muted-foreground"
    },
    "readability_rules": [
      "Prefer 65–80ch max width for long explanatory text blocks.",
      "Use tabular numbers for metrics and counts.",
      "Avoid center alignment for paragraphs; left-align all reading content."
    ]
  },
  "color_system": {
    "strategy": "Neutral base + semantic status colors only. No decorative gradients. Keep backgrounds light for long reading.",
    "tokens_css_variables": {
      "source_of_truth": "/app/frontend/src/index.css",
      "notes": [
        "Existing tokens already match the desired minimal data-tool aesthetic.",
        "Primary is a muted teal; use sparingly for focus rings, primary CTA, and subtle accents only."
      ],
      "core": {
        "--background": "210 33% 98%",
        "--foreground": "222 47% 11%",
        "--card": "0 0% 100%",
        "--muted": "210 25% 95%",
        "--muted-foreground": "215 16% 40%",
        "--border": "214 20% 88%",
        "--primary": "173 80% 28%",
        "--ring": "173 80% 28%"
      },
      "semantic_status": {
        "success": {
          "bg": "--success-bg",
          "fg": "--success-fg",
          "border": "--success-border"
        },
        "warning": {
          "bg": "--warning-bg",
          "fg": "--warning-fg",
          "border": "--warning-border"
        },
        "danger": {
          "bg": "--danger-bg",
          "fg": "--danger-fg",
          "border": "--danger-border"
        },
        "info": {
          "bg": "--info-bg",
          "fg": "--info-fg",
          "border": "--info-border"
        }
      }
    },
    "usage_rules": [
      "Default text uses foreground; secondary text uses muted-foreground.",
      "Borders are always subtle (border-border).",
      "Use semantic colors only for status chips/alerts and readiness category label.",
      "Do not introduce new decorative colors; keep the UI calm and report-like."
    ]
  },
  "layout_and_grid": {
    "page_container": {
      "outer": "min-h-screen bg-background",
      "inner": "mx-auto w-full max-w-6xl px-4 sm:px-6 lg:px-8",
      "vertical_rhythm": "space-y-6 sm:space-y-8",
      "section_padding": "py-6 sm:py-8"
    },
    "section_structure": {
      "pattern": "Each section is a Card with a CardHeader (title + description) and CardContent (dense content).",
      "section_header_row": "flex items-start justify-between gap-4",
      "section_title_block": "space-y-1"
    },
    "summary_cards_grid": {
      "grid": "grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-3 sm:gap-4",
      "card_density": "Compact cards; keep content to 2 metric rows + a status badge."
    },
    "detailed_panels_stack": {
      "stack": "space-y-4 sm:space-y-6",
      "panel": "Card with table-like content; avoid nested cards unless necessary."
    }
  },
  "components": {
    "component_path": {
      "button": "/app/frontend/src/components/ui/button.jsx",
      "card": "/app/frontend/src/components/ui/card.jsx",
      "input": "/app/frontend/src/components/ui/input.jsx",
      "label": "/app/frontend/src/components/ui/label.jsx",
      "table": "/app/frontend/src/components/ui/table.jsx",
      "badge": "/app/frontend/src/components/ui/badge.jsx",
      "separator": "/app/frontend/src/components/ui/separator.jsx",
      "alert": "/app/frontend/src/components/ui/alert.jsx",
      "progress": "/app/frontend/src/components/ui/progress.jsx",
      "skeleton": "/app/frontend/src/components/ui/skeleton.jsx",
      "scroll_area": "/app/frontend/src/components/ui/scroll-area.jsx",
      "tooltip": "/app/frontend/src/components/ui/tooltip.jsx",
      "sonner_toast": "/app/frontend/src/components/ui/sonner.jsx"
    },
    "page_sections_top_to_bottom": [
      {
        "id": "header",
        "title": "Header",
        "structure": "Plain header block (not a hero). Title + subtitle + small environment hint.",
        "recommended_markup": {
          "container": "div className=\"pt-10 pb-6\"",
          "title": "h1 className=\"text-4xl sm:text-5xl lg:text-6xl font-heading font-semibold tracking-tight\" data-testid=\"app-title\"",
          "subtitle": "p className=\"mt-3 text-base md:text-lg text-muted-foreground max-w-3xl\" data-testid=\"app-subtitle\"",
          "meta_row": "div className=\"mt-4 flex flex-wrap items-center gap-2 text-xs text-muted-foreground\""
        },
        "meta_row_items": [
          "Badge: 'Single-page audit' (variant secondary)",
          "Badge: 'CSV only'",
          "Badge: 'No data leaves browser until upload' (placeholder copy; adjust if untrue)"
        ]
      },
      {
        "id": "upload",
        "title": "CSV Upload Area",
        "shadcn": ["Card", "Input", "Label", "Button", "Alert", "Badge"],
        "layout": "Card with 2-column layout on desktop: left instructions, right upload control + status.",
        "tailwind": {
          "grid": "grid grid-cols-1 lg:grid-cols-5 gap-4",
          "left": "lg:col-span-3 space-y-2",
          "right": "lg:col-span-2 space-y-3"
        },
        "controls": [
          {
            "name": "file_input",
            "component": "Input type=\"file\" accept=\".csv,text/csv\"",
            "data_testid": "csv-upload-input",
            "notes": "Keep native file input for reliability; wrap with Label and helper text."
          },
          {
            "name": "run_audit_button",
            "component": "Button",
            "variant": "default",
            "data_testid": "run-audit-button",
            "state_rules": "Disabled until a file is selected and parsing succeeds."
          }
        ],
        "status_block": {
          "component": "Alert",
          "data_testid": "upload-status-alert",
          "states": {
            "empty": "Alert variant default: 'No file selected'",
            "parsing": "Alert variant default + inline Progress (indeterminate style via Progress value placeholder)",
            "error": "Alert variant destructive: show parsing error summary + next steps",
            "ready": "Alert styled with severity-low utility: 'Parsed successfully'"
          }
        }
      },
      {
        "id": "preview",
        "title": "Dataset Preview Table",
        "shadcn": ["Card", "Table", "ScrollArea", "Skeleton", "Badge"],
        "behavior": "In empty state, show a muted empty-state panel; in audit complete, show first N rows.",
        "table_wrapper": "Use .table-scroll-wrapper (already in App.css) or ScrollArea for max-height 400px.",
        "data_testids": {
          "section": "dataset-preview-section",
          "table": "dataset-preview-table",
          "empty": "dataset-preview-empty-state"
        },
        "table_density": {
          "header": "text-xs uppercase tracking-wide",
          "cells": "text-sm",
          "row": "hover:bg-muted/40 (optional; keep subtle)"
        }
      },
      {
        "id": "audit_summary",
        "title": "Audit Summary Cards (6)",
        "shadcn": ["Card", "Badge", "Separator"],
        "layout": "6 compact cards in a responsive grid (1→2→3 columns). Each card has: title, small status badge, two metric rows with placeholder '--'.",
        "grid": "grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-3 sm:gap-4",
        "card_template": {
          "header": "flex items-start justify-between gap-3",
          "title": "text-sm font-heading font-semibold",
          "badge": "Badge variant secondary OR semantic severity utility",
          "metrics": [
            "Row 1: label + value (tabular-nums)",
            "Row 2: label + value (tabular-nums)"
          ]
        },
        "cards": [
          { "key": "schema", "data_testid": "audit-summary-card-schema" },
          { "key": "missingness", "data_testid": "audit-summary-card-missingness" },
          { "key": "duplicates", "data_testid": "audit-summary-card-duplicates" },
          { "key": "outliers", "data_testid": "audit-summary-card-outliers" },
          { "key": "class-imbalance", "data_testid": "audit-summary-card-class-imbalance" },
          { "key": "leakage", "data_testid": "audit-summary-card-leakage" }
        ]
      },
      {
        "id": "audit_details",
        "title": "Detailed Audit Panels (6 stacked)",
        "shadcn": ["Card", "Table", "Badge", "Separator", "Tooltip"],
        "stack": "space-y-4 sm:space-y-6",
        "panel_pattern": {
          "header": "CardHeader with title + short description + right-aligned status badge",
          "content": "Dense table(s) + short bullet list of findings (placeholders).",
          "footer": "Optional: small helper text 'Generated at …' or 'Based on first N rows'"
        },
        "panels": [
          {
            "key": "schema",
            "title": "Schema Summary",
            "data_testid": "audit-panel-schema",
            "content_placeholders": [
              "Table: column name, inferred type, nullable, unique %, notes",
              "Inline note: 'Type coercions: --'"
            ]
          },
          {
            "key": "missingness",
            "title": "Missingness Analysis",
            "data_testid": "audit-panel-missingness",
            "content_placeholders": [
              "Table: column, missing count, missing %, suggested action",
              "Text block: 'Overall missingness: --'"
            ]
          },
          {
            "key": "duplicates",
            "title": "Duplicate Analysis",
            "data_testid": "audit-panel-duplicates",
            "content_placeholders": [
              "Table: duplicate rows, duplicate %, candidate keys (placeholder)",
              "Text block: 'Potential primary key: --'"
            ]
          },
          {
            "key": "outliers",
            "title": "Numeric Outlier Analysis",
            "data_testid": "audit-panel-outliers",
            "content_placeholders": [
              "Table: numeric column, method, outlier count, outlier %, notes",
              "Text block: 'Method: IQR/Z-score (placeholder)'"
            ]
          },
          {
            "key": "class_imbalance",
            "title": "Class Imbalance",
            "data_testid": "audit-panel-class-imbalance",
            "content_placeholders": [
              "Table: target column, top class %, minority class %, imbalance ratio",
              "Text block: 'Suggested resampling: --'"
            ]
          },
          {
            "key": "leakage",
            "title": "Leakage Risk",
            "data_testid": "audit-panel-leakage",
            "content_placeholders": [
              "Table: suspicious column, reason, severity",
              "Text block: 'Potential leakage signals: --'"
            ]
          }
        ]
      },
      {
        "id": "readiness_score",
        "title": "Modeling Readiness Score",
        "shadcn": ["Card", "Badge", "Separator"],
        "layout": "A single prominent card with a large score on the left and explanation on the right (stacks on mobile).",
        "tailwind": {
          "grid": "grid grid-cols-1 md:grid-cols-5 gap-4",
          "score_col": "md:col-span-2",
          "text_col": "md:col-span-3"
        },
        "score_display": {
          "value": "Large numeric (placeholder '--') with tabular nums",
          "label": "Badge for category: 'Ready'/'Needs Review'/'Not Ready' (semantic colors)",
          "data_testids": {
            "score": "modeling-readiness-score",
            "category": "modeling-readiness-category",
            "explanation": "modeling-readiness-explanation"
          }
        },
        "copy_rules": [
          "Keep explanation short (2–4 lines).",
          "Use bullet list for 'Top blockers' (placeholders)."
        ]
      },
      {
        "id": "download",
        "title": "Download Report",
        "shadcn": ["Button", "Card"],
        "layout": "Full-width primary button inside a Card footer-like area.",
        "button": {
          "text": "Download report",
          "variant": "default",
          "className": "w-full btn-press",
          "data_testid": "download-report-button",
          "state_rules": "Disabled until audit completes. When disabled, show helper text above: 'Run an audit to enable downloads.'"
        }
      }
    ],
    "state_management_ui": {
      "three_states": {
        "empty": {
          "rules": [
            "Show upload section.",
            "Preview + audit sections should be visually disabled: either hidden OR shown as muted skeleton blocks.",
            "Download button disabled."
          ],
          "recommended": "Prefer showing sections but in a muted 'locked' state to communicate what will appear after upload."
        },
        "parsing_error": {
          "rules": [
            "Show destructive Alert in upload section with error summary.",
            "Keep preview hidden or show empty state.",
            "Keep audit sections disabled.",
            "Download disabled."
          ]
        },
        "audit_complete": {
          "rules": [
            "All sections visible.",
            "Summary cards populated.",
            "Detailed panels populated.",
            "Download enabled."
          ]
        }
      }
    }
  },
  "interaction_design": {
    "principle": "No animations. Only essential interaction feedback: hover, focus, pressed, disabled.",
    "allowed_micro_interactions": [
      "Button pressed scale (already in App.css: .btn-press:active { transform: scale(0.98); })",
      "Input focus ring (ring token)",
      "Table row hover background (very subtle)",
      "Sticky table header for preview (already in App.css: .audit-table thead th)"
    ],
    "disallowed": [
      "Framer Motion",
      "Entrance animations",
      "Parallax",
      "Charts/graphs",
      "Auto-advancing carousels"
    ],
    "css_rules": [
      "Do not use transition: all.",
      "If adding transitions, scope them to border-color/background-color/opacity only."
    ]
  },
  "accessibility": {
    "requirements": [
      "All form controls have associated Label.",
      "Focus states must be visible (ring).",
      "Use semantic table markup (TableHead/TableRow/TableCell).",
      "Error messages must be programmatically associated with the upload input (aria-describedby).",
      "Color is never the only indicator: include text labels like 'Error', 'Warning', 'OK'."
    ],
    "keyboard": [
      "Upload input reachable by tab.",
      "Buttons reachable by tab.",
      "If using Tooltip, ensure it is keyboard accessible (Radix)."
    ]
  },
  "data_testid_conventions": {
    "format": "kebab-case describing role",
    "examples": [
      "csv-upload-input",
      "run-audit-button",
      "upload-status-alert",
      "dataset-preview-table",
      "audit-summary-card-missingness",
      "audit-panel-leakage",
      "modeling-readiness-score",
      "download-report-button",
      "parsing-error-message"
    ],
    "coverage_rule": "Apply data-testid to: all buttons, inputs, alerts, key metric values, section containers, and empty/error state messages."
  },
  "images_and_illustrations": {
    "policy": "No decorative images. This is a data tool; keep it text/table-first.",
    "image_urls": []
  },
  "libraries": {
    "required": [],
    "explicitly_not_used": [
      "recharts",
      "d3",
      "three.js",
      "react-three-fiber",
      "lottie",
      "framer-motion"
    ],
    "notes": "Constraints explicitly forbid charts and animations; keep dependencies minimal."
  },
  "implementation_notes_for_main_agent": {
    "instructions_to_main_agent": [
      "Keep the entire app as a single vertical page; no sidebar/TOC/tabs.",
      "Use shadcn components from /app/frontend/src/components/ui (JSX files).",
      "Use Cards for every major section; consistent CardHeader/CardContent structure.",
      "Use the existing CSS tokens in index.css; do not introduce new palette unless necessary.",
      "Remove/avoid any existing sidebar-related CSS usage (e.g., .toc-sidebar) in the UI scaffold.",
      "Avoid hover-elevation 'panel-card:hover' if it reads as decorative; if used, keep extremely subtle or remove.",
      "Ensure empty/parsing/error/audit-complete states are clearly represented with Alerts + muted placeholders.",
      "All interactive and key informational elements must include data-testid attributes (kebab-case).",
      "No animations: do not add motion libs; keep only focus/hover/pressed feedback."
    ],
    "suggested_section_order": [
      "Header",
      "CSV Upload",
      "Dataset Preview",
      "Audit Summary Cards",
      "Detailed Audit Panels (6)",
      "Modeling Readiness Score",
      "Download Report"
    ]
  },
  "general_ui_ux_design_guidelines_appendix": "<General UI UX Design Guidelines>  \n    - You must **not** apply universal transition. Eg: `transition: all`. This results in breaking transforms. Always add transitions for specific interactive elements like button, input excluding transforms\n    - You must **not** center align the app container, ie do not add `.App { text-align: center; }` in the css file. This disrupts the human natural reading flow of text\n   - NEVER: use AI assistant Emoji characters like`🤖🧠💭💡🔮🎯📚🎭🎬🎪🎉🎊🎁🎀🎂🍰🎈🎨🎰💰💵💳🏦💎🪙💸🤑📊📈📉💹🔢🏆🥇 etc for icons. Always use **FontAwesome cdn** or **lucid-react** library already installed in the package.json\n\n **GRADIENT RESTRICTION RULE**\nNEVER use dark/saturated gradient combos (e.g., purple/pink) on any UI element.  Prohibited gradients: blue-500 to purple 600, purple 500 to pink-500, green-500 to blue-500, red to pink etc\nNEVER use dark gradients for logo, testimonial, footer etc\nNEVER let gradients cover more than 20% of the viewport.\nNEVER apply gradients to text-heavy content or reading areas.\nNEVER use gradients on small UI elements (<100px width).\nNEVER stack multiple gradient layers in the same viewport.\n\n**ENFORCEMENT RULE:**\n    • Id gradient area exceeds 20% of viewport OR affects readability, **THEN** use solid colors\n\n**How and where to use:**\n   • Section backgrounds (not content backgrounds)\n   • Hero section header content. Eg: dark to light to dark color\n   • Decorative overlays and accent elements only\n   • Hero section with 2-3 mild color\n   • Gradients creation can be done for any angle say horizontal, vertical or diagonal\n\n- For AI chat, voice application, **do not use purple color. Use color like light green, ocean blue, peach orange etc**\n\n</Font Guidelines>\n\n- Every interaction needs micro-animations - hover states, transitions, parallax effects, and entrance animations. Static = dead. \n   \n- Use 2-3x more spacing than feels comfortable. Cramped designs look cheap.\n\n- Subtle grain textures, noise overlays, custom cursors, selection states, and loading animations: separates good from extraordinary.\n   \n- Before generating UI, infer the visual style from the problem statement (palette, contrast, mood, motion) and immediately instantiate it by setting global design tokens (primary, secondary/accent, background, foreground, ring, state colors), rather than relying on any library defaults. Don't make the background dark as a default step, always understand problem first and define colors accordingly\n    Eg: - if it implies playful/energetic, choose a colorful scheme\n           - if it implies monochrome/minimal, choose a black–white/neutral scheme\n\n**Component Reuse:**\n\t- Prioritize using pre-existing components from src/components/ui when applicable\n\t- Create new components that match the style and conventions of existing components when needed\n\t- Examine existing components to understand the project's component patterns before creating new ones\n\n**IMPORTANT**: Do not use HTML based component like dropdown, calendar, toast etc. You **MUST** always use `/app/frontend/src/components/ui/ ` only as a primary components as these are modern and stylish component\n\n**Best Practices:**\n\t- Use Shadcn/UI as the primary component library for consistency and accessibility\n\t- Import path: ./components/[component-name]\n\n**Export Conventions:**\n\t- Components MUST use named exports (export const ComponentName = ...)\n\t- Pages MUST use default exports (export default function PageName() {...})\n\n**Toasts:**\n  - Use `sonner` for toasts\"\n  - Sonner component are located in `/app/src/components/ui/sonner.tsx`\n\nUse 2–4 color gradients, subtle textures/noise overlays, or CSS-based noise to avoid flat visuals.\n</General UI UX Design Guidelines>"
}
