import os

css_content = """
@import url('https://fonts.googleapis.com/css2?family=Outfit:wght@300;400;500;600;700;800&family=Space+Grotesk:wght@400;500;700&family=JetBrains+Mono:ital,wght@0,400;0,700;1,400&display=swap');

:root {
  --bg-color: #f8fafc;
  --panel-bg: rgba(255, 255, 255, 0.85);
  --panel-hover: rgba(255, 255, 255, 1);
  --panel-border: rgba(15, 23, 42, 0.08);
  --panel-border-hover: rgba(15, 23, 42, 0.15);
  
  --primary: #4f46e5;
  --primary-hover: #4338ca;
  --primary-glow: rgba(79, 70, 229, 0.3);
  
  --accent-1: #db2777;
  --accent-1-glow: rgba(219, 39, 119, 0.3);
  --accent-2: #7c3aed;
  --accent-2-glow: rgba(124, 58, 237, 0.3);
  --accent-3: #059669;
  
  --text-main: #0f172a;
  --text-dim: #475569;
  --text-muted: #64748b;
  
  --success: #059669;
  --success-bg: rgba(5, 150, 105, 0.1);
  --success-border: rgba(5, 150, 105, 0.2);
  
  --error: #dc2626;
  --error-bg: rgba(220, 38, 38, 0.1);
  --error-border: rgba(220, 38, 38, 0.2);

  --font-sans: 'Outfit', -apple-system, sans-serif;
  --font-display: 'Space Grotesk', -apple-system, sans-serif;
  --font-mono: 'JetBrains Mono', monospace;

  --shadow-sm: 0 2px 4px rgba(15, 23, 42, 0.05);
  --shadow-md: 0 10px 25px rgba(15, 23, 42, 0.08);
  --shadow-lg: 0 20px 40px rgba(15, 23, 42, 0.1);
  --shadow-glow: 0 0 30px var(--primary-glow);
  
  --radius-sm: 8px;
  --radius-md: 16px;
  --radius-lg: 24px;
  --radius-xl: 32px;
  --radius-full: 9999px;
  
  --transition-fast: 150ms cubic-bezier(0.4, 0, 0.2, 1);
  --transition-base: 300ms cubic-bezier(0.4, 0, 0.2, 1);
  --transition-smooth: 500ms cubic-bezier(0.2, 0.8, 0.2, 1);
}

/* Global Reset & Base */
*, *::before, *::after { box-sizing: border-box; }
html { scroll-behavior: smooth; }
body {
  margin: 0;
  padding: 0;
  font-family: var(--font-sans);
  background-color: var(--bg-color);
  color: var(--text-main);
  line-height: 1.6;
  min-height: 100vh;
  overflow-x: hidden;
  position: relative;
  -webkit-font-smoothing: antialiased;
  -moz-osx-font-smoothing: grayscale;
}

/* Dynamic Background Glows */
body::before, body::after {
  content: '';
  position: fixed;
  border-radius: 50%;
  filter: blur(140px);
  z-index: -1;
  animation: float 20s infinite ease-in-out alternate;
  opacity: 0.4;
  pointer-events: none;
}
body::before {
  top: -10%; left: -10%; width: 50vw; height: 50vw;
  background: radial-gradient(circle, var(--accent-2-glow), transparent 70%);
}
body::after {
  bottom: -10%; right: -10%; width: 40vw; height: 40vw;
  background: radial-gradient(circle, var(--accent-1-glow), transparent 70%);
  animation-delay: -10s;
}

@keyframes float {
  0% { transform: translate(0, 0) scale(1); }
  50% { transform: translate(5%, 10%) scale(1.1); }
  100% { transform: translate(-5%, 5%) scale(0.9); }
}

@keyframes fadeInUp {
  from { opacity: 0; transform: translateY(20px); }
  to { opacity: 1; transform: translateY(0); }
}

@keyframes slideIn {
  from { opacity: 0; transform: translateX(-20px); }
  to { opacity: 1; transform: translateX(0); }
}

/* Typography elements */
h1, h2, h3, h4, h5, h6 {
  font-family: var(--font-display);
  font-weight: 700;
  line-height: 1.2;
  margin: 0;
  letter-spacing: -0.02em;
  color: var(--text-main);
}

a { color: var(--primary); text-decoration: none; transition: all var(--transition-base); }
a:hover { color: var(--primary-hover); text-shadow: 0 0 8px var(--primary-glow); }
p { margin: 0; }
strong { color: var(--text-main); font-weight: 700; }

button {
  font-family: var(--font-sans);
  cursor: pointer;
  border: none;
  background: transparent;
  color: inherit;
  padding: 0;
}

input, select, textarea {
  font-family: var(--font-sans);
  background: rgba(255, 255, 255, 0.8);
  border: 1px solid var(--panel-border);
  color: var(--text-main);
  padding: 12px 16px;
  border-radius: var(--radius-md);
  transition: all var(--transition-base);
  width: 100%;
}
input:focus, select:focus, textarea:focus {
  outline: none;
  border-color: var(--primary);
  background: #ffffff;
  box-shadow: 0 0 0 3px rgba(79, 70, 229, 0.2);
}
input::placeholder { color: var(--text-muted); }

/* Common Glassmorphism Panels */
.glass-panel {
  background: var(--panel-bg);
  backdrop-filter: blur(20px);
  -webkit-backdrop-filter: blur(20px);
  border: 1px solid var(--panel-border);
  border-radius: var(--radius-lg);
  box-shadow: var(--shadow-md);
  transition: all var(--transition-base);
}

/* Typography styles */
.eyebrow, .card-kicker, .hero-badge, .page-hero-badge {
  font-family: var(--font-mono);
  font-size: 0.75rem;
  text-transform: uppercase;
  letter-spacing: 0.1em;
  color: var(--primary);
  background: rgba(79, 70, 229, 0.1);
  padding: 4px 12px;
  border-radius: var(--radius-full);
  display: inline-flex;
  align-items: center;
  border: 1px solid rgba(79, 70, 229, 0.2);
}

/* --- Auth Shell --- */
.auth-shell {
  min-height: 100vh;
  display: grid;
  grid-template-columns: 1.2fr 0.8fr;
  gap: 2rem;
  padding: 2rem;
  animation: fadeInUp 0.8s ease-out forwards;
}

.auth-hero {
  position: relative;
  border-radius: var(--radius-xl);
  padding: 4rem;
  display: flex;
  flex-direction: column;
  justify-content: center;
  overflow: hidden;
  background: linear-gradient(135deg, rgba(255,255,255,0.7), rgba(248,250,252,0.8));
  box-shadow: inset 0 0 100px rgba(255,255,255,0.8);
  border: 1px solid var(--panel-border);
}
.auth-hero::before {
  content: '';
  position: absolute;
  inset: 0;
  background: linear-gradient(to top right, var(--primary-glow), transparent);
  mix-blend-mode: overlay;
}

.auth-hero h1 {
  font-size: clamp(3rem, 5vw, 4.5rem);
  margin-top: 1.5rem;
  background: linear-gradient(to right, var(--primary), var(--accent-1));
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
  position: relative;
  z-index: 1;
}

.hero-copy {
  font-size: 1.25rem;
  color: var(--text-dim);
  margin-top: 1.5rem;
  max-width: 80%;
  position: relative;
  z-index: 1;
}

.hero-signal-grid {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 1.5rem;
  margin-top: 4rem;
  position: relative;
  z-index: 1;
}

.hero-signal-card {
  background: rgba(255, 255, 255, 0.7);
  border: 1px solid var(--panel-border);
  padding: 1.5rem;
  border-radius: var(--radius-lg);
  backdrop-filter: blur(10px);
  transition: all var(--transition-base);
  box-shadow: var(--shadow-sm);
}

.hero-signal-card strong {
  font-size: 2.5rem;
  font-family: var(--font-display);
  background: linear-gradient(to right, var(--primary), var(--accent-1));
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
  display: block;
}

.hero-signal-card span {
  font-size: 0.875rem;
  color: var(--text-dim);
  margin-top: 0.5rem;
  display: block;
  text-transform: uppercase;
  letter-spacing: 0.05em;
  font-weight: 600;
}

.auth-panel {
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 2rem;
}

.auth-card {
  width: 100%;
  max-width: 480px;
  background: rgba(255, 255, 255, 0.9);
  backdrop-filter: blur(30px);
  border: 1px solid var(--panel-border);
  padding: 3rem;
  border-radius: var(--radius-xl);
  box-shadow: var(--shadow-lg), 0 0 40px rgba(79, 70, 229, 0.05);
}

.mode-switch {
  display: flex;
  background: rgba(15, 23, 42, 0.05);
  border-radius: var(--radius-full);
  padding: 4px;
  margin-bottom: 2rem;
  border: 1px solid var(--panel-border);
}

.mode-switch button {
  flex: 1;
  padding: 0.75rem;
  border-radius: var(--radius-full);
  font-weight: 600;
  color: var(--text-muted);
  transition: all var(--transition-base);
}

.mode-switch button.active {
  background: var(--primary);
  color: #fff;
  box-shadow: 0 4px 15px var(--primary-glow);
}

.auth-submit, button.primary {
  width: 100%;
  padding: 1rem;
  background: linear-gradient(135deg, var(--primary), var(--accent-2));
  color: #fff;
  font-weight: 700;
  font-size: 1rem;
  border-radius: var(--radius-md);
  box-shadow: 0 4px 15px var(--primary-glow);
}

/* --- Workspace Shell --- */
.workspace-shell {
  display: grid;
  grid-template-columns: 280px 1fr;
  min-height: 100vh;
  padding: 1.5rem;
  gap: 1.5rem;
  max-width: 1800px;
  margin: 0 auto;
}

/* Sidebar */
.workspace-sidebar {
  background: var(--panel-bg);
  backdrop-filter: blur(20px);
  border: 1px solid var(--panel-border);
  border-radius: var(--radius-xl);
  padding: 1.5rem;
  display: flex;
  flex-direction: column;
  height: calc(100vh - 3rem);
  position: sticky;
  top: 1.5rem;
  overflow-y: auto;
  box-shadow: var(--shadow-sm);
}

.workspace-brand-mark {
  width: 48px;
  height: 48px;
  background: linear-gradient(135deg, var(--primary), var(--accent-1));
  border-radius: var(--radius-md);
  display: flex;
  align-items: center;
  justify-content: center;
  font-family: var(--font-display);
  font-weight: 800;
  font-size: 1.25rem;
  color: #fff;
  box-shadow: 0 0 15px var(--primary-glow);
}

.workspace-brand p { font-size: 0.75rem; text-transform: uppercase; letter-spacing: 0.1em; color: var(--text-muted); margin-bottom: 0.25rem; }
.workspace-brand strong { font-family: var(--font-display); font-size: 1.1rem; color: var(--text-main); line-height: 1.2; }
.workspace-user-card { background: rgba(15,23,42,0.03); border: 1px solid var(--panel-border); padding: 1rem; border-radius: var(--radius-lg); margin-bottom: 2rem; }
.workspace-user-card strong { display: block; font-size: 1.1rem; margin-top: 0.25rem; color: var(--text-main); }
.workspace-user-card span { display: block; font-size: 0.875rem; color: var(--text-dim); }

.workspace-nav-link {
  display: flex;
  flex-direction: column;
  padding: 1rem;
  border-radius: var(--radius-md);
  text-align: left;
  transition: all var(--transition-base);
  border: 1px solid transparent;
}
.workspace-nav-link strong { font-size: 1rem; color: var(--text-main); margin-bottom: 0.25rem; }
.workspace-nav-link span { font-size: 0.8rem; color: var(--text-muted); }
.workspace-nav-link:hover { background: rgba(15, 23, 42, 0.03); margin-left: 5px; }
.workspace-nav-link.active {
  background: linear-gradient(90deg, rgba(79, 70, 229, 0.08), transparent);
  border-left: 3px solid var(--primary);
  border-radius: 0 var(--radius-md) var(--radius-md) 0;
}
.workspace-nav-link.active strong { color: var(--primary); }

.sidebar-brief {
  margin-top: auto;
  background: linear-gradient(135deg, rgba(255,255,255,0.9), rgba(248,250,252,0.9));
  border: 1px solid var(--panel-border);
  padding: 1.5rem;
  border-radius: var(--radius-lg);
  margin-bottom: 1.5rem;
  box-shadow: var(--shadow-sm);
}

/* Workspace Main */
.workspace-main {
  display: flex;
  flex-direction: column;
  gap: 2rem;
  animation: slideIn 0.5s ease-out forwards;
}

.page-hero {
  position: relative;
  background: linear-gradient(135deg, rgba(255,255,255,0.95), rgba(241,245,249,0.95));
  backdrop-filter: blur(20px);
  border: 1px solid var(--panel-border);
  border-radius: var(--radius-xl);
  padding: 3rem;
  display: flex;
  justify-content: space-between;
  align-items: center;
  overflow: hidden;
  box-shadow: var(--shadow-md);
}

.page-hero h1 {
  font-size: 3rem;
  margin: 1rem 0;
  color: var(--text-main);
  background: none;
  -webkit-text-fill-color: initial;
}

.page-hero-glance {
  background: rgba(255, 255, 255, 0.9);
  border: 1px solid var(--panel-border);
  padding: 1.5rem;
  border-radius: var(--radius-lg);
  text-align: right;
  backdrop-filter: blur(10px);
  box-shadow: var(--shadow-sm);
}
.page-hero-glance span { display: block; font-size: 0.875rem; color: var(--text-muted); text-transform: uppercase; letter-spacing: 0.05em; }
.page-hero-glance strong { display: block; font-size: 1.5rem; color: var(--text-main); margin-top: 0.5rem; font-family: var(--font-display); }

/* Metric Ribbon */
.metric-ribbon {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: 1.5rem;
}

.metric-ribbon-item {
  background: var(--panel-bg);
  border: 1px solid var(--panel-border);
  border-radius: var(--radius-lg);
  padding: 1.5rem;
  transition: all var(--transition-base);
  box-shadow: var(--shadow-sm);
}
.metric-ribbon-item:hover {
  transform: translateY(-5px);
  box-shadow: var(--shadow-md);
  border-color: rgba(79, 70, 229, 0.3);
}
.metric-ribbon-item span { font-size: 0.875rem; color: var(--text-dim); text-transform: uppercase; letter-spacing: 0.05em; }
.metric-ribbon-item strong {
  display: block; font-size: 2.25rem; font-family: var(--font-display); color: var(--text-main); margin: 0.5rem 0;
}

/* Page Sections & Stage Panel */
.page-section {  display: grid; gap: 1.5rem; }
.stage-grid { display: grid; grid-template-columns: 2fr 1fr; gap: 1.5rem; }

.stage-panel, .card, .chart-card, .chart-card-wide, .ledger-card, .signal-card, .spotlight-card, .timeline-card, .tool-panel, .sales-feed-card {
  background: var(--panel-bg);
  backdrop-filter: blur(20px);
  border: 1px solid var(--panel-border);
  border-radius: var(--radius-xl);
  padding: 2rem;
  transition: all var(--transition-base);
  box-shadow: var(--shadow-sm);
}
.stage-panel:hover, .card:hover, .tool-panel:hover {
  box-shadow: var(--shadow-md);
}

/* FIXING SPACING ISSUE FOR .run-list & .run-item */
.run-list {
  display: flex;
  flex-direction: column;
  gap: 1rem;
}

.run-item {
  background: #ffffff;
  padding: 1.25rem;
  border-radius: var(--radius-md);
  border-left: 4px solid var(--primary);
  display: flex;
  align-items: center;
  justify-content: space-between;
  box-shadow: var(--shadow-sm);
  border-top: 1px solid var(--panel-border);
  border-right: 1px solid var(--panel-border);
  border-bottom: 1px solid var(--panel-border);
}

/* THIS ensures strong and span flow nicely as a column instead of touching */
.run-item > div:first-child {
  display: flex;
  flex-direction: column;
  gap: 0.35rem;
}

.run-item.success { border-left-color: var(--success); }
.run-item.error { border-left-color: var(--error); }

.run-item span, .run-item span.subtle-span { font-size: 0.85rem; color: var(--text-muted); }
.run-item strong { font-size: 1.05rem; color: var(--text-main); }

.status-pill {
  padding: 0.35rem 0.85rem;
  border-radius: var(--radius-full);
  font-size: 0.75rem !important;
  font-weight: 700;
  text-transform: uppercase;
}
.status-pill-completed, .status-pill-success {
  background: var(--success-bg);
  color: var(--success) !important;
  border: 1px solid var(--success-border);
}

/* Tables and Records */
.table-wrap {
  overflow-x: auto;
  border-radius: var(--radius-lg);
  border: 1px solid var(--panel-border);
  background: #ffffff;
}
table { width: 100%; border-collapse: collapse; text-align: left; }
th, td { padding: 1.25rem 1.5rem; border-bottom: 1px solid var(--panel-border); }
th {
  font-size: 0.875rem;
  color: var(--text-dim);
  text-transform: uppercase;
  letter-spacing: 0.05em;
  background: rgba(248, 250, 252, 1);
  font-weight: 600;
}
td { color: var(--text-main); font-size: 0.95rem; font-weight: 500; }
tr:last-child td { border-bottom: none; }
tr:hover td { background: rgba(241, 245, 249, 0.8); }

/* Interactive tooltips styling (recharts tooltip override for light theme) */
.recharts-tooltip-wrapper .recharts-default-tooltip {
  background-color: rgba(255, 255, 255, 0.95) !important;
  border: 1px solid var(--panel-border) !important;
  border-radius: var(--radius-md) !important;
  box-shadow: var(--shadow-md) !important;
  color: var(--text-main) !important;
}

/* Form Grid */
.form-grid { display: grid; grid-template-columns: repeat(2, 1fr); gap: 1.5rem; }
.form-grid .field { margin-bottom: 0; }

/* Dashboard spacing fixes */
.highlight-metrics { display: flex; gap: 2rem; margin-top: 1rem; }
.highlight-metrics div {
  background: #ffffff;
  padding: 1rem 1.5rem;
  border-radius: var(--radius-md);
  border: 1px solid var(--panel-border);
}
.highlight-metrics span { font-size: 0.75rem; color: var(--text-dim); text-transform: uppercase; display: block; }
.highlight-metrics strong { font-size: 1.25rem; font-family: var(--font-mono); color: var(--text-main); display: block; margin-top: 0.5rem; }

button.secondary {
  background: #ffffff;
  border: 1px solid var(--panel-border);
  color: var(--text-main);
  padding: 0.75rem 1.5rem;
  border-radius: var(--radius-md);
  transition: all var(--transition-base);
  font-weight: 600;
}
button.secondary:hover {
  background: rgba(241, 245, 249, 1);
  box-shadow: var(--shadow-sm);
}

.notice { padding: 1rem; border-radius: var(--radius-md); font-size: 0.875rem; display: flex; align-items: center; gap: 0.75rem; margin-top: 1.5rem; animation: slideIn 0.3s ease-out forwards; }
.notice-success { background: var(--success-bg); border: 1px solid var(--success-border); color: #059669; }
.notice-error { background: var(--error-bg); border: 1px solid var(--error-border); color: #dc2626; }

.subtle-copy { color: var(--text-muted); font-size: 0.9rem; font-style: italic; }

/* Dashboard layout grid adjustments */
.analytics-feature-grid { display: grid; grid-template-columns: repeat(3, 1fr); gap: 1.5rem; }
.tool-grid { display: grid; grid-template-columns: 1fr 1fr; gap: 1.5rem; }

.sidebar-brief-list { display: flex; flex-direction: column; gap: 1rem; }
.sidebar-brief-list div {
  display: flex; justify-content: space-between; align-items: center;
  padding: 1rem; background: rgba(15,23,42,0.03); border-radius: var(--radius-md);
}
.sidebar-brief-list span { color: var(--text-dim); font-size: 0.875rem; }
.sidebar-brief-list strong { color: var(--text-main); font-weight: 700; }
"""
with open("frontend/src/styles.css", "w") as f:
    f.write(css_content)

print("Light Theme applied.")
