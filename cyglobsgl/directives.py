"""Validated directive packets for CyGlobsGL.

The packet format is intentionally small and hex-editor friendly:

    byte 0  opcode:4 | flags:4
    byte 1  object id
    byte 2-3 x as signed Q8.8
    byte 4-5 y as signed Q8.8
    byte 6-7 z as signed Q8.8
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import IntEnum
import math
import struct
from typing import Iterable, Sequence, TypeVar


DEFAULT_RADIUS = 0.62
_PACKET = struct.Struct(">BBhhh")
_T = TypeVar("_T")


class Opcode(IntEnum):
    """Directive opcodes and their named domains."""

    SORT = 0x1       # Jecht
    TRANSLATE = 0x2  # Daq
    ROTATE = 0x3     # MVP
    SCALE = 0x4      # Cap


DOMAIN_BY_OPCODE = {
    Opcode.SORT: "Jecht",
    Opcode.TRANSLATE: "Daq",
    Opcode.ROTATE: "MVP",
    Opcode.SCALE: "Cap",
}


@dataclass(frozen=True, slots=True)
class Directive:
    opcode: Opcode
    object_id: int = 0
    x: float = 0.0
    y: float = 0.0
    z: float = 0.0
    flags: int = 0

    def __post_init__(self) -> None:
        if not 0 <= self.object_id <= 0xFF:
            raise ValueError("object_id must fit in one byte")
        if not 0 <= self.flags <= 0x0F:
            raise ValueError("flags must fit in four bits")
        for name, value in (("x", self.x), ("y", self.y), ("z", self.z)):
            if not math.isfinite(value):
                raise ValueError(f"{name} must be finite")
            if not -128.0 <= value <= 127.99609375:
                raise ValueError(f"{name} is outside signed Q8.8 range")

    @property
    def domain(self) -> str:
        return DOMAIN_BY_OPCODE[self.opcode]


@dataclass(frozen=True, slots=True)
class DirectivePacket:
    directive: Directive

    @staticmethod
    def _encode_q8_8(value: float) -> int:
        return int(round(value * 256.0))

    @staticmethod
    def _decode_q8_8(value: int) -> float:
        return value / 256.0

    def pack(self) -> bytes:
        d = self.directive
        opcode_and_flags = (int(d.opcode) << 4) | d.flags
        return _PACKET.pack(
            opcode_and_flags,
            d.object_id,
            self._encode_q8_8(d.x),
            self._encode_q8_8(d.y),
            self._encode_q8_8(d.z),
        )

    def to_hex(self) -> str:
        return self.pack().hex()

    @classmethod
    def unpack(cls, raw: bytes) -> "DirectivePacket":
        if len(raw) != _PACKET.size:
            raise ValueError(f"directive packet must be exactly {_PACKET.size} bytes")
        opcode_and_flags, object_id, x, y, z = _PACKET.unpack(raw)
        opcode_value = opcode_and_flags >> 4
        flags = opcode_and_flags & 0x0F
        try:
            opcode = Opcode(opcode_value)
        except ValueError as exc:
            raise ValueError(f"unknown directive opcode: 0x{opcode_value:x}") from exc
        return cls(
            Directive(
                opcode=opcode,
                object_id=object_id,
                x=cls._decode_q8_8(x),
                y=cls._decode_q8_8(y),
                z=cls._decode_q8_8(z),
                flags=flags,
            )
        )

    @classmethod
    def from_hex(cls, value: str) -> "DirectivePacket":
        try:
            raw = bytes.fromhex(value)
        except ValueError as exc:
            raise ValueError("packet is not valid hexadecimal") from exc
        return cls.unpack(raw)


def sort_jecht(values: Iterable[_T]) -> list[_T]:
    """Return a stable, deterministic ordering for the Sort/Jecht domain."""

    return sorted(values)


def translate_daq(position: Sequence[float], directive: Directive) -> tuple[float, float, float]:
    """Translate a 3D position according to a Translate/Daq directive."""

    if directive.opcode is not Opcode.TRANSLATE:
        raise ValueError("translate_daq requires a TRANSLATE directive")
    if len(position) != 3:
        raise ValueError("position must contain exactly three values")
    return (
        float(position[0]) + directive.x,
        float(position[1]) + directive.y,
        float(position[2]) + directive.z,
    )


def scale_cap(position: Sequence[float], directive: Directive | None = None) -> tuple[float, float, float]:
    """Scale a position in the Scale/Cap domain, defaulting to radius 0.62."""

    if len(position) != 3:
        raise ValueError("position must contain exactly three values")
    if directive is None:
        factors = (DEFAULT_RADIUS, DEFAULT_RADIUS, DEFAULT_RADIUS)
    else:
        if directive.opcode is not Opcode.SCALE:
            raise ValueError("scale_cap requires a SCALE directive")
        factors = (directive.x, directive.y, directive.z)
    return tuple(float(value) * factor for value, factor in zip(position, factors))
