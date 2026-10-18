const $ = (id) => document.getElementById(id);
const esc = (value) => String(value ?? "").replace(/[&<>"']/g, c => ({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#039;'}[c]));
const score = (value) => value == null ? "—" : Number(value).toFixed(2);
let queueItems = [];
let studentItems = [];
async function get(path) { const response = await fetch(path); if (!response.ok) throw new Error(await response.text()); return response.json(); }
function showError(message) { $("queue").innerHTML = `<div class="error">${esc(message)}</div>`; $("results").innerHTML = `<tr><td colspan="8" class="error">${esc(message)}</td></tr>`; }
function renderQueue(items) {
  queueItems = items;
  $("queue-count").textContent = items.length;
  $("queue").innerHTML = items.length ? items.map(item => `<article class="case">
    <div class="case-top"><div><div class="case-id">${esc(item.assessment_id)}</div><div class="case-meta">Question ${esc(item.question_id)} · <span class="badge review">LECTURER VALIDATION</span></div></div></div>
    <div class="metrics"><span>CARI <strong>${score(item.cari)}</strong></span><span>AI score <strong>${score(item.ai_score)}</strong></span><span>Gate <strong>${esc((item.gates || []).join(", ") || "—")}</strong></span></div>
    <div class="answer">${esc(item.student_response)}</div>
    <div class="case-actions"><button class="override" data-action="override" data-id="${esc(item.assessment_id)}">Override score</button><button class="approve" data-action="approve" data-id="${esc(item.assessment_id)}">Approve & release</button></div>
  </article>`).join("") : '<div class="empty">All caught up. No answers need validation.</div>';
  document.querySelectorAll("[data-action]").forEach(button => button.addEventListener("click", () => review(button.dataset.id, button.dataset.action)));
}
function renderResults(items) {
  $("results").innerHTML = items.length ? items.map(item => `<tr><td>${esc(item.assessment_id)}</td><td>${esc(item.question_id)}</td><td><strong>${score(item.final_score)}</strong>${item.max_score ? " / " + score(item.max_score) : ""}${item.review_action === "override" ? '<small class="score-note">Manual override</small>' : ""}</td><td>${score(item.cari)}</td><td><span class="route ${item.decision === "AUTO_RELEASE" ? "auto" : "manual"}">${item.decision === "AUTO_RELEASE" ? "Automatic" : item.review_action === "override" ? "Lecturer override" : "Lecturer approved"}</span></td><td class="review-note">${esc(item.review_note || "—")}</td><td>${esc(item.student_email || "—")}</td><td class="result-actions"><button class="edit-result" data-id="${esc(item.assessment_id)}">Edit score</button></td></tr>`).join("") : '<tr><td colspan="8" class="empty">No released results yet.</td></tr>';
  document.querySelectorAll(".edit-result").forEach(button => button.addEventListener("click", () => editResult(button.dataset.id)));
}
function renderStudentResults(items) {
  studentItems = items;
  $("student-results").innerHTML = items.length ? items.map(item => {
    const marks = Object.values(item.question_scores).map(value => value == null ? '<span class="pending-mark">Pending</span>' : `<span class="released-mark">${score(value)}</span>`).join(" · ");
    const status = item.complete ? "Ready to send" : item.released_questions ? `Partial release · ${item.released_questions}/5` : "Waiting for release";
    return `<tr><td><strong>${esc(item.student_id)}</strong>${item.sample_data ? '<small class="sample-label">Sample data</small>' : ""}</td><td>${esc(item.student_email)}</td><td>${marks}</td><td><strong>${score(item.total_score)} / ${score(item.max_total_score)}</strong></td><td><span class="status ${item.complete ? "ready" : item.released_questions ? "partial" : "waiting"}">${status}</span></td><td>${item.complete ? `<button class="email-student" data-id="${esc(item.student_id)}">Send final email</button>` : "—"}</td></tr>`;
  }).join("") : '<tr><td colspan="6" class="empty">No student totals yet.</td></tr>';
  document.querySelectorAll(".email-student").forEach(button => button.addEventListener("click", () => emailStudent(button.dataset.id)));
}
function filterQueue() {
  const query = $("queue-search").value.trim().toLowerCase();
  renderQueue(queueItems.filter(item => [
    item.assessment_id, item.question_id, item.student_response, item.reason,
    ...(item.gates || [])
  ].join(" ").toLowerCase().includes(query)));
}
function filterStudents() {
  const query = $("student-search").value.trim().toLowerCase();
  renderStudentResults(studentItems.filter(item => `${item.student_id} ${item.student_email}`.toLowerCase().includes(query)));
}
async function load() {
  try {
    const [dashboard, queue, released, reviewed, students] = await Promise.all([get("/dashboard"), get("/queue?limit=1000"), get("/results?status=released&limit=1000"), get("/results?status=reviewed&limit=1000"), get("/student-results")]);
    $("total").textContent = dashboard.total; $("released").textContent = dashboard.released; $("pending").textContent = dashboard.pending_validation; $("reviewed").textContent = dashboard.reviewed; $("release-rate").textContent = `${dashboard.release_rate}% of submitted answers`;
    renderQueue(queue); renderResults([...released, ...reviewed]); renderStudentResults(students);
  } catch (error) { showError("Unable to load dashboard. Is the API running?"); console.error(error); }
}
async function review(id, action) {
  let final_score = null, comment = null;
  if (action === "override") {
    final_score = prompt("Enter the lecturer's final score:");
    if (final_score === null || final_score.trim() === "" || Number.isNaN(Number(final_score))) return;
    comment = prompt("Add a review note (optional):") || null;
  }
  try { await fetch("/lecturer-decision", {method:"POST", headers:{"Content-Type":"application/json"}, body:JSON.stringify({assessment_id:id, action, final_score: final_score === null ? null : Number(final_score), comment})}).then(async response => { if (!response.ok) throw new Error(await response.text()); return response.json(); }); $("toast").textContent = action === "approve" ? "Result approved and released." : "Score override recorded."; $("toast").style.display = "block"; setTimeout(() => $("toast").style.display = "none", 3000); load(); } catch (error) { alert("Could not save the lecturer decision."); console.error(error); }
}
async function editResult(id) {
  const scoreValue = prompt("Enter the updated final score:");
  if (scoreValue === null || scoreValue.trim() === "" || Number.isNaN(Number(scoreValue))) return;
  const comment = prompt("Add a note about this score edit (optional):") || null;
  try {
    const response = await fetch(`/results/${encodeURIComponent(id)}/score`, {method:"PUT", headers:{"Content-Type":"application/json"}, body:JSON.stringify({final_score:Number(scoreValue), comment})});
    if (!response.ok) throw new Error(await response.text());
    notify("Score updated."); load();
  } catch (error) { alert("Could not update the score."); console.error(error); }
}
async function emailResult(id) {
  try {
    const response = await fetch(`/results/${encodeURIComponent(id)}/email`, {method:"POST"});
    const data = await response.json();
    if (!response.ok) throw new Error(data.detail || "Email failed");
    notify(`Sample feedback email prepared for ${data.recipient}.`);
    alert(`Sample email to ${data.recipient}\n\n${data.subject}\n\n${data.body}`);
  } catch (error) { alert(error.message); }
}
async function emailStudent(id) {
  try {
    const response = await fetch(`/students/${encodeURIComponent(id)}/email`, {method:"POST"});
    const data = await response.json();
    if (!response.ok) throw new Error(data.detail || "Email failed");
    notify(data.mode === "smtp" ? `Email sent to ${data.recipient}.` : `Sample email prepared for ${data.recipient}.`);
    alert(`Final feedback email\n\nTo: ${data.recipient}\n\n${data.body}`);
  } catch (error) { alert(error.message); }
}
function notify(message) { $("toast").textContent = message; $("toast").style.display = "block"; setTimeout(() => $("toast").style.display = "none", 3000); }
$("refresh").addEventListener("click", load);
$("queue-search").addEventListener("input", filterQueue);
$("student-search").addEventListener("input", filterStudents);
$("download").addEventListener("click", () => { window.location.href = "/results/export.csv"; });
$("filter").addEventListener("change", async event => { try { renderResults(event.target.value ? await get(`/results?status=${event.target.value}&limit=1000`) : [...await get("/results?status=released&limit=1000"), ...await get("/results?status=reviewed&limit=1000")]); } catch { alert("Could not load results."); } });
load();
