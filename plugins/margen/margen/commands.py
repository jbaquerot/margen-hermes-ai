from __future__ import annotations

from dataclasses import dataclass
import re
from .domain import UserError, valid_reference

FORMATS = {
    "libro": "/libro Título | Autor", "activar": "/activar Título", "libros": "/libros",
    "nota": "/nota texto", "ver": "/ver referencia", "editar": "/editar referencia nuevo texto",
    "mover": "/mover referencia | Título", "historial": "/historial referencia",
    "eliminar": "/eliminar referencia", "resumen": "/resumen [detallado]",
    "resumenes": "/resumenes", "ver_resumen": "/ver_resumen referencia",
    "buscar": "/buscar descripción", "mas": "/mas", "exportar": "/exportar",
    "confirmar": "/confirmar", "cancelar": "/cancelar",
}


@dataclass(frozen=True)
class Intent:
    command: str
    args: tuple[str, ...] = ()


def parse(text: str, *, bot_username: str | None = None) -> Intent:
    if not text.strip():
        raise UserError("La nota no puede estar vacía.")
    if not text.lstrip().startswith("/"):
        return Intent("text", (text,))
    match = re.match(r"^\s*/([a-z_]+)(?:@([A-Za-z0-9_]+))?(?:\s([\s\S]*))?$", text)
    if not match:
        raise UserError("Comando no reconocido. Disponibles: " + ", ".join('/'+c for c in FORMATS))
    cmd, target, tail = match.groups()
    if target and (not bot_username or target.casefold() != bot_username.casefold()):
        raise UserError("Ese comando se dirige a otro bot.")
    if cmd not in FORMATS:
        raise UserError("Comando desconocido. Disponibles: " + ", ".join('/'+c for c in FORMATS))
    arg = (tail or "").strip()

    def bad():
        raise UserError("Uso: " + FORMATS[cmd])

    if cmd in {"libros", "mas", "resumenes", "exportar", "confirmar", "cancelar"}:
        if arg:
            bad()
        return Intent(cmd)
    if cmd == "resumen":
        if arg not in ("", "detallado"):
            bad()
        return Intent(cmd, ("detailed" if arg else "brief",))
    if not arg:
        bad()
    if cmd in {"libro", "mover"}:
        parts = arg.split("|")
        if len(parts) != 2 or not all(x.strip() for x in parts):
            bad()
        args = tuple(x.strip() for x in parts)
        if cmd == "mover" and not valid_reference(args[0]):
            bad()
        return Intent(cmd, args)
    if cmd == "editar":
        parts = arg.split(maxsplit=1)
        if len(parts) != 2 or not valid_reference(parts[0]):
            bad()
        return Intent(cmd, tuple(parts))
    if cmd in {"ver", "historial", "eliminar", "ver_resumen"}:
        if not valid_reference(arg, "R" if cmd == "ver_resumen" else "N"):
            bad()
    return Intent(cmd, ((tail or "") if cmd == "nota" else arg,))
