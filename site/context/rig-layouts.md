# Known rig layouts on omnifin0

Question: What do the real canvas files say about where each camera, arena, and experimental area sits, and how does a camera pixel land on the canvas?

Curated context bundle. Each block is a verbatim excerpt from a source repository at the commit named in its header. Contract precedence rules inside the excerpts still apply.

## Who owns rig, canvas, and arena geometry

### canonical-owners

source: agent-contracts @ e648029cc8c4318b17e8c1d97bb7a00d0fe8ca39  
path: pancake-orange-citrus/rig_canvas_inventory_contract.md (lines 27-33)  
url: https://github.com/jmdelahanty/agent-contracts/blob/e648029cc8c4318b17e8c1d97bb7a00d0fe8ca39/pancake-orange-citrus/rig_canvas_inventory_contract.md#L27-L33

## Canonical Owners

| Concern | Canonical location | Stable IDs | Notes |
|---|---|---|---|
| Static machine and camera inventory | `pancakebatter/system_config.yml` | `host_id`, `camera_serial` | Hardware facts that change when the host is rewired, rebuilt, or different hardware is attached. |
| Per-camera runtime capture presets | `~/orange_data/config/local/<preset>/<camera_serial>.json` and `~/orange_data/config/network/...` | `camera_serial` | Startup/runtime camera behavior for Orange. Not a hardware inventory or calibration source of truth. |
| Rig/canvas/arena geometry and calibration | `citrus/targets/rigs/<rig_id>/<canvas_name>/` | `rig_id`, `canvas_name`, `arena_id`, `camera_serial` | Canvas JSON, arena geometry, per-camera calibration, calibration artifacts, and arena-level IPC binding. |

### citrus-rig-config-struct

source: citrus @ 48ad93e4d2c84782d0d084a6e3f1352c7c5e3162  
path: src/core/rig_config.h (lines 33-42)  
url: https://github.com/JohnsonLabJanelia/citrus/blob/48ad93e4d2c84782d0d084a6e3f1352c7c5e3162/src/core/rig_config.h#L33-L42

```cpp
struct RigConfig {
    std::string schema_version = "rig_config_v1";
    std::string rig_id;
    int rig_geometry_revision = 0;
    std::string stimulus_display_output_name;
    int projector_mount_rotation_deg_about_optical_axis = 0;
    std::string projector_mount_notes;
    nlohmann::json display_signal_chain = nlohmann::json::object();
    PhotodiodeMarkerConfig photodiode_marker;
};
```

### omnifin0-rig-config

source: local data snapshot omnifin0-rig, sha256 d53ccc76eca0eaf04fcc6b3e62a6eb42f48bd34f0021df14ac65bb6c15a2da9a  
path: /home/jeremy/citrus/targets/rigs/omnifin0/omnifin0_config.json (lines 1-7)

```json
{
    "schema_version": "rig_config_v1",
    "rig_id": "omnifin0",
    "rig_geometry_revision": 3,
    "stimulus_display_output_name": "DP-3",
    "projector_mount_rotation_deg_about_optical_axis": 180,
    "projector_mount_notes": "Projector body is rotated 180 degrees about its optical axis on this rig.",
```

### citrus-projector-body-frame

source: citrus @ 48ad93e4d2c84782d0d084a6e3f1352c7c5e3162  
path: docs/coordinate_systems.md (lines 198-210)  
url: https://github.com/JohnsonLabJanelia/citrus/blob/48ad93e4d2c84782d0d084a6e3f1352c7c5e3162/docs/coordinate_systems.md#L198-L210

### `projector_body_frame`

The physical coordinate frame attached to the projector chassis.

- Status: `Manual rig metadata`
- Units: degrees about the optical axis
- Current field:
  - `projector_mount_rotation_deg_about_optical_axis`
- Evidence:
  - configured in [`src/core/rig_config.h`](../src/core/rig_config.h)
  - stored in `/rig_snapshot`

This frame is not automatically inferred from homography or `xrandr`.

### citrus-display-output-transform

source: citrus @ 48ad93e4d2c84782d0d084a6e3f1352c7c5e3162  
path: docs/coordinate_systems.md (lines 183-196)  
url: https://github.com/JohnsonLabJanelia/citrus/blob/48ad93e4d2c84782d0d084a6e3f1352c7c5e3162/docs/coordinate_systems.md#L183-L196

### `display_output_transform`

The runtime desktop/session transform for the configured stimulus display output.

- Status: `Code-defined runtime snapshot`
- Source: `xrandr --query`
- Examples:
  - output name such as `DP-3`
  - transform token such as `normal` or `inverted`
- Evidence:
  - parsed from `xrandr` in [`src/core/display_snapshot.cpp`](../src/core/display_snapshot.cpp)
  - stored under `/display_snapshot`

This is not the same thing as physical projector-body orientation.

## What a canvas file contains

### citrus-canvas-size-loader

source: citrus @ 48ad93e4d2c84782d0d084a6e3f1352c7c5e3162  
path: src/core/Canvas.cpp (lines 17-22)  
url: https://github.com/JohnsonLabJanelia/citrus/blob/48ad93e4d2c84782d0d084a6e3f1352c7c5e3162/src/core/Canvas.cpp#L17-L22

```cpp
        m_canvas_name = data.value("canvas_name", "Unnamed Canvas");

        // Load canvas dimensions with backward compatibility
        // Try new field names first, fallback to old names
        m_canvas_width_px = data.value("canvas_width_px", 1920);
        m_canvas_height_px = data.value("canvas_height_px", 1080);
```

### citrus-camera-calibration-struct

source: citrus @ 48ad93e4d2c84782d0d084a6e3f1352c7c5e3162  
path: src/calibration/arena_config.h (lines 110-131)  
url: https://github.com/JohnsonLabJanelia/citrus/blob/48ad93e4d2c84782d0d084a6e3f1352c7c5e3162/src/calibration/arena_config.h#L110-L131

```cpp
struct CameraCalibration {
    std::string camera_id = "DefaultCamera";

    int native_width_px = 0;
    int native_height_px = 0;
    
    // Arena definition for this camera.
    // These fields define the active arena placement within the final display
    // canvas for this camera calibration.
    int arena_center_x_px = 960;     // Was: sub_arena_x_px
    int arena_center_y_px = 540;     // Was: sub_arena_y_px
    int arena_width_px = 1920;       // Was: sub_arena_width_px
    int arena_height_px = 980;       // Was: sub_arena_height_px

    // Calibration image paths
    std::string homography_image_path;
    std::string scale_image_path;

    // Per-camera rig calibration
    float real_world_ref_mm = 10.0f; // Reference size in mm for calibration
    float pixels_per_mm_camera = 0.0f;
    float pixels_per_mm_projector = 0.0f; // Pixels per mm in display/canvas space
```

### citrus-arena-origin-accessors

source: citrus @ 48ad93e4d2c84782d0d084a6e3f1352c7c5e3162  
path: src/calibration/arena_config.h (lines 308-350)  
url: https://github.com/JohnsonLabJanelia/citrus/blob/48ad93e4d2c84782d0d084a6e3f1352c7c5e3162/src/calibration/arena_config.h#L308-L350
curator note: The accessors below are the rule the diagrams use to place each arena: origin = center − size / 2.

```cpp
    int GetArenaCenterXInCanvasPx() const {
        if (const auto* active_cam = GetActiveCameraCalibration()) {
            if (active_cam->arena_width_px > 0 || active_cam->arena_height_px > 0) {
                return active_cam->arena_center_x_px + runtime_arena_translation_x_px;
            }
        }
        return sub_arena_x_px + runtime_arena_translation_x_px;
    }

    int GetArenaCenterYInCanvasPx() const {
        if (const auto* active_cam = GetActiveCameraCalibration()) {
            if (active_cam->arena_width_px > 0 || active_cam->arena_height_px > 0) {
                return active_cam->arena_center_y_px + runtime_arena_translation_y_px;
            }
        }
        return sub_arena_y_px + runtime_arena_translation_y_px;
    }

    int GetArenaWidthPx() const {
        if (const auto* active_cam = GetActiveCameraCalibration()) {
            if (active_cam->arena_width_px > 0) {
                return active_cam->arena_width_px;
            }
        }
        return sub_arena_width_px;
    }

    int GetArenaHeightPx() const {
        if (const auto* active_cam = GetActiveCameraCalibration()) {
            if (active_cam->arena_height_px > 0) {
                return active_cam->arena_height_px;
            }
        }
        return sub_arena_height_px;
    }

    int GetArenaOriginXInCanvasPx() const {
        return GetArenaCenterXInCanvasPx() - (GetArenaWidthPx() / 2);
    }

    int GetArenaOriginYInCanvasPx() const {
        return GetArenaCenterYInCanvasPx() - (GetArenaHeightPx() / 2);
    }
```

### citrus-homography-sidecar-loader

source: citrus @ 48ad93e4d2c84782d0d084a6e3f1352c7c5e3162  
path: src/ui/arena_view_ui.cpp (lines 783-798)  
url: https://github.com/JohnsonLabJanelia/citrus/blob/48ad93e4d2c84782d0d084a6e3f1352c7c5e3162/src/ui/arena_view_ui.cpp#L783-L798

```cpp

        const std::string homography_filename =
            "homography_" + arena.config.config_name + "_" + safe_cam_id + ".yml";
        const std::string full_homography_path = FileUtils::resolve_calibration_artifact_path(
            arena.rig_name,
            canvas_name,
            homography_filename);

        if (!std::filesystem::exists(full_homography_path)) {
            return;
        }

        try {
            cv::FileStorage fs(full_homography_path, cv::FileStorage::READ);
            if (fs.isOpened()) {
                fs["homography_matrix"] >> arena.config.homography_matrix;
```

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

## Canvas casper

### casper-canvas-size

source: local data snapshot omnifin0-casper, sha256 0779e3751af9d4a1dce5554cc488488df72f922c44337f7ba96e4d5449f9efb9  
path: /home/jeremy/citrus/targets/rigs/omnifin0/casper/casper.json (lines 232-234)

```json
    "canvas_height_px": 980,
    "canvas_name": "casper",
    "canvas_width_px": 1920,
```

### casper-arena-1

source: local data snapshot omnifin0-casper, sha256 0779e3751af9d4a1dce5554cc488488df72f922c44337f7ba96e4d5449f9efb9  
path: /home/jeremy/citrus/targets/rigs/omnifin0/casper/casper.json (lines 3-59)
curator note: Arenas 2 to 4 follow the same shape; the diagram reads all four.

```json
        "arena_1": {
            "calculated_z_eff_mm": 8.600000381469727,
            "camera_calibrations": [
                {
                    "arena_center_x_px": 233,
                    "arena_center_y_px": 518,
                    "arena_height_px": 358,
                    "arena_width_px": 358,
                    "camera_id": "2010093",
                    "homography_image_path": "Cam2010093_arena1_homography.png",
                    "native_height_px": 4512,
                    "native_width_px": 4512,
                    "pixels_per_mm_camera": 50.13677978515625,
                    "pixels_per_mm_projector": 4.13323974609375,
                    "real_world_ref_mm": 10.0,
                    "scale_image_path": "Cam2010093_arena1_scale.png",
                    "sub_arena_height_px": 358,
                    "sub_arena_width_px": 358,
                    "sub_arena_x_px": 233,
                    "sub_arena_y_px": 518
                }
            ],
            "config_name": "arena_1",
            "dot_radius_px": 5.0,
            "experimental_area_center_x_px": 179.0,
            "experimental_area_center_y_px": 179.0,
            "experimental_area_corner_radius_mm": 12.097047805786133,
            "experimental_area_corner_radius_px": 50.0,
            "experimental_area_height_mm": 261.2962341308594,
            "experimental_area_height_px": 1080.0,
            "experimental_area_radius_mm": 39.0,
            "experimental_area_radius_px": 161.19635009765625,
            "experimental_area_shape": "CIRCLE",
            "experimental_area_width_mm": 464.5266418457031,
            "experimental_area_width_px": 1920.0,
            "grid_cols": 10,
            "grid_rows": 10,
            "selected_dish_type": 0,
            "selected_dish_type_name": "alpine",
            "sub_arena_height_mm": 86.6148681640625,
            "sub_arena_height_px": 358,
            "sub_arena_width_mm": 86.6148681640625,
            "sub_arena_width_px": 358,
            "sub_arena_x_px": 233,
            "sub_arena_y_px": 518,
            "swimmable_area_center_x_px": 179.0,
            "swimmable_area_center_y_px": 179.0,
            "swimmable_area_corner_radius_mm": 12.097047805786133,
            "swimmable_area_corner_radius_px": 50.0,
            "swimmable_area_height_mm": 261.2962341308594,
            "swimmable_area_height_px": 1080.0,
            "swimmable_area_radius_mm": 39.0,
            "swimmable_area_radius_px": 161.19635009765625,
            "swimmable_area_shape": "CIRCLE",
            "swimmable_area_width_mm": 464.5266418457031,
            "swimmable_area_width_px": 1920.0
        },
```

### casper-h-2010093

source: local data snapshot omnifin0-casper, sha256 fdcc3fc145a4adfdd1e07f19d8e8909c6c7c6d06fc86b1e78556e3c9126cb449  
path: /home/jeremy/citrus/targets/rigs/omnifin0/casper/calibration_artifacts/homography_arena_1_2010093.yml (lines 1-11)

```yaml
%YAML:1.0
---
calibration_timestamp_utc: "2025-09-17T20:18:21Z"
homography_matrix: !!opencv-matrix
   rows: 3
   cols: 3
   dt: d
   data: [ 0.082207453082140877, -0.00066412810328021418,
       47.420417721206299, -8.9454253274016412e-05, 0.083756452591587066,
       329.69881415866479, -1.3409654806698208e-06,
       7.8935385992712704e-07, 1. ]
```

### casper-h-2010094

source: local data snapshot omnifin0-casper, sha256 da86a65a8c18779a6180bfcad0d1fbc5085413abc5ad8cb9a013c535a1b1b7be  
path: /home/jeremy/citrus/targets/rigs/omnifin0/casper/calibration_artifacts/homography_arena_2_2010094.yml (lines 1-11)

```yaml
%YAML:1.0
---
calibration_timestamp_utc: "2025-09-17T20:02:13Z"
homography_matrix: !!opencv-matrix
   rows: 3
   cols: 3
   dt: d
   data: [ 0.081886033441020245, -0.0020771447404461254,
       505.58800694720321, 0.0001926936601442456, 0.081828041416371677,
       328.02427490300983, -9.6997948595970616e-07,
       -2.5839676833045028e-06, 1. ]
```

### casper-h-2010095

source: local data snapshot omnifin0-casper, sha256 78d940e9c3d301c228317af0269b0c4e1c86d9096ded5cf13fcb88731d0df011  
path: /home/jeremy/citrus/targets/rigs/omnifin0/casper/calibration_artifacts/homography_arena_3_2010095.yml (lines 1-11)

```yaml
%YAML:1.0
---
calibration_timestamp_utc: "2025-09-17T19:40:14Z"
homography_matrix: !!opencv-matrix
   rows: 3
   cols: 3
   dt: d
   data: [ 0.082909630001767279, -0.0002622864390851616,
       950.81092323202608, 0.00022825197426609283, 0.083712022286087387,
       329.89189456156413, -6.2063443322505952e-07,
       -5.2083469382779818e-08, 0.99999999999999989 ]
```

### casper-h-2010096

source: local data snapshot omnifin0-casper, sha256 78287f4af01f3df6468823066e3b0691fae813c1c8df0a50ab102c6d1e697d6b  
path: /home/jeremy/citrus/targets/rigs/omnifin0/casper/calibration_artifacts/homography_arena_4_2010096.yml (lines 1-11)

```yaml
%YAML:1.0
---
calibration_timestamp_utc: "2025-08-07T18:13:24Z"
homography_matrix: !!opencv-matrix
   rows: 3
   cols: 3
   dt: d
   data: [ 0.081147981086110682, -0.0020955747136053512,
       1408.219892517151, 4.4540080357911953e-06, 0.08250310332982029,
       317.8566782440501, -1.1406447654227366e-06,
       -1.2853170879874564e-06, 0.99999999999999989 ]
```

## Canvas shadow

### shadow-canvas-size

source: local data snapshot omnifin0-shadow, sha256 aa36e307fe2781cd5e441ec66dc5590295ec962ee675824a313b00a4cb16abfe  
path: /home/jeremy/citrus/targets/rigs/omnifin0/shadow/shadow.json (lines 568-570)

```json
    "canvas_height_px": 1080,
    "canvas_name": "shadow",
    "canvas_width_px": 1920
```

### shadow-arena-1

source: local data snapshot omnifin0-shadow, sha256 aa36e307fe2781cd5e441ec66dc5590295ec962ee675824a313b00a4cb16abfe  
path: /home/jeremy/citrus/targets/rigs/omnifin0/shadow/shadow.json (lines 3-81)

```json
        "arena_1": {
            "active_camera_id": "2010093",
            "recording_context": {
                "schema_id": "citrus.parent_recording_context",
                "schema_version": 2,
                "recording_type": "behavior",
                "behavior_mode": "free",
                "recording_intent": "stimulus_experiment",
                "data_origin": "acquired"
            },
            "arena_region_height_mm": 82.82921600341797,
            "arena_region_width_mm": 82.82921600341797,
            "calculated_z_eff_mm": 14.94233512878418,
            "calibration_pattern_mask_policy": "experimental_area",
            "calibration_pattern_mode": "circular_rings",
            "calibration_ring_chirality_marker_radius_scale": 1.2999999523162842,
            "calibration_ring_count": 4,
            "calibration_ring_dots_inner": 8,
            "calibration_ring_dots_outer": 32,
            "calibration_ring_include_center_dot": true,
            "calibration_ring_inner_radius_px": 40.0,
            "calibration_ring_orientation_marker_angle_deg": 0.0,
            "calibration_ring_orientation_marker_radius_scale": 1.600000023841858,
            "calibration_ring_outer_radius_px": 140.0,
            "calibration_ring_show_chirality_marker": false,
            "calibration_ring_show_orientation_marker": true,
            "calibration_verification_include_center_dot": true,
            "calibration_verification_inner_angle_offset_deg": 45.0,
            "calibration_verification_inner_point_count": 4,
            "calibration_verification_inner_radius_fraction": 0.3799999952316284,
            "calibration_verification_outer_angle_offset_deg": 22.5,
            "calibration_verification_outer_point_count": 8,
            "calibration_verification_outer_radius_fraction": 0.7799999713897705,
            "camera_calibrations": [
                {
                    "arena_center_x_px": 257,
                    "arena_center_y_px": 330,
                    "arena_height_px": 348,
                    "arena_width_px": 348,
                    "camera_id": "2010093",
                    "homography_detector_strategy": "",
                    "homography_fit_inlier_count": 0,
                    "homography_fit_max_reprojection_error_px": 0.0,
                    "homography_fit_method": "",
                    "homography_fit_point_count": 0,
                    "homography_fit_quality_available": false,
                    "homography_fit_rms_reprojection_error_px": 0.0,
                    "homography_image_path": "Cam2010093_arena1_homography.png",
                    "native_height_px": 4512,
                    "native_width_px": 4512,
                    "pixels_per_mm_camera": 52.731327056884766,
                    "pixels_per_mm_projector": 4.201416015625,
                    "real_world_ref_mm": 5.0,
                    "scale_image_path": "/home/jeremy/orange_data/calibrations/sessions/calsess_2026_07_20T16_16_39Z_shadow/artifacts/Cam2010093_arena_1/scale_observations/calgrp_2026_07_20T16_16_38Z_shadow_projected_surface_scale_calibration_projected_surface_g1/observation.json",
                    "scale_models": [
                        {
                            "clicked_points_camera_px": [
                                {
                                    "x": -1.0,
                                    "y": -1.0
                                },
                                {
                                    "x": -1.0,
                                    "y": -1.0
                                }
                            ],
                            "kind": "projective_local_jacobian_at_target_origin",
                            "notes": "Loaded from immutable active projected-surface scale pointer",
                            "pixels_per_mm_camera": 52.731327056884766,
                            "pixels_per_mm_projector": 4.201416015625,
                            "real_world_ref_mm": 5.0,
                            "scale_image_path": "/home/jeremy/orange_data/calibrations/sessions/calsess_2026_07_20T16_16_39Z_shadow/artifacts/Cam2010093_arena_1/scale_observations/calgrp_2026_07_20T16_16_38Z_shadow_projected_surface_scale_calibration_projected_surface_g1/observation.json",
                            "status": "accepted",
                            "target_plane": "projected_surface"
                        }
                    ]
                }
            ],
            "config_name": "arena_1",
```

### shadow-h-2010093

source: local data snapshot omnifin0-shadow, sha256 64389adc05b8d5edd1c94a82a2643294b5d79c34fb2897abfd94dcb8f87828c8  
path: /home/jeremy/citrus/targets/rigs/omnifin0/shadow/calibration_artifacts/homography_arena_1_2010093.yml (lines 1-28)

```yaml
%YAML:1.0
---
artifact_schema_id: "citrus.calibration.homography_candidate"
artifact_schema_version: 1
candidate_id: homography_arena_1_2010093_holder_operational_calgrp_2026_09_14T21_14_03Z_shadow_homography_grid_projected_surface_g4
candidate_set_id: homography_set_holder_operational_calgrp_2026_09_14T21_14_03Z_shadow_homography_grid_projected_surface_g4
homography_direction: camera_native_px_to_final_display_canvas_px
target_plane: projected_surface
pattern_mode: circular_rings
orientation_validation_status: passed
orientation_normalization_transform: ""
configuration_fingerprint: "sha256:acdf5e997e9534a5aacf1a5918dcdd5c39b82083723a1c97e9f8c797d7b590dd"
source_capture_checksum: "fnv1a64:59a824924a20c5b8"
fit_quality_schema: "citrus.homography_fit_quality.v2"
point_count: 81
inlier_count: 81
rms_reprojection_error_px: 0.15760693143058349
max_reprojection_error_px: 0.55931097552812092
holdout_rms_reprojection_error_px: 0.26288468800299092
holdout_max_reprojection_error_px: 0.8113809254153006
homography_matrix: !!opencv-matrix
   rows: 3
   cols: 3
   dt: d
   data: [ 0.079491864932271408, -0.00030229498036896943,
       77.133992465809925, -0.0002757502180579138, -0.080094974712873052,
       510.53996688386758, -5.5941326802569046e-07,
       -1.5604039838712963e-07, 1. ]
```

### shadow-h-2010094

source: local data snapshot omnifin0-shadow, sha256 9ecc6fd22e9daaf6c24c162109a7cfba7f796534b3daa8e3c6c0591b9bb5e163  
path: /home/jeremy/citrus/targets/rigs/omnifin0/shadow/calibration_artifacts/homography_arena_2_2010094.yml (lines 1-28)

```yaml
%YAML:1.0
---
artifact_schema_id: "citrus.calibration.homography_candidate"
artifact_schema_version: 1
candidate_id: homography_arena_2_2010094_holder_operational_calgrp_2026_09_14T21_14_03Z_shadow_homography_grid_projected_surface_g4
candidate_set_id: homography_set_holder_operational_calgrp_2026_09_14T21_14_03Z_shadow_homography_grid_projected_surface_g4
homography_direction: camera_native_px_to_final_display_canvas_px
target_plane: projected_surface
pattern_mode: circular_rings
orientation_validation_status: passed
orientation_normalization_transform: ""
configuration_fingerprint: "sha256:d72e9f92a659d5a82300fd5f459901f57b66bb32c3f10e9c0dff90868635445f"
source_capture_checksum: "fnv1a64:0ba1ed8aac5fa422"
fit_quality_schema: "citrus.homography_fit_quality.v2"
point_count: 81
inlier_count: 81
rms_reprojection_error_px: 0.10770023906032811
max_reprojection_error_px: 0.19808838955150102
holdout_rms_reprojection_error_px: 0.097546878939541851
holdout_max_reprojection_error_px: 0.21875675225054581
homography_matrix: !!opencv-matrix
   rows: 3
   cols: 3
   dt: d
   data: [ 0.079749699673856339, -0.00016696639198430951,
       534.10987430089563, 9.7135909416466784e-07, -0.080221795348528954,
       515.65136969047126, -2.4060414289172904e-08,
       -2.0730202530434087e-07, 1. ]
```

### shadow-h-2010095

source: local data snapshot omnifin0-shadow, sha256 5a34ec42fa0f3ff4757ba087f38cdeead495b575ee7eb95ab96a190635fc9fef  
path: /home/jeremy/citrus/targets/rigs/omnifin0/shadow/calibration_artifacts/homography_arena_3_2010095.yml (lines 1-28)

```yaml
%YAML:1.0
---
artifact_schema_id: "citrus.calibration.homography_candidate"
artifact_schema_version: 1
candidate_id: homography_arena_3_2010095_holder_operational_calgrp_2026_09_14T21_14_03Z_shadow_homography_grid_projected_surface_g4
candidate_set_id: homography_set_holder_operational_calgrp_2026_09_14T21_14_03Z_shadow_homography_grid_projected_surface_g4
homography_direction: camera_native_px_to_final_display_canvas_px
target_plane: projected_surface
pattern_mode: circular_rings
orientation_validation_status: passed
orientation_normalization_transform: ""
configuration_fingerprint: "sha256:eb537d7ccafe30c060a47dbb873a30f5e163df957bc999549bbd65e8764efdb9"
source_capture_checksum: "fnv1a64:4e6556a50bcffc03"
fit_quality_schema: "citrus.homography_fit_quality.v2"
point_count: 81
inlier_count: 81
rms_reprojection_error_px: 0.10510913896910379
max_reprojection_error_px: 0.18766646396702313
holdout_rms_reprojection_error_px: 0.089778931591189701
holdout_max_reprojection_error_px: 0.19379527155274262
homography_matrix: !!opencv-matrix
   rows: 3
   cols: 3
   dt: d
   data: [ 0.079776648055879154, -0.00035172875892869603,
       992.89076791707544, -0.0001315853717091643, -0.080414900406512849,
       508.13242693376446, -8.1480313487639167e-08,
       -4.1264831497215999e-07, 1. ]
```

### shadow-h-2010096

source: local data snapshot omnifin0-shadow, sha256 50f5ad5c3b517e2683cdabf3b252e460ff33e234137e45c5b6397a77919233f7  
path: /home/jeremy/citrus/targets/rigs/omnifin0/shadow/calibration_artifacts/homography_arena_4_2010096.yml (lines 1-28)

```yaml
%YAML:1.0
---
artifact_schema_id: "citrus.calibration.homography_candidate"
artifact_schema_version: 1
candidate_id: homography_arena_4_2010096_holder_operational_calgrp_2026_09_14T21_14_03Z_shadow_homography_grid_projected_surface_g4
candidate_set_id: homography_set_holder_operational_calgrp_2026_09_14T21_14_03Z_shadow_homography_grid_projected_surface_g4
homography_direction: camera_native_px_to_final_display_canvas_px
target_plane: projected_surface
pattern_mode: circular_rings
orientation_validation_status: passed
orientation_normalization_transform: ""
configuration_fingerprint: "sha256:dbf5a368656f5693824d54474d0d44c757d57dbe35e18fd0ed7604f1f021c19a"
source_capture_checksum: "fnv1a64:83be12be94f9afe9"
fit_quality_schema: "citrus.homography_fit_quality.v2"
point_count: 81
inlier_count: 81
rms_reprojection_error_px: 0.10346316182563985
max_reprojection_error_px: 0.18949248947106911
holdout_rms_reprojection_error_px: 0.10203517579609787
holdout_max_reprojection_error_px: 0.18449438895003067
homography_matrix: !!opencv-matrix
   rows: 3
   cols: 3
   dt: d
   data: [ 0.079789382117857285, -0.00050997723109478654,
       1471.539452875699, -0.00038137965481465632, -0.080710715149257969,
       501.65602085052916, -2.8975815431741569e-07,
       -4.6056798093723558e-07, 1. ]
```

## Canvas shadow as Citrus recorded it (session H5, 2026-08-25)

### h5-arena-embedding-contract

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

### h5-per-camera-homography-contract

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

### citrus-h5-direction-writer

source: citrus @ 48ad93e4d2c84782d0d084a6e3f1352c7c5e3162  
path: src/logging/session_logger.cpp (lines 5801-5831)  
url: https://github.com/JohnsonLabJanelia/citrus/blob/48ad93e4d2c84782d0d084a6e3f1352c7c5e3162/src/logging/session_logger.cpp#L5801-L5831

```cpp

            const auto direction_mapping =
                BuildDirectionFrameMapping(cam_calib, arena_config.homography_matrix);
            if (direction_mapping.has_value()) {
                writeFloatAttr(camGroup, "direction_mapping_ref_camera_x",
                               direction_mapping->reference_camera_point_px.x);
                writeFloatAttr(camGroup, "direction_mapping_ref_camera_y",
                               direction_mapping->reference_camera_point_px.y);
                writeFloatAttr(camGroup, "direction_mapping_ref_canvas_x",
                               direction_mapping->reference_canvas_point_px.x);
                writeFloatAttr(camGroup, "direction_mapping_ref_canvas_y",
                               direction_mapping->reference_canvas_point_px.y);
                writeFloatAttr(camGroup, "camera_view_right_in_canvas_x",
                               direction_mapping->camera_view_right_in_canvas.x);
                writeFloatAttr(camGroup, "camera_view_right_in_canvas_y",
                               direction_mapping->camera_view_right_in_canvas.y);
                writeFloatAttr(camGroup, "camera_view_right_in_canvas_angle_deg",
                               direction_mapping->camera_view_right_angle_deg);
                writeFloatAttr(camGroup, "camera_view_down_in_canvas_x",
                               direction_mapping->camera_view_down_in_canvas.x);
                writeFloatAttr(camGroup, "camera_view_down_in_canvas_y",
                               direction_mapping->camera_view_down_in_canvas.y);
                writeFloatAttr(camGroup, "camera_view_down_in_canvas_angle_deg",
                               direction_mapping->camera_view_down_angle_deg);
                writeFloatAttr(camGroup, "direction_mapping_scale_x",
                               direction_mapping->canvas_px_per_camera_px_x);
                writeFloatAttr(camGroup, "direction_mapping_scale_y",
                               direction_mapping->canvas_px_per_camera_px_y);
                writeStrAttr(camGroup, "direction_mapping_handedness",
                             direction_mapping->is_mirrored ? "mirrored" : "preserved");
                writeStrAttr(camGroup, "direction_mapping_canvas_angle_convention",
```

### citrus-h5-homography-writer

source: citrus @ 48ad93e4d2c84782d0d084a6e3f1352c7c5e3162  
path: src/logging/session_logger.cpp (lines 5835-5849)  
url: https://github.com/JohnsonLabJanelia/citrus/blob/48ad93e4d2c84782d0d084a6e3f1352c7c5e3162/src/logging/session_logger.cpp#L5835-L5849

```cpp
            if (!arena_config.homography_matrix.empty() &&
                arena_config.homography_matrix.rows == 3 &&
                arena_config.homography_matrix.cols == 3) {
                cv::Mat homography_matrix_f64;
                arena_config.homography_matrix.convertTo(homography_matrix_f64, CV_64F);
                hsize_t matrix_dims[2] = {3, 3};
                H5::DataSpace matrix_dspace(2, matrix_dims);
                H5::DataSet matrix_dset = camGroup.createDataSet(
                    "homography_matrix",
                    H5::PredType::NATIVE_DOUBLE,
                    matrix_dspace);
                matrix_dset.write(homography_matrix_f64.ptr<double>(), H5::PredType::NATIVE_DOUBLE);
                WriteHomographyDatasetAttrs(matrix_dset, cam_calib.camera_id);
                WriteHomographyProvenanceAttrs(matrix_dset,
                                               homography_provenance,
```

### shadow-session-root-attrs

source: local data snapshot omnifin0-shadow-session-2026-08-25, sha256 0209571b3f107f2d5bc46ac0e2a86a3f8b28882bdacf6b664d7bcad1f0ab16c3  
path: /home/jeremy/orange_data/exp/unsorted/2026_08_25_23_12_06/citrus/citsess_45fac0f71f098cf00f44065893c773b7847ab224edba618cb2a1c9744731065e_redbat.calibration_snapshot.json (lines 7-52)
curator note: Session identity and the canvas size Citrus actually rendered (stimulus_output_width/height). The other three sessions share canvas_name and rig_id.

```json
  "root_attrs": {
    "active_ipc_source": "SHAMAN",
    "arena_id": "arena_1",
    "artifact_schema_id": "behavior_v1",
    "behavior_mode": "free",
    "canvas_name": "shadow",
    "display_mode_height_reported_px": 1080,
    "display_mode_observation_source": "xrandr_selected_output_verbose_current_mode",
    "display_mode_pixel_clock_reported_mhz": 296.7,
    "display_mode_width_reported_px": 1920,
    "display_refresh_rate_reported_hz": 119.88,
    "display_refresh_rate_source": "xrandr_selected_output_current_mode",
    "display_submission_rate_source": "citrus_frame_rate_limiter_nominal",
    "display_submission_rate_target_hz": 120.0,
    "display_swap_interval": 0,
    "expected_bounding_boxes_rows": 173563,
    "expected_chaser_states_rows": 180232,
    "expected_display_frame_submission_rows": 215977,
    "expected_events_rows": 152,
    "expected_frame_metadata_rows": 216232,
    "expected_independent_motion_grid_states_rows": 0,
    "expected_moving_grating_states_rows": 0,
    "expected_runtime_trials_rows": 4,
    "experimental_chamber": "palm1",
    "hostname": "pancake0.hhmi.org",
    "ipc_first_nonzero_frame_id": 1008,
    "ipc_first_nonzero_frame_timestamp_ns_session": 1388876200,
    "ipc_reader_init_status": "initialized",
    "ipc_source_name": "/shm_cam_2010093",
    "loaded_protocol_filepath": "redbat.json",
    "protocol_name_from_definition": "redbat",
    "recording_subtype": "free",
    "recording_type": "behavior",
    "rig_id": "omnifin0",
    "session_output_dir": "/home/jeremy/orange_data/exp/unsorted/2026_08_25_23_12_06/citrus",
    "session_start_iso8601_utc": "2026-08-26T03-12-19Z",
    "session_start_ns_epoch": 1787713939114183878,
    "session_status": "COMPLETE",
    "session_uuid": "citsess_45fac0f71f098cf00f44065893c773b7847ab224edba618cb2a1c9744731065e",
    "software_version": "",
    "stimulus_frame_rate_nominal_hz": 120.0,
    "stimulus_output_height": 1080,
    "stimulus_output_width": 1920,
    "tracking_bounding_boxes_rows": 173563,
    "tracking_chaser_states_rows": 180232
  },
```

### shadow-session-arena-1-geometry

source: local data snapshot omnifin0-shadow-session-2026-08-25, sha256 0209571b3f107f2d5bc46ac0e2a86a3f8b28882bdacf6b664d7bcad1f0ab16c3  
path: /home/jeremy/orange_data/exp/unsorted/2026_08_25_23_12_06/citrus/citsess_45fac0f71f098cf00f44065893c773b7847ab224edba618cb2a1c9744731065e_redbat.calibration_snapshot.json (lines 231-254)

```json
        "attrs": {
          "arena_geometry_source": "active_camera_calibration",
          "arena_origin_in_canvas_x_px": 90.0,
          "arena_origin_in_canvas_y_px": 164.0,
          "arena_region_center_in_canvas_x_px": 264.0,
          "arena_region_center_in_canvas_y_px": 338.0,
          "arena_region_height_px": 348.0,
          "arena_region_width_px": 348.0,
          "coordinate_frame": "arena_relative_canvas_px",
          "coordinate_origin": "top_left_of_active_arena",
          "experimental_area_center_x_px": 173.0,
          "experimental_area_center_y_px": 173.0,
          "experimental_area_corner_radius_mm": 11.99231243133545,
          "experimental_area_corner_radius_px": 50.1770133972168,
          "experimental_area_height_mm": 80.0,
          "experimental_area_height_px": 334.72784423828125,
          "experimental_area_radius_mm": 40.0,
          "experimental_area_radius_px": 167.36392211914062,
          "experimental_area_shape": "CIRCLE",
          "experimental_area_width_mm": 80.0,
          "experimental_area_width_px": 334.72784423828125,
          "x_axis_direction": "right",
          "y_axis_direction": "down"
        }
```

### shadow-session-arena-1-direction

source: local data snapshot omnifin0-shadow-session-2026-08-25, sha256 0209571b3f107f2d5bc46ac0e2a86a3f8b28882bdacf6b664d7bcad1f0ab16c3  
path: /home/jeremy/orange_data/exp/unsorted/2026_08_25_23_12_06/citrus/citsess_45fac0f71f098cf00f44065893c773b7847ab224edba618cb2a1c9744731065e_redbat.calibration_snapshot.json (lines 61-79)

```json
        "attrs": {
          "camera_view_down_in_canvas_angle_deg": -90.35123443603516,
          "camera_view_down_in_canvas_x": -0.006130152847617865,
          "camera_view_down_in_canvas_y": -0.999981164932251,
          "camera_view_right_in_canvas_angle_deg": -0.35421979427337646,
          "camera_view_right_in_canvas_x": 0.9999808073043823,
          "camera_view_right_in_canvas_y": -0.0061822617426514626,
          "direction_mapping_canvas_angle_convention": "0=right,90=down",
          "direction_mapping_handedness": "mirrored",
          "direction_mapping_ref_camera_x": 2229.577392578125,
          "direction_mapping_ref_camera_y": 2245.14892578125,
          "direction_mapping_ref_canvas_x": 259.0,
          "direction_mapping_ref_canvas_y": 332.0,
          "direction_mapping_scale_x": 0.07898100465536118,
          "direction_mapping_scale_y": 0.07965237647294998,
          "pixels_per_mm_camera": 52.75507354736328,
          "pixels_per_mm_projector": 4.184098243713379,
          "real_world_ref_mm": 5.0
        },
```

### shadow-session-arena-1-homography

source: local data snapshot omnifin0-shadow-session-2026-08-25, sha256 0209571b3f107f2d5bc46ac0e2a86a3f8b28882bdacf6b664d7bcad1f0ab16c3  
path: /home/jeremy/orange_data/exp/unsorted/2026_08_25_23_12_06/citrus/citsess_45fac0f71f098cf00f44065893c773b7847ab224edba618cb2a1c9744731065e_redbat.calibration_snapshot.json (lines 132-184)

```json
          "homography_matrix": {
            "attrs": {
              "arena_config_name": "arena_1",
              "axes": "x_right_y_down",
              "camera_id": "2010093",
              "canvas_name": "shadow",
              "coordinate_origin": "top_left",
              "dest_frame": "final_display_canvas_px",
              "homography_artifact_checksum_algorithm": "fnv1a64",
              "homography_artifact_checksum_fnv1a64": "af351bdb2310837d",
              "homography_artifact_exists": "true",
              "homography_artifact_filename": "homography_arena_1_2010093.yml",
              "homography_artifact_mtime_unix_ns": 1786323758019198158,
              "homography_artifact_path": "/home/jeremy/citrus/targets/rigs/omnifin0/shadow/calibration_artifacts/homography_arena_1_2010093.yml",
              "homography_artifact_size_bytes": 1295,
              "homography_fit_inlier_count": 81,
              "homography_fit_max_reprojection_error_px": 0.2432277899465086,
              "homography_fit_point_count": 81,
              "homography_fit_quality_available": "true",
              "homography_fit_quality_schema": "citrus.homography_fit_quality.v1",
              "homography_fit_rms_reprojection_error_px": 0.12110689401871437,
              "homography_payload_source": "runtime_arena_config.homography_matrix",
              "homography_provenance_schema": "citrus.homography_provenance.v1",
              "image_space": "raw",
              "rig_id": "omnifin0",
              "runtime_matrix_checksum_algorithm": "sha256",
              "runtime_matrix_checksum_serialization": "json_row_major_float64_v1",
              "runtime_matrix_checksum_sha256": "sha256:cfdbbbf45b75226f42cdadeb77831a9cd5fa7b7d31834237f41e18d85c729112",
              "source_frame": "camera_view_px"
            },
            "dtype": "float64",
            "shape": [
              3,
              3
            ],
            "value": [
              [
                0.07874250445494245,
                -0.0005856985662148073,
                84.33456319725997
              ],
              [
                -0.0006186948810984491,
                -0.07962950658326917,
                511.62381365417457
              ],
              [
                -3.960271677654378e-07,
                -3.2541264852901244e-07,
                1.0
              ]
            ]
          },
```

### shadow-session-arena-2-geometry

source: local data snapshot omnifin0-shadow-session-2026-08-25, sha256 75f3378881b9502c1cb7f9fe4b7c13bbd2acdc934d5894cad028d0feae29c925  
path: /home/jeremy/orange_data/exp/unsorted/2026_08_25_23_12_06/citrus/citsess_dfa15a4b01f45041f60d8bc571389db77000fa9c8d030d300b76f4636f89d021_redbat.calibration_snapshot.json (lines 231-254)

```json
        "attrs": {
          "arena_geometry_source": "active_camera_calibration",
          "arena_origin_in_canvas_x_px": 551.0,
          "arena_origin_in_canvas_y_px": 159.0,
          "arena_region_center_in_canvas_x_px": 726.0,
          "arena_region_center_in_canvas_y_px": 334.0,
          "arena_region_height_px": 350.0,
          "arena_region_width_px": 350.0,
          "coordinate_frame": "arena_relative_canvas_px",
          "coordinate_origin": "top_left_of_active_arena",
          "experimental_area_center_x_px": 174.0,
          "experimental_area_center_y_px": 174.0,
          "experimental_area_corner_radius_mm": 11.97751522064209,
          "experimental_area_corner_radius_px": 50.25548553466797,
          "experimental_area_height_mm": 80.0,
          "experimental_area_height_px": 335.66552734375,
          "experimental_area_radius_mm": 40.0,
          "experimental_area_radius_px": 167.832763671875,
          "experimental_area_shape": "CIRCLE",
          "experimental_area_width_mm": 80.0,
          "experimental_area_width_px": 335.66552734375,
          "x_axis_direction": "right",
          "y_axis_direction": "down"
        }
```

### shadow-session-arena-2-direction

source: local data snapshot omnifin0-shadow-session-2026-08-25, sha256 75f3378881b9502c1cb7f9fe4b7c13bbd2acdc934d5894cad028d0feae29c925  
path: /home/jeremy/orange_data/exp/unsorted/2026_08_25_23_12_06/citrus/citsess_dfa15a4b01f45041f60d8bc571389db77000fa9c8d030d300b76f4636f89d021_redbat.calibration_snapshot.json (lines 61-79)

```json
        "attrs": {
          "camera_view_down_in_canvas_angle_deg": -90.131103515625,
          "camera_view_down_in_canvas_x": -0.002288323361426592,
          "camera_view_down_in_canvas_y": -0.9999973773956299,
          "camera_view_right_in_canvas_angle_deg": -0.2858169376850128,
          "camera_view_right_in_canvas_x": 0.9999875426292419,
          "camera_view_right_in_canvas_y": -0.004988425876945257,
          "direction_mapping_canvas_angle_convention": "0=right,90=down",
          "direction_mapping_handedness": "mirrored",
          "direction_mapping_ref_camera_x": 2247.4580078125,
          "direction_mapping_ref_camera_y": 2261.30322265625,
          "direction_mapping_ref_canvas_x": 721.0,
          "direction_mapping_ref_canvas_y": 337.0,
          "direction_mapping_scale_x": 0.07952979952096939,
          "direction_mapping_scale_y": 0.08001729846000671,
          "pixels_per_mm_camera": 52.58562088012695,
          "pixels_per_mm_projector": 4.195818901062012,
          "real_world_ref_mm": 5.0
        },
```

### shadow-session-arena-2-homography

source: local data snapshot omnifin0-shadow-session-2026-08-25, sha256 75f3378881b9502c1cb7f9fe4b7c13bbd2acdc934d5894cad028d0feae29c925  
path: /home/jeremy/orange_data/exp/unsorted/2026_08_25_23_12_06/citrus/citsess_dfa15a4b01f45041f60d8bc571389db77000fa9c8d030d300b76f4636f89d021_redbat.calibration_snapshot.json (lines 132-184)

```json
          "homography_matrix": {
            "attrs": {
              "arena_config_name": "arena_2",
              "axes": "x_right_y_down",
              "camera_id": "2010094",
              "canvas_name": "shadow",
              "coordinate_origin": "top_left",
              "dest_frame": "final_display_canvas_px",
              "homography_artifact_checksum_algorithm": "fnv1a64",
              "homography_artifact_checksum_fnv1a64": "2106f36756e5fbd8",
              "homography_artifact_exists": "true",
              "homography_artifact_filename": "homography_arena_2_2010094.yml",
              "homography_artifact_mtime_unix_ns": 1786323758055198160,
              "homography_artifact_path": "/home/jeremy/citrus/targets/rigs/omnifin0/shadow/calibration_artifacts/homography_arena_2_2010094.yml",
              "homography_artifact_size_bytes": 1295,
              "homography_fit_inlier_count": 81,
              "homography_fit_max_reprojection_error_px": 0.2901524344662282,
              "homography_fit_point_count": 81,
              "homography_fit_quality_available": "true",
              "homography_fit_quality_schema": "citrus.homography_fit_quality.v1",
              "homography_fit_rms_reprojection_error_px": 0.1147780064519357,
              "homography_payload_source": "runtime_arena_config.homography_matrix",
              "homography_provenance_schema": "citrus.homography_provenance.v1",
              "image_space": "raw",
              "rig_id": "omnifin0",
              "runtime_matrix_checksum_algorithm": "sha256",
              "runtime_matrix_checksum_serialization": "json_row_major_float64_v1",
              "runtime_matrix_checksum_sha256": "sha256:ffdb4429ed3fe0c3a534960ff15e2a92ea8b57e7cf2fda316f306404867264b2",
              "source_frame": "camera_view_px"
            },
            "dtype": "float64",
            "shape": [
              3,
              3
            ],
            "value": [
              [
                0.07906860271482405,
                -0.00047793029202255766,
                542.9984779325481
              ],
              [
                -0.0005470654070846848,
                -0.07998867525696146,
                518.4636429271127
              ],
              [
                -4.5995586459547647e-07,
                -3.886052250950324e-07,
                1.0
              ]
            ]
          },
```

### shadow-session-arena-3-geometry

source: local data snapshot omnifin0-shadow-session-2026-08-25, sha256 36b589f184cb16aafa8f9a708e6b41fb5e45e2577210a74bc2c6ef462551af0c  
path: /home/jeremy/orange_data/exp/unsorted/2026_08_25_23_12_06/citrus/citsess_8b4b3225db87e46aed185e1358300c839157a13d2d87c6a2ee1d2eb88668221b_redbat.calibration_snapshot.json (lines 231-254)

```json
        "attrs": {
          "arena_geometry_source": "active_camera_calibration",
          "arena_origin_in_canvas_x_px": 1012.0,
          "arena_origin_in_canvas_y_px": 156.0,
          "arena_region_center_in_canvas_x_px": 1188.0,
          "arena_region_center_in_canvas_y_px": 332.0,
          "arena_region_height_px": 352.0,
          "arena_region_width_px": 352.0,
          "coordinate_frame": "arena_relative_canvas_px",
          "coordinate_origin": "top_left_of_active_arena",
          "experimental_area_center_x_px": 173.0,
          "experimental_area_center_y_px": 173.0,
          "experimental_area_corner_radius_mm": 11.802724838256836,
          "experimental_area_corner_radius_px": 49.67599868774414,
          "experimental_area_height_mm": 80.0,
          "experimental_area_height_px": 336.70867919921875,
          "experimental_area_radius_mm": 40.0,
          "experimental_area_radius_px": 168.35433959960938,
          "experimental_area_shape": "CIRCLE",
          "experimental_area_width_mm": 80.0,
          "experimental_area_width_px": 336.70867919921875,
          "x_axis_direction": "right",
          "y_axis_direction": "down"
        }
```

### shadow-session-arena-3-direction

source: local data snapshot omnifin0-shadow-session-2026-08-25, sha256 36b589f184cb16aafa8f9a708e6b41fb5e45e2577210a74bc2c6ef462551af0c  
path: /home/jeremy/orange_data/exp/unsorted/2026_08_25_23_12_06/citrus/citsess_8b4b3225db87e46aed185e1358300c839157a13d2d87c6a2ee1d2eb88668221b_redbat.calibration_snapshot.json (lines 61-79)

```json
        "attrs": {
          "camera_view_down_in_canvas_angle_deg": -90.0,
          "camera_view_down_in_canvas_x": 0.0,
          "camera_view_down_in_canvas_y": -1.0,
          "camera_view_right_in_canvas_angle_deg": -0.37119460105895996,
          "camera_view_right_in_canvas_x": 0.9999789595603943,
          "camera_view_right_in_canvas_y": -0.006478522438555956,
          "direction_mapping_canvas_angle_convention": "0=right,90=down",
          "direction_mapping_handedness": "mirrored",
          "direction_mapping_ref_camera_x": 2235.46533203125,
          "direction_mapping_ref_camera_y": 2230.24267578125,
          "direction_mapping_ref_canvas_x": 1178.0,
          "direction_mapping_ref_canvas_y": 335.0,
          "direction_mapping_scale_x": 0.0800798088312149,
          "direction_mapping_scale_y": 0.080413818359375,
          "pixels_per_mm_camera": 52.43170166015625,
          "pixels_per_mm_projector": 4.208858489990234,
          "real_world_ref_mm": 5.0
        },
```

### shadow-session-arena-3-homography

source: local data snapshot omnifin0-shadow-session-2026-08-25, sha256 36b589f184cb16aafa8f9a708e6b41fb5e45e2577210a74bc2c6ef462551af0c  
path: /home/jeremy/orange_data/exp/unsorted/2026_08_25_23_12_06/citrus/citsess_8b4b3225db87e46aed185e1358300c839157a13d2d87c6a2ee1d2eb88668221b_redbat.calibration_snapshot.json (lines 132-184)

```json
          "homography_matrix": {
            "attrs": {
              "arena_config_name": "arena_3",
              "axes": "x_right_y_down",
              "camera_id": "2010095",
              "canvas_name": "shadow",
              "coordinate_origin": "top_left",
              "dest_frame": "final_display_canvas_px",
              "homography_artifact_checksum_algorithm": "fnv1a64",
              "homography_artifact_checksum_fnv1a64": "e033634141030c5d",
              "homography_artifact_exists": "true",
              "homography_artifact_filename": "homography_arena_3_2010095.yml",
              "homography_artifact_mtime_unix_ns": 1786323758071198160,
              "homography_artifact_path": "/home/jeremy/citrus/targets/rigs/omnifin0/shadow/calibration_artifacts/homography_arena_3_2010095.yml",
              "homography_artifact_size_bytes": 1296,
              "homography_fit_inlier_count": 81,
              "homography_fit_max_reprojection_error_px": 0.2105458119777816,
              "homography_fit_point_count": 81,
              "homography_fit_quality_available": "true",
              "homography_fit_quality_schema": "citrus.homography_fit_quality.v1",
              "homography_fit_rms_reprojection_error_px": 0.11368694460021456,
              "homography_payload_source": "runtime_arena_config.homography_matrix",
              "homography_provenance_schema": "citrus.homography_provenance.v1",
              "image_space": "raw",
              "rig_id": "omnifin0",
              "runtime_matrix_checksum_algorithm": "sha256",
              "runtime_matrix_checksum_serialization": "json_row_major_float64_v1",
              "runtime_matrix_checksum_sha256": "sha256:309025e02d4179828304bb2deb0f18c63cdf71c6839c2048cb7c458298bc187a",
              "source_frame": "camera_view_px"
            },
            "dtype": "float64",
            "shape": [
              3,
              3
            ],
            "value": [
              [
                0.0790050268403753,
                -0.0006674120271375568,
                999.5425773946706
              ],
              [
                -0.0007720151510413161,
                -0.0803815604980243,
                515.0483915388191
              ],
              [
                -7.216399587149153e-07,
                -5.452778809885962e-07,
                1.0
              ]
            ]
          },
```

### shadow-session-arena-4-geometry

source: local data snapshot omnifin0-shadow-session-2026-08-25, sha256 816ed7c105e0fb776daa839fb233bcc9992d1280fa5b802164743a07e298185a  
path: /home/jeremy/orange_data/exp/unsorted/2026_08_25_23_12_06/citrus/citsess_59e779ca13bc9eaa4c11195d0b79ffe6fb3653e854a0d3bc93f95cd166b55b81_redbat.calibration_snapshot.json (lines 231-254)

```json
        "attrs": {
          "arena_geometry_source": "active_camera_calibration",
          "arena_origin_in_canvas_x_px": 1480.0,
          "arena_origin_in_canvas_y_px": 152.0,
          "arena_region_center_in_canvas_x_px": 1657.0,
          "arena_region_center_in_canvas_y_px": 329.0,
          "arena_region_height_px": 354.0,
          "arena_region_width_px": 354.0,
          "coordinate_frame": "arena_relative_canvas_px",
          "coordinate_origin": "top_left_of_active_arena",
          "experimental_area_center_x_px": 175.0,
          "experimental_area_center_y_px": 175.0,
          "experimental_area_corner_radius_mm": 11.901163101196289,
          "experimental_area_corner_radius_px": 50.36293411254883,
          "experimental_area_height_mm": 80.0,
          "experimental_area_height_px": 338.541259765625,
          "experimental_area_radius_mm": 40.0,
          "experimental_area_radius_px": 169.2706298828125,
          "experimental_area_shape": "CIRCLE",
          "experimental_area_width_mm": 80.0,
          "experimental_area_width_px": 338.541259765625,
          "x_axis_direction": "right",
          "y_axis_direction": "down"
        }
```

### shadow-session-arena-4-direction

source: local data snapshot omnifin0-shadow-session-2026-08-25, sha256 816ed7c105e0fb776daa839fb233bcc9992d1280fa5b802164743a07e298185a  
path: /home/jeremy/orange_data/exp/unsorted/2026_08_25_23_12_06/citrus/citsess_59e779ca13bc9eaa4c11195d0b79ffe6fb3653e854a0d3bc93f95cd166b55b81_redbat.calibration_snapshot.json (lines 61-79)

```json
        "attrs": {
          "camera_view_down_in_canvas_angle_deg": -89.91357421875,
          "camera_view_down_in_canvas_x": 0.0015082939062267542,
          "camera_view_down_in_canvas_y": -0.9999988675117493,
          "camera_view_right_in_canvas_angle_deg": -0.47601136565208435,
          "camera_view_right_in_canvas_x": 0.9999655485153198,
          "camera_view_right_in_canvas_y": -0.008307870477437973,
          "direction_mapping_canvas_angle_convention": "0=right,90=down",
          "direction_mapping_handedness": "mirrored",
          "direction_mapping_ref_camera_x": 2251.96240234375,
          "direction_mapping_ref_camera_y": 2247.328369140625,
          "direction_mapping_ref_canvas_x": 1654.0,
          "direction_mapping_ref_canvas_y": 322.0,
          "direction_mapping_scale_x": 0.08081333339214325,
          "direction_mapping_scale_y": 0.08093270659446716,
          "pixels_per_mm_camera": 52.31583786010742,
          "pixels_per_mm_projector": 4.2317657470703125,
          "real_world_ref_mm": 5.0
        },
```

### shadow-session-arena-4-homography

source: local data snapshot omnifin0-shadow-session-2026-08-25, sha256 816ed7c105e0fb776daa839fb233bcc9992d1280fa5b802164743a07e298185a  
path: /home/jeremy/orange_data/exp/unsorted/2026_08_25_23_12_06/citrus/citsess_59e779ca13bc9eaa4c11195d0b79ffe6fb3653e854a0d3bc93f95cd166b55b81_redbat.calibration_snapshot.json (lines 132-184)

```json
          "homography_matrix": {
            "attrs": {
              "arena_config_name": "arena_4",
              "axes": "x_right_y_down",
              "camera_id": "2010096",
              "canvas_name": "shadow",
              "coordinate_origin": "top_left",
              "dest_frame": "final_display_canvas_px",
              "homography_artifact_checksum_algorithm": "fnv1a64",
              "homography_artifact_checksum_fnv1a64": "f82c955660f61ee8",
              "homography_artifact_exists": "true",
              "homography_artifact_filename": "homography_arena_4_2010096.yml",
              "homography_artifact_mtime_unix_ns": 1786323758083198159,
              "homography_artifact_path": "/home/jeremy/citrus/targets/rigs/omnifin0/shadow/calibration_artifacts/homography_arena_4_2010096.yml",
              "homography_artifact_size_bytes": 1296,
              "homography_fit_inlier_count": 81,
              "homography_fit_max_reprojection_error_px": 0.26431522471725416,
              "homography_fit_point_count": 81,
              "homography_fit_quality_available": "true",
              "homography_fit_quality_schema": "citrus.homography_fit_quality.v1",
              "homography_fit_rms_reprojection_error_px": 0.12366124769422783,
              "homography_payload_source": "runtime_arena_config.homography_matrix",
              "homography_provenance_schema": "citrus.homography_provenance.v1",
              "image_space": "raw",
              "rig_id": "omnifin0",
              "runtime_matrix_checksum_algorithm": "sha256",
              "runtime_matrix_checksum_serialization": "json_row_major_float64_v1",
              "runtime_matrix_checksum_sha256": "sha256:8e4e0b0739547dc6901e0e6f5fe6757f65716e146f2644e660fb72de78e40637",
              "source_frame": "camera_view_px"
            },
            "dtype": "float64",
            "shape": [
              3,
              3
            ],
            "value": [
              [
                0.07941404014474829,
                -0.00035544630587712374,
                1472.08739971268
              ],
              [
                -0.0009073157076933863,
                -0.08084017897724494,
                504.9634861168206
              ],
              [
                -7.445148038954546e-07,
                -2.9615715082307834e-07,
                1.0
              ]
            ]
          },
```

## Canvas blindfish

### blindfish-canvas-size

source: local data snapshot omnifin0-blindfish, sha256 1229038c835f09f053b2441b3e7e1338dea36e29abfb7827f7151cb9ac4fa1b4  
path: /home/jeremy/citrus/targets/rigs/omnifin0/blindfish/blindfish.json (lines 536-538)

```json
    "canvas_height_px": 1080,
    "canvas_name": "blindfish",
    "canvas_width_px": 1920,
```

### blindfish-arena-1

source: local data snapshot omnifin0-blindfish, sha256 1229038c835f09f053b2441b3e7e1338dea36e29abfb7827f7151cb9ac4fa1b4  
path: /home/jeremy/citrus/targets/rigs/omnifin0/blindfish/blindfish.json (lines 3-73)

```json
        "arena_1": {
            "active_camera_id": "2010093",
            "arena_region_height_mm": 83.17204284667969,
            "arena_region_width_mm": 83.17204284667969,
            "calculated_z_eff_mm": 16.731597900390625,
            "calibration_pattern_mask_policy": "full_arena_unmasked",
            "calibration_pattern_mode": "rectangular_grid",
            "calibration_ring_chirality_marker_radius_scale": 1.2999999523162842,
            "calibration_ring_count": 4,
            "calibration_ring_dots_inner": 8,
            "calibration_ring_dots_outer": 32,
            "calibration_ring_include_center_dot": true,
            "calibration_ring_inner_radius_px": 40.0,
            "calibration_ring_orientation_marker_angle_deg": 0.0,
            "calibration_ring_orientation_marker_radius_scale": 1.600000023841858,
            "calibration_ring_outer_radius_px": 140.0,
            "calibration_ring_show_chirality_marker": false,
            "calibration_ring_show_orientation_marker": true,
            "calibration_verification_include_center_dot": true,
            "calibration_verification_inner_angle_offset_deg": 45.0,
            "calibration_verification_inner_point_count": 4,
            "calibration_verification_inner_radius_fraction": 0.3799999952316284,
            "calibration_verification_outer_angle_offset_deg": 22.5,
            "calibration_verification_outer_point_count": 8,
            "calibration_verification_outer_radius_fraction": 0.7799999713897705,
            "camera_calibrations": [
                {
                    "arena_center_x_px": 259,
                    "arena_center_y_px": 332,
                    "arena_height_px": 348,
                    "arena_width_px": 348,
                    "camera_id": "2010093",
                    "homography_detector_strategy": "",
                    "homography_fit_inlier_count": 0,
                    "homography_fit_max_reprojection_error_px": 0.0,
                    "homography_fit_method": "",
                    "homography_fit_point_count": 0,
                    "homography_fit_quality_available": false,
                    "homography_fit_rms_reprojection_error_px": 0.0,
                    "homography_image_path": "Cam2010093_arena1_homography.png",
                    "native_height_px": 4512,
                    "native_width_px": 4512,
                    "pixels_per_mm_camera": 52.75507354736328,
                    "pixels_per_mm_projector": 4.184098243713379,
                    "real_world_ref_mm": 5.0,
                    "scale_image_path": "Cam2010093_arena1_scale.png",
                    "scale_models": [
                        {
                            "clicked_points_camera_px": [
                                {
                                    "x": -1.0,
                                    "y": -1.0
                                },
                                {
                                    "x": -1.0,
                                    "y": -1.0
                                }
                            ],
                            "kind": "projective_local_jacobian_at_target_origin",
                            "notes": "Loaded from immutable active projected-surface scale pointer",
                            "pixels_per_mm_camera": 52.75507354736328,
                            "pixels_per_mm_projector": 4.184098243713379,
                            "real_world_ref_mm": 5.0,
                            "scale_image_path": "/home/jeremy/orange_data/calibrations/sessions/calsess_2026_08_10T01_53_54Z_shadow/artifacts/Cam2010093_arena_1/scale_observations/calgrp_2026_08_10T01_53_53Z_shadow_projected_surface_scale_calibration_projected_surface_g1/observation.json",
                            "status": "accepted",
                            "target_plane": "projected_surface"
                        }
                    ]
                }
            ],
            "config_name": "arena_1",
```

### blindfish-h-2010093

source: local data snapshot omnifin0-blindfish, sha256 0b1c0bccd1369faa4efa60fdd728350b9858be81d8f145198b47e91b1206a2ae  
path: /home/jeremy/citrus/targets/rigs/omnifin0/blindfish/calibration_artifacts/homography_arena_1_2010093.yml (lines 1-11)

```yaml
%YAML:1.0
---
calibration_timestamp_utc: "2026-04-20T13:53:09Z"
homography_matrix: !!opencv-matrix
   rows: 3
   cols: 3
   dt: d
   data: [ 0.081190495253022743, -5.8629227576639497e-05,
       78.016343251990492, -6.615283571743281e-05, 0.08208723961407946,
       145.61594704306023, -1.4179512772275522e-06,
       8.1150695283403544e-07, 1. ]
```

### blindfish-h-2010094

source: local data snapshot omnifin0-blindfish, sha256 e00bab2d53140a105d56c6ca332234533e2124d3878ad5fc71d98be3890f6f14  
path: /home/jeremy/citrus/targets/rigs/omnifin0/blindfish/calibration_artifacts/homography_arena_2_2010094.yml (lines 1-11)

```yaml
%YAML:1.0
---
calibration_timestamp_utc: "2026-04-20T13:41:24Z"
homography_matrix: !!opencv-matrix
   rows: 3
   cols: 3
   dt: d
   data: [ 0.080939913970578259, -0.00058851917693874514,
       546.50709930182188, 7.4047431215621808e-05, 0.081426285214485819,
       150.95990421765154, -5.597081221294883e-07,
       -6.291259115207835e-07, 1. ]
```

### blindfish-h-2010095

source: local data snapshot omnifin0-blindfish, sha256 cfaf7a25871a448a62637bfdf748afb9c0151093a4292a4ab2e86956a3c37562  
path: /home/jeremy/citrus/targets/rigs/omnifin0/blindfish/calibration_artifacts/homography_arena_3_2010095.yml (lines 1-11)

```yaml
%YAML:1.0
---
calibration_timestamp_utc: "2026-04-20T13:31:54Z"
homography_matrix: !!opencv-matrix
   rows: 3
   cols: 3
   dt: d
   data: [ 0.081830026421205487, 0.00027137249386961022,
       1000.2767635708324, 0.00030792815696202162, 0.08237628931575354,
       144.9714247530712, -3.0271908617221341e-07,
       3.5077112303254264e-07, 1. ]
```

### blindfish-h-2010096

source: local data snapshot omnifin0-blindfish, sha256 5965502a4c77b94e7d096a444fb679a6322d1c608682aff0222920437dc51f1a  
path: /home/jeremy/citrus/targets/rigs/omnifin0/blindfish/calibration_artifacts/homography_arena_4_2010096.yml (lines 1-11)

```yaml
%YAML:1.0
---
calibration_timestamp_utc: "2026-04-20T13:22:29Z"
homography_matrix: !!opencv-matrix
   rows: 3
   cols: 3
   dt: d
   data: [ 0.082441037531989614, 0.0023408737657269587,
       1453.1024204077116, 0.00043275717954872499, 0.083561105698659363,
       136.43324401838655, -7.7015124750487782e-07,
       1.696994773321424e-06, 1. ]
```
