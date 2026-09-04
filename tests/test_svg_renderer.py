import json
import xml.etree.ElementTree as ET

from td1_simulacrum import (
    GeometryKind,
    GeometryPrimitive,
    GeometryScene,
    LatticePoint,
    SVGRenderOptions,
    SVGTheme,
    build_geometry_scene,
    project_point,
    render_svg,
)
from td1_simulacrum.machine import Machine
from td1_simulacrum.render_state import RenderState

SVG_NS = {"svg": "http://www.w3.org/2000/svg"}


def _reference_scene() -> GeometryScene:
    machine = Machine()
    machine.registers[0] = machine.registers[0].from_int(17)
    machine.registers[4] = machine.registers[4].from_int(-9)
    return build_geometry_scene(RenderState.capture(machine))


def _parse(svg: str) -> ET.Element:
    return ET.fromstring(svg)


def test_relic_svg_is_byte_deterministic_and_valid_xml() -> None:
    scene = _reference_scene()
    first = render_svg(scene)
    second = render_svg(scene)

    assert first.svg == second.svg
    assert first.digest() == second.digest()
    assert first.scene_digest == scene.digest()
    root = _parse(first.svg)
    assert root.tag == "{http://www.w3.org/2000/svg}svg"


def test_every_geometry_primitive_is_rendered_exactly_once() -> None:
    scene = _reference_scene()
    root = _parse(render_svg(scene).svg)
    rendered = root.findall(".//*[@data-primitive-id]")
    rendered_ids = [item.attrib["data-primitive-id"] for item in rendered]

    assert len(rendered_ids) == len(scene.primitives)
    assert sorted(rendered_ids) == sorted(item.primitive_id for item in scene.primitives)


def test_renderer_embeds_geometry_and_machine_provenance() -> None:
    scene = _reference_scene()
    artifact = render_svg(scene)
    root = _parse(artifact.svg)
    metadata = root.find("svg:metadata", SVG_NS)
    assert metadata is not None and metadata.text is not None
    payload = json.loads(metadata.text)

    assert payload["schema"] == "td1.svg-render"
    assert payload["version"] == 1
    assert payload["scene_digest"] == scene.digest()
    assert payload["source_render_digest"] == scene.source_render_digest
    assert payload["source_machine_digest"] == scene.source_machine_digest
    assert payload["primitive_count"] == len(scene.primitives)
    assert payload["projection"] == "axial-int-oblique/v1"


def test_relic_and_engineering_themes_preserve_native_geometry_coordinates() -> None:
    scene = _reference_scene()
    relic = _parse(render_svg(scene, SVGRenderOptions(theme=SVGTheme.RELIC)).svg)
    engineering = _parse(
        render_svg(scene, SVGRenderOptions(theme=SVGTheme.ENGINEERING)).svg
    )

    def geometry_attributes(root: ET.Element) -> dict[str, tuple[tuple[str, str], ...]]:
        result: dict[str, tuple[tuple[str, str], ...]] = {}
        coordinate_names = {"cx", "cy", "r", "x1", "y1", "x2", "y2", "points"}
        for element in root.findall(".//*[@data-primitive-id]"):
            primitive_id = element.attrib["data-primitive-id"]
            result[primitive_id] = tuple(
                sorted(
                    (name, value)
                    for name, value in element.attrib.items()
                    if name in coordinate_names
                )
            )
        return result

    assert geometry_attributes(relic) == geometry_attributes(engineering)
    assert relic.attrib["data-td1-scene-digest"] == engineering.attrib["data-td1-scene-digest"]


def test_relic_theme_has_no_display_text_by_default() -> None:
    root = _parse(render_svg(_reference_scene()).svg)
    assert root.findall(".//svg:text", SVG_NS) == []


def test_engineering_theme_exposes_only_geometry_derived_labels() -> None:
    scene = _reference_scene()
    root = _parse(
        render_svg(scene, SVGRenderOptions(theme=SVGTheme.ENGINEERING)).svg
    )
    labels = root.findall(".//svg:text", SVG_NS)
    assert len(labels) == len(scene.primitives)
    assert {label.attrib["data-for"] for label in labels} == {
        primitive.primitive_id for primitive in scene.primitives
    }
    assert all(" | " in (label.text or "") for label in labels)


def test_projection_uses_integer_axial_and_depth_mapping() -> None:
    options = SVGRenderOptions(unit=3, depth_x=2, depth_y=1)
    assert project_point(LatticePoint(2, 4, 0), options) == (24, 36)
    assert project_point(LatticePoint(2, 4, 100), options) == (224, -64)


def test_renderer_preserves_polyline_topology_point_count() -> None:
    scene = GeometryScene(
        source_render_digest="render",
        source_machine_digest="machine",
        primitives=(
            GeometryPrimitive(
                primitive_id="braid",
                kind=GeometryKind.POLYLINE,
                role="test-polyline",
                points=(
                    LatticePoint(0, 0, 0),
                    LatticePoint(2, 3, 5),
                    LatticePoint(4, 0, 0),
                ),
            ),
        ),
    )
    root = _parse(render_svg(scene).svg)
    element = root.find(".//*[@data-primitive-id='braid']")
    assert element is not None
    assert len(element.attrib["points"].split()) == 3


def test_malicious_geometry_identifiers_are_xml_escaped_and_not_executed() -> None:
    malicious_id = 'bad"><script>alert(1)</script>'
    malicious_role = "role<&\"'"
    scene = GeometryScene(
        source_render_digest="render",
        source_machine_digest="machine",
        primitives=(
            GeometryPrimitive(
                primitive_id=malicious_id,
                kind=GeometryKind.NODE,
                role=malicious_role,
                points=(LatticePoint(0, 0, 0),),
            ),
        ),
    )
    artifact = render_svg(scene, SVGRenderOptions(theme=SVGTheme.ENGINEERING))
    root = _parse(artifact.svg)
    element = root.find(".//*[@data-primitive-id]")
    assert element is not None
    assert element.attrib["data-primitive-id"] == malicious_id
    assert element.attrib["data-role"] == malicious_role
    assert root.findall(".//script") == []
    assert "<script>alert(1)</script>" not in artifact.svg


def test_scene_json_round_trip_produces_same_svg() -> None:
    scene = _reference_scene()
    restored = GeometryScene.from_json(scene.canonical_json())
    options = SVGRenderOptions(theme=SVGTheme.RELIC, show_labels=False)
    assert render_svg(scene, options).svg == render_svg(restored, options).svg
