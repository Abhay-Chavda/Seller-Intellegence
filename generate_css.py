import os

css_content = """
@import url('https://fonts.googleapis.com/css2?family=Outfit:wght@300;400;500;600;700;800&family=Space+Grotesk:wght@400;500;700&family=JetBrains+Mono:ital,wght@0,400;0,700;1,400&display=swap');

:root {
  --bg-color: #03040b;
  --panel-bg: rgba(14, 16, 25, 0.6);
  --panel-hover: rgba(22, 25, 38, 0.7);
  --panel-border: rgba(255, 255, 255, 0.05);
  --panel-border-hover: rgba(255, 255, 255, 0.15);
  
  --primary: #6366f1;
  --primary-hover: #4f46e5;
  --primary-glow: rgba(99, 102, 241, 0.4);
  
  --accent-1: #ec4899;
  --accent-1-glow: rgba(236, 72, 153, 0.4);
  --accent-2: #8b5cf6;
  --accent-2-glow: rgba(139, 92, 246, 0.4);
  --accent-3: #10b981;
  
  --text-main: #f8fafc;
  --text-dim: #94a3b8;
  --text-muted: #64748b;
  
  --success: #10b981;
  --success-bg: rgba(16, 185, 129, 0.1);
  --success-border: rgba(16, 185, 129, 0.2);
  
  --error: #ef4444;
  --error-bg: rgba(239, 68, 68, 0.1);
  --error-border: rgba(239, 68, 68, 0.2);

  --font-sans: 'Outfit', -apple-system, sans-serif;
  --font-display: 'Space Grotesk', -apple-system, sans-serif;
  --font-mono: 'JetBrains Mono', monospace;

  --shadow-sm: 0 4px 6px -1px rgba(0, 0, 0, 0.3);
  --shadow-md: 0 10px 15px -3px rgba(0, 0, 0, 0.4);
  --shadow-lg: 0 20px 25px -5px rgba(0, 0, 0, 0.5), 0 8px 10px -6px rgba(0, 0, 0, 0.5);
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
  filter: blur(120px);
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

@keyframes pulseGlow {
  0% { box-shadow: 0 0 10px var(--primary-glow); }
  50% { box-shadow: 0 0 25px var(--primary-glow); }
  100% { box-shadow: 0 0 10px var(--primary-glow); }
}

@keyframes shimmer {
  0% { background-position: 200% center; }
  100% { background-position: -200% center; }
}

/* Typography elements */
h1, h2, h3, h4, h5, h6 {
  font-family: var(--font-display);
  font-weight: 700;
  line-height: 1.2;
  margin: 0;
  letter-spacing: -0.02em;
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
  background: rgba(0, 0, 0, 0.2);
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
  background: rgba(0, 0, 0, 0.4);
  box-shadow: 0 0 0 3px rgba(99, 102, 241, 0.2);
}
input::placeholder { color: var(--text-muted); }

/* Common Glassmorphism Panels */
.glass-panel {
  background: var(--panel-bg);
  backdrop-filter: blur(20px);
  -webkit-backdrop-filter: blur(20px);
  border: 1px solid var(--panel-border);
  border-radius: var(--radius-lg);
  box-shadow: var(--shadow-lg);
  transition: all var(--transition-base);
}
.glass-panel:hover {
  background: var(--panel-hover);
  border-color: var(--panel-border-hover);
  transform: translateY(-2px);
}

/* Typography styles */
.eyebrow, .card-kicker, .hero-badge, .page-hero-badge {
  font-family: var(--font-mono);
  font-size: 0.75rem;
  text-transform: uppercase;
  letter-spacing: 0.1em;
  color: var(--primary);
  background: rgba(99, 102, 241, 0.1);
  padding: 4px 12px;
  border-radius: var(--radius-full);
  display: inline-flex;
  align-items: center;
  border: 1px solid rgba(99, 102, 241, 0.2);
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
  background: linear-gradient(135deg, rgba(20,20,30,0.8), rgba(10,12,20,0.9)), url('https://images.unsplash.com/photo-1618005182384-a83a8bd57fbe?q=80&w=2564&auto=format&fit=crop');
  background-size: cover;
  background-position: center;
  box-shadow: inset 0 0 100px rgba(0,0,0,0.8);
  border: 1px solid rgba(255,255,255,0.05);
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
  background: linear-gradient(to right, #fff, #a5b4fc);
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
  text-shadow: 0 4px 20px rgba(0,0,0,0.5);
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
  background: rgba(255, 255, 255, 0.03);
  border: 1px solid rgba(255, 255, 255, 0.05);
  padding: 1.5rem;
  border-radius: var(--radius-lg);
  backdrop-filter: blur(10px);
  transition: all var(--transition-base);
}
.hero-signal-card:hover {
  background: rgba(255, 255, 255, 0.05);
  border-color: var(--primary);
  transform: translateY(-5px);
  box-shadow: 0 10px 30px rgba(0,0,0,0.3);
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

.hero-feature-card {
  margin-top: 2rem;
  padding: 2rem;
  background: rgba(0,0,0,0.3);
  border: 1px solid rgba(255,255,255,0.05);
  border-radius: var(--radius-lg);
  backdrop-filter: blur(10px);
  position: relative;
  z-index: 1;
}

.hero-feature-title {
  font-family: var(--font-display);
  font-size: 1.25rem;
  color: #fff;
  margin-bottom: 1rem;
}

.hero-feature-list {
  padding-left: 1.5rem;
  color: var(--text-dim);
  line-height: 1.8;
}
.hero-feature-list li { margin-bottom: 0.5rem; }

.auth-panel {
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 2rem;
}

.auth-card {
  width: 100%;
  max-width: 480px;
  background: rgba(15, 17, 26, 0.7);
  backdrop-filter: blur(30px);
  border: 1px solid var(--panel-border);
  padding: 3rem;
  border-radius: var(--radius-xl);
  box-shadow: var(--shadow-lg), 0 0 40px rgba(99,102,241,0.1);
  position: relative;
}
.auth-card::before {
  content: '';
  position: absolute;
  top: 0; left: 0; right: 0; height: 2px;
  background: linear-gradient(to right, transparent, var(--primary), transparent);
  opacity: 0.5;
}

.mode-switch {
  display: flex;
  background: rgba(0,0,0,0.3);
  border-radius: var(--radius-full);
  padding: 4px;
  margin-bottom: 2rem;
  border: 1px solid rgba(255,255,255,0.05);
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

.auth-card h2 {
  font-size: 2.25rem;
  margin: 1rem 0;
  color: #fff;
}

.auth-copy {
  color: var(--text-dim);
  margin-bottom: 2rem;
}

.field { margin-bottom: 1.5rem; }
.field-label {
  display: block;
  font-size: 0.875rem;
  font-weight: 600;
  margin-bottom: 0.5rem;
  color: var(--text-dim);
}

.field-hint {
  display: block;
  font-size: 0.75rem;
  color: var(--text-muted);
  margin-top: 0.5rem;
}

.auth-submit, button.primary {
  width: 100%;
  padding: 1rem;
  background: linear-gradient(135deg, var(--primary), var(--accent-2));
  color: #fff;
  font-weight: 700;
  font-size: 1rem;
  border-radius: var(--radius-md);
  transition: all var(--transition-base);
  box-shadow: 0 4px 15px var(--primary-glow);
  position: relative;
  overflow: hidden;
}

.auth-submit::after, button.primary::after {
  content: '';
  position: absolute;
  top: 0; left: -100%; width: 50%; height: 100%;
  background: linear-gradient(to right, transparent, rgba(255,255,255,0.3), transparent);
  transform: skewX(-20deg);
  transition: all 0.5s ease;
}

.auth-submit:hover:not(:disabled)::after, button.primary:hover:not(:disabled)::after {
  left: 150%;
}

.auth-submit:hover:not(:disabled), button.primary:hover:not(:disabled) {
  transform: translateY(-2px);
  box-shadow: 0 8px 25px var(--primary-glow);
}

.auth-submit:disabled, button.primary:disabled {
  opacity: 0.6;
  cursor: not-allowed;
  filter: grayscale(0.5);
}

.auth-note {
  font-size: 0.875rem;
  color: var(--text-muted);
  text-align: center;
  margin-top: 1.5rem;
}

/* --- Notices & Messages --- */
.notice {
  padding: 1rem;
  border-radius: var(--radius-md);
  font-size: 0.875rem;
  font-weight: 500;
  margin-top: 1.5rem;
  display: flex;
  align-items: center;
  gap: 0.75rem;
  animation: slideIn 0.3s ease-out forwards;
}

.notice-success {
  background: var(--success-bg);
  border: 1px solid var(--success-border);
  color: #34d399;
}

.notice-error {
  background: var(--error-bg);
  border: 1px solid var(--error-border);
  color: #f87171;
}

.inline-result {
  background: rgba(255,255,255,0.05);
  border: 1px dashed var(--primary);
  padding: 1rem;
  border-radius: var(--radius-md);
  font-family: var(--font-mono);
  font-size: 0.875rem;
  color: #fff;
  margin-top: 1rem;
  white-space: pre-wrap;
  word-break: break-all;
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
}
.workspace-sidebar::-webkit-scrollbar { width: 0; }

.workspace-brand {
  display: flex;
  align-items: center;
  gap: 1rem;
  margin-bottom: 2rem;
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
  box-shadow: 0 0 20px var(--primary-glow);
}

.workspace-brand p {
  font-size: 0.75rem;
  text-transform: uppercase;
  letter-spacing: 0.1em;
  color: var(--text-muted);
  margin-bottom: 0.25rem;
}

.workspace-brand strong {
  font-family: var(--font-display);
  font-size: 1.1rem;
  color: #fff;
  line-height: 1.2;
}

.workspace-user-card {
  background: rgba(0,0,0,0.3);
  border: 1px solid rgba(255,255,255,0.05);
  padding: 1rem;
  border-radius: var(--radius-lg);
  margin-bottom: 2rem;
}

.workspace-user-label {
  font-size: 0.75rem;
  color: var(--text-muted);
  text-transform: uppercase;
  letter-spacing: 0.1em;
}

.workspace-user-card strong {
  display: block;
  font-size: 1.1rem;
  margin-top: 0.25rem;
  color: #fff;
}

.workspace-user-card span {
  display: block;
  font-size: 0.875rem;
  color: var(--text-dim);
}

.workspace-source-pill {
  display: inline-block;
  margin-top: 0.75rem;
  font-size: 0.75rem;
  background: rgba(16, 185, 129, 0.1);
  color: #34d399;
  border: 1px solid rgba(16, 185, 129, 0.2);
  padding: 2px 8px;
  border-radius: var(--radius-full);
}

.workspace-nav {
  display: flex;
  flex-direction: column;
  gap: 0.5rem;
  margin-bottom: 2rem;
}

.workspace-nav-link {
  display: flex;
  flex-direction: column;
  padding: 1rem;
  border-radius: var(--radius-md);
  text-align: left;
  transition: all var(--transition-base);
  border: 1px solid transparent;
}

.workspace-nav-link strong {
  font-size: 1rem;
  color: var(--text-main);
  margin-bottom: 0.25rem;
}

.workspace-nav-link span {
  font-size: 0.8rem;
  color: var(--text-muted);
}

.workspace-nav-link:hover {
  background: rgba(255,255,255,0.03);
  border-color: rgba(255,255,255,0.05);
  transform: translateX(5px);
}

.workspace-nav-link.active {
  background: linear-gradient(90deg, rgba(99, 102, 241, 0.1), transparent);
  border-left: 3px solid var(--primary);
  border-radius: 0 var(--radius-md) var(--radius-md) 0;
}

.workspace-nav-link.active strong {
  color: var(--primary);
}

.sidebar-brief {
  margin-top: auto;
  background: linear-gradient(135deg, rgba(20,20,30,0.8), rgba(0,0,0,0.5));
  border: 1px solid var(--panel-border);
  padding: 1.5rem;
  border-radius: var(--radius-lg);
  margin-bottom: 1.5rem;
}

.sidebar-brief h2 {
  font-size: 1.25rem;
  margin: 0.5rem 0 1rem;
}

.sidebar-brief-list {
  display: flex;
  flex-direction: column;
  gap: 1rem;
}

.sidebar-brief-list div, .operations-flow div, .sale-ticket {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 0.75rem;
  background: rgba(255,255,255,0.03);
  border-radius: var(--radius-md);
  border: 1px solid rgba(255,255,255,0.02);
}

.sidebar-brief-list span, .operations-flow span {
  color: var(--text-dim);
  font-size: 0.875rem;
}

.sidebar-brief-list strong, .operations-flow strong {
  color: #fff;
  font-family: var(--font-mono);
}

.sidebar-logout {
  width: 100%;
  padding: 1rem;
  background: rgba(255,255,255,0.05);
  border: 1px solid rgba(255,255,255,0.1);
  border-radius: var(--radius-md);
  color: var(--text-main);
  font-weight: 600;
  transition: all var(--transition-base);
}
.sidebar-logout:hover {
  background: rgba(239, 68, 68, 0.1);
  border-color: rgba(239, 68, 68, 0.3);
  color: #fca5a5;
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
  background: linear-gradient(135deg, rgba(30, 27, 75, 0.6), rgba(15, 23, 42, 0.6));
  backdrop-filter: blur(20px);
  border: 1px solid var(--panel-border);
  border-radius: var(--radius-xl);
  padding: 3rem;
  display: flex;
  justify-content: space-between;
  align-items: center;
  overflow: hidden;
  box-shadow: var(--shadow-lg);
}

.page-hero::before {
  content: '';
  position: absolute;
  top: -50%; right: -10%;
  width: 50%; height: 200%;
  background: radial-gradient(ellipse at center, var(--primary-glow), transparent 70%);
  transform: rotate(30deg);
  pointer-events: none;
}

.page-hero-copy {
  position: relative;
  max-width: 60%;
  z-index: 1;
}

.page-hero h1 {
  font-size: 3rem;
  margin: 1rem 0;
  color: #fff;
  background: linear-gradient(to right, #fff, #a5b4fc);
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
}

.dashboard-copy {
  font-size: 1.1rem;
  color: var(--text-dim);
  line-height: 1.6;
}

.page-hero-aside {
  position: relative;
  z-index: 1;
  display: flex;
  flex-direction: column;
  align-items: flex-end;
  gap: 1rem;
}

.page-hero-glance {
  background: rgba(0,0,0,0.5);
  border: 1px solid rgba(255,255,255,0.1);
  padding: 1.5rem;
  border-radius: var(--radius-lg);
  text-align: right;
  backdrop-filter: blur(10px);
}

.page-hero-glance span {
  display: block;
  font-size: 0.875rem;
  color: var(--text-muted);
  text-transform: uppercase;
  letter-spacing: 0.05em;
}

.page-hero-glance strong {
  display: block;
  font-size: 1.5rem;
  color: #fff;
  margin-top: 0.5rem;
  font-family: var(--font-display);
}

/* Metric Ribbon */
.metric-ribbon {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: 1.5rem;
}

.metric-ribbon-item {
  background: var(--panel-bg);
  backdrop-filter: blur(20px);
  border: 1px solid var(--panel-border);
  padding: 1.5rem;
  border-radius: var(--radius-lg);
  transition: all var(--transition-base);
  position: relative;
  overflow: hidden;
}
.metric-ribbon-item::before {
  content: '';
  position: absolute;
  top: 0; left: 0; width: 100%; height: 2px;
  background: linear-gradient(to right, var(--primary), var(--accent-2));
  opacity: 0;
  transition: opacity 0.3s;
}

.metric-ribbon-item:hover {
  transform: translateY(-5px);
  border-color: rgba(255,255,255,0.1);
  box-shadow: var(--shadow-md), 0 10px 30px rgba(0,0,0,0.5);
}
.metric-ribbon-item:hover::before { opacity: 1; }

.metric-ribbon-item span {
  font-size: 0.875rem;
  color: var(--text-dim);
  text-transform: uppercase;
  letter-spacing: 0.05em;
}

.metric-ribbon-item strong {
  display: block;
  font-size: 2.25rem;
  font-family: var(--font-display);
  color: #fff;
  margin: 0.5rem 0;
  background: linear-gradient(to right, #fff, #e2e8f0);
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
}

.metric-ribbon-item p {
  font-size: 0.8rem;
  color: var(--text-muted);
}

/* Page Sections & Stage Panel */
.page-section {
  display: grid;
  gap: 1.5rem;
}

.stage-grid {
  display: grid;
  grid-template-columns: 2fr 1fr;
  gap: 1.5rem;
}

.analytics-feature-grid, .signal-board, .tool-grid, .mix-list, .form-grid {
  display: grid;
  gap: 1.5rem;
}

.analytics-feature-grid { grid-template-columns: repeat(3, 1fr); }
.tool-grid { grid-template-columns: 1fr 1fr; }
.signal-board { grid-template-columns: 1fr; }

.stage-panel, .card, .chart-card, .chart-card-wide, .ledger-card, .signal-card, .spotlight-card, .timeline-card, .tool-panel, .sales-feed-card {
  background: var(--panel-bg);
  backdrop-filter: blur(20px);
  border: 1px solid var(--panel-border);
  border-radius: var(--radius-xl);
  padding: 2rem;
  transition: all var(--transition-base);
}

.stage-panel:hover, .card:hover, .tool-panel:hover {
  border-color: var(--panel-border-hover);
  box-shadow: var(--shadow-md);
}

.stage-panel h2, .card h2, .tool-panel h2 {
  font-size: 1.5rem;
  color: #fff;
  margin-bottom: 1.5rem;
  display: flex;
  align-items: center;
  gap: 0.5rem;
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 1.5rem;
}

/* Specific inner components */
.stage-stat-row {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 1rem;
  margin-top: 2rem;
}

.stage-stat {
  background: rgba(0,0,0,0.3);
  padding: 1.5rem;
  border-radius: var(--radius-lg);
  border: 1px solid rgba(255,255,255,0.05);
}

.stage-stat span {
  font-size: 0.875rem;
  color: var(--text-dim);
  text-transform: uppercase;
  letter-spacing: 0.05em;
}

.stage-stat strong {
  display: block;
  font-size: 1.75rem;
  font-family: var(--font-display);
  color: #fff;
  margin-top: 0.5rem;
}

.brief-list {
  list-style: none;
  padding: 0;
  margin: 0;
}
.brief-list li {
  padding: 1rem;
  border-bottom: 1px solid rgba(255,255,255,0.05);
  color: var(--text-dim);
}
.brief-list li:last-child { border-bottom: none; }

/* Custom Inputs and Buttons in tools */
.tool-panel .auth-submit, .tool-panel button.primary {
  margin-top: 1.5rem;
}

/* Revenue Chart Mockup */
.revenue-chart {
  display: flex;
  align-items: flex-end;
  height: 250px;
  gap: 1rem;
  padding-top: 2rem;
  border-bottom: 1px solid rgba(255,255,255,0.1);
}

.revenue-column {
  flex: 1;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: flex-end;
  gap: 0.5rem;
  height: 100%;
  position: relative;
}

.revenue-bar-track {
  width: 100%;
  max-width: 40px;
  background: rgba(255,255,255,0.05);
  border-radius: var(--radius-sm) var(--radius-sm) 0 0;
  height: 100%;
  position: relative;
  overflow: hidden;
}

.revenue-bar-fill {
  position: absolute;
  bottom: 0;
  left: 0;
  width: 100%;
  background: linear-gradient(to top, var(--primary), var(--accent-1));
  border-radius: var(--radius-sm) var(--radius-sm) 0 0;
  transition: height 1s ease-out;
  box-shadow: 0 0 15px var(--primary-glow);
}

.revenue-value {
  font-size: 0.75rem;
  color: #fff;
  font-family: var(--font-mono);
  position: absolute;
  top: -20px;
}

.revenue-column strong {
  font-size: 0.75rem;
  color: var(--text-dim);
}

.revenue-column span {
  font-size: 0.7rem;
  color: var(--text-muted);
}

/* Tables and Records */
.table-wrap {
  overflow-x: auto;
  border-radius: var(--radius-lg);
  border: 1px solid rgba(255,255,255,0.05);
  background: rgba(0,0,0,0.2);
}
table {
  width: 100%;
  border-collapse: collapse;
  text-align: left;
}
th, td {
  padding: 1rem 1.5rem;
  border-bottom: 1px solid rgba(255,255,255,0.05);
}
th {
  font-size: 0.875rem;
  color: var(--text-muted);
  text-transform: uppercase;
  letter-spacing: 0.05em;
  background: rgba(0,0,0,0.4);
}
td {
  color: var(--text-main);
  font-size: 0.95rem;
}
tr:last-child td { border-bottom: none; }
tr:hover td { background: rgba(255,255,255,0.02); }

.table-subcopy {
  font-size: 0.8rem;
  color: var(--text-dim);
  display: block;
}

.empty-cell {
  color: var(--text-muted);
  font-style: italic;
}

/* Highlight components */
.highlight-metrics {
  display: flex;
  gap: 2rem;
  margin-top: 1rem;
}

.highlight-metrics div {
  background: rgba(255,255,255,0.03);
  padding: 1rem 1.5rem;
  border-radius: var(--radius-md);
  border: 1px solid rgba(255,255,255,0.02);
}

.highlight-metrics span {
  font-size: 0.75rem;
  color: var(--text-dim);
  text-transform: uppercase;
  display: block;
}

.highlight-metrics strong {
  font-size: 1.25rem;
  font-family: var(--font-mono);
  color: #fff;
  display: block;
  margin-top: 0.5rem;
}

.highlight-footer {
  margin-top: 1.5rem;
  padding-top: 1.5rem;
  border-top: 1px solid rgba(255,255,255,0.05);
  font-size: 0.875rem;
  color: var(--text-muted);
  display: flex;
  justify-content: space-between;
}

/* Mix List Elements (Category Bars) */
.category-list, .mix-list {
  display: flex;
  flex-direction: column;
  gap: 1rem;
}

.category-row, .mix-item {
  display: flex;
  flex-direction: column;
  gap: 0.5rem;
}

.category-meta, .mix-meta {
  display: flex;
  justify-content: space-between;
  align-items: center;
  font-size: 0.875rem;
}

.category-meta span, .mix-meta span { color: var(--text-dim); }
.category-meta strong, .mix-meta strong { color: #fff; font-family: var(--font-mono); }

.category-track, .mix-track {
  height: 8px;
  background: rgba(255,255,255,0.05);
  border-radius: var(--radius-full);
  overflow: hidden;
}

.category-fill, .mix-fill {
  height: 100%;
  border-radius: var(--radius-full);
  background: linear-gradient(to right, var(--primary), var(--accent-1));
  box-shadow: 0 0 10px var(--primary-glow);
}

.category-fill-warm { background: linear-gradient(to right, #f59e0b, #ef4444); box-shadow: 0 0 10px rgba(245, 158, 11, 0.4); }
.category-fill-cool { background: linear-gradient(to right, #3b82f6, #10b981); box-shadow: 0 0 10px rgba(59, 130, 246, 0.4); }


/* Form Grid & Inputs inside Dashboard */
.form-grid {
  display: grid;
  grid-template-columns: repeat(2, 1fr);
  gap: 1.5rem;
}
.form-grid .field { margin-bottom: 0; }

.run-list {
  display: flex;
  flex-direction: column;
  gap: 1rem;
}

.run-item {
  background: rgba(0,0,0,0.3);
  padding: 1rem;
  border-radius: var(--radius-md);
  border-left: 3px solid var(--primary);
  display: flex;
  flex-direction: column;
  gap: 0.5rem;
}
.run-item.success { border-left-color: var(--success); }
.run-item.error { border-left-color: var(--error); }

.run-item span { font-size: 0.75rem; color: var(--text-muted); }
.run-item strong { font-size: 1rem; color: #fff; }

/* Subcopy and Subtle Text */
.subtle-copy { color: var(--text-muted); font-size: 0.9rem; font-style: italic; }

/* Signal Row Layouts */
.signal-row {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 1rem;
  background: rgba(255,255,255,0.02);
  border-radius: var(--radius-md);
  margin-bottom: 0.5rem;
}

.signal-row span { color: var(--text-dim); }
.signal-values strong { color: #fff; font-family: var(--font-mono); margin-left: 1rem; }

/* Primary Button overrides inside dashboard tools */
.tool-panel button {
  padding: 0.75rem 1.5rem;
  background: var(--primary);
  color: #fff;
  border-radius: var(--radius-md);
  font-weight: 600;
  transition: all var(--transition-base);
}
.tool-panel button:hover {
  background: var(--primary-hover);
  box-shadow: 0 4px 15px var(--primary-glow);
}

button.secondary {
  background: rgba(255,255,255,0.05);
  border: 1px solid rgba(255,255,255,0.1);
  color: var(--text-main);
  padding: 0.75rem 1.5rem;
  border-radius: var(--radius-md);
  transition: all var(--transition-base);
}
button.secondary:hover {
  background: rgba(255,255,255,0.1);
}

/* Animations */
.glass-panel, .tool-panel, .stage-panel, .metric-ribbon-item, .card {
  animation: fadeInUp 0.6s ease-out backwards;
}

.metric-ribbon-item:nth-child(1) { animation-delay: 0.1s; }
.metric-ribbon-item:nth-child(2) { animation-delay: 0.2s; }
.metric-ribbon-item:nth-child(3) { animation-delay: 0.3s; }
.metric-ribbon-item:nth-child(4) { animation-delay: 0.4s; }
.stage-grid > div:nth-child(1) { animation-delay: 0.5s; }
.stage-grid > div:nth-child(2) { animation-delay: 0.6s; }

/* Special sale tickets and feeds */
.sales-feed { display: flex; flex-direction: column; gap: 1rem; }
.sale-ticket {
  background: linear-gradient(135deg, rgba(255,255,255,0.05), rgba(255,255,255,0.01));
  border: 1px solid rgba(255,255,255,0.05);
  border-radius: var(--radius-md);
  padding: 1rem;
  display: flex;
  flex-direction: column;
  gap: 0.5rem;
  position: relative;
  overflow: hidden;
}
.sale-ticket::before {
  content: '';
  position: absolute; left: 0; top: 0; width: 4px; height: 100%;
  background: var(--success);
}
.sale-ticket-top, .sale-ticket-bottom {
  display: flex; justify-content: space-between; align-items: center;
}
.sale-ticket-top strong { font-family: var(--font-mono); color: #fff; }
.sale-ticket-top span { font-size: 0.75rem; color: var(--text-muted); }
.sale-ticket-bottom span { font-size: 0.875rem; color: var(--text-dim); }
.sale-ticket-bottom strong { color: var(--success); }

/* Ledger/Split Layout */
.split-ledger {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 2rem;
}

/* Base Responsive */
@media (max-width: 1200px) {
  .metric-ribbon { grid-template-columns: repeat(2, 1fr); }
  .stage-grid { grid-template-columns: 1fr; }
  .split-ledger { grid-template-columns: 1fr; }
}

@media (max-width: 992px) {
  .workspace-shell { grid-template-columns: 1fr; }
  .workspace-sidebar {
    height: auto;
    position: static;
    margin-bottom: 2rem;
  }
}

@media (max-width: 768px) {
  .auth-shell { grid-template-columns: 1fr; }
  .auth-hero { display: none; }
  .page-hero { flex-direction: column; align-items: flex-start; gap: 2rem; }
  .page-hero-aside { align-items: flex-start; text-align: left; }
  .metric-ribbon { grid-template-columns: 1fr; }
  .analytics-feature-grid { grid-template-columns: 1fr; }
  .form-grid { grid-template-columns: 1fr; }
}
"""

with open("frontend/src/styles.css", "w") as f:
    f.write(css_content)

print("CSS generated beautifully!")
