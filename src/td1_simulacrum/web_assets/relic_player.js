(() => {
  "use strict";

  const NS = "http://www.w3.org/2000/svg";
  const speedSteps = [0.5, 1, 2, 4];

  const state = {
    manifest: null,
    timeline: null,
    morphs: null,
    frameIndex: 0,
    playing: false,
    transitioning: false,
    speed: 1,
    timer: null,
    projection: null,
    engineering: false,
    provenance: false,
    verified: false,
  };

  const stage = document.getElementById("td1-stage");
  const verification = document.getElementById("td1-verification");
  const playButton = document.getElementById("td1-play");
  const prevButton = document.getElementById("td1-prev");
  const nextButton = document.getElementById("td1-next");
  const restartButton = document.getElementById("td1-restart");
  const speedButton = document.getElementById("td1-speed");
  const engineeringButton = document.getElementById("td1-engineering");
  const provenanceButton = document.getElementById("td1-provenance");
  const engineeringPanel = document.getElementById("td1-engineering-panel");
  const provenancePanel = document.getElementById("td1-provenance-panel");

  function payloadElement(id) {
    const element = document.getElementById(id);
    if (!element) {
      throw new Error(`missing embedded payload ${id}`);
    }
    return element;
  }

  function decodeBase64(text) {
    const binary = atob(text.trim());
    const bytes = new Uint8Array(binary.length);
    for (let index = 0; index < binary.length; index += 1) {
      bytes[index] = binary.charCodeAt(index);
    }
    return bytes;
  }

  function decodeJson(bytes) {
    return JSON.parse(new TextDecoder("utf-8", { fatal: true }).decode(bytes));
  }

  async function sha256Hex(bytes) {
    if (!globalThis.crypto || !globalThis.crypto.subtle) {
      throw new Error("WebCrypto SubtleCrypto is unavailable; payload verification cannot run");
    }
    const digest = await globalThis.crypto.subtle.digest("SHA-256", bytes);
    return Array.from(new Uint8Array(digest), (byte) => byte.toString(16).padStart(2, "0")).join("");
  }

  async function loadAndVerifyPayloads() {
    const manifestElement = payloadElement("td1-manifest");
    const manifestBytes = decodeBase64(manifestElement.textContent);
    const manifestDigest = await sha256Hex(manifestBytes);
    const expectedManifestDigest = manifestElement.dataset.sha256;
    if (manifestDigest !== expectedManifestDigest) {
      throw new Error("embedded Relic player manifest digest mismatch");
    }

    const manifest = decodeJson(manifestBytes);
    if (manifest.schema !== "td1.relic-player-artifact" || manifest.version !== 1) {
      throw new Error("unsupported Relic player artifact schema");
    }

    const timelineBytes = decodeBase64(payloadElement("td1-timeline").textContent);
    const morphBytes = decodeBase64(payloadElement("td1-morphs").textContent);
    const [timelineDigest, morphDigest] = await Promise.all([
      sha256Hex(timelineBytes),
      sha256Hex(morphBytes),
    ]);

    if (timelineDigest !== manifest.timeline_bytes_sha256) {
      throw new Error("embedded timeline payload digest mismatch");
    }
    if (morphDigest !== manifest.morph_manifest_bytes_sha256) {
      throw new Error("embedded morph-manifest payload digest mismatch");
    }

    const timeline = decodeJson(timelineBytes);
    const morphs = decodeJson(morphBytes);
    if (timeline.schema !== "td1.relic-timeline") {
      throw new Error("embedded payload is not a TD-1 Relic timeline");
    }
    if (morphs.schema !== "td1.timeline-morph-manifest") {
      throw new Error("embedded payload is not a TD-1 timeline morph manifest");
    }
    if (morphs.timeline_digest !== manifest.timeline_digest) {
      throw new Error("morph manifest is linked to a different timeline digest");
    }
    if (timelineDigest !== manifest.timeline_digest) {
      throw new Error("timeline canonical-byte digest disagrees with artifact manifest");
    }
    if (morphDigest !== manifest.morph_manifest_digest) {
      throw new Error("morph canonical-byte digest disagrees with artifact manifest");
    }
    if (timeline.frames.length !== manifest.frame_count) {
      throw new Error("timeline frame count disagrees with artifact manifest");
    }
    if (morphs.entries.length !== timeline.frames.length - 1) {
      throw new Error("morph manifest cardinality disagrees with timeline");
    }

    state.manifest = manifest;
    state.timeline = timeline;
    state.morphs = morphs;
    state.verified = true;
    verification.dataset.state = "verified";
    verification.title = "TD-1 payload provenance verified";
    verification.setAttribute("aria-label", "TD-1 payload provenance verified");
  }

  function projectPoint(point) {
    const [q, r, z] = point;
    const { unit, depth_x: depthX, depth_y: depthY } = state.manifest.projection;
    return {
      x: (2 * q + r) * unit + z * depthX,
      y: 3 * r * unit - z * depthY,
    };
  }

  function projectTranslation(translation) {
    const [dq, dr, dz] = translation;
    const { unit, depth_x: depthX, depth_y: depthY } = state.manifest.projection;
    return {
      x: (2 * dq + dr) * unit + dz * depthX,
      y: 3 * dr * unit - dz * depthY,
    };
  }

  function computeProjectionBounds() {
    const points = [];
    for (const frame of state.timeline.frames) {
      for (const primitive of frame.scene.primitives) {
        for (const point of primitive.points) {
          points.push(projectPoint(point));
        }
      }
    }
    if (points.length === 0) {
      throw new Error("Relic timeline contains no renderable geometry");
    }
    const margin = state.manifest.projection.margin;
    const minX = Math.min(...points.map((point) => point.x));
    const maxX = Math.max(...points.map((point) => point.x));
    const minY = Math.min(...points.map((point) => point.y));
    const maxY = Math.max(...points.map((point) => point.y));
    const width = Math.max(1, maxX - minX + 2 * margin);
    const height = Math.max(1, maxY - minY + 2 * margin);
    state.projection = {
      translateX: margin - minX,
      translateY: margin - minY,
      width,
      height,
    };
    stage.setAttribute("viewBox", `0 0 ${width} ${height}`);
    stage.setAttribute("preserveAspectRatio", "xMidYMid meet");
  }

  function shifted(point) {
    const projected = projectPoint(point);
    return {
      x: projected.x + state.projection.translateX,
      y: projected.y + state.projection.translateY,
    };
  }

  function strokeWidth(primitive) {
    return Math.max(1, Math.min(6, Math.floor((primitive.scale_milli + 999) / 1000)));
  }

  function nodeRadius(primitive) {
    return Math.max(2, Math.min(8, 1 + Math.floor((primitive.scale_milli + 999) / 1000)));
  }

  function applyPrimitiveMetadata(element, primitive) {
    element.classList.add("td1-primitive", `td1-${primitive.kind}`);
    element.dataset.primitiveId = primitive.primitive_id;
    element.dataset.kind = primitive.kind;
    element.dataset.role = primitive.role;
    element.dataset.scaleMilli = String(primitive.scale_milli);
    if (primitive.glyph_id !== undefined) {
      element.dataset.glyphId = String(primitive.glyph_id);
    }
    if (primitive.semantic_root_id !== undefined) {
      element.dataset.semanticRootId = String(primitive.semantic_root_id);
    }
    if (primitive.state_value !== undefined) {
      element.dataset.stateValue = String(primitive.state_value);
    }
    if (primitive.motifs) {
      element.dataset.motifs = primitive.motifs.join(",");
    }
    element.setAttribute("stroke-width", String(strokeWidth(primitive)));
  }

  function primitiveElement(primitive, transient = false) {
    let element;
    if (primitive.kind === "node") {
      element = document.createElementNS(NS, "circle");
      const point = shifted(primitive.points[0]);
      element.setAttribute("cx", String(point.x));
      element.setAttribute("cy", String(point.y));
      element.setAttribute("r", String(nodeRadius(primitive)));
    } else if (primitive.kind === "segment") {
      element = document.createElementNS(NS, "line");
      const start = shifted(primitive.points[0]);
      const end = shifted(primitive.points[1]);
      element.setAttribute("x1", String(start.x));
      element.setAttribute("y1", String(start.y));
      element.setAttribute("x2", String(end.x));
      element.setAttribute("y2", String(end.y));
    } else if (primitive.kind === "polyline") {
      element = document.createElementNS(NS, "polyline");
      const points = primitive.points
        .map((point) => shifted(point))
        .map((point) => `${point.x},${point.y}`)
        .join(" ");
      element.setAttribute("points", points);
    } else {
      throw new Error(`unsupported geometry primitive ${primitive.kind}`);
    }
    applyPrimitiveMetadata(element, primitive);
    if (transient) {
      element.classList.add("td1-transient");
    }
    return element;
  }

  function geometryLayer() {
    let layer = stage.querySelector("#td1-native-geometry");
    if (!layer) {
      layer = document.createElementNS(NS, "g");
      layer.id = "td1-native-geometry";
      stage.appendChild(layer);
    }
    return layer;
  }

  function currentElements() {
    const map = new Map();
    for (const element of geometryLayer().children) {
      if (!element.classList.contains("td1-transient") && element.dataset.primitiveId) {
        map.set(element.dataset.primitiveId, element);
      }
    }
    return map;
  }

  function reconcileScene(frameIndex) {
    const frame = state.timeline.frames[frameIndex];
    const layer = geometryLayer();
    const fragment = document.createDocumentFragment();
    for (const primitive of frame.scene.primitives) {
      fragment.appendChild(primitiveElement(primitive));
    }
    layer.replaceChildren(fragment);
    state.frameIndex = frameIndex;
    stage.dataset.frameIndex = String(frameIndex);
    stage.dataset.sceneDigest = frame.scene_digest;
    stage.dataset.machineDigest = frame.machine_digest;
    updatePanels();
  }

  function effectiveDuration(milliseconds) {
    if (window.matchMedia("(prefers-reduced-motion: reduce)").matches) {
      return 0;
    }
    return Math.max(0, Math.round(milliseconds / state.speed));
  }

  function animateElement(element, keyframes, duration) {
    if (duration <= 0) {
      return Promise.resolve();
    }
    const animation = element.animate(keyframes, {
      duration,
      easing: state.manifest.config.easing,
      fill: "forwards",
    });
    return animation.finished.catch(() => undefined);
  }

  function descriptorAnimation(descriptor, elementMap, layer) {
    const transitionMs = effectiveDuration(state.manifest.config.transition_ms);
    const persistenceMs = effectiveDuration(state.manifest.config.persistence_ms);
    const existing = elementMap.get(descriptor.primitive_id);

    if (descriptor.intent === "enter") {
      const incoming = primitiveElement(descriptor.after, true);
      incoming.style.opacity = "0";
      layer.appendChild(incoming);
      return animateElement(incoming, [{ opacity: 0 }, { opacity: 1 }], transitionMs);
    }

    if (descriptor.intent === "exit") {
      if (!existing) {
        throw new Error(`missing exit primitive ${descriptor.primitive_id}`);
      }
      const eligible = descriptor.hints.includes("context-persistence-eligible");
      const duration = transitionMs + (eligible ? persistenceMs : 0);
      return animateElement(existing, [{ opacity: 1 }, { opacity: 0 }], duration);
    }

    if (descriptor.intent === "translate") {
      if (!existing || !descriptor.translation) {
        throw new Error(`incomplete translation descriptor ${descriptor.primitive_id}`);
      }
      const delta = projectTranslation(descriptor.translation);
      if (descriptor.hints.includes("focus-through-eligible")) {
        existing.classList.add("td1-focus-eligible");
      }
      return animateElement(
        existing,
        [
          { transform: "translate(0px, 0px)" },
          { transform: `translate(${delta.x}px, ${delta.y}px)` },
        ],
        transitionMs,
      );
    }

    if (descriptor.intent === "reform") {
      if (!existing) {
        throw new Error(`missing reform primitive ${descriptor.primitive_id}`);
      }
      const incoming = primitiveElement(descriptor.after, true);
      incoming.style.opacity = "0";
      if (descriptor.strategy === "continuous_reform_eligible") {
        incoming.classList.add("td1-morph-eligible");
        existing.classList.add("td1-morph-eligible");
      }
      layer.appendChild(incoming);
      return Promise.all([
        animateElement(existing, [{ opacity: 1 }, { opacity: 0 }], transitionMs),
        animateElement(incoming, [{ opacity: 0 }, { opacity: 1 }], transitionMs),
      ]);
    }

    if (descriptor.intent === "retag") {
      if (!existing) {
        throw new Error(`missing retag primitive ${descriptor.primitive_id}`);
      }
      return animateElement(existing, [{ opacity: 1 }, { opacity: 0.68 }, { opacity: 1 }], transitionMs);
    }

    throw new Error(`unsupported morph intent ${descriptor.intent}`);
  }

  function morphEntryForFrame(frameIndex) {
    if (frameIndex <= 0) {
      return null;
    }
    const entry = state.morphs.entries[frameIndex - 1];
    if (!entry || entry.frame_index !== frameIndex) {
      throw new Error(`missing deterministic morph plan for frame ${frameIndex}`);
    }
    return entry;
  }

  async function transitionTo(frameIndex) {
    if (state.transitioning || frameIndex === state.frameIndex) {
      return;
    }
    if (frameIndex < 0 || frameIndex >= state.timeline.frames.length) {
      return;
    }

    const adjacentForward = frameIndex === state.frameIndex + 1;
    if (!adjacentForward) {
      reconcileScene(frameIndex);
      return;
    }

    state.transitioning = true;
    const entry = morphEntryForFrame(frameIndex);
    const plan = entry.plan;
    const layer = geometryLayer();
    const elementMap = currentElements();
    try {
      const animations = plan.descriptors.map((descriptor) =>
        descriptorAnimation(descriptor, elementMap, layer),
      );
      await Promise.all(animations);
      reconcileScene(frameIndex);
    } finally {
      state.transitioning = false;
    }
  }

  function clearTimer() {
    if (state.timer !== null) {
      clearTimeout(state.timer);
      state.timer = null;
    }
  }

  function scheduleNext() {
    clearTimer();
    if (!state.playing || !state.verified) {
      return;
    }
    const frameMs = effectiveDuration(state.manifest.config.frame_ms);
    state.timer = setTimeout(async () => {
      if (!state.playing) {
        return;
      }
      const lastIndex = state.timeline.frames.length - 1;
      if (state.frameIndex >= lastIndex) {
        if (!state.manifest.config.loop) {
          setPlaying(false);
          return;
        }
        reconcileScene(0);
        scheduleNext();
        return;
      }
      await transitionTo(state.frameIndex + 1);
      scheduleNext();
    }, frameMs);
  }

  function setPlaying(playing) {
    state.playing = Boolean(playing) && state.verified;
    playButton.textContent = state.playing ? "❚❚" : "▶";
    playButton.setAttribute("aria-pressed", String(state.playing));
    if (state.playing) {
      scheduleNext();
    } else {
      clearTimer();
    }
  }

  async function nextFrame() {
    const wasPlaying = state.playing;
    setPlaying(false);
    if (state.frameIndex < state.timeline.frames.length - 1) {
      await transitionTo(state.frameIndex + 1);
    } else if (state.manifest.config.loop) {
      reconcileScene(0);
    }
    if (wasPlaying) {
      setPlaying(true);
    }
  }

  function previousFrame() {
    const wasPlaying = state.playing;
    setPlaying(false);
    reconcileScene(Math.max(0, state.frameIndex - 1));
    if (wasPlaying) {
      setPlaying(true);
    }
  }

  function restart() {
    setPlaying(false);
    reconcileScene(0);
  }

  function cycleSpeed() {
    const index = speedSteps.indexOf(state.speed);
    state.speed = speedSteps[(index + 1) % speedSteps.length];
    speedButton.textContent = `${state.speed}×`;
    if (state.playing) {
      scheduleNext();
    }
    updatePanels();
  }

  function setEngineering(enabled) {
    state.engineering = Boolean(enabled);
    engineeringPanel.hidden = !state.engineering;
    engineeringButton.setAttribute("aria-pressed", String(state.engineering));
    updatePanels();
  }

  function setProvenance(enabled) {
    state.provenance = Boolean(enabled);
    provenancePanel.hidden = !state.provenance;
    provenanceButton.setAttribute("aria-pressed", String(state.provenance));
    updatePanels();
  }

  function node(tag, text = null, className = null) {
    const element = document.createElement(tag);
    if (text !== null) {
      element.textContent = text;
    }
    if (className) {
      element.className = className;
    }
    return element;
  }

  function addKv(list, key, value, digest = false) {
    list.appendChild(node("dt", key));
    const dd = node("dd", String(value));
    if (digest) {
      dd.classList.add("td1-digest");
    }
    list.appendChild(dd);
  }

  function currentFrame() {
    return state.timeline.frames[state.frameIndex];
  }

  function currentMorphEntry() {
    return state.frameIndex > 0 ? morphEntryForFrame(state.frameIndex) : null;
  }

  function updateEngineeringPanel() {
    if (!state.engineering || !state.timeline) {
      return;
    }
    const frame = currentFrame();
    engineeringPanel.replaceChildren();
    engineeringPanel.appendChild(node("h2", "TD-1 / ENGINEERING", "td1-panel-title"));
    const list = node("dl", null, "td1-kv");
    addKv(list, "frame", `${state.frameIndex} / ${state.timeline.frames.length - 1}`);
    addKv(list, "event", frame.event_index ?? "initial");
    addKv(list, "instruction", frame.instruction_index ?? "—");
    addKv(list, "operation", frame.op ?? "initial state");
    addKv(list, "IP", frame.render_state.ip);
    addKv(list, "condition", frame.render_state.cond);
    addKv(list, "halted", frame.render_state.halted);
    addKv(list, "steps", frame.render_state.steps);
    addKv(list, "speed", `${state.speed}×`);
    addKv(list, "machine", frame.machine_digest, true);
    addKv(list, "render", frame.render_digest, true);
    addKv(list, "scene", frame.scene_digest, true);
    engineeringPanel.appendChild(list);

    const changed = currentMorphEntry();
    if (changed) {
      const title = node("div", `transition descriptors: ${changed.plan.descriptors.length}`);
      engineeringPanel.appendChild(title);
      const items = node("ul", null, "td1-list");
      for (const descriptor of changed.plan.descriptors) {
        const vector = descriptor.translation ? ` [${descriptor.translation.join(",")}]` : "";
        items.appendChild(
          node(
            "li",
            `${descriptor.primitive_id} :: ${descriptor.intent}/${descriptor.strategy}${vector}`,
          ),
        );
      }
      engineeringPanel.appendChild(items);
    }
  }

  function updateProvenancePanel() {
    if (!state.provenance || !state.manifest) {
      return;
    }
    const frame = currentFrame();
    const entry = currentMorphEntry();
    provenancePanel.replaceChildren();
    provenancePanel.appendChild(node("h2", "TD-1 / PROVENANCE", "td1-panel-title"));

    const list = node("dl", null, "td1-kv");
    addKv(list, "verified", state.verified);
    addKv(list, "artifact schema", `${state.manifest.schema}/v${state.manifest.version}`);
    addKv(list, "source version", state.manifest.player_source_version);
    addKv(list, "timeline", state.manifest.timeline_digest, true);
    addKv(list, "morph manifest", state.manifest.morph_manifest_digest, true);
    addKv(list, "frame scene", frame.scene_digest, true);
    addKv(list, "HTML digest", "external SHA-256 (reported by compiler)");
    provenancePanel.appendChild(list);

    if (frame.scene.profile) {
      const profile = node("dl", null, "td1-kv");
      addKv(profile, "corpus", frame.scene.profile.snapshot_id);
      addKv(profile, "corpus digest", frame.scene.profile.snapshot_digest, true);
      addKv(profile, "threshold", frame.scene.profile.threshold_milli);
      provenancePanel.appendChild(profile);
    }

    const geometryRules = frame.scene.applied_rules || [];
    if (geometryRules.length > 0) {
      provenancePanel.appendChild(node("div", "GEOMETRY RULES", "td1-panel-title"));
      for (const rule of geometryRules) {
        const box = node("div", null, "td1-rule");
        box.appendChild(node("div", `${rule.rule_id} / ${rule.motif}`));
        box.appendChild(node("div", rule.effect));
        box.appendChild(node("div", `sources: ${rule.source_ids.join(", ")}`));
        provenancePanel.appendChild(box);
      }
    }

    if (entry && entry.plan.applied_rules.length > 0) {
      provenancePanel.appendChild(node("div", "MORPH RULES", "td1-panel-title"));
      for (const rule of entry.plan.applied_rules) {
        const box = node("div", null, "td1-rule");
        box.appendChild(node("div", `${rule.rule_id} / ${rule.motif}`));
        box.appendChild(node("div", rule.effect));
        box.appendChild(node("div", `sources: ${rule.source_ids.join(", ")}`));
        provenancePanel.appendChild(box);
      }
    }
  }

  function updatePanels() {
    updateEngineeringPanel();
    updateProvenancePanel();
  }

  function installControls() {
    playButton.addEventListener("click", () => setPlaying(!state.playing));
    prevButton.addEventListener("click", previousFrame);
    nextButton.addEventListener("click", () => void nextFrame());
    restartButton.addEventListener("click", restart);
    speedButton.addEventListener("click", cycleSpeed);
    engineeringButton.addEventListener("click", () => setEngineering(!state.engineering));
    provenanceButton.addEventListener("click", () => setProvenance(!state.provenance));

    window.addEventListener("keydown", (event) => {
      if (event.target instanceof HTMLInputElement || event.target instanceof HTMLTextAreaElement) {
        return;
      }
      if (event.code === "Space") {
        event.preventDefault();
        setPlaying(!state.playing);
      } else if (event.code === "ArrowRight") {
        event.preventDefault();
        void nextFrame();
      } else if (event.code === "ArrowLeft") {
        event.preventDefault();
        previousFrame();
      } else if (event.code === "Home") {
        event.preventDefault();
        restart();
      } else if (event.key.toLowerCase() === "e") {
        setEngineering(!state.engineering);
      } else if (event.key.toLowerCase() === "p") {
        setProvenance(!state.provenance);
      } else if (event.key === "+" || event.key === "=") {
        const next = Math.min(speedSteps.length - 1, speedSteps.indexOf(state.speed) + 1);
        state.speed = speedSteps[next];
        speedButton.textContent = `${state.speed}×`;
        updatePanels();
      } else if (event.key === "-") {
        const next = Math.max(0, speedSteps.indexOf(state.speed) - 1);
        state.speed = speedSteps[next];
        speedButton.textContent = `${state.speed}×`;
        updatePanels();
      }
    });
  }

  function showFailure(error) {
    setPlaying(false);
    state.verified = false;
    verification.dataset.state = "failed";
    verification.title = `TD-1 verification failed: ${error.message}`;
    verification.setAttribute("aria-label", "TD-1 payload verification failed");
    provenancePanel.hidden = false;
    provenancePanel.replaceChildren();
    provenancePanel.appendChild(node("h2", "TD-1 / VERIFICATION FAULT", "td1-panel-title"));
    provenancePanel.appendChild(node("div", error.message, "td1-fault"));
  }

  async function boot() {
    installControls();
    try {
      await loadAndVerifyPayloads();
      computeProjectionBounds();
      reconcileScene(0);
      setEngineering(Boolean(state.manifest.config.engineering_overlay));
      setProvenance(Boolean(state.manifest.config.provenance_open));
      if (state.manifest.config.autoplay) {
        setPlaying(true);
      }
    } catch (error) {
      showFailure(error instanceof Error ? error : new Error(String(error)));
    }
  }

  void boot();
})();
