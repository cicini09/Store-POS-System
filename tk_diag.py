import sys
from pathlib import Path

output = Path(__file__).with_name("tk_diag_result.txt")

try:
    import tkinter as tk

    root = tk.Tk()
    output.write_text(
        "\n".join(
            [
                "success",
                sys.executable,
                root.tk.eval("info patchlevel"),
                root.tk.eval("set tcl_library"),
                root.tk.eval("set tk_library"),
            ]
        ),
        encoding="utf-8",
    )
    root.destroy()
except Exception as exc:
    output.write_text(
        "\n".join(["error", sys.executable, repr(exc)]),
        encoding="utf-8",
    )
    raise
