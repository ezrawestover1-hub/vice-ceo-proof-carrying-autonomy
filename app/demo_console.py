"""A calm, read-only executive review surface for the synthetic Vice CEO demo."""

from __future__ import annotations

from html import escape

from .action_warrant_dossier import build_action_warrant_dossier
from .agent_topology import build_agent_topology_manifest
from .capability_boundaries import build_capability_boundary_manifest
from .demo_verification import build_demo_verification_report
from .judge_demo import build_judge_demo
from .proof_bundle import build_proof_bundle
from .release_readiness import assess_release_readiness
from .time_machine_dossier import build_time_machine_dossier


def render_demo_console() -> str:
    """Render an evidence-led review document without client-side dependencies."""

    demo = build_judge_demo()
    verification = build_demo_verification_report()
    readiness = assess_release_readiness()
    capabilities = build_capability_boundary_manifest()
    proof_bundle = build_proof_bundle()
    warrant_dossier = build_action_warrant_dossier()
    time_machine_dossier = build_time_machine_dossier()
    deployment_status = "Not deployed" if not readiness.deployment_verified else "Deployed"
    provider_status = "Not connected" if not readiness.provider_connectivity_verified else "Connected"
    verified = "Verified" if verification.all_verified else "Needs review"
    acts = "".join(
        "<article class='proof-row act'>"
        f"<span class='proof-index'>{index:02d}</span>"
        f"<span><strong>{escape(act.headline)}</strong>"
        f"<small>{escape(act.claim)}</small>"
        f"<em>{escape(act.status)}</em></span>"
        "</article>"
        for index, act in enumerate(demo.acts, start=1)
    )
    capability_rows = "".join(
        "<article class='proof-row capability'>"
        f"<span class='proof-index'>{index:02d}</span>"
        f"<span><strong>{escape(item.capability_id.replace('_', ' '))}</strong>"
        f"<small>{escape(item.authority_boundary)}</small>"
        f"<em>{escape(item.effect_boundary)}</em></span>"
        "</article>"
        for index, item in enumerate(capabilities.capabilities, start=1)
    )
    gates = "".join(
        "<div class='gate'>"
        f"<strong>{escape(gate.gate_id.replace('_', ' '))}</strong>"
        f"<span>{escape(gate.status)}</span>"
        f"<small>{escape(gate.reason_code)}</small>"
        "</div>"
        for gate in readiness.gates
    )
    return f"""<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>Vice CEO — Review</title>
  <style>
    :root {{ color-scheme:light; --ink:#172426; --soft-ink:#324145; --muted:#697578; --paper:#fff; --wash:#f4f6f4; --line:#dbe1df; --forest:#0e5149; --forest-dark:#093b35; --focus:#b8d8d1; }}
    * {{ box-sizing:border-box; }} html {{ scroll-behavior:smooth; }} body {{ margin:0; background:var(--paper); color:var(--ink); font:16px/1.58 Inter,ui-sans-serif,system-ui,-apple-system,BlinkMacSystemFont,"Segoe UI",sans-serif; }}
    .shell {{ display:grid; grid-template-columns:110px minmax(0,1fr); min-height:100vh; }} .rail {{ display:flex; flex-direction:column; border-right:1px solid var(--line); background:#fbfcfb; }} .mark {{ display:grid; place-items:center; height:78px; border-bottom:1px solid var(--line); color:var(--forest); font-family:Georgia,serif; font-size:2rem; letter-spacing:-.11em; }} .rail nav {{ display:grid; gap:8px; padding:22px 12px; }} .rail a {{ display:grid; place-items:center; gap:7px; min-height:64px; padding:8px 4px; color:var(--soft-ink); font-size:.74rem; font-weight:650; text-align:center; text-decoration:none; }} .rail a.active {{ border-left:3px solid var(--forest); color:var(--forest); background:#f3f7f5; }} .rail svg {{ width:21px; height:21px; fill:none; stroke:currentColor; stroke-width:1.55; stroke-linecap:round; stroke-linejoin:round; }}
    main {{ min-width:0; }} .topbar {{ display:flex; align-items:center; justify-content:space-between; min-height:78px; padding:0 clamp(24px,4vw,56px); border-bottom:1px solid var(--line); }} .office {{ color:var(--soft-ink); font-size:.9rem; font-weight:650; }} .topbar nav {{ display:flex; gap:21px; }} .topbar a {{ color:var(--muted); font-size:.84rem; text-decoration:none; }} .topbar a:hover {{ color:var(--forest); }}
    .document {{ display:grid; grid-template-columns:minmax(0,1fr) 296px; min-height:calc(100vh - 78px); }} .content {{ min-width:0; padding:clamp(40px,6vw,86px) clamp(28px,6vw,100px) 160px; }} .back {{ display:inline-flex; align-items:center; gap:8px; margin-bottom:25px; color:var(--forest); font-size:.84rem; font-weight:650; text-decoration:none; }} .back:hover {{ text-decoration:underline; }} h1,h2,h3,p {{ margin-top:0; }} h1 {{ max-width:780px; margin-bottom:17px; font-family:Georgia,"Times New Roman",serif; font-size:clamp(3rem,6vw,5.4rem); font-weight:400; line-height:.94; letter-spacing:-.065em; }} h1 em {{ color:var(--forest); font-style:normal; }} .lede {{ max-width:650px; margin-bottom:54px; color:var(--muted); font-size:1.08rem; }} .case-meta {{ display:grid; grid-template-columns:135px minmax(0,1fr); gap:9px 22px; max-width:590px; margin:0 0 52px; font-size:.87rem; }} .case-meta dt {{ color:var(--muted); }} .case-meta dd {{ min-width:0; margin:0; color:var(--soft-ink); font-weight:600; overflow-wrap:anywhere; }} .case-meta dd.ok {{ color:var(--forest); }}
    .review-grid {{ display:grid; grid-template-columns:minmax(0,1fr) minmax(0,1fr); gap:52px; }} .review-grid > section + section {{ border-left:1px solid var(--line); padding-left:52px; }} .document-section {{ margin:0 0 47px; }} .document-section h2 {{ margin-bottom:18px; padding-bottom:12px; border-bottom:1px solid var(--line); color:var(--forest); font-family:Georgia,"Times New Roman",serif; font-size:1.2rem; font-weight:400; }} .document-section p {{ color:var(--soft-ink); }} .document-section ul,.document-section ol {{ margin:0; padding-left:22px; color:var(--soft-ink); }} .document-section li {{ margin:0 0 8px; }}
    .proof-list {{ display:grid; gap:0; }} .proof-row {{ display:grid; grid-template-columns:28px minmax(0,1fr) auto; gap:11px; align-items:start; padding:15px 0; border-bottom:1px solid var(--line); color:var(--soft-ink); text-decoration:none; }} .proof-row:first-child {{ border-top:1px solid var(--line); }} a.proof-row:hover {{ color:var(--forest); }} .proof-row svg {{ width:21px; height:21px; fill:none; stroke:currentColor; stroke-width:1.45; stroke-linecap:round; stroke-linejoin:round; }} .proof-row strong,.proof-row small,.proof-row em {{ display:block; }} .proof-row strong {{ font-size:.88rem; font-weight:700; text-transform:capitalize; }} .proof-row small {{ margin-top:2px; color:var(--muted); font-size:.79rem; }} .proof-row em {{ margin-top:4px; color:var(--forest); font-size:.74rem; font-style:normal; font-weight:650; }} .proof-index {{ color:var(--muted); font-size:.74rem; font-variant-numeric:tabular-nums; }} .arrow {{ color:var(--muted); font-size:1rem; }}
    .evidence-rail {{ min-width:0; border-left:1px solid var(--line); padding:51px 30px 170px; }} .evidence-rail h2 {{ margin-bottom:16px; font-size:.9rem; font-weight:750; }} .evidence-rail p {{ color:var(--muted); font-size:.86rem; }} .readiness {{ margin-top:34px; padding-top:24px; border-top:1px solid var(--line); }} .readiness h3 {{ margin-bottom:12px; color:var(--forest); font-size:.79rem; letter-spacing:.08em; text-transform:uppercase; }} .gate {{ padding:12px 0; border-bottom:1px solid var(--line); }} .gate strong {{ display:block; color:var(--soft-ink); font-size:.86rem; text-transform:capitalize; overflow-wrap:anywhere; }} .gate span,.gate small {{ display:block; color:var(--muted); font-size:.78rem; overflow-wrap:anywhere; }} .gate span {{ color:var(--forest); font-weight:700; }}
    .decision-bar {{ position:fixed; z-index:5; right:0; bottom:0; left:110px; display:flex; align-items:center; justify-content:space-between; gap:24px; min-height:106px; padding:20px clamp(24px,4vw,58px); border-top:1px solid var(--line); background:rgba(255,255,255,.96); box-shadow:0 -12px 30px rgba(18,34,31,.05); backdrop-filter:blur(10px); }} .decision-copy {{ display:flex; align-items:flex-start; gap:14px; }} .decision-icon {{ display:grid; flex:0 0 auto; place-items:center; width:38px; height:38px; border:1px solid #c9ddd8; border-radius:50%; color:var(--forest); }} .decision-icon svg {{ width:19px; height:19px; fill:none; stroke:currentColor; stroke-width:1.55; stroke-linecap:round; stroke-linejoin:round; }} .decision-copy strong {{ display:block; color:var(--soft-ink); font-family:Georgia,"Times New Roman",serif; font-size:1.04rem; font-weight:400; }} .decision-copy span {{ display:block; max-width:520px; color:var(--muted); font-size:.82rem; }} .approval-actions {{ display:flex; flex:0 0 auto; gap:12px; }} button {{ min-height:52px; padding:12px 22px; border:1px solid var(--soft-ink); border-radius:7px; background:#fff; color:var(--soft-ink); cursor:pointer; font:650 .88rem/1 Inter,ui-sans-serif,sans-serif; transition:background .16s ease,color .16s ease,border-color .16s ease,transform .16s ease; }} button:hover {{ border-color:var(--forest); color:var(--forest); }} button.primary {{ border-color:var(--forest); background:var(--forest); color:#fff; }} button.primary:hover {{ background:var(--forest-dark); border-color:var(--forest-dark); transform:translateY(-1px); }} button:focus-visible,a:focus-visible {{ outline:3px solid var(--focus); outline-offset:3px; }} button:disabled {{ cursor:wait; opacity:.65; transform:none; }} pre {{ position:fixed; right:24px; bottom:124px; z-index:6; display:none; width:min(390px,calc(100vw - 48px)); max-height:260px; margin:0; padding:16px; overflow:auto; border:1px solid var(--line); border-radius:8px; background:#fff; box-shadow:0 18px 50px rgba(18,34,31,.16); color:var(--soft-ink); font:12px/1.5 ui-monospace,SFMono-Regular,Menlo,monospace; white-space:pre-wrap; }} pre.visible {{ display:block; }}
    @media (max-width:1080px) {{ .document {{ grid-template-columns:1fr; }} .evidence-rail {{ display:grid; grid-template-columns:1fr 1fr; gap:34px; border-top:1px solid var(--line); border-left:0; padding:42px clamp(28px,6vw,100px) 170px; }} .readiness {{ margin:0; padding-top:0; border-top:0; }} }} @media (max-width:760px) {{ .shell {{ display:block; }} .rail {{ display:none; }} .topbar {{ min-height:64px; }} .topbar nav {{ display:none; }} .content {{ padding:36px 24px 180px; }} h1 {{ font-size:3.25rem; }} .case-meta {{ grid-template-columns:100px 1fr; }} .review-grid {{ grid-template-columns:1fr; gap:0; }} .review-grid > section + section {{ border-top:1px solid var(--line); border-left:0; padding-top:38px; padding-left:0; }} .evidence-rail {{ grid-template-columns:1fr; padding:35px 24px 180px; }} .decision-bar {{ left:0; align-items:stretch; flex-direction:column; gap:14px; padding:16px 20px; }} .approval-actions {{ display:grid; grid-template-columns:1fr 1fr; }} button {{ width:100%; padding:12px 10px; }} }} @media (max-width:420px) {{ .approval-actions {{ grid-template-columns:1fr; }} .decision-bar {{ min-height:156px; }} .content,.evidence-rail {{ padding-bottom:215px; }} }} @media (prefers-reduced-motion:reduce) {{ *,*::before,*::after {{ scroll-behavior:auto!important; transition:none!important; }} }}
  </style>
</head>
<body>
  <div class="shell">
    <aside class="rail" aria-label="Product navigation"><div class="mark" aria-label="Vice CEO">VC</div><nav><a class="active" href="#review"><svg viewBox="0 0 24 24" aria-hidden="true"><path d="M7 3h8l4 4v14H7z"/><path d="M15 3v5h5M10 12h6M10 16h6"/></svg>Review</a><a href="#evidence"><svg viewBox="0 0 24 24" aria-hidden="true"><path d="M4 7h16M4 12h16M4 17h16"/><circle cx="7" cy="7" r="1"/><circle cx="12" cy="12" r="1"/><circle cx="17" cy="17" r="1"/></svg>Evidence</a><a href="#decision"><svg viewBox="0 0 24 24" aria-hidden="true"><circle cx="12" cy="12" r="9"/><path d="m8 12 2.5 2.5L16 9"/></svg>Decision</a></nav></aside>
    <main><header class="topbar"><div class="office">Office of the Vice CEO</div><nav aria-label="Page sections"><a href="#review">Review</a><a href="#evidence">Evidence</a></nav></header><div class="document">
      <article class="content" id="review"><a class="back" href="/demo/judge-flow">&larr; View the five-act proof flow</a><h1>A recommendation,<br>ready for <em>review.</em></h1><p class="lede">Vice CEO makes a bounded recommendation only when its evidence, reasoning trail, and authority limits can be inspected together.</p><dl class="case-meta"><dt>Case</dt><dd>Synthetic support-request simulation</dd><dt>Scope</dt><dd>Local demonstration only</dd><dt>Authority</dt><dd class="ok">No external business tools</dd><dt>Release state</dt><dd>{escape(deployment_status)} · provider {escape(provider_status).lower()}</dd></dl>
      <div class="review-grid"><section class="document-section"><h2>1. Recommendation</h2><p>Review a fixed, source-backed synthetic support case before allowing its only permitted transition: a simulated outcome with no customer contact, persistence, or external effect.</p><h2>Rationale</h2><p>Evidence is supplied as a bounded case file. Specialists can advise, but no agent has direct business tools; a one-use Action Warrant constrains the permitted simulation.</p><h2>Proposed next step</h2><ol><li>Inspect the proof bundle and warrant.</li><li>Compare the recorded alternatives.</li><li>Approve or retain the fixed synthetic simulation for review.</li></ol></section><section class="document-section"><h2>2. Review standard</h2><p>Every recommendation must be traceable, warranted, replayable, and bounded before an effect could occur. This screen demonstrates that standard without granting real-world authority.</p><h2>3. Reviewer checks</h2><ul><li>Evidence chain is locally verified: {escape(verified)}.</li><li>{verification.safety_probe_count} adversarial safety probes are recorded.</li><li>{verification.evaluation_case_count} evaluation cases are included.</li><li>Local evaluation score: {verification.evaluation_score:.0%}.</li></ul></section></div>
      <section class="document-section" id="evidence"><h2>Evidence trail</h2><div class="proof-list"><a class="proof-row" href="/demo/proof-bundle"><span class="proof-index">01</span><span><strong>Integrity-linked proof bundle</strong><small>{escape(proof_bundle.bundle_id)}</small></span><span class="arrow">&nearr;</span></a><a class="proof-row" href="/demo/action-warrant-dossier"><span class="proof-index">02</span><span><strong>One-use Action Warrant</strong><small>First use: {escape(warrant_dossier.first_use_state)} · external effect: false</small></span><span class="arrow">&nearr;</span></a><a class="proof-row" href="/demo/time-machine-dossier"><span class="proof-index">03</span><span><strong>Replay record</strong><small>{escape(time_machine_dossier.replay_status)}</small></span><span class="arrow">&nearr;</span></a></div></section>
      <section class="document-section"><h2>Reasoning, in five acts</h2><div class="proof-list">{acts}</div></section><section class="document-section"><h2>Capability boundaries</h2><div class="proof-list">{capability_rows}</div></section></article>
      <aside class="evidence-rail"><section><h2>Evidence</h2><p>Source-backed artifacts available to the reviewer. Each is structured, local, and synthetic-only.</p><div class="proof-list"><a class="proof-row" href="/demo/judge-flow"><span class="proof-index">01</span><span><strong>Five-act proof flow</strong><small>Traceable decision story</small></span><span class="arrow">&nearr;</span></a><a class="proof-row" href="/demo/agent-topology"><span class="proof-index">02</span><span><strong>Agent topology</strong><small>0 direct business tools</small></span><span class="arrow">&nearr;</span></a><a class="proof-row" href="/demo/recording-packet"><span class="proof-index">03</span><span><strong>Recording packet</strong><small>Provider call not required</small></span><span class="arrow">&nearr;</span></a></div></section><section class="readiness"><h3>Release reality</h3>{gates}</section></aside>
    </div></main>
  </div>
  <section class="decision-bar" id="decision" aria-label="Reviewer decision"><div class="decision-copy"><span class="decision-icon"><svg viewBox="0 0 24 24" aria-hidden="true"><path d="M12 3 4 7v5c0 5 3.4 8.4 8 9 4.6-.6 8-4 8-9V7z"/><path d="m9 12 2 2 4-4"/></svg></span><div><strong>Your decision is requested.</strong><span>This is only a synthetic review action. It does not verify identity, persist approval, or grant production authority.</span></div></div><div class="approval-actions"><button type="button" data-demo-approval="decline_simulation">Keep in review</button><button type="button" class="primary" data-demo-approval="approve_simulation">Approve simulation</button></div></section>
  <pre id="approval-result" aria-live="polite">Decision required. No simulation has started.</pre>
  <script>
    const result = document.getElementById("approval-result");
    document.querySelectorAll("[data-demo-approval]").forEach((button) => {{
      button.addEventListener("click", async () => {{
        document.querySelectorAll("[data-demo-approval]").forEach((control) => control.disabled = true);
        result.classList.add("visible");
        result.textContent = "Resolving fixed synthetic decision…";
        try {{
          const response = await fetch("/demo/human-approval", {{ method: "POST", headers: {{ "content-type": "application/json" }}, body: JSON.stringify({{ decision: button.dataset.demoApproval }}) }});
          const payload = await response.json();
          result.textContent = JSON.stringify(payload.human_approval, null, 2);
        }} catch (error) {{
          result.textContent = "Demo decision unavailable. No simulation was started.";
        }} finally {{
          document.querySelectorAll("[data-demo-approval]").forEach((control) => control.disabled = false);
        }}
      }});
    }});
  </script>
</body>
</html>"""
