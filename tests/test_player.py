import re

import pytest

from td1_simulacrum import (
    PLAYER_ENDPOINT_POLICY,
    PLAYER_STATE_INTERPOLATION_POLICY,
    PLAYER_UNCHANGED_POLICY,
    LatticePoint,
    PlayerArtifactError,
    PlayerEasing,
    RelicPlayerConfig,
    SVGRenderOptions,
    assemble,
    build_relic_player_artifact,
    build_relic_timeline,
    project_player_translation,
    project_point,
    verify_relic_player_html,
)


def _timeline():
    return build_relic_timeline(
        assemble(
            """
LDI R0, 3
ADDI R0, -1
LDI R1, 2
ADD R0, R1
HALT
"""
        )
    )


def test_standalone_player_generation_is_byte_deterministic_and_self_verifying() -> None:
    timeline = _timeline()
    config = RelicPlayerConfig(
        frame_ms=900,
        transition_ms=500,
        persistence_ms=175,
        easing=PlayerEasing.LINEAR,
        autoplay=False,
        loop=False,
    )
    first = build_relic_player_artifact(timeline, config)
    second = build_relic_player_artifact(timeline, config)

    assert first.html == second.html
    assert first.digest() == second.digest()
    assert first.manifest == second.manifest
    assert first.html.startswith("<!doctype html>")
    assert "https://" not in first.html
    assert "http://" not in first.html.replace("http://www.w3.org/2000/svg", "")

    verification = verify_relic_player_html(first.html)
    assert verification.timeline == timeline
    assert verification.manifest == first.manifest
    assert verification.html_sha256 == first.digest()


def test_player_manifest_freezes_endpoint_and_no_invented_motion_policies() -> None:
    artifact = build_relic_player_artifact(_timeline())
    manifest = artifact.manifest

    assert manifest.endpoint_policy == PLAYER_ENDPOINT_POLICY
    assert manifest.unchanged_primitive_policy == PLAYER_UNCHANGED_POLICY
    assert manifest.state_interpolation_policy == PLAYER_STATE_INTERPOLATION_POLICY
    assert manifest.frame_count == manifest.event_count + 1
    assert manifest.timeline_digest == manifest.timeline_bytes_sha256
    assert manifest.morph_manifest_digest == manifest.morph_manifest_bytes_sha256
    assert manifest.as_dict()["html_digest_strategy"] == "external-sha256/full-html"


def test_player_translation_projection_matches_reference_svg_projection() -> None:
    config = RelicPlayerConfig(
        unit=5,
        depth_x=4,
        depth_y=2,
        frame_ms=1000,
        transition_ms=500,
    )
    translation = (7, -3, 4)
    projected = project_player_translation(translation, config)

    options = SVGRenderOptions(
        unit=config.unit,
        depth_x=config.depth_x,
        depth_y=config.depth_y,
        margin=config.margin,
    )
    origin = project_point(LatticePoint(0, 0, 0), options)
    destination = project_point(LatticePoint(*translation), options)
    assert projected == (
        destination[0] - origin[0],
        destination[1] - origin[1],
    )


def test_player_rejects_tampered_embedded_timeline_bytes() -> None:
    artifact = build_relic_player_artifact(_timeline())
    pattern = re.compile(r'(<script id="td1-timeline"[^>]*>)([^<]+)(</script>)')
    match = pattern.search(artifact.html)
    assert match is not None
    payload = match.group(2)
    replacement = ("A" if payload[0] != "A" else "B") + payload[1:]
    tampered = artifact.html[: match.start(2)] + replacement + artifact.html[match.end(2) :]

    with pytest.raises(PlayerArtifactError, match="timeline payload digest mismatch"):
        verify_relic_player_html(tampered)


def test_player_rejects_manifest_digest_tampering() -> None:
    artifact = build_relic_player_artifact(_timeline())
    pattern = re.compile(r'(id="td1-manifest"[^>]*data-sha256=")([0-9a-f]{64})(")')
    match = pattern.search(artifact.html)
    assert match is not None
    digest = match.group(2)
    replacement = ("0" if digest[0] != "0" else "1") + digest[1:]
    tampered = artifact.html[: match.start(2)] + replacement + artifact.html[match.end(2) :]

    with pytest.raises(PlayerArtifactError, match="manifest digest mismatch"):
        verify_relic_player_html(tampered)


def test_player_config_rejects_normatively_unsafe_or_invalid_timing() -> None:
    with pytest.raises(PlayerArtifactError):
        RelicPlayerConfig(frame_ms=0)
    with pytest.raises(PlayerArtifactError):
        RelicPlayerConfig(frame_ms=500, transition_ms=501)
    with pytest.raises(PlayerArtifactError):
        RelicPlayerConfig(persistence_ms=-1)


def test_standalone_player_contains_controls_and_no_external_runtime_dependency() -> None:
    artifact = build_relic_player_artifact(_timeline())
    html = artifact.html

    assert 'id="td1-play"' in html
    assert 'id="td1-prev"' in html
    assert 'id="td1-next"' in html
    assert 'id="td1-engineering"' in html
    assert 'id="td1-provenance"' in html
    assert "WebCrypto" in html
    assert "reconcileScene(frameIndex);" in html
    assert "descriptorAnimation" in html
    assert "fetch(" not in html
    assert "<script src=" not in html
