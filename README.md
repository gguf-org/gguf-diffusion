# diffusion

`gguf-diffusion` or `gguf-diffusion.cpp` is a C/C++ inference library and set of example applications for diffusion models backed by GGML. It focuses on local image and video generation, GGUF/safetensors model loading, quantized weights, mixed backend placement, and practical command-line or HTTP server workflows.

The project builds a reusable library, `gguf-diffusion`, plus examples:

- `sd-cli`: command-line generation, conversion, upscaling, metadata inspection, and preview output.
- `sd-server`: HTTP server exposing OpenAI-compatible, Stable Diffusion WebUI-compatible, and native `sdcpp` APIs.

## Features

- Image generation, image-to-image, inpaint/edit-style workflows, reference-image workflows, and video generation.
- Multiple diffusion families, including SD 1.x/2.x, SDXL, SD3, Flux, Flux.2, Chroma, Wan, Qwen Image, Z-Image, HiDream, LTX, and others documented under `docs/`.
- GGML execution backends: CPU by default, with optional CUDA, HIP/ROCm, Metal, Vulkan, OpenCL, SYCL, and MUSA builds.
- GGUF and safetensors-oriented model loading and conversion utilities.
- Quantized weight types through GGML, including common `q4_*`, `q5_*`, `q8_*`, `iq*`, BF16, and related formats.
- LoRA, ControlNet, PhotoMaker, ESRGAN/latent upscaling, TAE/VAE preview, cache modes, and VRAM-aware graph execution controls.
- Optional WebP image I/O and WebM video output support in examples.

## Quick Start

Clone with submodules:

```sh
git clone https://github.com/gguf-org/diffusion
cd gguf-diffusion
```

Build a CPU-only release:

```sh
cmake -B build -DCMAKE_BUILD_TYPE=Release
cmake --build build --config Release
```

Build with CUDA:

```sh
cmake -B build -DCMAKE_BUILD_TYPE=Release -DSD_CUDA=ON
cmake --build build --config Release
```

Run the CLI:

```sh
./build/bin/sd-cli \
  --diffusion-model ./models/diffusion_model.gguf \
  --vae ./models/vae.gguf \
  --t5xxl ./models/text_encoder.gguf \
  --prompt "a cinematic photo of a mountain lake" \
  --width 1024 \
  --height 1024 \
  --steps 30 \
  --output output.png
```

Run the server:

```sh
./build/bin/sd-server \
  --diffusion-model ./models/diffusion_model.gguf \
  --vae ./models/vae.gguf \
  --t5xxl ./models/text_encoder.gguf \
  --listen-ip 127.0.0.1 \
  --listen-port 1234
```

## Build Options

Common CMake options:

| Option | Purpose |
| --- | --- |
| `SD_BUILD_EXAMPLES` | Build `examples/cli` and `examples/server`. Defaults to on for standalone builds. |
| `SD_BUILD_SHARED_LIBS` | Build `gguf-diffusion` as a shared library. Defaults to on. |
| `SD_BUILD_SHARED_GGML_LIB` | Build GGML as a separate shared library. Defaults to on. |
| `SD_USE_SYSTEM_GGML` | Use a system-installed GGML package instead of the bundled `ggml/` tree. |
| `SD_WEBP` | Enable WebP support for example image I/O. |
| `SD_WEBM` | Enable WebM output support; requires WebP. |
| `SD_USE_SYSTEM_WEBP` | Link against system WebP instead of `thirdparty/libwebp`. |
| `SD_USE_SYSTEM_WEBM` | Link against system WebM instead of `thirdparty/libwebm`. |
| `SD_CUDA` | Enable the GGML CUDA backend. |
| `SD_HIPBLAS` | Enable the GGML HIP/ROCm backend. |
| `SD_METAL` | Enable the GGML Metal backend. |
| `SD_VULKAN` | Enable the GGML Vulkan backend. |
| `SD_OPENCL` | Enable the GGML OpenCL backend. |
| `SD_SYCL` | Enable the GGML SYCL backend. |
| `SD_MUSA` | Enable the GGML MUSA backend. |

## Project Structure

```text
.
|-- CMakeLists.txt              # top-level build configuration
|-- include/
|   `-- gguf-diffusion.h        # public C API
|-- src/
|   |-- gguf-diffusion.cpp      # public API implementation and orchestration
|   |-- model.*                 # model metadata, detection, loading helpers
|   |-- convert.cpp             # conversion entry points
|   |-- upscaler.*              # upscaler context API
|   |-- conditioning/           # prompt/text conditioning orchestration
|   |-- core/                   # GGML helpers, backend management, graph utilities, RNG
|   |-- model/
|   |   |-- diffusion/          # UNet, DiT, Flux, Wan, Qwen, SD3, etc.
|   |   |-- te/                 # CLIP, T5, LLM text encoders
|   |   |-- vae/                # VAE, TAE, Wan/LTX/audio VAEs
|   |   |-- adapter/            # LoRA and PhotoMaker adapters
|   |   `-- upscaler/           # ESRGAN and latent upscalers
|   |-- model_io/               # GGUF, safetensors, torch zip/legacy, pickle readers
|   |-- runtime/                # denoisers, guidance, cache modes, previews
|   `-- tokenizers/             # CLIP, T5, Qwen, Mistral, Gemma, GPT-OSS tokenizers
|-- examples/
|   |-- common/                 # shared CLI/server argument, logging, media helpers
|   |-- cli/                    # sd-cli application
|   `-- server/                 # sd-server HTTP APIs and async job runtime
|-- ggml/                       # bundled GGML backend library
`-- thirdparty/                 # zip, stb, httplib, JSON, WebP/WebM, tokenizer deps
```

## Architecture

At a high level, applications call the public C API in `include/gguf-diffusion.h`. The implementation in `src/gguf-diffusion.cpp` creates an `sd_ctx_t`, resolves model files and backend assignments, initializes model runners, and executes generation or utility workflows.

```text
CLI / Server / External C API user
        |
        v
include/gguf-diffusion.h
        |
        v
src/gguf-diffusion.cpp
        |
        +--> model loading and format detection
        |       |-- src/model.cpp
        |       `-- src/model_io/*
        |
        +--> tokenizer and conditioning stack
        |       |-- src/tokenizers/*
        |       |-- src/model/te/*
        |       `-- src/conditioning/*
        |
        +--> diffusion execution stack
        |       |-- src/model/diffusion/*
        |       |-- src/runtime/denoiser.hpp
        |       |-- src/runtime/guidance.*
        |       `-- src/runtime/sample-cache.*
        |
        +--> decode and postprocess
        |       |-- src/model/vae/*
        |       |-- src/model/upscaler/*
        |       `-- examples/common/media_io.*
        |
        v
GGML tensors, graphs, allocators, and backend devices
```

### Main Components

- Public API: `include/gguf-diffusion.h` defines context creation, image/video generation, upscaling, conversion, preprocessing, callbacks, and enum/string helpers.
- Context orchestration: `StableDiffusionGGML` in `src/gguf-diffusion.cpp` owns the loaded model modules, backend manager, RNGs, LoRA state, VAE settings, and runtime options.
- Model I/O: `src/model_io/` reads GGUF, safetensors, torch archives, and related metadata into tensor stores.
- Backend management: `src/core/` wraps GGML backend devices, graph helpers, graph-cut VRAM controls, tensor wrappers, and RNG implementations.
- Conditioning: `src/conditioning/`, `src/model/te/`, and `src/tokenizers/` turn prompts and image references into conditioning tensors.
- Diffusion runners: `src/model/diffusion/` contains architecture-specific runners for supported model families.
- Runtime policies: `src/runtime/` contains denoiser selection, guidance handling, caching strategies, and latent preview generation.
- Decode/upscale: `src/model/vae/`, `src/upscaler.*`, and `src/model/upscaler/` decode latents and optionally upscale outputs.
- Applications: `examples/cli` maps command-line options to API structs; `examples/server` maps HTTP requests to the same generation structs and runs async jobs.

## Generation Workflow

Image generation follows this path:

```text
1. Parse options or API request
2. Fill sd_ctx_params_t and create sd_ctx_t with new_sd_ctx()
3. Load model tensors and instantiate required modules
4. Resolve runtime and parameter backends per module
5. Tokenize prompt and build conditioning tensors
6. Create initial latent from seed, init image, mask, or references
7. Run sampler/denoiser loop over the diffusion model
8. Apply guidance, LoRA, cache policy, ControlNet, or PhotoMaker as configured
9. Decode final latents through VAE or TAE/VAE preview path
10. Write image/video output or return API response
```

Server requests use the same core path. `sd-server` adds HTTP parsing, compatibility mappings, async job management, cancellation, and response serialization.

## Backend Placement Workflow

Runtime execution and parameter storage can be assigned independently:

```sh
sd-cli \
  --diffusion-model model.gguf \
  --vae vae.gguf \
  --t5xxl text_encoder.gguf \
  --backend diffusion=cuda0,te=cpu,vae=cpu \
  --params-backend diffusion=cuda0,te=cpu,vae=cpu \
  --prompt "a cat"
```

- `--backend` controls where each module executes.
- `--params-backend` controls where weights are allocated.
- `--offload-to-cpu` is equivalent to CPU parameter placement when no explicit parameter backend is set.
- `--max-vram` enables graph-cut segmented execution for constrained VRAM scenarios.

## Server APIs

`sd-server` exposes three API families:

- OpenAI-compatible image endpoints under `/v1/...`
- Stable Diffusion WebUI-compatible endpoints under `/sdapi/v1/...`
- Native async `sdcpp` endpoints under `/sdcpp/v1/...`

The native API is documented in `examples/server/api.md`. The root path `/` returns a plain server status page unless `--serve-html-path <index.html>` is provided.

## Public API Sketch

A minimal embedding flow looks like this:

```c
#include "gguf-diffusion.h"

sd_ctx_params_t ctx_params;
sd_ctx_params_init(&ctx_params);
ctx_params.diffusion_model_path = "model.gguf";
ctx_params.vae_path = "vae.gguf";
ctx_params.t5xxl_path = "text_encoder.gguf";

sd_ctx_t *ctx = new_sd_ctx(&ctx_params);

sd_img_gen_params_t gen_params;
sd_img_gen_params_init(&gen_params);
gen_params.prompt = "a small cabin beside a lake";
gen_params.width = 1024;
gen_params.height = 1024;
gen_params.sample_params.sample_steps = 30;

generate_image(ctx, &gen_params);
free_sd_ctx(ctx);
```

Applications should check return values, own and free generated images according to the API contract used by their call path, and install log/progress callbacks when interactive feedback is needed.

## Development Notes

- The project uses C11 and C++17.
- Source files are collected by CMake glob patterns under `src/`, so adding new implementation files usually requires reconfiguring CMake.
- Shared CLI/server parsing utilities live under `examples/common`.
- Keep model-family-specific code close to the existing runner folders under `src/model/`.
- Use `format-code.sh` before submitting broad formatting-sensitive changes.

## Acknowledgments/references

stable-diffusion.cpp (MIT License) [leejet](https://github.com/leejet/stable-diffusion.cpp) and llama.cpp (MIT License) [ggml](https://github.com/ggml-org/ggml)

## License

See `LICENSE`.
