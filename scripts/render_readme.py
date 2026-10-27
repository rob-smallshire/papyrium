#!/usr/bin/env python3
"""Render Papyrium's READMEs, and the sample pages they show, from templates.

README.md, the landing page on GitHub, is rendered from
scripts/readme-templates/README.md.j2, and so is README-pypi.md, the long
description of the papyrium distribution, with links made absolute for
PyPI. A module whose README states facts the code also holds, such as a
printer model's options and their defaults, keeps a template beside it,
src/papyrium/<module>/README.md.j2, rendered to README.md there.

Templates see Papyrium's modules (each described by the first line of its
docstring), the installed plug-ins on each axis, and these functions:

- ``transcript(name)`` runs scripts/readme-examples/<name>.py, a recipe
  that prints ``$ command`` transcripts with ``readme_helper.show``, and
  shows its output.
- ``options_table(model, meanings, defaults=...)`` tabulates a printer
  model's options with the defaults its constructor declares. *meanings*
  must name every option the model has, and no others.
- ``repo_url(path, raw=False)`` gives a link to a file in the repository:
  relative on GitHub, absolute on PyPI, from raw.githubusercontent.com for
  an image.
- ``demo_image(image_name, model, crop=..., ...)`` does the same for a
  printer model's demonstration page, printed with ``papyrium demo``.
- ``page_image(image_name, capture, model, crop=..., ...)`` prints the
  capture written by scripts/readme-examples/<capture>.py with the
  ``papyrium`` command, crops the first page to *crop* inches, saves it as
  docs/images/<image_name>.png and returns the image's repository path.

Everything is run against Papyrium's own code, so a change that
alters a transcript, an option or a printed page changes the README.

Usage:
    uv run python scripts/render_readme.py          # write every README
    uv run python scripts/render_readme.py --check  # exit 1 if any is stale

The pre-commit hook runs it without --check: it rewrites what is stale and
pre-commit fails the commit, so the regenerated files can be looked at and
staged.
"""

from __future__ import annotations

import argparse
import importlib
import inspect
import os
import subprocess
import sys
import tempfile
from collections.abc import Callable, Mapping
from dataclasses import dataclass, field
from functools import partial
from importlib.metadata import entry_points
from pathlib import Path

from jinja2 import ChoiceLoader, Environment, FileSystemLoader, StrictUndefined
from PIL import Image

from papyrium.extension import create_extension, describe_extension, namespace_for

REPO_DIRPATH = Path(__file__).resolve().parent.parent
SCRIPTS_DIRPATH = REPO_DIRPATH / "scripts"
TEMPLATE_DIRPATH = SCRIPTS_DIRPATH / "readme-templates"
EXAMPLES_DIRPATH = SCRIPTS_DIRPATH / "readme-examples"
SOURCE_DIRPATH = REPO_DIRPATH / "src"
IMAGES_DIRPATH = REPO_DIRPATH / "docs" / "images"

#: Where the repository's files are seen from PyPI, whose pages cannot
#: follow links relative to the repository.
REPOSITORY_URL = "https://github.com/rob-smallshire/papyrium/blob/master/"
RAW_REPOSITORY_URL = "https://raw.githubusercontent.com/rob-smallshire/papyrium/master/"

README_TEMPLATE_FILENAME = "README.md.j2"

#: The plug-in axes, in the order bytes flow through a printer.
AXES = ("transport", "language", "model", "font", "output", "advertiser")

#: The modules the README lists first, the foundations, and last.
FIRST_MODULES = ("papyrium.exception", "papyrium.extension", "papyrium.core")
LAST_MODULES = ("papyrium.cli",)


@dataclass(frozen=True)
class ModuleMeta:
    name: str
    description: str

    @property
    def dirpath(self) -> str:
        """The module's directory, relative to the repository."""
        return "src/" + self.name.replace(".", "/") + "/"


@dataclass(frozen=True)
class Plugin:
    name: str
    description: str
    module: ModuleMeta


def _module_meta(name: str) -> ModuleMeta:
    docstring = importlib.import_module(name).__doc__ or ""
    return ModuleMeta(name, docstring.strip().splitlines()[0].rstrip(".") if docstring else "")


def load_modules() -> list[ModuleMeta]:
    """Papyrium's modules: the foundations, then each axis's in the order bytes
    flow through a printer, then the command."""
    papyrium_dirpath = SOURCE_DIRPATH / "papyrium"
    names = [
        "papyrium." + ".".join(init.parent.relative_to(papyrium_dirpath).parts)
        for init in papyrium_dirpath.glob("**/__init__.py")
        if len(init.parent.relative_to(papyrium_dirpath).parts) <= 2
        and "__pycache__" not in init.parts
    ]
    # A module directly under an axis, such as papyrium.model.star_lc10.
    by_axis = {axis: sorted(n for n in names if n.startswith(f"papyrium.{axis}.")) for axis in AXES}
    ordered = [*FIRST_MODULES, *(n for axis in AXES for n in by_axis[axis]), *LAST_MODULES]
    return [_module_meta(name) for name in ordered if name in names]


def load_plugins() -> dict[str, list[Plugin]]:
    """The installed plug-ins on each axis, by name."""
    plugins = {}
    for kind in AXES:
        namespace = namespace_for(kind)
        plugins[kind] = [
            Plugin(
                point.name,
                describe_extension(kind, namespace, point.name, single_line=True).rstrip("."),
                _module_meta(point.value.split(":")[0]),
            )
            for point in sorted(entry_points(group=namespace), key=lambda point: point.name)
        ]
    return plugins


def _environment() -> dict[str, str]:
    """For example subprocesses: the helper importable and a fixed width."""
    python_path = [str(SCRIPTS_DIRPATH), *filter(None, [os.environ.get("PYTHONPATH")])]
    return {**os.environ, "PYTHONPATH": os.pathsep.join(python_path), "COLUMNS": "80"}


def _run_example(example_name: str, *arguments: str, cwd: Path) -> str:
    """Run an example script in *cwd* and return its output; failing is an error."""
    example_filepath = EXAMPLES_DIRPATH / f"{example_name}.py"
    if not example_filepath.is_file():
        raise FileNotFoundError(f"example not found: {example_filepath}")
    result = subprocess.run(
        [sys.executable, str(example_filepath), *arguments],
        capture_output=True,
        text=True,
        check=False,
        cwd=cwd,
        env=_environment(),
    )
    if result.returncode != 0:
        raise RuntimeError(
            f"example {example_name!r} failed with exit {result.returncode}:\n"
            f"--- stdout ---\n{result.stdout}--- stderr ---\n{result.stderr}"
        )
    return result.stdout


def render_transcript(example_name: str) -> str:
    """A Markdown code block holding a recipe's ``$ command`` transcript."""
    with tempfile.TemporaryDirectory(prefix="papyrium-readme-") as work_dirname:
        stdout = _run_example(example_name, cwd=Path(work_dirname))
    return f"```\n{stdout.rstrip()}\n```"


def _show_default(value: object) -> str:
    if isinstance(value, bool):
        return "yes" if value else "no"
    return str(value)


def render_options_table(
    model: str, meanings: Mapping[str, str], defaults: Mapping[str, str] | None = None
) -> str:
    """A Markdown table of *model*'s options, with their meanings and defaults.

    Defaults come from the model's constructor; *defaults* gives the text
    for an option whose default depends on others (declared as None).

    Raises:
        ValueError: *meanings* does not name exactly the model's options, or
            an option defaulting to None has no text in *defaults*.
    """
    defaults = defaults or {}
    model_class = type(create_extension("model", namespace_for("model"), model))
    parameters = {
        name.replace("_", "-"): parameter.default
        for name, parameter in inspect.signature(model_class).parameters.items()
        if parameter.kind is parameter.KEYWORD_ONLY
    }
    if set(meanings) != set(parameters):
        raise ValueError(
            f"{model} options differ from the README: "
            f"undocumented {sorted(set(parameters) - set(meanings))}, "
            f"no such option {sorted(set(meanings) - set(parameters))}"
        )
    rows = ["| Option | Default | Meaning |", "|---|---|---|"]
    for option, meaning in meanings.items():
        default = parameters[option]
        if default is None and option not in defaults:
            raise ValueError(f"{model} option {option!r} defaults to None; describe its default")
        shown = defaults.get(option, f"`{_show_default(default)}`")
        rows.append(f"| `{option}` | {shown} | {meaning} |")
    return "\n".join(rows)


@dataclass
class ImageSet:
    """The sample page images a render produces, by repository path."""

    images: dict[Path, Image.Image] = field(default_factory=dict)
    _paths: dict[tuple, str] = field(default_factory=dict)

    def page_image(
        self,
        image_name: str,
        capture: str,
        model: str,
        *,
        crop: tuple[float, float, float, float],
        options: Mapping[str, str] | None = None,
        dpi: int = 150,
    ) -> str:
        """Print an example capture and keep a crop of its first page.

        *crop* is (left, top, right, bottom) in inches from the sheet's
        top-left corner. Returns the image's path relative to the
        repository, for a Markdown image link. Each image is printed once
        however many READMEs show it.
        """
        key = ("page", image_name, capture, model, crop, _items(options), dpi)
        if key not in self._paths:

            def arguments(work_dirpath: Path) -> list[str]:
                capture_filepath = work_dirpath / f"{capture}.prn"
                _run_example(capture, str(capture_filepath), cwd=work_dirpath)
                return ["render", str(capture_filepath), "--model", model]

            self._paths[key] = self._print(image_name, arguments, crop, options, dpi)
        return self._paths[key]

    def demo_image(
        self,
        image_name: str,
        model: str,
        *,
        height: float,
        options: Mapping[str, str] | None = None,
        dpi: int = 100,
    ) -> str:
        """Print *model*'s demonstration page and keep its top *height* inches.

        Returns the image's path relative to the repository, as page_image does.
        """
        crop = (0, 0, None, height)
        key = ("demo", image_name, model, crop, _items(options), dpi)
        if key not in self._paths:
            self._paths[key] = self._print(
                image_name, lambda _: ["demo", model], crop, options, dpi
            )
        return self._paths[key]

    def _print(self, image_name, arguments, crop, options, dpi) -> str:
        """Print with the papyrium command and keep a crop of the first page.

        *arguments* gives the command's arguments up to the options, for a
        working directory it may write into.
        """
        with tempfile.TemporaryDirectory(prefix="papyrium-readme-") as work_dirname:
            work_dirpath = Path(work_dirname)
            command = [
                str(Path(sys.executable).parent / "papyrium"),
                *arguments(work_dirpath),
                "--output",
                "png",
                "--output-option",
                f"png.dpi={dpi}",
                "--output-dir",
                str(work_dirpath),
                "--no-reports",
            ]
            for key, value in (options or {}).items():
                command += ["--model-option", f"{key}={value}"]
            subprocess.run(command, check=True, env=_environment())
            with Image.open(work_dirpath / "page-0001.png") as page:
                # A right edge of None is the page's own.
                box = tuple(
                    page.width if inches is None else round(inches * dpi) for inches in crop
                )
                image = page.crop(box)
        image_filepath = IMAGES_DIRPATH / f"{image_name}.png"
        self.images[image_filepath] = image
        return str(image_filepath.relative_to(REPO_DIRPATH))


def _items(options: Mapping[str, str] | None) -> tuple:
    return tuple(sorted((options or {}).items()))


def _jinja_environment(*template_dirpaths: Path) -> Environment:
    return Environment(
        loader=ChoiceLoader(
            [FileSystemLoader(dirpath) for dirpath in (*template_dirpaths, TEMPLATE_DIRPATH)]
        ),
        undefined=StrictUndefined,
        keep_trailing_newline=True,
    )


def _relative_url(path: str, raw: bool = False) -> str:
    return path


def _repository_url(path: str, raw: bool = False) -> str:
    return (RAW_REPOSITORY_URL if raw else REPOSITORY_URL) + path


def _render(
    template_dirpath: Path,
    images: ImageSet,
    *,
    repo_url: Callable[..., str] = _relative_url,
    **context: object,
) -> str:
    template = _jinja_environment(template_dirpath).get_template(README_TEMPLATE_FILENAME)
    return template.render(
        repo_url=repo_url,
        modules=load_modules(),
        plugins=load_plugins(),
        transcript=render_transcript,
        options_table=render_options_table,
        page_image=images.page_image,
        demo_image=images.demo_image,
        **context,
    )


@dataclass(frozen=True)
class RenderTarget:
    output_filepath: Path
    render: Callable[[ImageSet], str]


def _targets() -> list[RenderTarget]:
    targets = [
        RenderTarget(REPO_DIRPATH / "README.md", partial(_render, TEMPLATE_DIRPATH)),
        RenderTarget(
            REPO_DIRPATH / "README-pypi.md",
            partial(_render, TEMPLATE_DIRPATH, repo_url=_repository_url),
        ),
    ]
    for template_filepath in sorted(SOURCE_DIRPATH.glob(f"papyrium/**/{README_TEMPLATE_FILENAME}")):
        targets.append(
            RenderTarget(
                template_filepath.parent / "README.md",
                # A module's README lies deep in the tree, so its links are
                # absolute rather than relative to the repository's root.
                partial(_render, template_filepath.parent, repo_url=_repository_url),
            )
        )
    return targets


def _image_is_current(image_filepath: Path, image: Image.Image) -> bool:
    """Whether the file holds *image*'s pixels; PNG encoders may differ in bytes."""
    if not image_filepath.exists():
        return False
    with Image.open(image_filepath) as current:
        return current.mode == image.mode and current.tobytes() == image.tobytes()


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument(
        "--check", action="store_true", help="Exit 1 if any README or image is stale."
    )
    arguments = parser.parse_args()

    images = ImageSet()
    rendered = {target.output_filepath: target.render(images) for target in _targets()}
    stale = [
        filepath
        for filepath, text in rendered.items()
        if not filepath.exists() or filepath.read_text() != text
    ]
    stale += [
        filepath
        for filepath, image in images.images.items()
        if not _image_is_current(filepath, image)
    ]

    for filepath in stale:
        name = filepath.relative_to(REPO_DIRPATH)
        if arguments.check:
            print(f"{name} is out of date", file=sys.stderr)
            continue
        if filepath in rendered:
            filepath.write_text(rendered[filepath])
        else:
            filepath.parent.mkdir(parents=True, exist_ok=True)
            images.images[filepath].save(filepath, optimize=True)
        print(f"wrote {name}")
    if arguments.check and stale:
        print("Regenerate with: uv run python scripts/render_readme.py", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
