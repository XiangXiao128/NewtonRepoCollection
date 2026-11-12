"use strict";

document.querySelectorAll(".demo-group").forEach((group) => {
  const carousel = group.querySelector(".carousel");
  const slides = Array.from(carousel.querySelectorAll(".slide"));
  const previous = group.querySelector('[data-direction="-1"]');
  const next = group.querySelector('[data-direction="1"]');
  const count = group.querySelector(".slide-count");
  const reducedMotion = window.matchMedia("(prefers-reduced-motion: reduce)");
  let index = 0;
  let targetIndex = 0;
  let scheduled = false;
  let playingIndex = -1;

  // Muted playback can start without a click under browser autoplay policies.
  slides.forEach((slide) => { slide.querySelector("video").muted = true; });

  function update() {
    const width = carousel.clientWidth;
    index = width ? Math.max(0, Math.min(slides.length - 1, Math.round(carousel.scrollLeft / width))) : 0;
    targetIndex = index;
    previous.disabled = index === 0;
    next.disabled = index === slides.length - 1;
    count.textContent = `${index + 1} / ${slides.length}`;
    slides.forEach((slide, i) => {
      if (i !== index) slide.querySelector("video").pause();
    });
    if (playingIndex !== index) {
      playingIndex = index;
      const playback = slides[index].querySelector("video").play();
      // Keep the controls usable if browser settings prevent autoplay.
      if (playback) playback.catch(() => {});
    }
  }

  function go(direction) {
    targetIndex = Math.max(0, Math.min(slides.length - 1, targetIndex + direction));
    carousel.scrollTo({
      left: carousel.clientWidth * targetIndex,
      behavior: reducedMotion.matches ? "auto" : "smooth",
    });
  }

  previous.addEventListener("click", () => go(-1));
  next.addEventListener("click", () => go(1));
  carousel.addEventListener("keydown", (event) => {
    // Preserve the video player's own keyboard controls.
    if (event.target !== carousel) return;
    if (event.key === "ArrowLeft" || event.key === "ArrowRight") {
      event.preventDefault();
      go(event.key === "ArrowLeft" ? -1 : 1);
    }
  });
  carousel.addEventListener("scroll", () => {
    if (scheduled) return;
    scheduled = true;
    requestAnimationFrame(() => {
      update();
      scheduled = false;
    });
  }, { passive: true });
  window.addEventListener("resize", () => {
    carousel.scrollTo({ left: carousel.clientWidth * index, behavior: "auto" });
    update();
  });
  update();
});
