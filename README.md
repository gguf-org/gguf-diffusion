# gguf-diffusion

Image generation GUI for GGUF diffusion models, packaged for Python. The GUI
runs in your browser against a local server; generation is done by the
diffusion.cpp engine, compiled during `pip install` and bundled with the
package as a single binary. Model and image files are referenced by
filesystem path through a built-in file browser — nothing is uploaded or
copied to temp storage.

## Install

```bash
pip install gguf-diffusion
```

Building the bundled engine requires a C/C++ toolchain and CMake ≥ 3.15
(on Windows: MSVC Build Tools). The engine source is resolved from a sibling
`../diffusion` checkout, a vendored `vendor/diffusion` copy (see
`scripts/vendor_engine.py`), or `GGUF_DIFFUSION_ENGINE_DIR`. GPU backends are
opt-in at build time via the engine's own options:

```bash
CMAKE_ARGS="-DSD_CUDA=ON"    pip install gguf-diffusion   # NVIDIA (CUDA toolkit)
CMAKE_ARGS="-DSD_HIPBLAS=ON" pip install gguf-diffusion   # AMD (ROCm/HIP)
CMAKE_ARGS="-DSD_METAL=ON"   pip install gguf-diffusion   # Apple (macOS)
CMAKE_ARGS="-DSD_VULKAN=ON"  pip install gguf-diffusion   # Vulkan
```

## Usage

```bash
python -m gguf_diffusion             # launch the GUI in the browser
gguf-diffusion                       # same
gguf-diffusion --port 8643 --no-browser
```

GUI features (as in the desktop app's diffusion panel):

- txt2img with the full model stack: `--model` / `--diffusion-model`, VAE,
  external text encoders (`--clip_l`, `--t5xxl`, `--llm`, …), additional
  models (ControlNet, TAESD, upscaler, PhotoMaker, …), tokenizer packs
- image inputs: init image (img2img), mask (inpainting), end frame,
  control image, reference images
- sampling controls: CFG scale, steps, size, seed, batch count, all engine
  sampling methods and schedules, flash attention, low-VRAM flags
- live progress and engine log, output gallery, saved workflows
  (localStorage + JSON export/import), copyable/editable CLI command

Engine CLI passthrough (runs the bundled `diffusion` binary):

```bash
python -m gguf_diffusion engine -- --diffusion-model model.gguf -p "a cat" -o cat.png
gguf-diffusion engine -- --help
```

## How it works

- `pip install` compiles the diffusion.cpp engine (static libdiffusion +
  static ggml linked into one CLI executable) via scikit-build-core and
  installs it into the package's `bin/` directory.
- `gguf-diffusion` starts a stdlib HTTP server (default port 8643) serving
  the static GUI and a small JSON API, and opens the browser.
- Each generation spawns one engine process; the server parses its progress
  bars, streams the log to the GUI, and lists the produced images.
- File selection uses a server-side directory listing (`/api/browse`) so the
  GUI gets real filesystem paths — no drag & drop uploads of multi-GB models.
