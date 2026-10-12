# Replay of a tracked fish through the three frames

Question: Press play and watch one real bounding box from Orange travel from camera pixels through the Citrus homography into the arena, next to the target point Citrus itself logged.

Curated context bundle. Each block is a verbatim excerpt from a source repository at the commit named in its header. Contract precedence rules inside the excerpts still apply.

## The two datasets and the mapping between them

### contract-raw-camera-tracking

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

### contract-arena-local-positions

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

### contract-mapping-rule

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

## The target rule Citrus applies to a box

### citrus-target-rule-note

source: citrus @ 48ad93e4d2c84782d0d084a6e3f1352c7c5e3162  
path: src/core/tracking_target_view.h (lines 72-80)  
url: https://github.com/JohnsonLabJanelia/citrus/blob/48ad93e4d2c84782d0d084a6e3f1352c7c5e3162/src/core/tracking_target_view.h#L72-L80

```cpp
// CV_64F, 3x3). False for a missing or degenerate homography.
bool ProjectCameraPoint(const cv::Mat& camera_to_canvas, float x, float y, cv::Point2f& out);

// The box centre in arena-local pixels: the centre of the integer bounding
// rectangle of the four projected corners, less the arena origin. This is the
// Chaser's established target rule, kept bit-identical. cv::boundingRect is
// inclusive, so the centre sits up to half a pixel past the geometric centre.
std::optional<cv::Point2f> ProjectBoxToArenaLocal(const LoggedBoundingBox& box,
                                                  const cv::Mat& camera_to_canvas,
```

### citrus-project-box-rect

source: citrus @ 48ad93e4d2c84782d0d084a6e3f1352c7c5e3162  
path: src/core/tracking_target_view.cpp (lines 26-40)  
url: https://github.com/JohnsonLabJanelia/citrus/blob/48ad93e4d2c84782d0d084a6e3f1352c7c5e3162/src/core/tracking_target_view.cpp#L26-L40

```cpp
// Integer bounding rectangle of the projected box corners, in canvas pixels.
std::optional<cv::Rect2f> ProjectBoxRect(const LoggedBoundingBox& box,
                                         const cv::Mat& camera_to_canvas) {
    if (camera_to_canvas.empty()) return std::nullopt;
    std::array<cv::Point2f, 4> corners;
    if (!ProjectCameraPoint(camera_to_canvas, box.x_min, box.y_min, corners[0]) ||
        !ProjectCameraPoint(camera_to_canvas, box.x_min + box.width, box.y_min, corners[1]) ||
        !ProjectCameraPoint(camera_to_canvas, box.x_min + box.width, box.y_min + box.height,
                            corners[2]) ||
        !ProjectCameraPoint(camera_to_canvas, box.x_min, box.y_min + box.height, corners[3])) {
        return std::nullopt;
    }
    const cv::Mat corners_mat(static_cast<int>(corners.size()), 1, CV_32FC2, corners.data());
    return cv::Rect2f(cv::boundingRect(corners_mat));
}
```

### citrus-project-camera-point

source: citrus @ 48ad93e4d2c84782d0d084a6e3f1352c7c5e3162  
path: src/core/tracking_target_view.cpp (lines 50-62)  
url: https://github.com/JohnsonLabJanelia/citrus/blob/48ad93e4d2c84782d0d084a6e3f1352c7c5e3162/src/core/tracking_target_view.cpp#L50-L62

```cpp
bool ProjectCameraPoint(const cv::Mat& camera_to_canvas, float x, float y, cv::Point2f& out) {
    double h[3][3];
    for (int row = 0; row < 3; ++row)
        for (int col = 0; col < 3; ++col)
            if (!ReadHomographyValue(camera_to_canvas, row, col, h[row][col])) return false;
    const double xd = static_cast<double>(x);
    const double yd = static_cast<double>(y);
    const double w = h[2][0] * xd + h[2][1] * yd + h[2][2];
    if (std::abs(w) <= 1e-12) return false;
    out.x = static_cast<float>((h[0][0] * xd + h[0][1] * yd + h[0][2]) / w);
    out.y = static_cast<float>((h[1][0] * xd + h[1][1] * yd + h[1][2]) / w);
    return true;
}
```

### citrus-target-point-method-attr

source: citrus @ 48ad93e4d2c84782d0d084a6e3f1352c7c5e3162  
path: src/logging/session_logger.cpp (lines 8244-8247)  
url: https://github.com/JohnsonLabJanelia/citrus/blob/48ad93e4d2c84782d0d084a6e3f1352c7c5e3162/src/logging/session_logger.cpp#L8244-L8247

```cpp
        WriteStringAttr(chaser_dataset_, "target_mapping_semantics",
                        "active_projection_surface_G_c");
        WriteStringAttr(chaser_dataset_, "target_point_method",
                        "transformed_bbox_corners_bounding_rect_center");
```

## The session's calibration (same values as the rig-layouts page)

### replay-calibration-arena-geometry

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

### replay-calibration-homography

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

## The tracking rows being replayed

### replay-window-selection

source: local data snapshot omnifin0-shadow-session-2026-08-25-tracking, sha256 4d0addf432ccd3dd428dc3a0fcc922e90d2e72697decbc7e6bcaa7b76c8b02bd  
path: /home/jeremy/orange_data/exp/unsorted/2026_08_25_23_12_06/citrus/citsess_45fac0f71f098cf00f44065893c773b7847ab224edba618cb2a1c9744731065e_redbat.tracking_window.json (lines 16-62)
curator note: The rows themselves are in the same file (link in the header); the player below embeds all of them.

```json
  "selection": {
    "chaser_dataset": "/tracking_data/chaser_states",
    "chaser_rows": [
      88400,
      89700
    ],
    "stride": 2,
    "chaser_fields": [
      "stimulus_frame_num",
      "timestamp_ns_session",
      "chaser_index",
      "is_chasing",
      "chaser_pos_x",
      "chaser_pos_y",
      "target_pos_x",
      "target_pos_y",
      "target_clamped_pos_x",
      "target_clamped_pos_y",
      "target_source_frame_id",
      "target_source_camera_id",
      "target_source_box_index_in_payload",
      "target_age_ms",
      "target_freshness_state",
      "target_area_state",
      "chaser_radius_px",
      "target_radius_px",
      "distance_to_target_px"
    ],
    "bbox_dataset": "/tracking_data/bounding_boxes",
    "bbox_rule": "payload_frame_id within [min, max] of the selected chaser rows' target_source_frame_id",
    "bbox_payload_frame_id_span": [
      104741,
      105824
    ],
    "bbox_fields": [
      "payload_frame_id",
      "payload_timestamp_ns_epoch",
      "payload_camera_id",
      "box_index_in_payload",
      "x_min",
      "y_min",
      "width",
      "height",
      "class_id",
      "confidence"
    ]
  },
```

### replay-chaser-states-attrs

source: local data snapshot omnifin0-shadow-session-2026-08-25-tracking, sha256 4d0addf432ccd3dd428dc3a0fcc922e90d2e72697decbc7e6bcaa7b76c8b02bd  
path: /home/jeremy/orange_data/exp/unsorted/2026_08_25_23_12_06/citrus/citsess_45fac0f71f098cf00f44065893c773b7847ab224edba618cb2a1c9744731065e_redbat.tracking_window.json (lines 65-87)

```json
      "attrs": {
        "angle_zero_direction": "right",
        "behavior_retreat_distance_fields": "behavior_retreat_requested_distance_mm,behavior_retreat_actual_distance_mm",
        "behavior_retreat_distance_units": "mm",
        "behavior_retreat_position_fields": "behavior_retreat_endpoint_x_mm,behavior_retreat_endpoint_y_mm,behavior_retreat_target_x_mm,behavior_retreat_target_y_mm",
        "behavior_retreat_position_units": "projected_surface_mm_derived_from_active_pixels_per_mm",
        "camera_id": "2010093",
        "coordinate_frame": "arena_relative_canvas_px",
        "coordinate_origin": "top_left_of_active_arena",
        "physical_frame_status": "arena_relative_canvas_px_not_accepted_world_mm",
        "position_fields": "chaser_pos_x,chaser_pos_y,target_pos_x,target_pos_y,target_clamped_pos_x,target_clamped_pos_y",
        "positive_rotation_direction": "clockwise",
        "runtime_behavior_plane_id": "projected_surface",
        "runtime_correction_active": "false",
        "runtime_render_plane_id": "projected_surface",
        "scale_source": "active_projected_surface_pixels_per_mm",
        "schema_version": 4,
        "target_mapping_semantics": "active_projection_surface_G_c",
        "target_point_method": "transformed_bbox_corners_bounding_rect_center",
        "units": "px",
        "x_axis_direction": "right",
        "y_axis_direction": "down"
      },
```

### replay-bbox-fields

source: local data snapshot omnifin0-shadow-session-2026-08-25-tracking, sha256 4d0addf432ccd3dd428dc3a0fcc922e90d2e72697decbc7e6bcaa7b76c8b02bd  
path: /home/jeremy/orange_data/exp/unsorted/2026_08_25_23_12_06/citrus/citsess_45fac0f71f098cf00f44065893c773b7847ab224edba618cb2a1c9744731065e_redbat.tracking_window.json (lines 13802-13815)

```json
      "dtype_fields": [
        "payload_timestamp_ns_epoch",
        "payload_timestamp_ns_monotonic",
        "received_timestamp_ns_epoch",
        "payload_frame_id",
        "payload_camera_id",
        "box_index_in_payload",
        "x_min",
        "y_min",
        "width",
        "height",
        "class_id",
        "confidence"
      ],
```

## Replay
