// Mobile nav toggle
const toggle = document.querySelector(".nav-toggle");
const nav = document.getElementById("nav");
toggle.addEventListener("click", () => {
  const open = nav.classList.toggle("open");
  toggle.setAttribute("aria-expanded", open);
});
nav.addEventListener("click", (ev) => {
  if (ev.target.closest("a")) { nav.classList.remove("open"); toggle.setAttribute("aria-expanded", "false"); }
});

// Copy email
for (const btn of document.querySelectorAll(".copy")) {
  btn.addEventListener("click", async () => {
    const status = btn.nextElementSibling;
    try {
      await navigator.clipboard.writeText(btn.dataset.copy);
      status.textContent = "Copied";
    } catch {
      status.textContent = "Press Ctrl+C to copy";
      getSelection().selectAllChildren(btn.previousElementSibling);
    }
    setTimeout(() => (status.textContent = ""), 2500);
  });
}

// Lightbox: a native <dialog> handles Escape and focus trapping
const links = [...document.querySelectorAll("a.lb")];
if (links.length) {
  const dlg = document.createElement("dialog");
  dlg.className = "lightbox";
  dlg.setAttribute("aria-label", "Image viewer");
  dlg.innerHTML = '<button class="lb-close" type="button" aria-label="Close">Close ✕</button>' +
    '<button class="lb-prev" type="button" aria-label="Previous image">←</button>' +
    '<button class="lb-next" type="button" aria-label="Next image">→</button>' +
    '<figure style="margin:0"><img alt=""><p></p></figure>';
  document.body.append(dlg);
  const img = dlg.querySelector("img"), cap = dlg.querySelector("p");
  let i = 0;
  const show = (n) => {
    i = (n + links.length) % links.length;
    img.src = links[i].href;
    img.alt = links[i].querySelector("img").alt;
    cap.textContent = links[i].dataset.caption + (links.length > 1 ? `  (${i + 1} / ${links.length})` : "");
  };
  links.forEach((a, n) => a.addEventListener("click", (ev) => { ev.preventDefault(); show(n); dlg.showModal(); }));
  dlg.querySelector(".lb-close").addEventListener("click", () => dlg.close());
  dlg.querySelector(".lb-prev").addEventListener("click", () => show(i - 1));
  dlg.querySelector(".lb-next").addEventListener("click", () => show(i + 1));
  dlg.querySelector(".lb-prev").hidden = dlg.querySelector(".lb-next").hidden = links.length < 2;
  dlg.addEventListener("keydown", (ev) => {
    if (ev.key === "ArrowLeft") show(i - 1);
    if (ev.key === "ArrowRight") show(i + 1);
  });
  dlg.addEventListener("click", (ev) => { if (ev.target === dlg) dlg.close(); });
  dlg.addEventListener("close", () => links[i].focus());
}
