from os import get_terminal_size


def color_tag(text: str, c: str):
    return f"<{c}>" + text + f"</{c}>"


def loguru_format(record: dict) -> str:
    time = color_tag("{time:YYYY-MM-DD HH:mm:ss.SSS}", "light-black")
    level = color_tag("{level: <8}", "level")
    msg = color_tag("{message:<24}", "level")
    name = color_tag("{name}", "light-blue")
    func = color_tag("{function}", "light-blue")
    lineno = color_tag("{line}", "light-blue")

    extras = ""
    if len(record["extra"]):
        for key in record["extra"].keys():
            extras = extras + key + "=" + "{extra[" + key + "]}, "
        extras = extras[:-2]
    fmt = f"{time} [ {level} ] {name}:{func}:{lineno} - {msg} {extras}\n"
    return fmt


def br(c: str = "_", length: int = None, *, newline=False) -> None:
    length = length if length is not None else get_terminal_size().columns
    s = c * length
    if newline:
        s += "\n"
    print(s)


__all__ = ["loguru_format", "br"]
