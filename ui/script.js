// ---------------------------------------------------------------
// DEMO_MODE = true shows fake data without a backend (open index.html directly,
// or add ?demo=1 to the address). Served by FastAPI, the page calls the real API.
// ---------------------------------------------------------------
const DEMO_MODE = location.protocol === "file:" || new URLSearchParams(location.search).has("demo");
const API_BASE = "";   // same origin as the FastAPI app

const $ = (id) => document.getElementById(id);
let sessionId = null;

/* ---------- tiny DOM helper (uses textContent, never innerHTML) ---------- */
function el(tag, props = {}, children = []) {
  const node = document.createElement(tag);
  for (const [k, v] of Object.entries(props)) {
    if (k === "class") node.className = v;
    else if (k === "text") node.textContent = v;
    else node.setAttribute(k, v);
  }
  [].concat(children).forEach((c) => c && node.appendChild(c));
  return node;
}

/* ---------- pipeline strip ---------- */
const STEP_ORDER = ["plan", "research", "slides", "code", "quiz", "draft", "review", "final"];

function setPipeline(selected, active) {
  const optional = ["research", "slides", "code", "quiz"];
  document.querySelectorAll("#pipeline li").forEach((li) => {
    const step = li.dataset.step;
    li.className = "";
    if (optional.includes(step) && selected && !selected.includes(step)) {
      li.classList.add("skipped");
    } else if (STEP_ORDER.indexOf(step) < STEP_ORDER.indexOf(active)) {
      li.classList.add("done");
    } else if (step === active) {
      li.classList.add("active");
    }
  });
}

/* ---------- tabs ---------- */
const tabs = ["outline", "slides", "code", "quiz"];

function showTab(name) {
  tabs.forEach((t) => {
    const selected = t === name;
    $(`tab-${t}`).setAttribute("aria-selected", selected);
    $(`tab-${t}`).tabIndex = selected ? 0 : -1;
    $(`panel-${t}`).hidden = !selected;
  });
}
tabs.forEach((t) => $(`tab-${t}`).addEventListener("click", () => showTab(t)));

/* ---------- renderers ---------- */
function verifiedLabel(verified) {
  if (verified === true) return "Checked: this example ran without errors.";
  if (verified === false) return "Warning: this example still failed when it was run. Review it before use.";
  return "Not run automatically (only Python examples are checked).";
}

function renderDraft(data) {
  const d = data.draft;

  $("plan-note").replaceChildren(
    el("strong", { text: "Plan: " }),
    document.createTextNode(data.reasoning || "Agents selected from your brief.")
  );

  // outline
  const ol = el("ol", { class: "outline-list" }, (d.outline || []).map((s) => el("li", { text: s })));
  $("panel-outline").replaceChildren(ol);

  // slides
  $("panel-slides").replaceChildren(
    ...((d.slides || []).map((s) =>
      el("article", { class: "slide" }, [
        el("h3", { text: s.title }),
        el("ul", {}, (s.bullets || []).map((b) => el("li", { text: b }))),
        (s.diagram_steps || []).length ? el("p", { class: "notes", text: "Diagram: " + s.diagram_steps.join("  →  ") }) : null,
        s.notes ? el("p", { class: "notes", text: "Speaker notes: " + s.notes }) : null,
      ])
    ))
  );
  if (!(d.slides || []).length) $("panel-slides").replaceChildren(el("p", { text: "Slides were not requested." }));

  // code
  $("panel-code").replaceChildren(
    ...((d.code_examples || []).map((c) =>
      el("div", { class: "code-block" }, [
        el("h3", { text: c.title }),
        el("pre", {}, [el("code", { text: c.code })]),
        el("p", { text: c.explanation }),
        el("p", { class: "notes", text: verifiedLabel(c.verified) }),
      ])
    ))
  );
  if (!(d.code_examples || []).length) $("panel-code").replaceChildren(el("p", { text: "Code was not requested." }));

  // quiz
  $("panel-quiz").replaceChildren(
    ...((d.quiz || []).map((q, i) =>
      el("div", { class: "q" }, [
        el("p", { class: "q-title", text: `${i + 1}. ${q.question}` }),
        el("ol", {}, q.options.map((o, idx) =>
          el("li", { class: idx === q.answer_index ? "correct" : "", text: o })
        )),
        el("p", { class: "why", text: q.explanation }),
      ])
    ))
  );
  if (!(d.quiz || []).length) $("panel-quiz").replaceChildren(el("p", { text: "Quiz was not requested." }));

  // long-term memory
  const mem = data.memory || [];
  $("memory").hidden = mem.length === 0;
  $("memory-list").replaceChildren(...mem.map((m) => el("li", { text: m })));

  // the lecturer can only send a draft back a limited number of times
  const left = data.revisions_left;
  $("revise").hidden = left === 0;
  $("feedback").placeholder = left === 0
    ? "No more change requests left for this session."
    : "Fewer words on each slide. Add a harder quiz question.";
}

function showError(msg) {
  const box = $("error");
  box.textContent = msg;
  box.hidden = !msg;
}

/* ---------- API ---------- */
async function post(path, body) {
  const res = await fetch(API_BASE + path, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(body),
  });
  if (!res.ok) {
    // FastAPI puts the reason in "detail": a string, or a list of validation problems.
    let detail = "";
    try {
      const body = await res.json();
      detail = Array.isArray(body.detail) ? body.detail.map((d) => d.msg).join(". ") : body.detail;
    } catch (_) { /* the reply was not JSON */ }
    throw new Error(detail || `Server returned ${res.status}. Check that the backend is running.`);
  }
  return res.json();
}

function collectBrief() {
  const f = $("brief-form");
  const fd = new FormData(f);
  return {
    lecturer_id: fd.get("lecturer_id").trim(),
    topic: fd.get("topic").trim(),
    course_name: fd.get("course_name").trim(),
    student_level: fd.get("student_level"),
    duration_minutes: Number(fd.get("duration_minutes")),
    language: fd.get("language"),
    programming_language: fd.get("programming_language"),
    needs: fd.getAll("needs"),
    num_quiz_questions: Number(fd.get("num_quiz_questions")),
    learning_objectives: fd.get("learning_objectives").trim(),
    notes: fd.get("notes").trim(),
  };
}

/* ---------- actions ---------- */
$("brief-form").addEventListener("submit", async (e) => {
  e.preventDefault();
  showError("");

  const brief = collectBrief();
  ["lecturer", "topic"].forEach((id) => $(id).classList.toggle("invalid", !$(id).value.trim()));
  if (!brief.lecturer_id || !brief.topic) return showError("Enter your name and the session topic.");
  if (brief.needs.length === 0) return showError("Choose at least one thing to prepare.");

  const btn = $("generate");
  btn.disabled = true;
  btn.textContent = "Generating...";
  $("empty").hidden = true;
  $("result").hidden = true;
  $("files").hidden = true;
  setPipeline(brief.needs, "plan");

  try {
    const data = DEMO_MODE ? await demoStart(brief) : await post("/api/session", brief);
    sessionId = data.session_id;
    setPipeline(data.selected_agents.map((a) => a.replace("_agent", "")), "review");
    renderDraft(data);
    showTab("outline");
    $("review").hidden = false;
    $("result").hidden = false;
  } catch (err) {
    $("empty").hidden = false;
    setPipeline(null, "");
    showError(err.message);
  } finally {
    btn.disabled = false;
    btn.textContent = "Generate session";
  }
});

async function sendDecision(decision) {
  showError("");
  const payload = { session_id: sessionId, decision, feedback: $("feedback").value.trim() };
  if (decision === "revise" && !payload.feedback) return showError("Describe the changes you want first.");
  $("approve").disabled = $("revise").disabled = true;
  try {
    if (decision === "approve") {
      const data = DEMO_MODE ? await demoApprove() : await post("/api/session/approve", payload);
      setPipeline(null, "final");
      document.querySelectorAll("#pipeline li").forEach((li) => (li.className = "done"));
      $("files-list").replaceChildren(
        ...data.files.map((f) =>
          el("li", {}, [el("a", { href: f.url, text: f.name, download: f.name })])
        )
      );
      $("review").hidden = true;
      $("files").hidden = false;
    } else {
      setPipeline(null, "plan");
      const data = DEMO_MODE ? await demoStart(collectBrief()) : await post("/api/session/approve", payload);
      renderDraft(data);
      setPipeline(data.selected_agents.map((a) => a.replace("_agent", "")), "review");
      $("feedback").value = "";
    }
  } catch (err) {
    showError(err.message);
  } finally {
    $("approve").disabled = $("revise").disabled = false;
  }
}
$("approve").addEventListener("click", () => sendDecision("approve"));
$("revise").addEventListener("click", () => sendDecision("revise"));

/* ---------- demo data (remove when the backend is ready) ---------- */
const wait = (ms) => new Promise((r) => setTimeout(r, ms));

async function demoStart(brief) {
  await wait(900);
  return {
    session_id: "demo-thread-1",
    selected_agents: ["research_agent", "slides_agent", "code_agent", "quiz_agent"]
      .filter((a) => brief.needs.includes(a.replace("_agent", "")) || a === "research_agent"),
    reasoning: `You asked for ${brief.needs.join(", ")}. Research runs first so the other parts share one outline.`,
    revisions_left: 3,
    memory: ["Prefers short slides (5 bullets max).", "Teaches in English, code in Python."],
    draft: {
      outline: ["What a function is, as an object", "Closures", "Writing a decorator", "Decorators with arguments", "Hands-on exercise"],
      slides: [
        { title: "Functions are objects", bullets: ["Assign them to variables", "Pass them as arguments", "Return them from other functions"], notes: "Show a 3-line example live." },
        { title: "Writing a decorator", bullets: ["Wrap a function", "Add behavior before and after", "Use @ syntax"], notes: "Ask students to predict the output first." },
      ],
      code_examples: [
        {
          title: "A timing decorator",
          code: "import time\n\ndef timer(fn):\n    def wrapper(*args, **kwargs):\n        start = time.perf_counter()\n        result = fn(*args, **kwargs)\n        print(f'{fn.__name__} took {time.perf_counter() - start:.4f}s')\n        return result\n    return wrapper\n\n@timer\ndef work():\n    sum(range(1_000_000))\n\nwork()",
          explanation: "Prints the elapsed time of work().",
          verified: true,
        },
      ],
      quiz: [
        { question: "What does the @ syntax do?", options: ["Imports a module", "Applies a decorator to a function", "Creates a class", "Declares a variable"], answer_index: 1, explanation: "@d above a function is shorthand for f = d(f)." },
        { question: "Why do decorators usually accept *args and **kwargs?", options: ["To run faster", "To work with any function signature", "To avoid imports", "To hide errors"], answer_index: 1, explanation: "The wrapper must forward whatever arguments the original function takes." },
      ],
    },
  };
}

async function demoApprove() {
  await wait(700);
  return {
    status: "done",
    files: [
      { name: "python-decorators.pptx", url: "#" },
      { name: "examples.py", url: "#" },
      { name: "quiz.json", url: "#" },
    ],
  };
}
