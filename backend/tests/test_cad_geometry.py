"""Geometry bounds and drawing-unit tests over in-memory ezdxf fixtures."""

from __future__ import annotations

import ezdxf
import pytest

from app.services.cad.geometry import drawing_units, entity_bounds


@pytest.fixture()
def msp():
    doc = ezdxf.new("R2010")
    return doc, doc.modelspace()


def close(a: float, b: float, tol: float = 1e-6) -> bool:
    return abs(a - b) <= tol


class TestBasicEntities:
    def test_line(self, msp) -> None:
        _, space = msp
        entity = space.add_line((1, 2), (4, 6))
        result = entity_bounds(entity)
        assert result.status == "computed"
        assert result.bounds == (1.0, 2.0, 4.0, 6.0)

    def test_point(self, msp) -> None:
        _, space = msp
        entity = space.add_point((3, 4))
        result = entity_bounds(entity)
        assert result.status == "computed"
        assert result.bounds == (3.0, 4.0, 3.0, 4.0)

    def test_circle(self, msp) -> None:
        _, space = msp
        entity = space.add_circle((10, 10), radius=5)
        result = entity_bounds(entity)
        assert result.status == "computed"
        assert result.bounds == (5.0, 5.0, 15.0, 15.0)

    def test_arc_quarter(self, msp) -> None:
        _, space = msp
        # Quarter arc from 0 to 90 degrees around the origin, radius 10.
        entity = space.add_arc((0, 0), radius=10, start_angle=0, end_angle=90)
        result = entity_bounds(entity)
        assert result.status == "computed"
        x_min, y_min, x_max, y_max = result.bounds
        assert close(x_min, 0.0) and close(y_min, 0.0)
        assert close(x_max, 10.0) and close(y_max, 10.0)

    def test_arc_crossing_zero(self, msp) -> None:
        _, space = msp
        entity = space.add_arc(
            (0, 0), radius=10, start_angle=350, end_angle=10
        )
        result = entity_bounds(entity)
        x_min, y_min, x_max, y_max = result.bounds
        # The arc crosses the positive x axis so x_max is the full radius.
        assert close(x_max, 10.0)
        assert x_min > 9.0

    def test_lwpolyline(self, msp) -> None:
        _, space = msp
        entity = space.add_lwpolyline([(0, 0), (10, 0), (10, 5)])
        result = entity_bounds(entity)
        assert result.status == "computed"
        assert result.bounds == (0.0, 0.0, 10.0, 5.0)

    def test_heavyweight_polyline(self, msp) -> None:
        _, space = msp
        entity = space.add_polyline2d([(0, 0), (4, 4), (8, 0)])
        result = entity_bounds(entity)
        assert result.status == "computed"
        assert result.bounds == (0.0, 0.0, 8.0, 4.0)

    def test_spline_is_approximate(self, msp) -> None:
        _, space = msp
        entity = space.add_spline(
            [(0, 0), (2, 4), (6, 4), (8, 0)]
        )
        result = entity_bounds(entity)
        assert result.status == "approximate"
        x_min, y_min, x_max, y_max = result.bounds
        assert x_min <= 0.0 and x_max >= 8.0

    def test_ellipse_is_approximate_overestimate(self, msp) -> None:
        _, space = msp
        entity = space.add_ellipse(
            (0, 0), major_axis=(5, 0), ratio=0.5
        )
        result = entity_bounds(entity)
        assert result.status == "approximate"
        x_min, y_min, x_max, y_max = result.bounds
        assert x_min <= -5.0 and x_max >= 5.0

    def test_hatch_boundary(self, msp) -> None:
        _, space = msp
        hatch = space.add_hatch()
        hatch.paths.add_polyline_path([(0, 0), (4, 0), (4, 4), (0, 4)])
        result = entity_bounds(hatch)
        assert result.status == "approximate"
        assert result.bounds == (0.0, 0.0, 4.0, 4.0)

    def test_solid(self, msp) -> None:
        _, space = msp
        entity = space.add_solid([(0, 0), (2, 0), (0, 2), (2, 2)])
        result = entity_bounds(entity)
        assert result.status == "computed"
        assert result.bounds == (0.0, 0.0, 2.0, 2.0)

    def test_xline_is_unsupported_with_reason(self, msp) -> None:
        _, space = msp
        entity = space.add_xline((0, 0), (1, 1))
        result = entity_bounds(entity)
        assert result.bounds is None
        assert result.status == "unsupported"
        assert "unbounded" in result.reason.lower()


class TestInserts:
    def _block_doc(self):
        doc = ezdxf.new("R2010")
        block = doc.blocks.new("UNIT")
        block.add_line((0, 0), (2, 2))
        return doc

    def test_plain_insert(self) -> None:
        doc = self._block_doc()
        space = doc.modelspace()
        insert = space.add_blockref("UNIT", (10, 10))
        result = entity_bounds(insert)
        assert result.status == "computed"
        assert result.bounds == (10.0, 10.0, 12.0, 12.0)

    def test_scaled_insert(self) -> None:
        doc = self._block_doc()
        space = doc.modelspace()
        insert = space.add_blockref(
            "UNIT", (0, 0), dxfattribs={"xscale": 3, "yscale": 3}
        )
        result = entity_bounds(insert)
        assert result.bounds == (0.0, 0.0, 6.0, 6.0)

    def test_rotated_insert(self) -> None:
        doc = self._block_doc()
        space = doc.modelspace()
        insert = space.add_blockref(
            "UNIT", (0, 0), dxfattribs={"rotation": 90}
        )
        result = entity_bounds(insert)
        x_min, y_min, x_max, y_max = result.bounds
        # Rotating the (0,0)-(2,2) line by 90 degrees lands at (-2,0)-(0,2).
        assert close(x_min, -2.0) and close(x_max, 0.0)
        assert close(y_min, 0.0) and close(y_max, 2.0)

    def test_nested_insert(self) -> None:
        doc = ezdxf.new("R2010")
        inner = doc.blocks.new("INNER")
        inner.add_line((0, 0), (1, 1))
        outer = doc.blocks.new("OUTER")
        outer.add_blockref("INNER", (5, 5))
        space = doc.modelspace()
        insert = space.add_blockref("OUTER", (10, 10))
        result = entity_bounds(insert)
        assert result.bounds == (15.0, 15.0, 16.0, 16.0)

    def test_missing_block_definition(self) -> None:
        doc = ezdxf.new("R2010")
        space = doc.modelspace()
        insert = space.add_blockref("DOES_NOT_EXIST", (1, 1))
        result = entity_bounds(insert)
        assert result.bounds is None or result.status in {
            "approximate",
            "unsupported",
        }


class TestDrawingUnits:
    def test_missing_units_are_not_assumed(self) -> None:
        doc = ezdxf.new("R2010")
        # ezdxf seeds $INSUNITS on new documents; remove it to model a file
        # with no declared units.
        del doc.header["$INSUNITS"]
        units = drawing_units(doc)
        assert units.name == "unitless"
        assert units.confidence == "low"
        assert "no unit is assumed" in units.note.lower()

    def test_feet(self) -> None:
        doc = ezdxf.new("R2010")
        doc.header["$INSUNITS"] = 2
        units = drawing_units(doc)
        assert units.name == "feet"
        assert units.confidence == "high"

    def test_meters(self) -> None:
        doc = ezdxf.new("R2010")
        doc.header["$INSUNITS"] = 6
        assert drawing_units(doc).name == "meters"

    def test_unsupported_value(self) -> None:
        doc = ezdxf.new("R2010")
        doc.header["$INSUNITS"] = 17
        units = drawing_units(doc)
        assert units.name == "unsupported"
        assert units.confidence == "low"


class TestUnicodeAndLargeCoordinates:
    def test_unicode_text_bounds(self) -> None:
        doc = ezdxf.new("R2010")
        space = doc.modelspace()
        entity = space.add_text(
            "排水盆 1", dxfattribs={"insert": (7, 8)}
        )
        result = entity_bounds(entity)
        assert result.bounds == (7.0, 8.0, 7.0, 8.0)

    def test_large_coordinates(self) -> None:
        doc = ezdxf.new("R2010")
        space = doc.modelspace()
        entity = space.add_line((1e7, 2e7), (1e7 + 5, 2e7 + 5))
        result = entity_bounds(entity)
        assert result.status == "computed"
        assert result.bounds[0] == 1e7
