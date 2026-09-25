/* Scroll driver for the story page: highlights the active step and
   reveals harness pieces on the sticky rail. Degrades gracefully with
   JavaScript disabled (all content is server-rendered in the HTML). */
import { piecesForStep } from "./lib.js";

const steps = Array.from(document.querySelectorAll(".steps .step"));
const rail = document.querySelector(".rail");

function applyPieces(index) {
  if (!rail) {
    return;
  }
  const visible = new Set(piecesForStep(index));
  for (const el of rail.querySelectorAll("[data-piece]")) {
    el.classList.toggle("on", visible.has(el.dataset.piece));
  }
  const caption = rail.querySelector("figcaption");
  const active = steps[index];
  if (caption && active?.dataset.railCaption) {
    caption.textContent = active.dataset.railCaption;
  }
}

function activate(index) {
  steps.forEach((s, i) => {
    s.classList.toggle("is-active", i === index);
  });
  applyPieces(index);
}

if (steps.length > 0 && "IntersectionObserver" in window) {
  const observer = new IntersectionObserver(
    (entries) => {
      for (const entry of entries) {
        if (entry.isIntersecting) {
          activate(steps.indexOf(entry.target));
        }
      }
    },
    { rootMargin: "-40% 0px -45% 0px" },
  );
  for (const s of steps) {
    observer.observe(s);
  }
  activate(0);
} else if (steps.length > 0) {
  // No observer support: show everything.
  steps.forEach((s) => {
    s.classList.add("is-active");
  });
  applyPieces(steps.length - 1);
}
