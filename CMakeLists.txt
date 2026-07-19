# Builds the diffusion.cpp engine (sibling ./diffusion checkout, an optional
# vendor/diffusion copy, or GGUF_DIFFUSION_ENGINE_DIR) as a single static CLI
# binary and installs it into the gguf_diffusion package, where the Python
# server spawns it per generation. Modeled on gguf_editor's CMakeLists.txt.
cmake_minimum_required(VERSION 3.15)
project(gguf_diffusion C CXX)

option(GGUF_DIFFUSION_BUILD "Build the diffusion engine binary and install it alongside the python package" ON)

if(NOT GGUF_DIFFUSION_BUILD)
    return()
endif()

if(NOT CMAKE_BUILD_TYPE AND NOT CMAKE_CONFIGURATION_TYPES)
    set(CMAKE_BUILD_TYPE Release CACHE STRING "Build type" FORCE)
endif()

# ── Locate the engine source tree ────────────────────────────────────────────
set(GGUF_DIFFUSION_ENGINE_DIR "" CACHE PATH "Path to the diffusion.cpp source tree")
if(NOT GGUF_DIFFUSION_ENGINE_DIR AND DEFINED ENV{GGUF_DIFFUSION_ENGINE_DIR})
    set(GGUF_DIFFUSION_ENGINE_DIR "$ENV{GGUF_DIFFUSION_ENGINE_DIR}")
endif()
if(NOT GGUF_DIFFUSION_ENGINE_DIR)
    if(EXISTS "${CMAKE_CURRENT_SOURCE_DIR}/vendor/diffusion/CMakeLists.txt")
        set(GGUF_DIFFUSION_ENGINE_DIR "${CMAKE_CURRENT_SOURCE_DIR}/vendor/diffusion")
    elseif(EXISTS "${CMAKE_CURRENT_SOURCE_DIR}/../diffusion/CMakeLists.txt")
        set(GGUF_DIFFUSION_ENGINE_DIR "${CMAKE_CURRENT_SOURCE_DIR}/../diffusion")
    endif()
endif()
if(NOT GGUF_DIFFUSION_ENGINE_DIR OR NOT EXISTS "${GGUF_DIFFUSION_ENGINE_DIR}/CMakeLists.txt")
    message(FATAL_ERROR
        "diffusion engine source not found. Provide it via one of:\n"
        "  - a sibling checkout at ../diffusion\n"
        "  - a vendored copy at vendor/diffusion (see scripts/vendor_engine.py)\n"
        "  - -DGGUF_DIFFUSION_ENGINE_DIR=/path/to/diffusion or the same env var")
endif()
get_filename_component(GGUF_DIFFUSION_ENGINE_DIR "${GGUF_DIFFUSION_ENGINE_DIR}" ABSOLUTE)
message(STATUS "gguf-diffusion: engine source at ${GGUF_DIFFUSION_ENGINE_DIR}")

# ── Build the engine as one self-contained executable ────────────────────────
# Static libdiffusion + static ggml linked into the CLI keeps the wheel to a
# single binary (no shared-library rpath handling). GPU backends are opt-in
# via the engine's own options, e.g. CMAKE_ARGS="-DSD_CUDA=ON" pip install .
set(SD_BUILD_SHARED_LIBS OFF CACHE BOOL "gguf-diffusion: static engine for a single-file install" FORCE)
set(SD_BUILD_CLI ON CACHE BOOL "gguf-diffusion: the CLI is the bundled artifact" FORCE)

# EXCLUDE_FROM_ALL drops the engine's own install() rules (ggml headers,
# libs, pkg-config) which would otherwise pollute the wheel; the custom
# target below still forces the CLI to build.
add_subdirectory("${GGUF_DIFFUSION_ENGINE_DIR}" "${CMAKE_BINARY_DIR}/diffusion-engine" EXCLUDE_FROM_ALL)

if(NOT TARGET diffusion-cli)
    message(FATAL_ERROR "engine did not define the diffusion-cli target — is ${GGUF_DIFFUSION_ENGINE_DIR} the diffusion.cpp source tree?")
endif()

add_custom_target(gguf_diffusion_engine ALL)
add_dependencies(gguf_diffusion_engine diffusion-cli)

# Install into the wheel (SKBUILD_PLATLIB_DIR) and also into the source tree
# so editable installs (`pip install -e .`) find the binary — same dual
# install gguf_editor uses.
install(
    PROGRAMS $<TARGET_FILE:diffusion-cli>
    DESTINATION "${CMAKE_CURRENT_SOURCE_DIR}/src/gguf_diffusion/bin"
)
if(DEFINED SKBUILD_PLATLIB_DIR)
    install(
        PROGRAMS $<TARGET_FILE:diffusion-cli>
        DESTINATION "${SKBUILD_PLATLIB_DIR}/gguf_diffusion/bin"
    )
endif()
