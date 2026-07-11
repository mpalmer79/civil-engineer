"""Safe spatial bounds and drawing-unit extraction for DXF entities.

Bounds are local drawing coordinates, never georeferenced positions. Each
result reports how the bound was computed:

* computed: exact from the entity definition
* approximate: a safe overestimate (spline control points, ellipse box)
* unsupported: no safe bound exists; the reason is explicit and no
  coordinates are fabricated

Block inserts are resolved through ezdxf virtual entities so insertion point,
rotation, scale, and nesting are applied, with a recursion and count limit for
pathological files.
"""

from __future__ import annotations

import math
from dataclasses import dataclass

# Cap on how many sub-entities one INSERT may expand to before the bound is
# reported as approximate-from-partial-expansion.
MAX_INSERT_VIRTUAL_ENTITIES = 500

# ezdxf $INSUNITS header values. Only the values relevant to civil drawings
# are named; everything else reports as unsupported.
INSUNITS_NAMES: dict[int, str] = {
    0: "unitless",
    1: "inches",
    2: "feet",
    3: "miles",
    4: "millimeters",
    5: "centimeters",
    6: "meters",
    10: "yards",
}


@dataclass(frozen=True)
class BoundsResult:
    """Bounds for one entity, or an explicit unsupported reason."""

    bounds: tuple[float, float, float, float] | None
    status: str  # computed, approximate, or unsupported
    reason: str | None = None


@dataclass(frozen=True)
class DrawingUnits:
    """Drawing units read from the DXF header."""

    insunits_code: int | None
    name: str
    confidence: str
    note: str


def _merge(
    boxes: list[tuple[float, float, float, float]],
) -> tuple[float, float, float, float] | None:
    if not boxes:
        return None
    return (
        min(b[0] for b in boxes),
        min(b[1] for b in boxes),
        max(b[2] for b in boxes),
        max(b[3] for b in boxes),
    )


def _points_box(
    points: list[tuple[float, float]],
) -> tuple[float, float, float, float] | None:
    if not points:
        return None
    xs = [p[0] for p in points]
    ys = [p[1] for p in points]
    return (min(xs), min(ys), max(xs), max(ys))


def _arc_box(
    center: tuple[float, float],
    radius: float,
    start_angle: float,
    end_angle: float,
) -> tuple[float, float, float, float]:
    """Exact arc box: endpoints plus any axis extremes the arc crosses."""

    cx, cy = center
    start = math.radians(start_angle % 360.0)
    end = math.radians(end_angle % 360.0)
    sweep_points = [
        (cx + radius * math.cos(start), cy + radius * math.sin(start)),
        (cx + radius * math.cos(end), cy + radius * math.sin(end)),
    ]

    def crosses(angle: float) -> bool:
        a = angle % (2 * math.pi)
        s = start % (2 * math.pi)
        e = end % (2 * math.pi)
        if s <= e:
            return s <= a <= e
        return a >= s or a <= e

    for quarter, point in (
        (0.0, (cx + radius, cy)),
        (math.pi / 2, (cx, cy + radius)),
        (math.pi, (cx - radius, cy)),
        (3 * math.pi / 2, (cx, cy - radius)),
    ):
        if crosses(quarter):
            sweep_points.append(point)
    box = _points_box(sweep_points)
    assert box is not None
    return box


def entity_bounds(entity, *, _depth: int = 0) -> BoundsResult:
    """Compute a safe bound for one DXF entity."""

    try:
        dxftype = entity.dxftype()
    except Exception:
        return BoundsResult(None, "unsupported", "Entity type unreadable.")

    try:
        if dxftype in {"TEXT", "MTEXT"}:
            point = entity.dxf.insert
            x, y = float(point[0]), float(point[1])
            return BoundsResult((x, y, x, y), "computed")

        if dxftype == "POINT":
            point = entity.dxf.location
            x, y = float(point[0]), float(point[1])
            return BoundsResult((x, y, x, y), "computed")

        if dxftype == "LINE":
            start, end = entity.dxf.start, entity.dxf.end
            box = _points_box(
                [
                    (float(start[0]), float(start[1])),
                    (float(end[0]), float(end[1])),
                ]
            )
            return BoundsResult(box, "computed")

        if dxftype == "LWPOLYLINE":
            points = [
                (float(p[0]), float(p[1])) for p in entity.get_points()
            ]
            box = _points_box(points)
            if box is None:
                return BoundsResult(
                    None, "unsupported", "Polyline has no vertices."
                )
            return BoundsResult(box, "computed")

        if dxftype == "POLYLINE":
            points = [
                (float(v.dxf.location[0]), float(v.dxf.location[1]))
                for v in entity.vertices
            ]
            box = _points_box(points)
            if box is None:
                return BoundsResult(
                    None, "unsupported", "Polyline has no vertices."
                )
            return BoundsResult(box, "computed")

        if dxftype == "CIRCLE":
            center = entity.dxf.center
            radius = float(entity.dxf.radius)
            cx, cy = float(center[0]), float(center[1])
            return BoundsResult(
                (cx - radius, cy - radius, cx + radius, cy + radius),
                "computed",
            )

        if dxftype == "ARC":
            center = entity.dxf.center
            box = _arc_box(
                (float(center[0]), float(center[1])),
                float(entity.dxf.radius),
                float(entity.dxf.start_angle),
                float(entity.dxf.end_angle),
            )
            return BoundsResult(box, "computed")

        if dxftype == "ELLIPSE":
            center = entity.dxf.center
            major = entity.dxf.major_axis
            ratio = float(entity.dxf.ratio)
            cx, cy = float(center[0]), float(center[1])
            mx, my = float(major[0]), float(major[1])
            major_len = math.hypot(mx, my)
            # Conservative box: the full-ellipse extent regardless of the
            # start and end parameters, so it can only overestimate.
            reach = major_len
            minor_reach = major_len * ratio
            radius = max(reach, minor_reach)
            return BoundsResult(
                (cx - radius, cy - radius, cx + radius, cy + radius),
                "approximate",
                "Full-ellipse overestimate; arc parameters not evaluated.",
            )

        if dxftype == "SPLINE":
            control = [
                (float(p[0]), float(p[1])) for p in entity.control_points
            ]
            if control:
                # A B-spline lies within the convex hull of its control
                # points, so this box is a safe overestimate.
                return BoundsResult(
                    _points_box(control),
                    "approximate",
                    "Control-point hull overestimate.",
                )
            fit = [(float(p[0]), float(p[1])) for p in entity.fit_points]
            if fit:
                return BoundsResult(
                    _points_box(fit),
                    "approximate",
                    "Fit-point box; the curve can extend slightly beyond it.",
                )
            return BoundsResult(
                None, "unsupported", "Spline has no defining points."
            )

        if dxftype == "HATCH":
            points: list[tuple[float, float]] = []
            for path in entity.paths:
                vertices = getattr(path, "vertices", None)
                if vertices:
                    points.extend(
                        (float(v[0]), float(v[1])) for v in vertices
                    )
                edges = getattr(path, "edges", None)
                if edges:
                    for edge in edges:
                        for attr in ("start", "end", "center"):
                            value = getattr(edge, attr, None)
                            if value is not None:
                                points.append(
                                    (float(value[0]), float(value[1]))
                                )
            box = _points_box(points)
            if box is None:
                return BoundsResult(
                    None,
                    "unsupported",
                    "Hatch boundary vertices unavailable.",
                )
            return BoundsResult(
                box, "approximate", "Boundary-path vertex box."
            )

        if dxftype == "DIMENSION":
            points = []
            for attr in ("defpoint", "defpoint2", "defpoint3", "text_midpoint"):
                value = getattr(entity.dxf, attr, None)
                if value is not None:
                    points.append((float(value[0]), float(value[1])))
            box = _points_box(points)
            if box is None:
                return BoundsResult(
                    None, "unsupported", "Dimension points unavailable."
                )
            return BoundsResult(
                box, "approximate", "Definition-point box."
            )

        if dxftype in {"SOLID", "3DFACE", "TRACE"}:
            points = []
            for attr in ("vtx0", "vtx1", "vtx2", "vtx3"):
                value = getattr(entity.dxf, attr, None)
                if value is not None:
                    points.append((float(value[0]), float(value[1])))
            box = _points_box(points)
            if box is None:
                return BoundsResult(
                    None, "unsupported", "Corner points unavailable."
                )
            return BoundsResult(box, "computed")

        if dxftype in {"LEADER", "MLEADER", "MULTILEADER"}:
            vertices = getattr(entity, "vertices", None)
            if vertices:
                points = [(float(v[0]), float(v[1])) for v in vertices]
                box = _points_box(points)
                if box is not None:
                    return BoundsResult(box, "computed")
            return BoundsResult(
                None, "unsupported", "Leader vertices unavailable."
            )

        if dxftype in {"XLINE", "RAY"}:
            return BoundsResult(
                None,
                "unsupported",
                "Construction line is unbounded by definition.",
            )

        if dxftype == "INSERT":
            if _depth >= 3:
                # Depth guard against reference cycles and pathological
                # nesting. ezdxf virtual entities arrive pre-transformed, so
                # each level composes correctly until this cutoff.
                return BoundsResult(
                    None, "unsupported", "Insert nesting limit reached."
                )
            boxes: list[tuple[float, float, float, float]] = []
            truncated = False
            count = 0
            try:
                for sub in entity.virtual_entities():
                    count += 1
                    if count > MAX_INSERT_VIRTUAL_ENTITIES:
                        truncated = True
                        break
                    sub_result = entity_bounds(sub, _depth=_depth + 1)
                    if sub_result.bounds is not None:
                        boxes.append(sub_result.bounds)
            except Exception:
                return BoundsResult(
                    None,
                    "unsupported",
                    "Block definition missing or unreadable.",
                )
            box = _merge(boxes)
            if box is None:
                point = entity.dxf.insert
                x, y = float(point[0]), float(point[1])
                return BoundsResult(
                    (x, y, x, y),
                    "approximate",
                    "Insertion point only; block content had no bounds.",
                )
            if truncated:
                return BoundsResult(
                    box,
                    "approximate",
                    "Partial expansion; sub-entity limit reached.",
                )
            return BoundsResult(box, "computed")

    except Exception as exc:  # Malformed geometry never fails the parse.
        return BoundsResult(
            None, "unsupported", f"Geometry unreadable: {type(exc).__name__}."
        )

    return BoundsResult(
        None,
        "unsupported",
        f"No safe bound rule for entity type {dxftype}.",
    )


def drawing_units(doc) -> DrawingUnits:
    """Read $INSUNITS from the DXF header without assuming feet."""

    try:
        if "$INSUNITS" not in doc.header:
            return DrawingUnits(
                insunits_code=None,
                name="unitless",
                confidence="low",
                note=(
                    "The drawing declares no insertion units. Coordinates "
                    "are local drawing units; no unit is assumed."
                ),
            )
        code = int(doc.header.get("$INSUNITS", 0))
    except Exception:
        return DrawingUnits(
            insunits_code=None,
            name="unknown",
            confidence="low",
            note="The units header could not be read.",
        )
    name = INSUNITS_NAMES.get(code)
    if name is None:
        return DrawingUnits(
            insunits_code=code,
            name="unsupported",
            confidence="low",
            note=f"Unsupported $INSUNITS value {code}.",
        )
    if code == 0:
        return DrawingUnits(
            insunits_code=0,
            name="unitless",
            confidence="low",
            note=(
                "The drawing declares no insertion units. Coordinates are "
                "local drawing units; no unit is assumed."
            ),
        )
    return DrawingUnits(
        insunits_code=code,
        name=name,
        confidence="high",
        note=f"Declared by the $INSUNITS header ({code}).",
    )
