import re

with open("frontend/src/styles.css", "r") as f:
    css = f.read()

# Make metric ribbon float smoothly
css = css.replace("""
.metric-ribbon-item {
  background: var(--panel-bg);
  backdrop-filter: blur(20px);
  border: 1px solid var(--panel-border);
  padding: 1.5rem;
  border-radius: var(--radius-lg);
  transition: all var(--transition-base);
  position: relative;
  overflow: hidden;
}""", """
.metric-ribbon-item {
  background: radial-gradient(circle at top left, rgba(255,255,255,0.03), transparent 70%);
  border-left: 2px solid var(--primary);
  padding: 1.5rem;
  transition: all var(--transition-base);
  position: relative;
  overflow: hidden;
}""")

css = css.replace("""
.stage-panel, .card, .chart-card, .chart-card-wide, .ledger-card, .signal-card, .spotlight-card, .timeline-card, .tool-panel, .sales-feed-card {
  background: var(--panel-bg);
  backdrop-filter: blur(20px);
  border: 1px solid var(--panel-border);
  border-radius: var(--radius-xl);
  padding: 2rem;
  transition: all var(--transition-base);
}""", """
.stage-panel, .card, .chart-card, .chart-card-wide, .ledger-card, .signal-card, .spotlight-card, .timeline-card, .tool-panel, .sales-feed-card {
  background: transparent;
  border-top: 1px solid rgba(255,255,255,0.05);
  border-radius: 0;
  padding: 3rem 0;
  transition: all var(--transition-base);
}""")

css = css.replace("""
.stage-panel:hover, .card:hover, .tool-panel:hover {
  border-color: var(--panel-border-hover);
  box-shadow: var(--shadow-md);
}""", """
.stage-panel:hover, .card:hover, .tool-panel:hover {
  background: radial-gradient(ellipse at center, rgba(99, 102, 241, 0.03) 0%, transparent 70%);
}""")

# Remove the default gap in grids to allow sections to overlap or breathe
css = css.replace(".stage-grid {\n  display: grid;\n  grid-template-columns: 2fr 1fr;\n  gap: 1.5rem;\n}", ".stage-grid {\n  display: grid;\n  grid-template-columns: 2fr 1fr;\n  gap: 4rem;\n}")

with open("frontend/src/styles.css", "w") as f:
    f.write(css)

print("CSS refined successfully!")
