(() => {
  "use strict";

  const root = document.documentElement;
  const danceToggle = document.querySelector("#dance-toggle");
  const danceLabel = danceToggle?.querySelector(".dance-label");
  const danceIcon = danceToggle?.querySelector(".play-icon");
  const danceVideo = document.querySelector("#hero-dance-video");
  const motionToggle = document.querySelector("#motion-toggle");
  const motionLabel = motionToggle?.querySelector(".motion-label");
  const visualStatus = document.querySelector("#visual-status");
  const mobileNavToggle = document.querySelector("#mobile-nav-toggle");
  const mobileNav = document.querySelector("#mobile-nav");
  const siteHeader = document.querySelector(".site-header");
  const hero = document.querySelector("#home");
  const reducedMotion = window.matchMedia("(prefers-reduced-motion: reduce)");

  let audioContext = null;
  let beatTimer = null;
  let beatCount = 0;
  let audioTransitioning = false;
  let pageIsUnloading = false;
  let headerFrame = null;

  function updateHeaderState() {
    if (!siteHeader) return;
    const threshold = hero ? hero.offsetHeight * 0.5 : window.innerHeight * 0.5;
    siteHeader.classList.toggle("is-scrolled", window.scrollY >= threshold);
    headerFrame = null;
  }

  function queueHeaderStateUpdate() {
    if (headerFrame !== null) return;
    headerFrame = window.requestAnimationFrame(updateHeaderState);
  }

  window.addEventListener("scroll", queueHeaderStateUpdate, { passive: true });
  window.addEventListener("resize", queueHeaderStateUpdate);
  updateHeaderState();

  function announce(message) {
    if (!visualStatus) return;
    visualStatus.textContent = message;
    visualStatus.classList.remove("status-pulse");
    void visualStatus.offsetWidth;
    visualStatus.classList.add("status-pulse");
  }

  visualStatus?.addEventListener("animationend", (event) => {
    if (event.animationName === "status-pulse") {
      visualStatus.classList.remove("status-pulse");
    }
  });

  function clearBeatTimer() {
    if (beatTimer !== null) {
      window.clearInterval(beatTimer);
      beatTimer = null;
    }
  }

  function hasApprovedDanceVideo() {
    const source = danceVideo?.getAttribute("src")?.trim();
    const ready = Boolean(source);
    root.classList.toggle("has-dance-video", ready);
    if (danceVideo) {
      danceVideo.dataset.videoState = ready ? "ready" : "awaiting-source";
    }
    return ready;
  }

  function setDanceUi(active) {
    root.classList.toggle("is-dancing", active);
    danceToggle?.setAttribute("aria-pressed", String(active));
    danceVideo?.setAttribute("aria-hidden", String(!active));
    if (danceLabel) danceLabel.textContent = active ? "Pause the dance" : "Join the dance";
    if (danceIcon) danceIcon.textContent = active ? "Ⅱ" : "▶";
  }

  function setAudioTransitioning(transitioning) {
    audioTransitioning = transitioning;
    if (!danceToggle) return;
    danceToggle.disabled = transitioning;
    if (transitioning) {
      danceToggle.setAttribute("aria-busy", "true");
    } else {
      danceToggle.removeAttribute("aria-busy");
    }
  }

  async function closeAudioContext(context) {
    if (!context) return true;

    let closed = true;
    try {
      if (context.state !== "closed") {
        await context.close();
      }
    } catch (error) {
      closed = false;
      console.warn("The audio context could not be closed cleanly.", error);
      try {
        if (context.state === "running") {
          await context.suspend();
        }
      } catch (suspendError) {
        console.warn("The audio context could not be suspended after close failed.", suspendError);
      }
    } finally {
      if (audioContext === context) audioContext = null;
    }

    return closed;
  }

  function makeBeat() {
    if (!audioContext || audioContext.state !== "running") return;

    const oscillator = audioContext.createOscillator();
    const gain = audioContext.createGain();
    const now = audioContext.currentTime;
    const accented = beatCount % 4 === 0;

    oscillator.type = accented ? "sine" : "triangle";
    oscillator.frequency.setValueAtTime(accented ? 92 : 138, now);
    oscillator.frequency.exponentialRampToValueAtTime(54, now + 0.11);
    gain.gain.setValueAtTime(accented ? 0.055 : 0.025, now);
    gain.gain.exponentialRampToValueAtTime(0.0001, now + 0.13);

    oscillator.connect(gain);
    gain.connect(audioContext.destination);
    oscillator.start(now);
    oscillator.stop(now + 0.14);
    beatCount += 1;
  }

  async function startDance() {
    if (audioTransitioning || root.classList.contains("is-dancing")) return;

    if (hasApprovedDanceVideo() && danceVideo) {
      setAudioTransitioning(true);
      try {
        await danceVideo.play();
        if (pageIsUnloading || document.hidden) {
          danceVideo.pause();
          setDanceUi(false);
          announce("Dance video was not started while the page is hidden.");
          return;
        }
        setDanceUi(true);
        announce("Dance video started in loop mode.");
      } catch (error) {
        danceVideo.pause();
        setDanceUi(false);
        console.warn("Dance video could not start.", error);
        announce("Dance video could not start. Try again.");
      } finally {
        setAudioTransitioning(false);
      }
      return;
    }

    const AudioContextClass = window.AudioContext || window.webkitAudioContext;
    setDanceUi(true);
    if (!AudioContextClass || !danceToggle || !danceLabel) {
      clearBeatTimer();
      audioContext = null;
      announce("Dance animation started without audio.");
      return;
    }

    setAudioTransitioning(true);
    let nextContext = null;

    try {
      nextContext = new AudioContextClass();
      audioContext = nextContext;

      try {
        if (nextContext.state !== "running") {
          await nextContext.resume();
        }
      } catch (error) {
        console.warn("The audio context could not be resumed.", error);
        throw error;
      }

      if (nextContext.state !== "running") {
        throw new Error("The audio context did not enter the running state.");
      }

      if (pageIsUnloading) {
        await closeAudioContext(nextContext);
        setDanceUi(false);
        announce("Dance mode was not started while the page is unloading.");
        return;
      }

      if (document.hidden) {
        await closeAudioContext(nextContext);
        announce("Dance animation started without audio while the page is hidden.");
        return;
      }

      clearBeatTimer();
      beatCount = 0;
      makeBeat();
      beatTimer = window.setInterval(makeBeat, 60000 / 128);
      setDanceUi(true);
      announce("Dance mode started at 128 BPM.");
    } catch (error) {
      console.warn("Dance mode could not start.", error);
      clearBeatTimer();
      beatCount = 0;
      await closeAudioContext(nextContext || audioContext);
      setDanceUi(true);
      announce("Dance animation started; browser audio is unavailable.");
    } finally {
      setAudioTransitioning(false);
    }
  }

  async function stopDance() {
    if (audioTransitioning) return;

    setAudioTransitioning(true);
    const contextToClose = audioContext;
    let closed = true;

    try {
      clearBeatTimer();
      danceVideo?.pause();
      setDanceUi(false);
      if (danceVideo) danceVideo.currentTime = 0;
      closed = await closeAudioContext(contextToClose);
    } catch (error) {
      closed = false;
      console.warn("Dance mode cleanup failed.", error);
    } finally {
      clearBeatTimer();
      audioContext = null;
      beatCount = 0;
      setDanceUi(false);
      setAudioTransitioning(false);
    }

    announce(closed ? "Dance mode paused." : "Dance mode paused; browser audio cleanup was limited.");
  }

  danceToggle?.addEventListener("click", () => {
    if (audioTransitioning) return;
    if (root.classList.contains("is-dancing")) {
      void stopDance();
    } else {
      void startDance();
    }
  });

  motionToggle?.addEventListener("click", () => {
    const paused = motionToggle.getAttribute("aria-pressed") !== "true";
    root.classList.toggle("motion-paused", paused);
    motionToggle.setAttribute("aria-pressed", String(paused));
    motionToggle.setAttribute("aria-label", paused ? "Resume decorative motion" : "Pause decorative motion");
    if (motionLabel) motionLabel.textContent = paused ? "Resume motion" : "Pause motion";
    announce(paused ? "Decorative motion paused." : "Decorative motion resumed.");
  });

  document.querySelectorAll(".pending-action, [data-link]").forEach((action) => {
    action.addEventListener("click", (event) => {
      if (!action.classList.contains("pending-action") && action.getAttribute("aria-disabled") !== "true") return;
      event.preventDefault();
      const message = action.dataset.pendingMessage || "This verified link is not available yet.";
      announce(message);
    });
  });

  document.querySelectorAll("[data-copy-contract]").forEach((button) => {
    button.addEventListener("click", async () => {
      const value = button.dataset.copyValue;
      if (!value || !navigator.clipboard?.writeText) {
        announce("The contract address is not available yet.");
        return;
      }
      try {
        await navigator.clipboard.writeText(value);
        announce("Contract address copied.");
      } catch (error) {
        console.warn("The contract address could not be copied.", error);
        announce("Contract address could not be copied.");
      }
    });
  });

  function setMobileNavOpen(open, returnFocus = false) {
    if (!mobileNav || !mobileNavToggle) return;
    mobileNav.classList.toggle("is-open", open);
    mobileNavToggle.setAttribute("aria-expanded", String(open));
    mobileNavToggle.textContent = open ? "Close" : "Menu";
    if (returnFocus) mobileNavToggle.focus();
  }

  mobileNavToggle?.addEventListener("click", () => {
    const open = mobileNavToggle.getAttribute("aria-expanded") !== "true";
    setMobileNavOpen(open);
  });

  mobileNav?.querySelectorAll("a").forEach((link) => {
    link.addEventListener("click", () => setMobileNavOpen(false));
  });

  document.addEventListener("keydown", (event) => {
    if (event.key === "Escape" && mobileNavToggle?.getAttribute("aria-expanded") === "true") {
      setMobileNavOpen(false, true);
    }
  });

  const mobileBreakpoint = window.matchMedia("(max-width: 980px)");
  const handleBreakpointChange = (event) => {
    if (!event.matches) setMobileNavOpen(false);
  };
  if (typeof mobileBreakpoint.addEventListener === "function") {
    mobileBreakpoint.addEventListener("change", handleBreakpointChange);
  } else {
    mobileBreakpoint.addListener(handleBreakpointChange);
  }

  const revealItems = document.querySelectorAll(".reveal");
  if (!reducedMotion.matches && "IntersectionObserver" in window) {
    let observer = null;
    try {
      observer = new IntersectionObserver((entries, currentObserver) => {
        entries.forEach((entry) => {
          if (!entry.isIntersecting) return;
          entry.target.classList.add("is-visible");
          currentObserver.unobserve(entry.target);
        });
      }, { threshold: 0.12, rootMargin: "0px 0px -6%" });
    } catch (error) {
      console.warn("Reveal observer could not be prepared; content remains visible.", error);
    }

    if (observer) {
      try {
        revealItems.forEach((item) => observer.observe(item));
        root.classList.add("js-ready");
      } catch (error) {
        observer.disconnect();
        root.classList.remove("js-ready");
        console.warn("Reveal items could not be observed; content remains visible.", error);
      }
    }
  }

  document.addEventListener("visibilitychange", () => {
    if (document.hidden && root.classList.contains("is-dancing")) {
      void stopDance();
    }
  });

  window.addEventListener("pagehide", () => {
    pageIsUnloading = true;
    clearBeatTimer();
    beatCount = 0;
    setDanceUi(false);
    danceVideo?.pause();
    const contextToClose = audioContext;
    audioContext = null;
    void closeAudioContext(contextToClose);
  });

  window.addEventListener("pageshow", () => {
    pageIsUnloading = false;
  });

  hasApprovedDanceVideo();
})();
