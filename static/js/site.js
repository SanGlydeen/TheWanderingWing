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



  /* --- immersive hover ------------------------------------------------
     Hovering a homepage photograph opens it to the whole screen, and it
     closes the moment the pointer leaves the patch of page the photograph
     came from.

     The expanded frame is a separate overlay appended to <body>, not the
     original element repositioned. A `position: fixed` element resolves
     against the nearest transformed ancestor rather than the viewport,
     and .feature carries a transform from the scroll-reveal — which sized
     the "fullscreen" frame to the feature block and pushed the card off
     the edge of the screen. An overlay on <body> cannot be captured that
     way, and leaves the page layout untouched.                          */

  var fine = window.matchMedia("(hover: hover) and (pointer: fine)");
  var wide = window.matchMedia("(min-width: 901px)");

  if (!reduced && fine.matches) {
    var overlay = null;
    var homeRect = null;

    function close() {
      if (!overlay) return;
      var node = overlay;
      var r = homeRect;
      overlay = null;
      homeRect = null;

      node.classList.remove("is-open");
      var frame = node.querySelector(".immersive__frame");
      frame.style.top = r.top + "px";
      frame.style.left = r.left + "px";
      frame.style.width = r.width + "px";
      frame.style.height = r.height + "px";

      var remove = function () { if (node.parentNode) node.remove(); };
      frame.addEventListener("transitionend", remove);
      setTimeout(remove, 700);
    }

    function open(feature) {
      if (overlay || !wide.matches) return;
      var media = feature.querySelector(".feature__media");
      var img = media && media.querySelector("img");
      var body = feature.querySelector(".feature__body");
      if (!img) return;

      var r = media.getBoundingClientRect();
      homeRect = { top: r.top, left: r.left, width: r.width, height: r.height };

      overlay = document.createElement("div");
      overlay.className = "immersive";
      if (feature.classList.contains("feature--right")) {
        overlay.classList.add("immersive--right");
      }

      var frame = document.createElement("div");
      frame.className = "immersive__frame";
      frame.style.top = r.top + "px";
      frame.style.left = r.left + "px";
      frame.style.width = r.width + "px";
      frame.style.height = r.height + "px";

      var copy = img.cloneNode(true);
      copy.removeAttribute("loading");
      copy.sizes = "100vw";
      frame.appendChild(copy);

      var card = document.createElement("div");
      card.className = "immersive__card";
      card.innerHTML = body ? body.innerHTML : "";

      overlay.appendChild(frame);
      overlay.appendChild(card);
      document.body.appendChild(overlay);

      // Reading the box flushes the starting geometry so the change below
      // animates from it. No rAF: its callbacks pause while a tab is
      // hidden, which left the state half-applied.
      frame.getBoundingClientRect();

      frame.style.top = "0px";
      frame.style.left = "0px";
      frame.style.width = "100%";
      frame.style.height = "100%";
      overlay.classList.add("is-open");
    }

    document.querySelectorAll(".feature").forEach(function (feature) {
      var media = feature.querySelector(".feature__media");
      if (!media) return;
      media.addEventListener("mouseenter", function () { open(feature); });
    });

    // Once expanded the photograph sits under the pointer, so leaving
    // cannot be read from the element. The pointer is tested against the
    // box the frame came from instead.
    document.addEventListener("mousemove", function (e) {
      if (!homeRect) return;
      var pad = 4;
      if (e.clientX < homeRect.left - pad ||
          e.clientX > homeRect.left + homeRect.width + pad ||
          e.clientY < homeRect.top - pad ||
          e.clientY > homeRect.top + homeRect.height + pad) {
        close();
      }
    }, { passive: true });

    document.addEventListener("keydown", function (e) {
      if (e.key === "Escape") close();
    });
    window.addEventListener("scroll", close, { passive: true });
    window.addEventListener("resize", close, { passive: true });
  }

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
  // Drawn rather than typed: serif punctuation rendered as thin ornament
  // at this size and read as decoration instead of a control.
  var chevron = '<svg viewBox="0 0 24 24" aria-hidden="true"><path d="M15 4 L7 12 L15 20" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/></svg>';
  box.innerHTML =
    '<button class="lightbox__btn lightbox__close" aria-label="Close">' +
      '<svg viewBox="0 0 24 24" aria-hidden="true"><path d="M5 5 L19 19 M19 5 L5 19" ' +
      'fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round"/></svg>' +
    '</button>' +
    '<button class="lightbox__btn lightbox__prev" aria-label="Previous">' + chevron + '</button>' +
    '<button class="lightbox__btn lightbox__next" aria-label="Next">' + chevron + '</button>' +
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
