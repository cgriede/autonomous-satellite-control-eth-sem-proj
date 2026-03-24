from dataclasses import dataclass

from .UNIT_REGISTRY import UREG as ureg


@dataclass(frozen=True)
class RenderConstants:
    figure_size: tuple[float, float]
    constrained_layout: bool
    space_background: str
    plot_margin: object
    zoom_pad_x: object
    zoom_pad_y_bottom: object
    zoom_pad_y_top: object
    num_stars: int
    star_size_min: float
    star_size_max: float
    star_alpha_min: float
    star_alpha_max: float
    star_color_rgb: tuple[float, float, float]
    earth_res: int
    earth_dark_rgb: tuple[float, float, float]
    earth_bright_rgb: tuple[float, float, float]
    light_dir: tuple[float, float, float]
    earth_outline_color: str
    earth_outline_linewidth: float
    earth_outline_alpha: float
    observer_color: str
    observer_marker_size: float
    observer_marker_edge_width: float
    cloud_color: str
    cloud_linewidth: float
    cloud_alpha: float
    sat_marker_size: float
    sat_marker_style: str
    los_color: str
    los_linewidth: float
    los_alpha: float
    los_fov_cone_color: str
    los_fov_cone_alpha: float
    trail_style: str
    trail_linewidth: float
    trail_alpha: float
    cone_color: str
    cone_alpha: float
    z_arrow_mutation_scale: float
    z_arrow_linewidth: float
    z_arrow_color: str
    z_arrow_alpha: float
    z_label_text: str
    z_label_fontsize: int
    z_label_color: str
    z_label_weight: str
    z_label_offset: object
    info_fontsize: int
    info_text_color: str
    info_bbox_boxstyle: str
    info_bbox_facecolor: str
    info_bbox_edgecolor: str
    info_bbox_alpha: float
    info_bbox_linewidth: float
    speed_button_specs: tuple[tuple[str, float, float], ...]
    speed_button_top: float
    speed_button_width: float
    speed_button_height: float
    speed_button_color: str
    speed_button_hover_color: str
    speed_button_label_color: str
    star_rng_seed: int
    trail_points: int
    cloud_segment_points: int
    zorder_stars: int
    zorder_earth: int
    zorder_earth_outline: int
    zorder_los: int
    zorder_z_axis: int
    zorder_z_label: int
    zorder_observer: int
    zorder_cloud: int
    zorder_info: int
    export_fps: int
    export_dpi: int
    export_filename: str


RENDER = RenderConstants(
    figure_size=(12.0, 5.0),
    constrained_layout=True,
    space_background="black",
    plot_margin=600.0 * ureg.km,
    zoom_pad_x=220.0 * ureg.km,
    zoom_pad_y_bottom=90.0 * ureg.km,
    zoom_pad_y_top=130.0 * ureg.km,
    num_stars=220,
    star_size_min=0.3,
    star_size_max=2.0,
    star_alpha_min=0.25,
    star_alpha_max=0.95,
    star_color_rgb=(0.95, 0.98, 1.0),
    earth_res=1000,
    earth_dark_rgb=(0.02, 0.08, 0.45),
    earth_bright_rgb=(0.20, 0.55, 1.00),
    light_dir=(-0.6, 0.8, 0.6),
    earth_outline_color="royalblue",
    earth_outline_linewidth=2.0,
    earth_outline_alpha=0.9,
    observer_color="red",
    observer_marker_size=8.0,
    observer_marker_edge_width=3.0,
    cloud_color="white",
    cloud_linewidth=3.0,
    cloud_alpha=0.95,
    sat_marker_size=10.0,
    sat_marker_style="ro",
    los_color="orange",
    los_linewidth=2.2,
    los_alpha=0.9,
    los_fov_cone_color="#2ecc71",
    los_fov_cone_alpha=0.45,
    trail_style="r-",
    trail_linewidth=1.6,
    trail_alpha=0.75,
    cone_color="cyan",
    cone_alpha=0.22,
    z_arrow_mutation_scale=16.0,
    z_arrow_linewidth=3.0,
    z_arrow_color="yellow",
    z_arrow_alpha=0.95,
    z_label_text="z",
    z_label_fontsize=15,
    z_label_color="yellow",
    z_label_weight="bold",
    z_label_offset=35.0 * ureg.km,
    info_fontsize=11,
    info_text_color="white",
    info_bbox_boxstyle="round,pad=0.35",
    info_bbox_facecolor="black",
    info_bbox_edgecolor="white",
    info_bbox_alpha=0.45,
    info_bbox_linewidth=0.8,
    speed_button_specs=(
        ("Real-time", 1.0, 0.56),
        ("5x", 5.0, 0.67),
        ("10x", 10.0, 0.76),
        ("30x", 30.0, 0.85),
    ),
    speed_button_top=0.92,
    speed_button_width=0.09,
    speed_button_height=0.055,
    speed_button_color="#1f1f1f",
    speed_button_hover_color="#3a3a3a",
    speed_button_label_color="white",
    star_rng_seed=42,
    trail_points=240,
    cloud_segment_points=30,
    zorder_stars=0,
    zorder_earth=1,
    zorder_earth_outline=2,
    zorder_los=5,
    zorder_z_axis=6,
    zorder_z_label=7,
    zorder_observer=8,
    zorder_cloud=9,
    zorder_info=20,
    export_fps=30,
    export_dpi=120,
    export_filename="satellite_orbit_one_pass_30x.mp4",
)
