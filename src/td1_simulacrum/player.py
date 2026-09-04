"""Self-contained browser playback artifacts for TD-1 Relic Mode.

The player is downstream of the normative Relic timeline and deterministic
morph-plan contracts. It is presentation software: timing, easing, glow, and
transient visual persistence are explicitly non-normative. Authoritative state
exists only at exact timeline endpoints, and the browser hard-reconciles to
those endpoints after every animated transition.
"""

from __future__ import annotations

import base64
import hashlib
import json
from dataclasses import dataclass
from enum import Enum
from html.parser import HTMLParser
from importlib import resources
from typing import Any

from .morph import TimelineMorphManifest, build_timeline_morph_manifest
from .timeline import RelicTimeline

PLAYER_CONFIG_SCHEMA = "td1.relic-player-config"
PLAYER_CONFIG_SCHEMA_VERSION = 1
PLAYER_ARTIFACT_SCHEMA = "td1.relic-player-artifact"
PLAYER_ARTIFACT_SCHEMA_VERSION = 1
PLAYER_SOURCE_VERSION = 1
PLAYER_PROJECTION = "axial-int-oblique/v1"
PLAYER_ENDPOINT_POLICY = "hard-reconcile-authoritative-scene-after-transition/v1"
PLAYER_UNCHANGED_POLICY = "no-animation-without-morph-descriptor/v1"
PLAYER_STATE_INTERPOLATION_POLICY = "forbidden/v1"
PLAYER_HTML_DIGEST_STRATEGY = "external-sha256/full-html"


class PlayerArtifactError(ValueError):
    """Raised when a Relic browser artifact or embedded payload is inconsistent."""


class PlayerEasing(str, Enum):
    LINEAR = "linear"
    EASE = "ease"
    EASE_IN = "ease-in"
    EASE_OUT = "ease-out"
    EASE_IN_OUT = "ease-in-out"


def _sha256_bytes(payload: bytes) -> str:
    return hashlib.sha256(payload).hexdigest()


def _sha256_text(text: str) -> str:
    return _sha256_bytes(text.encode("utf-8"))


def _canonical_json(payload: object) -> str:
    return json.dumps(payload, sort_keys=True, separators=(",", ":"), ensure_ascii=True)


def _is_sha256(value: str) -> bool:
    return len(value) == 64 and all(character in "0123456789abcdef" for character in value)


@dataclass(frozen=True, slots=True)
class RelicPlayerConfig:
    """Non-normative presentation configuration for one standalone player."""

    frame_ms: int = 1100
    transition_ms: int = 620
    persistence_ms: int = 260
    easing: PlayerEasing = PlayerEasing.EASE_IN_OUT
    autoplay: bool = True
    loop: bool = True
    engineering_overlay: bool = False
    provenance_open: bool = False
    unit: int = 3
    depth_x: int = 2
    depth_y: int = 1
    margin: int = 36
    schema: str = PLAYER_CONFIG_SCHEMA
    version: int = PLAYER_CONFIG_SCHEMA_VERSION

    def __post_init__(self) -> None:
        if self.schema != PLAYER_CONFIG_SCHEMA or self.version != PLAYER_CONFIG_SCHEMA_VERSION:
            raise PlayerArtifactError("unsupported Relic player config schema")
        if self.frame_ms <= 0:
            raise PlayerArtifactError("player frame_ms must be positive")
        if self.transition_ms < 0 or self.transition_ms > self.frame_ms:
            raise PlayerArtifactError("player transition_ms must be in 0..frame_ms")
        if self.persistence_ms < 0:
            raise PlayerArtifactError("player persistence_ms must be nonnegative")
        if self.unit <= 0:
            raise PlayerArtifactError("player projection unit must be positive")
        if self.depth_x < 0 or self.depth_y < 0:
            raise PlayerArtifactError("player depth projection components must be nonnegative")
        if self.margin < 0:
            raise PlayerArtifactError("player margin must be nonnegative")

    def as_dict(self) -> dict[str, object]:
        return {
            "schema": self.schema,
            "version": self.version,
            "frame_ms": self.frame_ms,
            "transition_ms": self.transition_ms,
            "persistence_ms": self.persistence_ms,
            "easing": self.easing.value,
            "autoplay": self.autoplay,
            "loop": self.loop,
            "engineering_overlay": self.engineering_overlay,
            "provenance_open": self.provenance_open,
            "unit": self.unit,
            "depth_x": self.depth_x,
            "depth_y": self.depth_y,
            "margin": self.margin,
        }

    def canonical_json(self) -> str:
        return _canonical_json(self.as_dict())

    def digest(self) -> str:
        return _sha256_text(self.canonical_json())

    @classmethod
    def from_dict(cls, payload: dict[str, object]) -> "RelicPlayerConfig":
        return cls(
            schema=str(payload["schema"]),
            version=int(payload["version"]),
            frame_ms=int(payload["frame_ms"]),
            transition_ms=int(payload["transition_ms"]),
            persistence_ms=int(payload["persistence_ms"]),
            easing=PlayerEasing(str(payload["easing"])),
            autoplay=bool(payload["autoplay"]),
            loop=bool(payload["loop"]),
            engineering_overlay=bool(payload["engineering_overlay"]),
            provenance_open=bool(payload["provenance_open"]),
            unit=int(payload["unit"]),
            depth_x=int(payload["depth_x"]),
            depth_y=int(payload["depth_y"]),
            margin=int(payload["margin"]),
        )


@dataclass(frozen=True, slots=True)
class RelicPlayerManifest:
    """Embedded provenance contract for one self-contained player artifact."""

    timeline_digest: str
    morph_manifest_digest: str
    timeline_bytes_sha256: str
    morph_manifest_bytes_sha256: str
    frame_count: int
    event_count: int
    config: RelicPlayerConfig
    template_sha256: str
    style_sha256: str
    script_sha256: str
    schema: str = PLAYER_ARTIFACT_SCHEMA
    version: int = PLAYER_ARTIFACT_SCHEMA_VERSION
    player_source_version: int = PLAYER_SOURCE_VERSION
    projection: str = PLAYER_PROJECTION
    endpoint_policy: str = PLAYER_ENDPOINT_POLICY
    unchanged_primitive_policy: str = PLAYER_UNCHANGED_POLICY
    state_interpolation_policy: str = PLAYER_STATE_INTERPOLATION_POLICY
    html_digest_strategy: str = PLAYER_HTML_DIGEST_STRATEGY

    def __post_init__(self) -> None:
        if self.schema != PLAYER_ARTIFACT_SCHEMA or self.version != PLAYER_ARTIFACT_SCHEMA_VERSION:
            raise PlayerArtifactError("unsupported Relic player artifact schema")
        if self.player_source_version != PLAYER_SOURCE_VERSION:
            raise PlayerArtifactError("unsupported Relic player source version")
        digests = (
            self.timeline_digest,
            self.morph_manifest_digest,
            self.timeline_bytes_sha256,
            self.morph_manifest_bytes_sha256,
            self.template_sha256,
            self.style_sha256,
            self.script_sha256,
        )
        if any(not _is_sha256(value) for value in digests):
            raise PlayerArtifactError("Relic player manifest digests must be SHA-256 hex")
        if self.timeline_digest != self.timeline_bytes_sha256:
            raise PlayerArtifactError("timeline digest must identify the exact embedded canonical bytes")
        if self.morph_manifest_digest != self.morph_manifest_bytes_sha256:
            raise PlayerArtifactError(
                "morph manifest digest must identify the exact embedded canonical bytes"
            )
        if self.frame_count <= 0 or self.event_count != self.frame_count - 1:
            raise PlayerArtifactError("Relic player frame/event cardinality is inconsistent")
        if self.projection != PLAYER_PROJECTION:
            raise PlayerArtifactError("unsupported Relic player projection")
        if self.endpoint_policy != PLAYER_ENDPOINT_POLICY:
            raise PlayerArtifactError("unsupported Relic player endpoint policy")
        if self.unchanged_primitive_policy != PLAYER_UNCHANGED_POLICY:
            raise PlayerArtifactError("unsupported unchanged-primitive policy")
        if self.state_interpolation_policy != PLAYER_STATE_INTERPOLATION_POLICY:
            raise PlayerArtifactError("unsupported state interpolation policy")
        if self.html_digest_strategy != PLAYER_HTML_DIGEST_STRATEGY:
            raise PlayerArtifactError("unsupported HTML digest strategy")

    @property
    def projection_dict(self) -> dict[str, object]:
        return {
            "id": self.projection,
            "unit": self.config.unit,
            "depth_x": self.config.depth_x,
            "depth_y": self.config.depth_y,
            "margin": self.config.margin,
        }

    def as_dict(self) -> dict[str, object]:
        return {
            "schema": self.schema,
            "version": self.version,
            "player_source_version": self.player_source_version,
            "timeline_digest": self.timeline_digest,
            "morph_manifest_digest": self.morph_manifest_digest,
            "timeline_bytes_sha256": self.timeline_bytes_sha256,
            "morph_manifest_bytes_sha256": self.morph_manifest_bytes_sha256,
            "frame_count": self.frame_count,
            "event_count": self.event_count,
            "config": self.config.as_dict(),
            "config_digest": self.config.digest(),
            "projection": self.projection_dict,
            "endpoint_policy": self.endpoint_policy,
            "unchanged_primitive_policy": self.unchanged_primitive_policy,
            "state_interpolation_policy": self.state_interpolation_policy,
            "assets": {
                "template_sha256": self.template_sha256,
                "style_sha256": self.style_sha256,
                "script_sha256": self.script_sha256,
            },
            "html_digest_strategy": self.html_digest_strategy,
        }

    def canonical_json(self) -> str:
        return _canonical_json(self.as_dict())

    def digest(self) -> str:
        return _sha256_text(self.canonical_json())

    @classmethod
    def from_dict(cls, payload: dict[str, object]) -> "RelicPlayerManifest":
        config_payload = payload.get("config")
        projection_payload = payload.get("projection")
        assets_payload = payload.get("assets")
        if not isinstance(config_payload, dict):
            raise PlayerArtifactError("Relic player manifest config must be an object")
        if not isinstance(projection_payload, dict):
            raise PlayerArtifactError("Relic player projection must be an object")
        if not isinstance(assets_payload, dict):
            raise PlayerArtifactError("Relic player asset provenance must be an object")
        config = RelicPlayerConfig.from_dict(config_payload)
        expected_projection = {
            "id": PLAYER_PROJECTION,
            "unit": config.unit,
            "depth_x": config.depth_x,
            "depth_y": config.depth_y,
            "margin": config.margin,
        }
        if projection_payload != expected_projection:
            raise PlayerArtifactError("Relic player projection disagrees with player config")
        expected_config_digest = payload.get("config_digest")
        if expected_config_digest is not None and str(expected_config_digest) != config.digest():
            raise PlayerArtifactError("Relic player config digest mismatch")
        return cls(
            schema=str(payload["schema"]),
            version=int(payload["version"]),
            player_source_version=int(payload["player_source_version"]),
            timeline_digest=str(payload["timeline_digest"]),
            morph_manifest_digest=str(payload["morph_manifest_digest"]),
            timeline_bytes_sha256=str(payload["timeline_bytes_sha256"]),
            morph_manifest_bytes_sha256=str(payload["morph_manifest_bytes_sha256"]),
            frame_count=int(payload["frame_count"]),
            event_count=int(payload["event_count"]),
            config=config,
            template_sha256=str(assets_payload["template_sha256"]),
            style_sha256=str(assets_payload["style_sha256"]),
            script_sha256=str(assets_payload["script_sha256"]),
            projection=str(projection_payload["id"]),
            endpoint_policy=str(payload["endpoint_policy"]),
            unchanged_primitive_policy=str(payload["unchanged_primitive_policy"]),
            state_interpolation_policy=str(payload["state_interpolation_policy"]),
            html_digest_strategy=str(payload["html_digest_strategy"]),
        )

    @classmethod
    def from_json(cls, text: str) -> "RelicPlayerManifest":
        payload = json.loads(text)
        if not isinstance(payload, dict):
            raise PlayerArtifactError("Relic player manifest JSON root must be an object")
        return cls.from_dict(payload)


@dataclass(frozen=True, slots=True)
class RelicPlayerArtifact:
    """Deterministic standalone HTML plus its validated embedded manifest."""

    html: str
    manifest: RelicPlayerManifest

    def __post_init__(self) -> None:
        if not self.html.startswith("<!doctype html>"):
            raise PlayerArtifactError("Relic player artifact must be standalone HTML")

    def digest(self) -> str:
        """Full-file digest reported externally to avoid self-referential HTML hashing."""
        return _sha256_text(self.html)

    def summary(self) -> dict[str, object]:
        return {
            "schema": self.manifest.schema,
            "version": self.manifest.version,
            "timeline_digest": self.manifest.timeline_digest,
            "morph_manifest_digest": self.manifest.morph_manifest_digest,
            "manifest_digest": self.manifest.digest(),
            "html_sha256": self.digest(),
            "html_digest_strategy": self.manifest.html_digest_strategy,
            "frames": self.manifest.frame_count,
            "events": self.manifest.event_count,
        }


@dataclass(frozen=True, slots=True)
class PlayerArtifactVerification:
    manifest: RelicPlayerManifest
    timeline: RelicTimeline
    morph_manifest_digest: str
    html_sha256: str

    def as_dict(self) -> dict[str, object]:
        return {
            "verified": True,
            "manifest_digest": self.manifest.digest(),
            "timeline_digest": self.timeline.digest(),
            "morph_manifest_digest": self.morph_manifest_digest,
            "html_sha256": self.html_sha256,
            "frames": len(self.timeline.frames),
            "events": self.timeline.event_count,
        }


@dataclass(slots=True)
class _EmbeddedPayload:
    text: str
    attributes: dict[str, str]


class _PlayerHTMLParser(HTMLParser):
    def __init__(self) -> None:
        super().__init__(convert_charrefs=False)
        self.payloads: dict[str, _EmbeddedPayload] = {}
        self._active_id: str | None = None
        self._active_data: list[str] = []
        self._active_attrs: dict[str, str] = {}

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        if tag != "script":
            return
        attributes = {key: value or "" for key, value in attrs}
        identifier = attributes.get("id")
        if identifier not in {"td1-manifest", "td1-timeline", "td1-morphs"}:
            return
        self._active_id = identifier
        self._active_data = []
        self._active_attrs = attributes

    def handle_data(self, data: str) -> None:
        if self._active_id is not None:
            self._active_data.append(data)

    def handle_endtag(self, tag: str) -> None:
        if tag != "script" or self._active_id is None:
            return
        self.payloads[self._active_id] = _EmbeddedPayload(
            "".join(self._active_data).strip(),
            dict(self._active_attrs),
        )
        self._active_id = None
        self._active_data = []
        self._active_attrs = {}


def _load_asset(name: str) -> str:
    root = resources.files("td1_simulacrum").joinpath("web_assets")
    return root.joinpath(name).read_text(encoding="utf-8")


def _encode_base64(payload: bytes) -> str:
    return base64.b64encode(payload).decode("ascii")


def _decode_base64(text: str, label: str) -> bytes:
    try:
        return base64.b64decode(text.encode("ascii"), validate=True)
    except (ValueError, UnicodeEncodeError) as exc:
        raise PlayerArtifactError(f"invalid base64 in embedded {label} payload") from exc


def project_player_translation(
    translation: tuple[int, int, int],
    config: RelicPlayerConfig | None = None,
) -> tuple[int, int]:
    """Project one exact native-lattice translation into player SVG coordinates."""
    config = config or RelicPlayerConfig()
    dq, dr, dz = translation
    x = (2 * dq + dr) * config.unit + dz * config.depth_x
    y = 3 * dr * config.unit - dz * config.depth_y
    return x, y


def _build_manifest(
    timeline: RelicTimeline,
    morphs: TimelineMorphManifest,
    config: RelicPlayerConfig,
    template: str,
    style: str,
    script: str,
) -> RelicPlayerManifest:
    timeline_bytes = timeline.canonical_json().encode("utf-8")
    morph_bytes = morphs.canonical_json().encode("utf-8")
    return RelicPlayerManifest(
        timeline_digest=timeline.digest(),
        morph_manifest_digest=morphs.digest(),
        timeline_bytes_sha256=_sha256_bytes(timeline_bytes),
        morph_manifest_bytes_sha256=_sha256_bytes(morph_bytes),
        frame_count=len(timeline.frames),
        event_count=timeline.event_count,
        config=config,
        template_sha256=_sha256_text(template),
        style_sha256=_sha256_text(style),
        script_sha256=_sha256_text(script),
    )


def build_relic_player_artifact(
    timeline: RelicTimeline,
    config: RelicPlayerConfig | None = None,
) -> RelicPlayerArtifact:
    """Compile one validated Relic timeline into dependency-free standalone HTML."""
    config = config or RelicPlayerConfig()
    morphs = build_timeline_morph_manifest(timeline)
    template = _load_asset("relic_player.html")
    style = _load_asset("relic_player.css")
    script = _load_asset("relic_player.js")
    if "</style" in style.lower() or "</script" in script.lower():
        raise PlayerArtifactError("player source asset contains an unsafe inline closing tag")

    timeline_bytes = timeline.canonical_json().encode("utf-8")
    morph_bytes = morphs.canonical_json().encode("utf-8")
    manifest = _build_manifest(timeline, morphs, config, template, style, script)
    manifest_bytes = manifest.canonical_json().encode("utf-8")

    replacements = {
        "__TD1_STYLE__": style.rstrip("\n"),
        "__TD1_SCRIPT__": script.rstrip("\n"),
        "__TD1_MANIFEST_DIGEST__": _sha256_bytes(manifest_bytes),
        "__TD1_MANIFEST_B64__": _encode_base64(manifest_bytes),
        "__TD1_TIMELINE_B64__": _encode_base64(timeline_bytes),
        "__TD1_MORPHS_B64__": _encode_base64(morph_bytes),
    }
    html = template
    for marker, value in replacements.items():
        if marker not in html:
            raise PlayerArtifactError(f"player template is missing marker {marker}")
        html = html.replace(marker, value)
    if "__TD1_" in html:
        raise PlayerArtifactError("player template contains unresolved TD-1 markers")
    html = html.replace("\r\n", "\n")
    if not html.endswith("\n"):
        html += "\n"

    artifact = RelicPlayerArtifact(html, manifest)
    verification = verify_relic_player_html(artifact.html)
    if verification.manifest != manifest:
        raise PlayerArtifactError("compiled Relic player failed internal manifest verification")
    return artifact


def _embedded_payloads(html: str) -> dict[str, _EmbeddedPayload]:
    parser = _PlayerHTMLParser()
    parser.feed(html)
    required = {"td1-manifest", "td1-timeline", "td1-morphs"}
    missing = required - parser.payloads.keys()
    if missing:
        raise PlayerArtifactError(
            "Relic player HTML is missing embedded payloads: " + ", ".join(sorted(missing))
        )
    return parser.payloads


def verify_relic_player_html(html: str) -> PlayerArtifactVerification:
    """Revalidate embedded canonical payloads and deterministic timeline/morph linkage."""
    payloads = _embedded_payloads(html)
    manifest_payload = payloads["td1-manifest"]
    manifest_bytes = _decode_base64(manifest_payload.text, "manifest")
    claimed_manifest_digest = manifest_payload.attributes.get("data-sha256")
    actual_manifest_digest = _sha256_bytes(manifest_bytes)
    if claimed_manifest_digest != actual_manifest_digest:
        raise PlayerArtifactError("embedded Relic player manifest digest mismatch")

    try:
        manifest_text = manifest_bytes.decode("utf-8")
    except UnicodeDecodeError as exc:
        raise PlayerArtifactError("embedded Relic player manifest is not UTF-8") from exc
    manifest = RelicPlayerManifest.from_json(manifest_text)
    if manifest.canonical_json().encode("utf-8") != manifest_bytes:
        raise PlayerArtifactError("embedded Relic player manifest is not canonical JSON")

    timeline_bytes = _decode_base64(payloads["td1-timeline"].text, "timeline")
    morph_bytes = _decode_base64(payloads["td1-morphs"].text, "morph manifest")
    if _sha256_bytes(timeline_bytes) != manifest.timeline_bytes_sha256:
        raise PlayerArtifactError("embedded timeline payload digest mismatch")
    if _sha256_bytes(morph_bytes) != manifest.morph_manifest_bytes_sha256:
        raise PlayerArtifactError("embedded morph-manifest payload digest mismatch")

    try:
        timeline_text = timeline_bytes.decode("utf-8")
        morph_text = morph_bytes.decode("utf-8")
    except UnicodeDecodeError as exc:
        raise PlayerArtifactError("embedded TD-1 payload is not UTF-8") from exc
    timeline = RelicTimeline.from_json(timeline_text)
    if timeline.canonical_json().encode("utf-8") != timeline_bytes:
        raise PlayerArtifactError("embedded Relic timeline is not canonical JSON")
    if timeline.digest() != manifest.timeline_digest:
        raise PlayerArtifactError("embedded Relic timeline digest disagrees with manifest")

    morph_payload: Any = json.loads(morph_text)
    if not isinstance(morph_payload, dict):
        raise PlayerArtifactError("embedded timeline morph manifest root must be an object")
    expected_morphs = build_timeline_morph_manifest(timeline)
    canonical_morph_payload = _canonical_json(morph_payload)
    if canonical_morph_payload.encode("utf-8") != morph_bytes:
        raise PlayerArtifactError("embedded timeline morph manifest is not canonical JSON")
    if canonical_morph_payload != expected_morphs.canonical_json():
        raise PlayerArtifactError("embedded morph manifest disagrees with deterministic timeline plans")
    if expected_morphs.digest() != manifest.morph_manifest_digest:
        raise PlayerArtifactError("embedded morph-manifest digest disagrees with manifest")
    if len(timeline.frames) != manifest.frame_count or timeline.event_count != manifest.event_count:
        raise PlayerArtifactError("embedded timeline cardinality disagrees with player manifest")

    return PlayerArtifactVerification(
        manifest=manifest,
        timeline=timeline,
        morph_manifest_digest=expected_morphs.digest(),
        html_sha256=_sha256_text(html),
    )
