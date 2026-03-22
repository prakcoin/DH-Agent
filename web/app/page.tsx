"use client";
import { useEffect, useRef, useState } from "react";

export default function Home() {
  const [scrolled, setScrolled] = useState(false);
  const heroRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    const onScroll = () => setScrolled(window.scrollY > 40);
    window.addEventListener("scroll", onScroll);
    return () => window.removeEventListener("scroll", onScroll);
  }, []);

  return (
    <>
      <style>{`
        @import url('https://fonts.googleapis.com/css2?family=DM+Serif+Display:ital@0;1&family=DM+Mono:wght@300;400;500&display=swap');

        *, *::before, *::after { box-sizing: border-box; margin: 0; padding: 0; }

        :root {
          --bg: #0a0a08;
          --surface: #111110;
          --border: #222220;
          --text: #e8e6df;
          --muted: #6b6960;
          --accent: #c8b89a;
          --accent2: #8fa68e;
          --mono: 'DM Mono', monospace;
          --serif: 'DM Serif Display', serif;
        }

        html { scroll-behavior: smooth; }

        body {
          background: var(--bg);
          color: var(--text);
          font-family: var(--mono);
          font-size: 14px;
          line-height: 1.6;
          overflow-x: hidden;
        }

        /* NAV */
        nav {
          position: fixed;
          top: 0; left: 0; right: 0;
          z-index: 100;
          display: flex;
          align-items: center;
          justify-content: space-between;
          padding: 20px 48px;
          transition: background 0.3s, border-color 0.3s;
          border-bottom: 1px solid transparent;
        }
        nav.scrolled {
          background: rgba(10,10,8,0.92);
          backdrop-filter: blur(12px);
          border-color: var(--border);
        }
        .nav-logo {
          font-family: var(--serif);
          font-size: 22px;
          color: var(--accent);
          letter-spacing: 0.02em;
          text-decoration: none;
        }
        .nav-links {
          display: flex;
          gap: 32px;
          list-style: none;
        }
        .nav-links a {
          color: var(--muted);
          text-decoration: none;
          font-size: 12px;
          letter-spacing: 0.12em;
          text-transform: uppercase;
          transition: color 0.2s;
        }
        .nav-links a:hover { color: var(--text); }
        .nav-cta {
          background: transparent;
          border: 1px solid var(--border);
          color: var(--accent) !important;
          padding: 8px 20px;
          border-radius: 2px;
          cursor: pointer;
          transition: border-color 0.2s, background 0.2s !important;
        }
        .nav-cta:hover {
          background: rgba(200,184,154,0.08) !important;
          border-color: var(--accent) !important;
          color: var(--accent) !important;
        }

        /* HERO */
        .hero {
          min-height: 100vh;
          display: flex;
          flex-direction: column;
          justify-content: flex-end;
          padding: 0 48px 80px;
          position: relative;
          overflow: hidden;
        }
        .hero-grid {
          position: absolute;
          inset: 0;
          background-image:
            linear-gradient(var(--border) 1px, transparent 1px),
            linear-gradient(90deg, var(--border) 1px, transparent 1px);
          background-size: 60px 60px;
          opacity: 0.4;
          mask-image: radial-gradient(ellipse 80% 60% at 50% 40%, black 30%, transparent 100%);
        }
        .hero-strand {
          position: absolute;
          top: 0; right: 0;
          width: 55%;
          height: 100%;
          overflow: hidden;
          pointer-events: none;
        }
        .strand-line {
          position: absolute;
          width: 1px;
          background: linear-gradient(180deg, transparent, var(--accent2), transparent);
          opacity: 0;
          animation: strandFall 4s ease-in-out infinite;
        }
        @keyframes strandFall {
          0% { opacity: 0; transform: translateY(-100px); }
          20% { opacity: 0.3; }
          80% { opacity: 0.3; }
          100% { opacity: 0; transform: translateY(100vh); }
        }

        .hero-eyebrow {
          font-size: 11px;
          letter-spacing: 0.2em;
          text-transform: uppercase;
          color: var(--accent2);
          margin-bottom: 24px;
          opacity: 0;
          animation: fadeUp 0.8s 0.2s forwards;
        }
        .hero-title {
          font-family: var(--serif);
          font-size: clamp(56px, 8vw, 112px);
          line-height: 0.95;
          letter-spacing: -0.02em;
          margin-bottom: 32px;
          opacity: 0;
          animation: fadeUp 0.8s 0.4s forwards;
        }
        .hero-title em {
          font-style: italic;
          color: var(--accent);
        }
        .hero-sub {
          max-width: 480px;
          color: var(--muted);
          line-height: 1.8;
          margin-bottom: 48px;
          font-size: 13px;
          opacity: 0;
          animation: fadeUp 0.8s 0.6s forwards;
        }
        .hero-actions {
          display: flex;
          gap: 16px;
          align-items: center;
          opacity: 0;
          animation: fadeUp 0.8s 0.8s forwards;
        }
        .btn-primary {
          background: var(--accent);
          color: var(--bg);
          border: none;
          padding: 14px 32px;
          font-family: var(--mono);
          font-size: 12px;
          letter-spacing: 0.1em;
          text-transform: uppercase;
          cursor: pointer;
          border-radius: 2px;
          text-decoration: none;
          transition: opacity 0.2s;
          display: inline-block;
        }
        .btn-primary:hover { opacity: 0.85; }
        .btn-ghost {
          color: var(--muted);
          text-decoration: none;
          font-size: 12px;
          letter-spacing: 0.08em;
          display: flex;
          align-items: center;
          gap: 8px;
          transition: color 0.2s;
        }
        .btn-ghost:hover { color: var(--text); }
        .btn-ghost svg { transition: transform 0.2s; }
        .btn-ghost:hover svg { transform: translateX(4px); }

        @keyframes fadeUp {
          from { opacity: 0; transform: translateY(24px); }
          to { opacity: 1; transform: translateY(0); }
        }

        /* TICKER */
        .ticker {
          border-top: 1px solid var(--border);
          border-bottom: 1px solid var(--border);
          padding: 12px 0;
          overflow: hidden;
          white-space: nowrap;
        }
        .ticker-inner {
          display: inline-flex;
          gap: 48px;
          animation: ticker 20s linear infinite;
        }
        .ticker-item {
          font-size: 11px;
          letter-spacing: 0.15em;
          text-transform: uppercase;
          color: var(--muted);
          display: flex;
          align-items: center;
          gap: 16px;
        }
        .ticker-item span { color: var(--accent2); }
        @keyframes ticker {
          from { transform: translateX(0); }
          to { transform: translateX(-50%); }
        }

        /* SECTIONS */
        section { padding: 120px 48px; }
        .section-label {
          font-size: 11px;
          letter-spacing: 0.2em;
          text-transform: uppercase;
          color: var(--accent2);
          margin-bottom: 16px;
        }
        .section-title {
          font-family: var(--serif);
          font-size: clamp(36px, 5vw, 64px);
          line-height: 1.05;
          margin-bottom: 24px;
        }
        .section-title em { font-style: italic; color: var(--accent); }

        /* HOW IT WORKS */
        .how-grid {
          display: grid;
          grid-template-columns: 1fr 1fr;
          gap: 2px;
          margin-top: 64px;
          border: 1px solid var(--border);
        }
        .how-cell {
          padding: 48px;
          border: 1px solid var(--border);
          position: relative;
          transition: background 0.3s;
        }
        .how-cell:hover { background: var(--surface); }
        .how-num {
          font-family: var(--serif);
          font-size: 48px;
          color: var(--border);
          position: absolute;
          top: 24px; right: 32px;
          line-height: 1;
        }
        .how-cell h3 {
          font-family: var(--serif);
          font-size: 22px;
          margin-bottom: 12px;
          font-weight: 400;
        }
        .how-cell p { color: var(--muted); line-height: 1.8; font-size: 13px; }

        /* AGENTS */
        .agents-section { background: var(--surface); }
        .agents-grid {
          display: grid;
          grid-template-columns: repeat(4, 1fr);
          gap: 1px;
          background: var(--border);
          margin-top: 64px;
        }
        .agent-card {
          background: var(--surface);
          padding: 40px 32px;
          transition: background 0.2s;
        }
        .agent-card:hover { background: #161614; }
        .agent-icon {
          width: 36px;
          height: 36px;
          border: 1px solid var(--border);
          border-radius: 50%;
          display: flex;
          align-items: center;
          justify-content: center;
          margin-bottom: 24px;
          color: var(--accent);
          font-size: 16px;
        }
        .agent-card h3 {
          font-size: 13px;
          letter-spacing: 0.08em;
          text-transform: uppercase;
          margin-bottom: 12px;
          color: var(--text);
        }
        .agent-card p { color: var(--muted); font-size: 12px; line-height: 1.8; }

        /* CODE BLOCK */
        .code-section {
          display: grid;
          grid-template-columns: 1fr 1fr;
          gap: 80px;
          align-items: center;
        }
        .code-block {
          background: var(--surface);
          border: 1px solid var(--border);
          border-radius: 4px;
          overflow: hidden;
        }
        .code-header {
          padding: 12px 20px;
          border-bottom: 1px solid var(--border);
          display: flex;
          align-items: center;
          gap: 8px;
        }
        .code-dot {
          width: 10px; height: 10px;
          border-radius: 50%;
          background: var(--border);
        }
        .code-filename {
          font-size: 11px;
          color: var(--muted);
          letter-spacing: 0.08em;
          margin-left: 8px;
        }
        .code-body {
          padding: 28px;
          font-size: 12px;
          line-height: 2;
          overflow-x: auto;
        }
        .code-body .kw { color: #8fa68e; }
        .code-body .str { color: var(--accent); }
        .code-body .fn { color: #a8b8d8; }
        .code-body .cm { color: var(--muted); }
        .code-body .num { color: #d4a574; }

        /* FOOTER */
        footer {
          border-top: 1px solid var(--border);
          padding: 48px;
          display: flex;
          justify-content: space-between;
          align-items: center;
        }
        .footer-logo {
          font-family: var(--serif);
          font-size: 20px;
          color: var(--accent);
        }
        .footer-links {
          display: flex;
          gap: 32px;
          list-style: none;
        }
        .footer-links a {
          color: var(--muted);
          text-decoration: none;
          font-size: 12px;
          letter-spacing: 0.08em;
          transition: color 0.2s;
        }
        .footer-links a:hover { color: var(--text); }
        .footer-copy {
          font-size: 11px;
          color: var(--muted);
          letter-spacing: 0.06em;
        }

        /* DIVIDER */
        .divider {
          height: 1px;
          background: var(--border);
          margin: 0 48px;
        }
      `}</style>

      {/* NAV */}
      <nav className={scrolled ? "scrolled" : ""}>
        <a href="#" className="nav-logo">Strandex</a>
        <ul className="nav-links">
          <li><a href="#how">How it works</a></li>
          <li><a href="#agents">Agents</a></li>
          <li><a href="#docs">Docs</a></li>
          <li><a href="https://github.com/prakcoin/DH-Agent" target="_blank" className="nav-cta">GitHub →</a></li>
        </ul>
      </nav>

      {/* HERO */}
      <div className="hero" ref={heroRef}>
        <div className="hero-grid" />
        <div className="hero-strand">
          {[
            { left: "8%", height: "65%", delay: "0s", duration: "3.2s" },
            { left: "16%", height: "48%", delay: "0.4s", duration: "4.1s" },
            { left: "24%", height: "72%", delay: "0.8s", duration: "3.8s" },
            { left: "32%", height: "55%", delay: "1.2s", duration: "5.0s" },
            { left: "40%", height: "40%", delay: "1.6s", duration: "3.5s" },
            { left: "48%", height: "68%", delay: "2.0s", duration: "4.4s" },
            { left: "56%", height: "52%", delay: "2.4s", duration: "3.9s" },
            { left: "64%", height: "75%", delay: "2.8s", duration: "4.7s" },
            { left: "72%", height: "44%", delay: "3.2s", duration: "3.3s" },
            { left: "80%", height: "60%", delay: "3.6s", duration: "5.2s" },
            { left: "88%", height: "50%", delay: "4.0s", duration: "4.0s" },
            { left: "96%", height: "70%", delay: "4.4s", duration: "3.6s" },
          ].map((s, i) => (
            <div
              key={i}
              className="strand-line"
              style={{
                left: s.left,
                height: s.height,
                animationDelay: s.delay,
                animationDuration: s.duration,
              }}
            />
          ))}
        </div>
        <h1 className="hero-title">
          Build agents<br />
          for fashion<br />
          collections.
        </h1>
        <p className="hero-sub">
          Strandex is an open-source framework for creating retrieval-augmented
          multi-agent AI systems over fashion runway data — visual, textual, and real-time.
        </p>
        <div className="hero-actions">
          <a href="#docs" className="btn-primary">Get Started</a>
          <a href="https://github.com/prakcoin/DH-Agent" className="btn-ghost" target="_blank">
            View on GitHub
            <svg width="16" height="16" viewBox="0 0 16 16" fill="none">
              <path d="M3 8h10M9 4l4 4-4 4" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round"/>
            </svg>
          </a>
        </div>
      </div>

      {/* HOW IT WORKS */}
      <section id="how">
        <p className="section-label">How it works</p>
        <h2 className="section-title">From collection data<br />to <em>intelligent agents</em></h2>
        <div className="how-grid">
          {[
            ["Ingest", "Point Strandex at your fashion collection data — runway images, lookbooks, item metadata. The pipeline handles annotation, embedding, and indexing automatically."],
            ["Configure", "Define your agent topology: which agents to deploy, what data they can access, and how they collaborate. No boilerplate required."],
            ["Deploy", "Ship agents via Docker or Bedrock AgentCore with one command. Built-in observability through OpenTelemetry and CloudWatch."],
            ["Query", "Users interact with a unified agent interface that routes queries to the right specialist — single item, collection-wide, visual, or real-time market data."],
          ].map(([title, desc], i) => (
            <div key={i} className="how-cell">
              <span className="how-num">0{i + 1}</span>
              <h3>{title}</h3>
              <p>{desc}</p>
            </div>
          ))}
        </div>
      </section>

      <div className="divider" />

      {/* AGENTS */}
      <section id="agents" className="agents-section">
        <p className="section-label">Agent Architecture</p>
        <h2 className="section-title">Specialist agents,<br /><em>collaborative</em> by design</h2>
        <div className="agents-grid">
          {[
            ["◈", "Item Agent", "Analyzes individual garments — silhouette, material, color, construction details — against your collection knowledge base."],
            ["◉", "Collection Agent", "Identifies trends, recurring motifs, and designer intent across an entire runway or archive."],
            ["◎", "Visual Agent", "Multimodal analysis of runway imagery using vision-language models for rich, grounded descriptions."],
            ["◇", "Search Agent", "Pulls real-time market listings and editorial context from the web to ground responses in current data."],
          ].map(([icon, name, desc]) => (
            <div key={name} className="agent-card">
              <div className="agent-icon">{icon}</div>
              <h3>{name}</h3>
              <p>{desc}</p>
            </div>
          ))}
        </div>
      </section>

      {/* CODE */}
      <section id="docs">
        <div className="code-section">
          <div>
            <p className="section-label">Developer First</p>
            <h2 className="section-title">Up and running<br />in <em>minutes</em></h2>
            <p style={{ color: "var(--muted)", lineHeight: 1.8, fontSize: 13, marginTop: 16, marginBottom: 32 }}>
              Strandex wraps the complexity of multi-agent orchestration, RAG pipelines,
              and multimodal retrieval into a clean, extensible Python API.
            </p>
            <a href="#" className="btn-primary">Read the Docs</a>
          </div>
          <div className="code-block">
            <div className="code-header">
              <div className="code-dot" />
              <div className="code-dot" />
              <div className="code-dot" />
              <span className="code-filename">quickstart.py</span>
            </div>
            <div className="code-body">
              <pre><code>
                <span className="cm"># Install</span>{"\n"}
                <span className="fn">pip install</span> <span className="str">strandex</span>{"\n\n"}
                <span className="kw">from</span> strandex <span className="kw">import</span> CollectionAgent{"\n\n"}
                <span className="cm"># Point at your data</span>{"\n"}
                agent = <span className="fn">CollectionAgent</span>({"\n"}
                {"  "}data_path=<span className="str">"./runway_2025"</span>,{"\n"}
                {"  "}agents=[{"\n"}
                {"    "}<span className="str">"item"</span>, <span className="str">"visual"</span>,{"\n"}
                {"    "}<span className="str">"collection"</span>, <span className="str">"search"</span>{"\n"}
                {"  "}],{"\n"}
                ){"\n\n"}
                <span className="cm"># Query your collection</span>{"\n"}
                result = agent.<span className="fn">query</span>({"\n"}
                {"  "}<span className="str">"What fabrics dominate look 12?"</span>{"\n"}
                )
              </code></pre>
            </div>
          </div>
        </div>
      </section>

      {/* FOOTER */}
      <footer>
        <span className="footer-logo">Strandex</span>
        <ul className="footer-links">
          <li><a href="#">Docs</a></li>
          <li><a href="https://github.com/prakcoin/DH-Agent">GitHub</a></li>
          <li><a href="#">License</a></li>
        </ul>
        <span className="footer-copy">MIT License · Open Source</span>
      </footer>
    </>
  );
}
