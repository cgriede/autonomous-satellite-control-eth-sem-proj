from dataclasses import dataclass

from .UNIT_REGISTRY import UREG as ureg


@dataclass(frozen=True)
class RenderConstants:
    #general parameters
    figure_size                 : tuple[float, float]
    constrained_layout          : bool
    space_background            : str
    plot_margin                 : object
    zoom_pad_x                  : object
    zoom_pad_y_bottom           : object
    zoom_pad_y_top              : object
    num_stars                   : int
    star_size_min               : float
    star_size_max               : float
    star_alpha_min              : float
    star_alpha_max              : float
    star_color_rgb              : tuple[float, float, float]
    earth_res                   : int
    earth_dark_rgb              : tuple[float, float, float]
    earth_bright_rgb            : tuple[float, float, float]
    # Shared top-down / strip styling (observer-local 500 km bird panel + 1d_sat_view earth code)
    earth_green_rgb             : tuple[float, float, float]
    fov_turquoise_rgba          : tuple[float, float, float, float]
    cloud_grey_rgb              : tuple[float, float, float]
    light_dir                   : tuple[float, float, float]
    earth_outline_color         : str
    earth_outline_linewidth     : float
    earth_outline_alpha         : float
    observer_color              : str
    observer_marker_size        : float
    observer_marker_edge_width  : float
    observer_marker_render_scale: float
    cloud_color                 : str
    cloud_linewidth             : float
    cloud_alpha                 : float
    cloud_growth_max_span_scale : float
    cloud_growth_linewidth_scale: float
    sat_marker_size             : float
    sat_marker_style            : str
    los_color                   : str
    los_linewidth               : float
    los_alpha                   : float
    los_fov_cone_color          : str
    los_fov_cone_alpha          : float
    trail_style                 : str
    trail_linewidth             : float
    trail_alpha                 : float
    cone_color                  : str
    cone_alpha                  : float
    cone_length_render_scale    : float
    cone_half_angle_render_scale: float
    z_arrow_mutation_scale      : float
    z_arrow_linewidth           : float
    z_arrow_color               : str
    z_arrow_alpha               : float
    z_label_text                : str
    z_label_fontsize            : int
    z_label_color               : str
    z_label_weight              : str
    z_label_offset              : object
    info_fontsize               : int
    info_panel_fontsize         : int
    info_panel_fontfamily       : str
    control_panel_height_frac   : float
    info_text_color             : str
    info_bbox_boxstyle          : str
    info_bbox_facecolor         : str
    info_bbox_edgecolor         : str
    info_bbox_alpha             : float
    info_bbox_linewidth         : float
    speed_button_specs          : tuple[tuple[str, float, float], ...]
    speed_button_top            : float
    speed_button_width          : float
    speed_button_height         : float
    speed_button_label_fontsize : int
    suptitle_fontsize           : int
    speed_button_color          : str
    speed_button_hover_color    : str
    speed_button_label_color    : str
    star_rng_seed               : int
    trail_points                : int
    cloud_segment_points        : int
    zorder_stars                : int
    zorder_earth                : int
    zorder_earth_outline        : int
    zorder_los                  : int
    zorder_z_axis               : int
    zorder_z_label              : int
    zorder_observer             : int
    zorder_cloud                : int
    zorder_info                 : int
    # 1D bird-view inset panel (bottom → top: footprint, centerline, observer, hit, clouds)
    zorder_inset_footprint        : int
    zorder_inset_centerline       : int
    zorder_inset_observer         : int
    zorder_inset_hit              : int
    zorder_inset_cloud_glow       : int
    zorder_inset_cloud_core       : int
    inset_footprint_fill_alpha    : float
    inset_footprint_edge_linewidth: float
    # Observer + cloud close-up YZ panel
    zorder_closeup_ground        : int
    zorder_closeup_cone          : int
    zorder_closeup_cloud_glow    : int
    zorder_closeup_cloud_core    : int
    zorder_closeup_hit           : int
    zorder_closeup_observer      : int
    closeup_ground_line_color    : str
    closeup_ground_line_linewidth: float
    export_fps                   : int
    export_dpi                   : int
    export_filename              : str
    animation_interval           : object
    default_speed_multiplier     : float
    default_num_frames           : int
    # Figure layout [left, bottom, width, height] in figure fraction; gutters reduce border collision.
    figure_inset_gutter_frac   : float
    main_axes_rect             : tuple[float, float, float, float]
    telemetry_axes_rect        : tuple[float, float, float, float]
    reward_axes_rect           : tuple[float, float, float, float]
    torque_axes_rect           : tuple[float, float, float, float]
    bird_view_1d_axes_rect     : tuple[float, float, float, float]
    # 1D camera observation strip (per-bin codes from SimulationStateSeries), below bird view.
    sat_view_1d_axes_rect      : tuple[float, float, float, float]
    # 1D secondary camera observation strip (above primary sat view, reuses former fixed-bird slot).
    sat_view_1d_secondary_axes_rect: tuple[float, float, float, float]
    closeup_axes_rect          : tuple[float, float, float, float]
    # Observer-centered ±fixed_bird_view_half_extent_km 1D fixed-bird strip coverage.
    fixed_bird_view_half_extent_km: object
    # Observer-centered ±bird_view_1d_half_extent_km top-down 2D panel (legacy naming kept for compatibility).
    fixed_bird_view_axes_rect  : tuple[float, float, float, float]
    transport_bar_rect         : tuple[float, float, float, float]
    interactive_start_maximized: bool
    closeup_half_window_km     : object
    closeup_cloud_height_scale : float
    # 1D bird-view XY: square window [-half, +half] km each axis (full width = 2 * half).
    bird_view_1d_half_extent_km: object


RENDER = RenderConstants(
    # WINDOW SIZE
    figure_size                  = (12.0, 7.0),

    constrained_layout           = True,
    # MARGINS
    plot_margin                  = 600.0 * ureg.km,
    zoom_pad_x                   = 220.0 * ureg.km,
    zoom_pad_y_bottom            = 90.0 * ureg.km,
    zoom_pad_y_top               = 130.0 * ureg.km,

    num_stars                    = 220,
    space_background             = "black",
    star_size_min                = 0.3,
    star_size_max                = 2.0,
    star_alpha_min               = 0.25,
    star_alpha_max               = 0.95,
    star_color_rgb               = (0.95, 0.98, 1.0),
    star_rng_seed=42,

    earth_res                    = 1000,
    earth_dark_rgb               = (0.02, 0.08, 0.45),
    earth_bright_rgb             = (0.20, 0.55, 1.00),
    earth_green_rgb              = (0.14, 0.52, 0.30),
    fov_turquoise_rgba           = (0.12, 0.72, 0.66, 0.38),
    cloud_grey_rgb               = (0.78, 0.79, 0.81),
    light_dir                    = (-0.6, 0.8, 0.6),
    earth_outline_color          = "royalblue",
    earth_outline_linewidth      = 2.0,
    earth_outline_alpha          = 0.9,

    observer_color               = "red",
    observer_marker_size         = 8.0,
    observer_marker_edge_width   = 3.0,
    observer_marker_render_scale = 1.8,

    cloud_color                  = "white",
    cloud_linewidth              = 3.0,
    cloud_alpha                  = 0.95,
    cloud_growth_max_span_scale  = 1.9,
    cloud_growth_linewidth_scale = 2.0,
    cloud_segment_points=30,

    sat_marker_size              = 10.0,
    sat_marker_style             = "ro",

    los_color                    = "orange",
    los_linewidth                = 2.2,
    los_alpha                    = 0.9,
    los_fov_cone_color           = "#2ecc71",
    los_fov_cone_alpha           = 0.45,

    trail_style                  = "r-",
    trail_linewidth              = 1.6,
    trail_alpha                  = 0.75,
    trail_points=240,

    cone_color                   = "cyan",
    cone_alpha                   = 0.22,
    cone_length_render_scale     = 1.22,
    cone_half_angle_render_scale = 1.7,

    z_arrow_mutation_scale       = 16.0,
    z_arrow_linewidth            = 3.0,
    z_arrow_color                = "yellow",
    z_arrow_alpha                = 0.95,
    z_label_text                 = "z",
    z_label_fontsize             = 15,
    z_label_color                = "yellow",
    z_label_weight               = "bold",
    z_label_offset               = 35.0 * ureg.km,

    control_panel_height_frac    = 0.22,
    
    info_fontsize                = 11,
    info_panel_fontsize          = 10,
    info_panel_fontfamily        = "monospace",
    info_text_color              = "white",
    info_bbox_boxstyle           = "round,pad=0.35",
    info_bbox_facecolor          = "black",
    info_bbox_edgecolor          = "white",
    info_bbox_alpha              = 0.45,
    info_bbox_linewidth          = 0.8,
    
    speed_button_specs           = (
        ("Real-time", 1.0, 0.56),
        ("5x", 5.0, 0.67),
        ("10x", 10.0, 0.76),
        ("30x", 30.0, 0.85),
    ),
    speed_button_top=0.92,
    speed_button_width=0.062,
    speed_button_height=0.034,
    speed_button_label_fontsize=8,

    suptitle_fontsize=13,
    speed_button_color="#1f1f1f",
    speed_button_hover_color="#3a3a3a",
    speed_button_label_color="white",
    
    zorder_stars                   = 0,
    zorder_earth                   = 1,
    zorder_earth_outline           = 2,
    zorder_los                     = 5,
    zorder_z_axis                  = 6,
    zorder_z_label                 = 7,
    zorder_observer                = 8,
    zorder_cloud                   = 9,
    zorder_info                    = 20,
    zorder_inset_footprint         = 2,
    zorder_inset_centerline        = 3,
    zorder_inset_observer          = 4,
    zorder_inset_hit               = 5,
    zorder_inset_cloud_glow        = 6,
    zorder_inset_cloud_core        = 7,
    inset_footprint_fill_alpha     = 0.28,
    inset_footprint_edge_linewidth = 1.8,
    zorder_closeup_ground          = 1,
    zorder_closeup_cone            = 2,
    zorder_closeup_hit             = 3,
    zorder_closeup_cloud_glow      = 4,
    zorder_closeup_cloud_core      = 5,
    zorder_closeup_observer        = 8,

    closeup_ground_line_color     = "#8B4513",
    closeup_ground_line_linewidth = 2.0,

    closeup_half_window_km=380.0 * ureg.km,
    closeup_cloud_height_scale=1.8,

    # Left telemetry | right: main (top) + lower half split (left stacked strips, right enlarged closeup).
    figure_inset_gutter_frac    = 0.012,
    telemetry_axes_rect         = (0.02, 0.270, 0.19, 0.710),
    torque_axes_rect            = (0.02, 0.078, 0.19, 0.085),
    reward_axes_rect            = (0.02, 0.168, 0.19, 0.085),
    main_axes_rect              = (0.222, 0.280, 0.758, 0.70),
    closeup_axes_rect           = (0.606, 0.068, 0.374, 0.192),
    fixed_bird_view_axes_rect   = (0.222, 0.125, 0.374, 0.055),
    transport_bar_rect          = (0.02, 0.02, 0.96, 0.048),
    interactive_start_maximized = True,
    
    # Stacked left column: secondary-cam strip above primary sat observation strip.
    sat_view_1d_axes_rect=(0.222, 0.068, 0.374, 0.055),
    sat_view_1d_secondary_axes_rect=(0.222, 0.125, 0.374, 0.055),
    bird_view_1d_axes_rect=(0.222, 0.125, 0.374, 0.055),
    fixed_bird_view_half_extent_km=500.0 * ureg.km,
    bird_view_1d_half_extent_km=500.0 * ureg.km,

    export_filename = "satellite_orbit_one_pass_30x.mp4",
    export_fps      = 20,
    export_dpi      = 120,
    animation_interval = 30.0 * ureg.ms,
    default_speed_multiplier = 30.0,
    default_num_frames = 2000,
)
