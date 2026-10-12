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
