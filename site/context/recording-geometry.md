# How the geometry of a recording is computed

Question: Where does a pixel in an Orange recording end up in Citrus and Palette, and which files, fields, and transforms carry it there?

Curated context bundle. Each block is a verbatim excerpt from a source repository at the commit named in its header. Contract precedence rules inside the excerpts still apply.

## Who owns which part of the geometry

### orange-owns-camera-space

source: agent-contracts @ e648029cc8c4318b17e8c1d97bb7a00d0fe8ca39  
path: orange-citrus/physical_layout_calibration_contract.md (lines 88-99)  
url: https://github.com/jmdelahanty/agent-contracts/blob/e648029cc8c4318b17e8c1d97bb7a00d0fe8ca39/orange-citrus/physical_layout_calibration_contract.md#L88-L99

### Orange Owns Camera-Space Evidence

Orange is the source of truth for:

- raw or diagnostic camera frames used for dish/tank observation
- detected top-rim circle proposals
- operator-confirmed accepted camera-space mask geometry
- review overlays that show what was accepted
- artifact fingerprints/checksums for the source evidence
- recording snapshots that say which Orange mask was active

Orange artifacts must remain usable when no Citrus experiment is involved.

### citrus-owns-spatial-interpretation

source: agent-contracts @ e648029cc8c4318b17e8c1d97bb7a00d0fe8ca39  
path: orange-citrus/physical_layout_calibration_contract.md (lines 101-114)  
url: https://github.com/jmdelahanty/agent-contracts/blob/e648029cc8c4318b17e8c1d97bb7a00d0fe8ca39/orange-citrus/physical_layout_calibration_contract.md#L101-L114

### Citrus Owns Spatial Interpretation

Citrus is the source of truth for:

- `rig_id`, `canvas_name`, and `arena_id`
- rig/canvas/arena geometry
- base homography and display/camera calibration
- previewing Orange evidence against Citrus geometry
- operator acceptance/rejection of a Citrus registration
- accepted `citrus.dish_pose_registration` artifacts
- Citrus session/H5 calibration snapshots

Citrus may reference or copy Orange artifacts, but Citrus is not the source of
truth for Orange camera-space evidence.

### stable-ids

source: agent-contracts @ e648029cc8c4318b17e8c1d97bb7a00d0fe8ca39  
path: pancake-orange-citrus/rig_canvas_inventory_contract.md (lines 35-45)  
url: https://github.com/jmdelahanty/agent-contracts/blob/e648029cc8c4318b17e8c1d97bb7a00d0fe8ca39/pancake-orange-citrus/rig_canvas_inventory_contract.md#L35-L45

## Stable IDs

- `host_id`: `pancakebatter/system_config.yml -> system_info.hostname`
- `camera_serial`: `pancakebatter/system_config.yml -> cameras[*].serial_number`
- `rig_id`: Citrus rig directory name under `targets/rigs/<rig_id>/`
- `canvas_name`: Citrus canvas directory name and the `canvas_name` field in the canvas JSON
- `arena_id`: key under `arenas` in the Citrus canvas JSON

Important:
- the YAML map key under `system_config.yml:cameras` is a local inventory key and may remain the camera MAC address
- the cross-repo camera join key is always `camera_serial`

### join-invariants

source: agent-contracts @ e648029cc8c4318b17e8c1d97bb7a00d0fe8ca39  
path: pancake-orange-citrus/rig_canvas_inventory_contract.md (lines 111-119)  
url: https://github.com/jmdelahanty/agent-contracts/blob/e648029cc8c4318b17e8c1d97bb7a00d0fe8ca39/pancake-orange-citrus/rig_canvas_inventory_contract.md#L111-L119

## Join Invariants

These invariants are required for cross-repo compatibility:

1. `orange` camera config filename stem must equal `camera_serial`.
2. `citrus` `camera_calibrations[].camera_id` must equal the same `camera_serial`.
3. `rig_id`, `canvas_name`, and `arena_id` are Citrus-owned identifiers and must not be redefined elsewhere with conflicting meaning.
4. Other repos may reference Citrus IDs, but must not copy Citrus calibration payloads as independent editable sources.
5. Other repos may read hardware facts from Pancakebatter, but must not maintain separate hand-edited full copies of that inventory.

## The three pixel frames

### frames-overlay-contract

source: agent-contracts @ e648029cc8c4318b17e8c1d97bb7a00d0fe8ca39  
path: citrus-crimson/spatial_overlay_contract.md (lines 32-45)  
url: https://github.com/jmdelahanty/agent-contracts/blob/e648029cc8c4318b17e8c1d97bb7a00d0fe8ca39/citrus-crimson/spatial_overlay_contract.md#L32-L45

## Canonical Frames

- `arena_relative_canvas_px`
  - local active-arena coordinates
  - origin = top-left of arena region
  - axes = `+x right`, `+y down`
- `final_display_canvas_px`
  - full Citrus display canvas coordinates
  - origin = top-left of fullscreen output canvas
  - axes = `+x right`, `+y down`
- `camera_view_px`
  - raw camera image coordinates
  - origin = top-left of camera image
  - axes = `+x right`, `+y down`

### frames-calibration-contract

source: agent-contracts @ e648029cc8c4318b17e8c1d97bb7a00d0fe8ca39  
path: orange-citrus/physical_layout_calibration_contract.md (lines 137-183)  
url: https://github.com/jmdelahanty/agent-contracts/blob/e648029cc8c4318b17e8c1d97bb7a00d0fe8ca39/orange-citrus/physical_layout_calibration_contract.md#L137-L183
curator note: This is the cross-repo definition, including the Orange alias camera_native_pixels and the physical plane IDs.

## Canonical Coordinate Frames

Every payload must name its pixel frame and, where applicable, physical plane.

- `camera_view_px`
  - Raw camera image coordinates.
  - Origin top-left, x right, y down.

- `camera_native_pixels`
  - Orange synonym used in existing Orange docs for full native camera image
    coordinates.
  - Contract payloads should prefer `camera_view_px` when crossing into Citrus,
    but Orange-native artifacts may preserve `camera_native_pixels`.

- `final_display_canvas_px`
  - Full Citrus display/projector canvas coordinates.
  - Origin top-left, x right, y down.

- `arena_relative_canvas_px`
  - Local Citrus active-arena coordinates.
  - Origin top-left of active arena region, x right, y down.

Recommended physical plane IDs:

- `dish_top_rim`
- `projected_surface`
- `tank_bottom_outer_surface`
- `tank_bottom_inner_surface`
- `estimated_fish_plane`

V0 Orange dish masks target `dish_top_rim`. They should not claim to describe
the projection plane, tank bottom, or fish plane.

Orange-native artifacts may use `camera_native_pixels`; Citrus-facing payloads
may use `camera_view_px`. A consumer must treat these as equivalent only when
the source image is the full native camera frame. If detection runs on a
downsampled or cropped array, the artifact must name that array role and image
shape explicitly.

Known Citrus implementation aliases:

- Orange `coordinate_space` maps to Citrus `source_frame`.
- Orange `image_shape_px` maps to Citrus `image_size_px`.
- Orange accepted circle geometry maps to Citrus `geometry_camera_px`.

Implementations should normalize these aliases deliberately rather than relying
on loose string matching.

### citrus-frame-camera-view

source: citrus @ 48ad93e4d2c84782d0d084a6e3f1352c7c5e3162  
path: docs/coordinate_systems.md (lines 32-45)  
url: https://github.com/JohnsonLabJanelia/citrus/blob/48ad93e4d2c84782d0d084a6e3f1352c7c5e3162/docs/coordinate_systems.md#L32-L45

### `camera_view_px`

The camera image coordinate system used by tracking and homography input points.

- Status: `Code-defined`
- Units: pixels
- Origin: top-left of the camera image
- Axes: `+x = right`, `+y = down`
- Typical data:
  - bounding-box `x_min`, `y_min`, `width`, `height`
  - object centers passed into homography
- Evidence:
  - Citrus uses incoming bbox image coordinates directly in [`src/ipc/ShamanIPCReader.cpp`](../src/ipc/ShamanIPCReader.cpp)
  - bbox centers are transformed with `cv::perspectiveTransform` in [`src/ipc/ShamanIPCReader.cpp`](../src/ipc/ShamanIPCReader.cpp)

### citrus-frame-final-display-canvas

source: citrus @ 48ad93e4d2c84782d0d084a6e3f1352c7c5e3162  
path: docs/coordinate_systems.md (lines 63-79)  
url: https://github.com/JohnsonLabJanelia/citrus/blob/48ad93e4d2c84782d0d084a6e3f1352c7c5e3162/docs/coordinate_systems.md#L63-L79

### `final_display_canvas_px`

The logical full-canvas composition buffer into which Citrus places arena
textures. The established name is retained for compatibility; `display` in the
name does not mean that these indices are already physical projector pixels or
top-left-oriented GLFW framebuffer pixels.

- Status: `Code-defined`
- Units: pixels
- Origin: top-left of the logical CUDA composition buffer
- Axes: `+x = right`, `+y = down`
- Typical data:
  - arena destination rectangles
  - full-canvas previews such as arena-definition preview and experimental-area preview
- Evidence:
  - arenas are composited by top-left destination coordinates `dest_x`, `dest_y` in [`src/core/StimulusDisplayManager.cpp`](../src/core/StimulusDisplayManager.cpp)
  - full-canvas previews use `dest_x = 0`, `dest_y = 0` in [`src/core/StimulusDisplayManager.cpp`](../src/core/StimulusDisplayManager.cpp)

### citrus-frame-arena-relative

source: citrus @ 48ad93e4d2c84782d0d084a6e3f1352c7c5e3162  
path: docs/coordinate_systems.md (lines 127-153)  
url: https://github.com/JohnsonLabJanelia/citrus/blob/48ad93e4d2c84782d0d084a6e3f1352c7c5e3162/docs/coordinate_systems.md#L127-L153

### `arena_relative_canvas_px`

The coordinate system for arena-local geometry inside the active arena region on the stimulus canvas.

- Status: `Code-defined`
- Units:
  - center and positions in pixels
  - sizes in pixels and optionally millimeters
- Origin: top-left of the active arena region
- Axes: `+x = right`, `+y = down`
- Typical data:
  - experimental area center
  - experimental area width/height/radius
- Evidence:
  - the UI explicitly labels experimental-area position as `Arena-Relative Coordinates` in [`src/ui/arena_view_ui.cpp`](../src/ui/arena_view_ui.cpp)
  - experimental-area center sliders run from `0 .. arena_width/height` in [`src/ui/arena_view_ui.cpp`](../src/ui/arena_view_ui.cpp)
  - Citrus now saves this explicitly in `/calibration_snapshot/arena_geometry`

Important distinction:

- `experimental_area_center_x_px` and `experimental_area_center_y_px` are
  arena-relative values in this frame.
- `arena_center_x_px` and `arena_center_y_px` in the active camera calibration
  are full `final_display_canvas_px` arena placement values.
- A consumer must not inverse-project `experimental_area_center_x_px/y_px`
  through the homography directly. Convert arena-relative coordinates to
  `final_display_canvas_px` first by adding the arena origin.

### orange-coordinate-space-enum

source: orange @ b3e8aa60bc8a325ebcc3b5035ec8c3397cea80e4  
path: docs/spatial_layout_schema.md (lines 88-103)  
url: https://github.com/jmdelahanty/orange/blob/b3e8aa60bc8a325ebcc3b5035ec8c3397cea80e4/docs/spatial_layout_schema.md#L88-L103

### Coordinate-space enum

Supported values in v1:

- `camera_native_pixels`
- `layout_mm`
- `layout_units`

Rules:

- `camera_native_pixels` means raw pixel coordinates in the producer camera's
  native stream resolution.
- `layout_mm` is preferred for canonical layout authoring when physical
  measurements are available.
- `layout_units` is allowed when a stable rig-level template exists but the
  layout has not yet been measured in real millimeters.

## The transform chain between frames

### citrus-transform-chain

source: citrus @ 48ad93e4d2c84782d0d084a6e3f1352c7c5e3162  
path: docs/coordinate_systems.md (lines 212-243)  
url: https://github.com/JohnsonLabJanelia/citrus/blob/48ad93e4d2c84782d0d084a6e3f1352c7c5e3162/docs/coordinate_systems.md#L212-L243

## Current Transform Chain

The current intended interpretation is:

1. Tracking arrives in `camera_view_px`.
2. Homography maps those points into Citrus stimulus/display coordinates.
3. Arena-local geometry such as the experimental area lives in `arena_relative_canvas_px`.
4. Arenas are composited into logical `final_display_canvas_px`.
5. The established OpenGL presentation mapping converts that buffer to the
   stimulus window, including its vertical reflection.
6. Desktop runtime state for the chosen display output is captured separately in `/display_snapshot`.
7. Physical projector-body orientation is recorded separately in `/rig_snapshot`.

The concrete mapping formulas are:

```text
arena_origin_canvas = (
  arena_region_center_in_canvas_x_px - arena_region_width_px / 2,
  arena_region_center_in_canvas_y_px - arena_region_height_px / 2
)

p_final_display_canvas = p_arena_relative_canvas + arena_origin_canvas
p_camera_view ~ inverse(H_camera_to_final_display_canvas) * p_final_display_canvas

p_final_display_canvas ~ H_camera_to_final_display_canvas * p_camera_view
p_arena_relative_canvas = p_final_display_canvas - arena_origin_canvas
```

For a daily Orange dish/top-rim observation in full camera pixels, Citrus should
map the accepted center through `H_camera_to_final_display_canvas`, then subtract
the active arena origin if it needs an `arena_relative_canvas_px` value. This is
the correct path for comparing against `experimental_area_center_x_px/y_px`.

### citrus-camera-to-canvas-mapping

source: citrus @ 48ad93e4d2c84782d0d084a6e3f1352c7c5e3162  
path: docs/coordinate_systems.md (lines 155-181)  
url: https://github.com/JohnsonLabJanelia/citrus/blob/48ad93e4d2c84782d0d084a6e3f1352c7c5e3162/docs/coordinate_systems.md#L155-L181

### `camera_view_to_canvas_mapping`

The effective mapping from `camera_view_px` into the stimulus canvas, computed from the active homography.

- Status: `Calibration-derived`
- Nature:
  - point mapping via homography
  - local direction mapping via finite differences around the active arena center
- Evidence:
  - camera points are transformed into stimulus coordinates with `cv::perspectiveTransform` in [`src/ipc/ShamanIPCReader.cpp`](../src/ipc/ShamanIPCReader.cpp)
  - direction basis is derived in [`src/calibration/direction_frame_mapping.h`](../src/calibration/direction_frame_mapping.h)
  - saved H5 fields live under `/calibration_snapshot/<camera_id>` and `/calibration_snapshot/arena_geometry`

The OpenCV sidecar `homography_<arena>_<camera>.yml` and the H5
`/calibration_snapshot/<camera_id>/homography_matrix` represent the same
direction:

```text
camera_view_px -> final_display_canvas_px
```

The homography source points are camera-image pixels from the calibration image.
For current Orange/Citrus workflows these should be full raw camera-frame pixels
when the source image is the native camera frame. If a future calibration is
derived from a crop or downsampled image, that source image shape and crop
transform must be documented in the artifact before Orange can consume it
safely.

### overlay-mapping-rule

source: agent-contracts @ e648029cc8c4318b17e8c1d97bb7a00d0fe8ca39  
path: citrus-crimson/spatial_overlay_contract.md (lines 149-174)  
url: https://github.com/jmdelahanty/agent-contracts/blob/e648029cc8c4318b17e8c1d97bb7a00d0fe8ca39/citrus-crimson/spatial_overlay_contract.md#L149-L174

## Canonical Mapping Rule

For the current square-arena overlay use case, consumers should use:

```text
arena_relative_canvas_px
  -> final_display_canvas_px
  -> camera_view_px
```

More explicitly:

```text
p_display = p_arena_local + arena_origin_in_canvas
p_camera  ~ inverse(H_camera_to_display) * p_display
```

Where:

- `p_arena_local = (x, y)` from `chaser_states`
- `arena_origin_in_canvas = (arena_origin_in_canvas_x_px, arena_origin_in_canvas_y_px)`
- `H_camera_to_display` is the per-camera homography from
  `/calibration_snapshot/<camera_id>/homography_matrix`

If a point already exists in `final_display_canvas_px`, the arena-origin step is
not needed.

### overlay-direct-answers

source: agent-contracts @ e648029cc8c4318b17e8c1d97bb7a00d0fe8ca39  
path: citrus-crimson/spatial_overlay_contract.md (lines 207-215)  
url: https://github.com/jmdelahanty/agent-contracts/blob/e648029cc8c4318b17e8c1d97bb7a00d0fe8ca39/citrus-crimson/spatial_overlay_contract.md#L207-L215

## Direct Answers For Consumers

- Homography is sufficient for the current square-arena use case if it is
  calibrated correctly and the starting point is already in
  `final_display_canvas_px`.
- If the starting point comes from `chaser_states`, homography alone is not
  sufficient; the arena-origin translation is required first.
- No extra offset should be applied before or after inverse homography beyond
  the explicit arena embedding step above.

### citrus-presentation-reflection

source: citrus @ 48ad93e4d2c84782d0d084a6e3f1352c7c5e3162  
path: docs/coordinate_systems.md (lines 81-97)  
url: https://github.com/JohnsonLabJanelia/citrus/blob/48ad93e4d2c84782d0d084a6e3f1352c7c5e3162/docs/coordinate_systems.md#L81-L97
curator note: The logical canvas is not the projected image; this is the one reflection in the chain and it is a compatibility constraint.

### `final_display_canvas_px` to presented display

Presentation is a separate mapping from the logical composition buffer. The
current implementation uploads the CUDA/PBO rows directly to an OpenGL texture
and draws a full-screen quad with texture `v=0` at the bottom. Therefore, before
desktop or projector transforms, the established render path presents:

```text
x_window = x_final_display_canvas
y_window = (canvas_height - 1) - y_final_display_canvas
```

This vertical reflection is existing behavior and is a compatibility
constraint, not a proposed correction. Homographies and orientation receipts
must measure and preserve the effective optical mapping; they must not assume
that camera, logical canvas, GLFW window, projector body, and laboratory axes
have matching signs.

## Where Citrus writes the numbers (session H5)

### h5-arena-embedding

source: agent-contracts @ e648029cc8c4318b17e8c1d97bb7a00d0fe8ca39  
path: citrus-crimson/spatial_overlay_contract.md (lines 77-96)  
url: https://github.com/jmdelahanty/agent-contracts/blob/e648029cc8c4318b17e8c1d97bb7a00d0fe8ca39/citrus-crimson/spatial_overlay_contract.md#L77-L96

### Arena embedding into full display canvas

Group:

- `/calibration_snapshot/arena_geometry`

Authoritative attrs:

- `arena_region_center_in_canvas_x_px`
- `arena_region_center_in_canvas_y_px`
- `arena_region_width_px`
- `arena_region_height_px`
- `arena_origin_in_canvas_x_px`
- `arena_origin_in_canvas_y_px`

Meaning:

- These place the active arena region inside `final_display_canvas_px`.
- Overlay consumers should use `arena_origin_in_canvas_x_px` and
  `arena_origin_in_canvas_y_px` as the authoritative local-to-global embedding.

### citrus-arena-origin-writer

source: citrus @ 48ad93e4d2c84782d0d084a6e3f1352c7c5e3162  
path: src/logging/session_logger.cpp (lines 5677-5706)  
url: https://github.com/JohnsonLabJanelia/citrus/blob/48ad93e4d2c84782d0d084a6e3f1352c7c5e3162/src/logging/session_logger.cpp#L5677-L5706
curator note: The writer computes arena_origin_in_canvas as center minus half size, exactly the formula in the contract above.

```cpp
        float arena_region_center_x_px = static_cast<float>(filtered_config.GetArenaCenterXInCanvasPx());
        float arena_region_center_y_px = static_cast<float>(filtered_config.GetArenaCenterYInCanvasPx());
        float arena_region_width_px = static_cast<float>(filtered_config.GetArenaWidthPx());
        float arena_region_height_px = static_cast<float>(filtered_config.GetArenaHeightPx());
        std::string arena_geometry_source = "legacy_sub_arena_fields";

        if (const auto* active_cam = filtered_config.GetActiveCameraCalibration()) {
            arena_region_center_x_px =
                static_cast<float>(filtered_config.GetArenaCenterXInCanvasPx());
            arena_region_center_y_px =
                static_cast<float>(filtered_config.GetArenaCenterYInCanvasPx());
            arena_region_width_px = static_cast<float>(active_cam->arena_width_px);
            arena_region_height_px = static_cast<float>(active_cam->arena_height_px);
            arena_geometry_source = "active_camera_calibration";
        }

        writeStrAttr(arena_geometry_group, "arena_geometry_source", arena_geometry_source);
        writeFloatAttr(arena_geometry_group, "arena_region_center_in_canvas_x_px",
                       arena_region_center_x_px);
        writeFloatAttr(arena_geometry_group, "arena_region_center_in_canvas_y_px",
                       arena_region_center_y_px);
        writeFloatAttr(arena_geometry_group, "arena_region_width_px",
                       arena_region_width_px);
        writeFloatAttr(arena_geometry_group, "arena_region_height_px",
                       arena_region_height_px);
        writeFloatAttr(arena_geometry_group, "arena_origin_in_canvas_x_px",
                       arena_region_center_x_px - (arena_region_width_px / 2.0f));
        writeFloatAttr(arena_geometry_group, "arena_origin_in_canvas_y_px",
                       arena_region_center_y_px - (arena_region_height_px / 2.0f));
        arena_geometry_group.close();
```

### h5-per-camera-homography

source: agent-contracts @ e648029cc8c4318b17e8c1d97bb7a00d0fe8ca39  
path: citrus-crimson/spatial_overlay_contract.md (lines 98-129)  
url: https://github.com/jmdelahanty/agent-contracts/blob/e648029cc8c4318b17e8c1d97bb7a00d0fe8ca39/citrus-crimson/spatial_overlay_contract.md#L98-L129

### Per-camera homography

Per-camera group:

- `/calibration_snapshot/<camera_id>`

Authoritative dataset:

- `homography_matrix` (`3x3`, float64)

Compatibility fallback:

- `homography_matrix_yml`

Required interpretation for both:

- `source_frame="camera_view_px"`
- `dest_frame="final_display_canvas_px"`
- `coordinate_origin="top_left"`
- `axes="x_right_y_down"`
- `image_space="raw"`
- `camera_id=<camera_id>` when present

Meaning:

- The stored homography direction is:

```text
camera_view_px -> final_display_canvas_px
```

- Consumers that need camera overlay coordinates must invert it.

### h5-arena-local-positions

source: agent-contracts @ e648029cc8c4318b17e8c1d97bb7a00d0fe8ca39  
path: citrus-crimson/spatial_overlay_contract.md (lines 49-75)  
url: https://github.com/jmdelahanty/agent-contracts/blob/e648029cc8c4318b17e8c1d97bb7a00d0fe8ca39/citrus-crimson/spatial_overlay_contract.md#L49-L75

### Arena-local tracked positions

Dataset:

- `/tracking_data/chaser_states`

Position fields:

- `chaser_pos_x`
- `chaser_pos_y`
- `target_pos_x`
- `target_pos_y`

Required interpretation:

- These fields are in `arena_relative_canvas_px`.
- They are not camera-space fields.
- They are not full-display-canvas fields.

Dataset attrs consumers should read:

- `coordinate_frame="arena_relative_canvas_px"`
- `coordinate_origin="top_left_of_active_arena"`
- `x_axis_direction="right"`
- `y_axis_direction="down"`
- `position_fields="chaser_pos_x,chaser_pos_y,target_pos_x,target_pos_y"`
- `camera_id` when present

### h5-raw-camera-tracking

source: agent-contracts @ e648029cc8c4318b17e8c1d97bb7a00d0fe8ca39  
path: citrus-crimson/spatial_overlay_contract.md (lines 131-147)  
url: https://github.com/jmdelahanty/agent-contracts/blob/e648029cc8c4318b17e8c1d97bb7a00d0fe8ca39/citrus-crimson/spatial_overlay_contract.md#L131-L147

### Raw camera-space tracking

Dataset:

- `/tracking_data/bounding_boxes`

Fields:

- `x_min`
- `y_min`
- `width`
- `height`

Meaning:

- These are already in `camera_view_px`.
- They do not require homography for camera-space rendering.

## Where Orange writes camera-space geometry (recordings)

### orange-crop-meta-contract

source: agent-contracts @ e648029cc8c4318b17e8c1d97bb7a00d0fe8ca39  
path: orange-consumers/output_artifacts_contract.md (lines 125-142)  
url: https://github.com/jmdelahanty/agent-contracts/blob/e648029cc8c4318b17e8c1d97bb7a00d0fe8ca39/orange-consumers/output_artifacts_contract.md#L125-L142

### Crop Metadata CSV (`Cam<serial>_crop_meta.csv`)

Header (exact):

```text
frame_id,timestamp,timestamp_sys,detection_confidence,crop_x,crop_y,crop_w,crop_h
```

Field semantics:
- `frame_id`: recording-frame counter
- `timestamp`: camera SDK timestamp (`uint64`, source-native unit)
- `timestamp_sys`: realtime nanoseconds
- `detection_confidence`: float
- `crop_x,crop_y,crop_w,crop_h`: source-frame pixel rect

Behavior note:
- blank crop frames may be encoded when detection is missing
- metadata row is appended only when detection exists

### orange-crop-meta-header

source: orange @ b3e8aa60bc8a325ebcc3b5035ec8c3397cea80e4  
path: src/crop_and_encode_worker.cpp (lines 228-228)  
url: https://github.com/jmdelahanty/orange/blob/b3e8aa60bc8a325ebcc3b5035ec8c3397cea80e4/src/crop_and_encode_worker.cpp#L228-L228

```cpp
                *writer_.metadata << "frame_id,timestamp,timestamp_sys,detection_confidence,crop_x,crop_y,crop_w,crop_h\n";
```

### orange-crop-meta-row

source: orange @ b3e8aa60bc8a325ebcc3b5035ec8c3397cea80e4  
path: src/crop_and_encode_worker.cpp (lines 312-318)  
url: https://github.com/jmdelahanty/orange/blob/b3e8aa60bc8a325ebcc3b5035ec8c3397cea80e4/src/crop_and_encode_worker.cpp#L312-L318

```cpp
                // Write metadata to file
                if (writer_.metadata && writer_.metadata->is_open()) {
                    *writer_.metadata << entry->recording_frame_id << ',' << entry->timestamp << ','
                                      << entry->timestamp_sys << ',' << best_detection.prob << ','
                                      << best_detection.rect.x << ',' << best_detection.rect.y << ','
                                      << best_detection.rect.width << ',' << best_detection.rect.height << '\n';
                }
```

## How Palette reads the geometry back

### palette-coordinate-transform-doc

source: palette @ 7ffb8143f54cc54f811e306a1e5be4396ffc1dc3  
path: src/fisheye/shared/coordinate_transform.py (lines 1-12)  
url: https://github.com/jmdelahanty/palette/blob/7ffb8143f54cc54f811e306a1e5be4396ffc1dc3/src/fisheye/shared/coordinate_transform.py#L1-L12

```python
"""Historical calibration lookup plus direction-neutral homography math.

The lookup helpers in this module are legacy compatibility surfaces.  They do
not prove a transform direction, selected camera, or reference extent and must
not authorize a future-normal coordinate publication.  Canonical callers load
a typed directed-transform record and pass its already validated numerical
matrix to :func:`apply_homography_xy`.

The historical ``projector_to_camera_*`` names remain for explicit legacy
inspection callers.  Their names describe the caller's assertion; they are not
coordinate authority.
"""
```

### palette-apply-homography

source: palette @ 7ffb8143f54cc54f811e306a1e5be4396ffc1dc3  
path: src/fisheye/shared/coordinate_transform.py (lines 173-243)  
url: https://github.com/jmdelahanty/palette/blob/7ffb8143f54cc54f811e306a1e5be4396ffc1dc3/src/fisheye/shared/coordinate_transform.py#L173-L243

```python
def apply_homography_xy(
    points_xy: np.ndarray,
    matrix: np.ndarray,
    *,
    denominator_epsilon: float = 1e-12,
) -> np.ndarray:
    """Apply one already direction-validated 3x3 homography to XY points.

    This function deliberately has no source/destination space names.  Those
    semantics belong to the persisted directed-transform authority used by the
    caller.  Malformed inputs and points whose homogeneous denominator is zero
    fail closed instead of being coerced to a plausible finite coordinate.

    Parameters
    ----------
    points_xy : (N, 2) or (2,) float
        XY coordinates in the transform record's declared source space.
    matrix : (3, 3) float
        Homography payload from that exact directed-transform record.
    denominator_epsilon : float
        Strict positive absolute threshold below which homogeneous ``w`` is
        treated as undefined.

    Returns
    -------
    transformed_xy : same shape as input, float64
        XY coordinates in the transform record's declared destination space.
    """
    pts = np.asarray(points_xy, dtype=np.float64)
    single = pts.ndim == 1
    if single:
        if pts.shape != (2,):
            raise ValueError("A single homography point must have shape (2,).")
        pts = pts.reshape(1, 2)
    elif pts.ndim != 2 or pts.shape[1] != 2:
        raise ValueError("Homography points must have shape (N, 2) or (2,).")

    transform = np.asarray(matrix, dtype=np.float64)
    if transform.shape != (3, 3) or not np.isfinite(transform).all():
        raise ValueError("Homography matrix must be one finite 3x3 array.")
    if (
        isinstance(denominator_epsilon, (bool, np.bool_))
        or not np.isscalar(denominator_epsilon)
        or not np.isfinite(float(denominator_epsilon))
        or float(denominator_epsilon) <= 0.0
    ):
        raise ValueError("denominator_epsilon must be one finite positive scalar.")

    if pts.size == 0:
        return np.empty_like(pts, dtype=np.float64)
    if not np.isfinite(pts).all():
        raise ValueError("Homography points must be finite; select valid rows first.")

    # Homogeneous coordinates.
    ones = np.ones((pts.shape[0], 1), dtype=np.float64)
    homogeneous = np.hstack([pts, ones])  # (N, 3)
    transformed = (transform @ homogeneous.T).T  # (N, 3)

    # Normalize by w.
    w = transformed[:, 2:3]
    if not np.isfinite(transformed).all() or np.any(
        np.abs(w) <= float(denominator_epsilon)
    ):
        raise ValueError(
            "Homography maps at least one point to an undefined point at infinity."
        )
    result = transformed[:, :2] / w

    if single:
        return result.ravel()
    return result
```

### palette-arena-origin

source: palette @ 7ffb8143f54cc54f811e306a1e5be4396ffc1dc3  
path: src/fisheye/shared/arena_geometry.py (lines 172-181)  
url: https://github.com/jmdelahanty/palette/blob/7ffb8143f54cc54f811e306a1e5be4396ffc1dc3/src/fisheye/shared/arena_geometry.py#L172-L181

```python
def _arena_origin_px(root: zarr.Group, run_group: zarr.Group) -> tuple[float, float] | None:
    source_path = str(run_group.attrs.get("source_stimulus_path") or "").strip()
    group = _get_group(root, f"{source_path}/calibration/arena_geometry") if source_path else None
    if group is None:
        return None
    x = _optional_float(group.attrs.get("arena_origin_in_canvas_x_px"))
    y = _optional_float(group.attrs.get("arena_origin_in_canvas_y_px"))
    if x is None or y is None:
        return None
    return float(x), float(y)
```

### palette-detection-frame-size

source: palette @ 7ffb8143f54cc54f811e306a1e5be4396ffc1dc3  
path: src/fisheye/shared/arena_geometry.py (lines 150-169)  
url: https://github.com/jmdelahanty/palette/blob/7ffb8143f54cc54f811e306a1e5be4396ffc1dc3/src/fisheye/shared/arena_geometry.py#L150-L169

```python
def detection_frame_size_px(root: zarr.Group) -> tuple[float, float] | None:
    """(width, height) of the frame the detections were produced in."""

    for family in ("detect_runs", "refined_detect_runs"):
        parent = root.get(family)
        if parent is None:
            continue
        for key in parent.keys():
            attrs = parent[key].attrs
            width = _optional_float(attrs.get("source_video_width")) or _optional_float(attrs.get("source_full_width"))
            height = _optional_float(attrs.get("source_video_height")) or _optional_float(attrs.get("source_full_height"))
            if width and height and width > 0 and height > 0:
                return float(width), float(height)
    calibration = _get_group(root, "analysis/calibration")
    if calibration is not None:
        width = _optional_float(calibration.attrs.get("native_width_px"))
        height = _optional_float(calibration.attrs.get("native_height_px"))
        if width and height and width > 0 and height > 0:
            return float(width), float(height)
    return None
```

### bbox-required-arrays

source: agent-contracts @ e648029cc8c4318b17e8c1d97bb7a00d0fe8ca39  
path: palette-crimson/detect_bbox_read.md (lines 58-65)  
url: https://github.com/jmdelahanty/agent-contracts/blob/e648029cc8c4318b17e8c1d97bb7a00d0fe8ca39/palette-crimson/detect_bbox_read.md#L58-L65

## Required Arrays (for any selected detect group)

- `frame_indices` (`int32`, shape `(N,)`)
- `bbox_norm_coords` (`float64` in current runtime, shape `(N, 4)`)

`bbox_norm_coords` ordering is:
- `[cx, cy, w, h]`
- normalized to detector input frame dimensions

### bbox-coordinate-conversion

source: agent-contracts @ e648029cc8c4318b17e8c1d97bb7a00d0fe8ca39  
path: palette-crimson/detect_bbox_read.md (lines 150-161)  
url: https://github.com/jmdelahanty/agent-contracts/blob/e648029cc8c4318b17e8c1d97bb7a00d0fe8ca39/palette-crimson/detect_bbox_read.md#L150-L161

## Coordinate Conversion

Given frame width `W` and height `H`:

- `x1 = (cx - w/2) * W`
- `y1 = (cy - h/2) * H`
- `x2 = (cx + w/2) * W`
- `y2 = (cy + h/2) * H`

Recommended safety:
- clip normalized values to `[0, 1]` before conversion
- then clip pixel bounds to `[0, W-1]` / `[0, H-1]`
