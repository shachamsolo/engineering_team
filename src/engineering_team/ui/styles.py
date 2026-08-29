APP_HEAD = """
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=Fraunces:opsz,wght@9..144,600;9..144,700&family=IBM+Plex+Mono:wght@400;500&family=Outfit:wght@400;500;600;700&display=swap" rel="stylesheet">
"""

APP_CSS = """
:root {
  --ink: #1c1914;
  --paper: #f4efe6;
  --panel: rgba(255, 251, 245, 0.86);
  --muted: #6f675c;
  --line: #d9d0c3;
  --gold: #ecad0a;
  --blue: #209dd7;
  --purple: #753991;
  --good: #2f9e6b;
  --bad: #c43c2c;
  --shadow: 0 18px 50px rgba(48, 36, 18, 0.10);
}
.dark,
.dark :root,
.gradio-container.dark {
  --ink: #f3eee6;
  --paper: #12100e;
  --panel: rgba(24, 21, 18, 0.88);
  --muted: #b3aa9e;
  --line: #3a342c;
  --shadow: 0 18px 50px rgba(0, 0, 0, 0.35);
}
.gradio-container {
  font-family: Outfit, ui-sans-serif, sans-serif !important;
  background:
    radial-gradient(circle at 12% -10%, rgba(236, 173, 10, 0.18), transparent 34%),
    radial-gradient(circle at 88% 0%, rgba(32, 157, 215, 0.16), transparent 32%),
    linear-gradient(180deg, var(--paper), var(--paper));
  color: var(--ink);
}
.gradio-container h1, .gradio-container h2, .gradio-container h3 {
  font-family: Fraunces, ui-serif, serif !important;
}
#build-shell {
  max-width: 1280px;
  margin: 0 auto;
}
.hero {
  display: grid;
  gap: 10px;
  padding: 28px 28px 22px;
  border: 1px solid var(--line);
  border-radius: 8px 28px 8px 28px;
  background:
    linear-gradient(135deg, rgba(236, 173, 10, 0.16), transparent 42%),
    linear-gradient(225deg, rgba(117, 57, 145, 0.12), rgba(32, 157, 215, 0.10));
  box-shadow: var(--shadow);
}
.kicker {
  font-family: "IBM Plex Mono", ui-monospace, monospace;
  font-size: 12px;
  letter-spacing: 0.22em;
  text-transform: uppercase;
  color: var(--purple);
}
.hero h1 {
  margin: 0;
  font-size: clamp(2rem, 4vw, 3.1rem);
  letter-spacing: -0.04em;
  line-height: 1.05;
}
.hero p {
  margin: 0;
  max-width: 62ch;
  color: var(--muted);
  font-size: 1.05rem;
}
.status-strip {
  display: flex;
  align-items: center;
  gap: 12px;
  min-height: 52px;
  padding: 12px 16px;
  border: 1px solid var(--line);
  border-radius: 6px;
  background: var(--panel);
  box-shadow: var(--shadow);
}
.status-dot {
  width: 10px;
  height: 10px;
  border-radius: 999px;
  background: var(--muted);
  flex: 0 0 auto;
}
.status-dot.live {
  background: var(--gold);
  box-shadow: 0 0 0 6px rgba(236, 173, 10, 0.18);
  animation: pulse 1.4s ease-in-out infinite;
}
.status-dot.done { background: var(--good); box-shadow: none; animation: none; }
.status-dot.error { background: var(--bad); box-shadow: none; animation: none; }
.status-copy {
  font-size: 0.98rem;
  color: var(--ink);
}
.status-copy strong { font-weight: 650; }
.pipeline {
  display: grid;
  grid-template-columns: repeat(4, minmax(0, 1fr));
  gap: 10px;
}
.stage {
  position: relative;
  min-height: 168px;
  padding: 14px;
  border: 1px solid var(--line);
  border-radius: 6px;
  background: var(--panel);
  overflow: hidden;
}
.stage::after {
  content: "";
  position: absolute;
  right: -7px;
  top: 28px;
  width: 12px;
  height: 2px;
  background: var(--line);
  z-index: 1;
}
.stage:last-child::after { display: none; }
.stage-station {
  font-family: "IBM Plex Mono", ui-monospace, monospace;
  font-size: 11px;
  letter-spacing: 0.16em;
  color: var(--muted);
}
.stage-role {
  margin-top: 8px;
  font-family: Fraunces, ui-serif, serif;
  font-size: 1.12rem;
  line-height: 1.15;
}
.stage-title {
  margin-top: 4px;
  font-size: 12px;
  letter-spacing: 0.08em;
  text-transform: uppercase;
  color: var(--blue);
}
.stage-action {
  margin-top: 12px;
  color: var(--muted);
  font-size: 0.88rem;
  line-height: 1.35;
}
.stage-flag {
  position: absolute;
  top: 12px;
  right: 12px;
  font-family: "IBM Plex Mono", ui-monospace, monospace;
  font-size: 10px;
  letter-spacing: 0.12em;
  color: var(--muted);
}
.stage.active {
  border-color: rgba(236, 173, 10, 0.7);
  box-shadow: inset 0 0 0 1px rgba(236, 173, 10, 0.25), var(--shadow);
}
.stage.active .stage-flag { color: var(--gold); }
.stage.done {
  border-color: rgba(47, 158, 107, 0.45);
}
.stage.done .stage-flag { color: var(--good); }
.stage.error {
  border-color: rgba(196, 60, 44, 0.55);
}
.stage.error .stage-flag { color: var(--bad); }
.log-panel {
  max-height: 420px;
  overflow: auto;
  padding: 8px 4px 8px 0;
  border: 1px solid var(--line);
  border-radius: 6px;
  background: var(--panel);
}
.log-item {
  display: grid;
  grid-template-columns: 74px 150px minmax(0, 1fr);
  gap: 10px;
  padding: 8px 14px;
  border-bottom: 1px dashed var(--line);
  align-items: start;
}
.log-item:last-child { border-bottom: 0; }
.log-time {
  font-family: "IBM Plex Mono", ui-monospace, monospace;
  font-size: 12px;
  color: var(--muted);
  padding-top: 2px;
}
.log-agent {
  font-size: 12px;
  font-weight: 650;
  color: var(--purple);
}
.log-agent.lead { color: var(--gold); }
.log-agent.backend { color: var(--blue); }
.log-agent.frontend { color: var(--purple); }
.log-agent.test { color: var(--good); }
.log-agent.crew { color: var(--muted); }
.log-msg {
  font-size: 0.92rem;
  color: var(--ink);
  line-height: 1.4;
}
.log-msg code {
  font-family: "IBM Plex Mono", ui-monospace, monospace;
  font-size: 0.86em;
  padding: 1px 5px;
  border-radius: 4px;
  background: rgba(32, 157, 215, 0.12);
}
.file-grid {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
}
.file-chip {
  font-family: "IBM Plex Mono", ui-monospace, monospace;
  font-size: 12px;
  padding: 7px 10px;
  border: 1px solid var(--line);
  border-radius: 999px;
  background: rgba(32, 157, 215, 0.08);
}
.empty-note { color: var(--muted); padding: 8px 2px; }
@keyframes pulse {
  0%, 100% { transform: scale(1); opacity: 1; }
  50% { transform: scale(1.25); opacity: 0.7; }
}
@media (max-width: 1100px) {
  .pipeline { grid-template-columns: 1fr 1fr; }
  .stage::after { display: none; }
  .log-item { grid-template-columns: 74px minmax(0, 1fr); }
  .log-agent { grid-column: 2; }
  .log-msg { grid-column: 1 / -1; }
}
"""
