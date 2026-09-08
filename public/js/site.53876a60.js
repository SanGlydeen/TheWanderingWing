/* The Wandering Wing — progressive enhancement only.
   Everything here is optional; the site works fully without it. */

(function () {
  "use strict";

  var reduced = window.matchMedia("(prefers-reduced-motion: reduce)").matches;

  /* --- header goes solid once the hero is behind it ---------------- */

  var header = document.querySelector(".site-header--hero");
  if (header) {
    var onScroll = function () {
      header.classList.toggle("is-stuck", window.scrollY > 60);
    };
    onScroll();
    window.addEventListener("scroll", onScroll, { passive: true });
  }

  /* --- reveal sections on scroll ----------------------------------- */

  if (!reduced && "IntersectionObserver" in window) {
    var targets = document.querySelectorAll(
      ".feature, .card, .films__item, .band__title, .band__text, .intro .measure"
    );
    var io = new IntersectionObserver(function (entries) {
      entries.forEach(function (entry) {
        if (entry.isIntersecting) {
          entry.target.classList.add("is-in");
          io.unobserve(entry.target);
        }
      });
    }, { rootMargin: "0px 0px -8% 0px", threshold: 0.05 });

    targets.forEach(function (el) {
      el.classList.add("reveal");
      io.observe(el);
    });
  }

  /* --- YouTube facade ---------------------------------------------
     The poster is a plain image until clicked, so no YouTube script
     or cookie is loaded for visitors who never press play.          */

  document.querySelectorAll("[data-youtube]").forEach(function (box) {
    var play = function () {
      if (box.classList.contains("is-playing")) return;
      var id = box.getAttribute("data-youtube");
      var frame = document.createElement("iframe");
      frame.src =
        "https://www.youtube-nocookie.com/embed/" + id +
        "?autoplay=1&rel=0&modestbranding=1";
      frame.title = box.getAttribute("aria-label") || "Film";
      frame.allow =
        "accelerometer; autoplay; clipboard-write; encrypted-media; " +
        "gyroscope; picture-in-picture; web-share";
      frame.allowFullscreen = true;
      frame.loading = "lazy";
      box.appendChild(frame);
      box.classList.add("is-playing");
    };

    box.addEventListener("click", play);
    box.addEventListener("keydown", function (e) {
      if (e.key === "Enter" || e.key === " ") {
        e.preventDefault();
        play();
      }
    });
  });


  /* --- carousel -----------------------------------------------------
     Enhancement only: without this the track stays a scroll-snapping
     horizontal scroller, so every photograph is still reachable.      */

  document.querySelectorAll("[data-carousel]").forEach(function (root) {
    var track = root.querySelector(".carousel__track");
    var slides = Array.prototype.slice.call(root.querySelectorAll(".carousel__slide"));
    var prev = root.querySelector(".carousel__nav--prev");
    var next = root.querySelector(".carousel__nav--next");
    var count = root.querySelector(".carousel__count");
    if (slides.length < 2) {
      if (prev) prev.hidden = true;
      if (next) next.hidden = true;
    }
    var at = 0;

    function go(i) {
      at = (i + slides.length) % slides.length;
      track.style.transform = "translateX(" + (-at * 100) + "%)";
      if (count) count.textContent = at + 1 + " / " + slides.length;
      slides.forEach(function (s, n) {
        s.setAttribute("aria-hidden", n === at ? "false" : "true");
        var img = s.querySelector("img");
        // Neighbours are fetched early so arrowing through feels instant.
        if (img && Math.abs(n - at) <= 1) img.loading = "eager";
      });
    }

    root.classList.add("is-ready");
    go(0);

    if (prev) prev.addEventListener("click", function () { go(at - 1); });
    if (next) next.addEventListener("click", function () { go(at + 1); });

    root.addEventListener("keydown", function (e) {
      if (e.key === "ArrowLeft") { e.preventDefault(); go(at - 1); }
      else if (e.key === "ArrowRight") { e.preventDefault(); go(at + 1); }
    });

    var x0 = null;
    root.addEventListener("touchstart", function (e) {
      x0 = e.changedTouches[0].clientX;
    }, { passive: true });
    root.addEventListener("touchend", function (e) {
      if (x0 === null) return;
      var dx = e.changedTouches[0].clientX - x0;
      if (Math.abs(dx) > 45) go(at + (dx < 0 ? 1 : -1));
      x0 = null;
    }, { passive: true });
  });

  /* --- lightbox ----------------------------------------------------- */

  var cells = Array.prototype.slice.call(
    document.querySelectorAll(".grid__cell[data-full], .carousel__slide[data-full]")
  );
  if (!cells.length) return;

  var box = document.createElement("div");
  box.className = "lightbox";
  box.setAttribute("role", "dialog");
  box.setAttribute("aria-modal", "true");
  box.setAttribute("aria-label", "Photograph");
  box.innerHTML =
    '<button class="lightbox__btn lightbox__close" aria-label="Close">&times;</button>' +
    '<button class="lightbox__btn lightbox__prev" aria-label="Previous">&#8249;</button>' +
    '<button class="lightbox__btn lightbox__next" aria-label="Next">&#8250;</button>' +
    '<img alt=""><p class="lightbox__count"></p>';
  document.body.appendChild(box);

  var image = box.querySelector("img");
  var count = box.querySelector(".lightbox__count");
  var index = 0;
  var lastFocus = null;

  function show(i) {
    index = (i + cells.length) % cells.length;
    var cell = cells[index];
    image.src = cell.getAttribute("data-full");
    image.alt = cell.getAttribute("data-alt") || "";
    count.textContent = index + 1 + " / " + cells.length;
    // Warm the neighbours so arrowing through feels instant.
    [index + 1, index - 1].forEach(function (n) {
      var neighbour = cells[(n + cells.length) % cells.length];
      new Image().src = neighbour.getAttribute("data-full");
    });
  }

  function open(i) {
    lastFocus = document.activeElement;
    show(i);
    box.classList.add("is-open");
    document.body.style.overflow = "hidden";
    box.querySelector(".lightbox__close").focus();
  }

  function close() {
    box.classList.remove("is-open");
    document.body.style.overflow = "";
    if (lastFocus) lastFocus.focus();
  }

  cells.forEach(function (cell, i) {
    cell.addEventListener("click", function () { open(i); });
  });

  box.querySelector(".lightbox__close").addEventListener("click", close);
  box.querySelector(".lightbox__prev").addEventListener("click", function (e) {
    e.stopPropagation();
    show(index - 1);
  });
  box.querySelector(".lightbox__next").addEventListener("click", function (e) {
    e.stopPropagation();
    show(index + 1);
  });
  box.addEventListener("click", function (e) {
    if (e.target === box || e.target === image) close();
  });

  document.addEventListener("keydown", function (e) {
    if (!box.classList.contains("is-open")) return;
    if (e.key === "Escape") close();
    else if (e.key === "ArrowRight") show(index + 1);
    else if (e.key === "ArrowLeft") show(index - 1);
  });

  /* Swipe on touch devices. */
  var startX = null;
  box.addEventListener("touchstart", function (e) {
    startX = e.changedTouches[0].clientX;
  }, { passive: true });
  box.addEventListener("touchend", function (e) {
    if (startX === null) return;
    var dx = e.changedTouches[0].clientX - startX;
    if (Math.abs(dx) > 45) show(index + (dx < 0 ? 1 : -1));
    startX = null;
  }, { passive: true });
})();
