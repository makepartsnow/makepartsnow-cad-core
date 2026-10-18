# Make Parts Now CAD core

The shared Python package inside the [Make Parts Now](https://makepartsnow.com) CAD add-ins: instant 3D printing
quotes (SLS nylon and FDM plastics) for the parts you select, and checkout on makepartsnow.com, with no account.

You don't need this repository to use the add-ins. Install one of them instead:

- **FreeCAD 1.0+:** the [Make Parts Now workbench](https://github.com/makepartsnow/makepartsnow-freecad)
- **Autodesk Fusion:** the [Make Parts Now add-in](https://makepartsnow.com/fusion)

## What it is

Each add-in carries a pinned, unedited copy of `makepartsnow_cad/` (its `core/` folder, with `CORE_PIN.json`). It holds
the parts that don't touch the CAD program: talking to makepartsnow.com, the quote and checkout steps, the units check,
settings, the consent text and the panel's state. The add-in supplies selection, export and the panel itself.

- Python 3.11 or newer, standard library only, package-relative imports only.
- Nothing runs on the network, in a thread or on disk when it is imported.
- It talks only to makepartsnow.com over HTTPS with certificate checks, opens only https links on makepartsnow.com,
  and uploads design files only there.
- Nothing is sent until the user accepts the consent text and asks for a quote. What is sent is listed in each add-in's
  README and in the [privacy policy](https://makepartsnow.com/legal/privacy).

## Checking a vendored copy

```bash
python scripts/sync-core.py --check path/to/addin/core
```

compares each file with the SHA-256 recorded in that copy's `CORE_PIN.json` and the commit it names here.

## Security

Report a vulnerability by email to nathan@makepartsnow.com with "security" in the subject. Don't open a public issue.

## License

[MIT](LICENSE). Make Parts Now is not affiliated with Autodesk or the FreeCAD project.
