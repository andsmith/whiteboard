# Fixed params for app, dimensions are pixels or relative to w/h of window.
import cv2


COLORS_RGB = {'black': (0, 0, 0),
              'white': (255, 255, 255),
              'off_white': (0xff, 0xfa, 0xf1),
              'red': (255, 0, 0),
              'green': (0, 255, 0),
              'neon green': (57, 255, 20),
              'blue': (0, 0, 255),
              'yellow': (255, 255, 0),
              'cyan': (0, 255, 255),
              'magenta': (255, 0, 255),
              'gray': (128, 128, 128),
              'dark_gray': (64, 64, 64),
              'dark_dark_gray': (32, 32, 32),
              'light_gray': (192, 192, 192),
              'orange': (255, 165, 0),
              'purple': (128, 0, 128),
              'brown': (165, 42, 42),
              'pink': (255, 192, 203),
              'olive': (128, 128, 0),
              'teal': (0, 128, 128),
              'navy': (0, 0, 128)}

COLORS_BGR = {k: tuple(reversed(v)) for k, v in COLORS_RGB.items()}

DEFAULT_ICON_MARGIN_FRAC = 0.35

UI_LINE_THICKNESS = 2
INIT_OPTIONS = {'show_grid': True,
                'snap_to_grid': False,
                'color': 'black',
                'thickness': 1,
                'font_size': 12,}

# Board is the main display window
BOARD_LAYOUT = {'win_size': (1000, 500),
                'win_name': 'Whiteboard Board',
                'bkg_color': 'off_white',  # shared w/control win
                'obj_color': 'dark_dark_gray',  # also shared
                'init_zoom': 1.0,
                'init_origin': (-20, -17),
                'init_zoom_window_extent': {'x': (0.05, 0.5),  # upper left corner
                                            'y': (0.05, 0.5)},
                'zoom_bar': {'loc': {'x': [.85, .95],
                                     'y': [.05, .475],
                                     'orientation': 'vertical'},
                             'label': "Zoom %.1f"}, }

GRID_SPACING = [10, 100]  # in board units  (TEMPORARY)

# Control is the user input window, with the tools and the precise drawing window
CONTROL_LAYOUT = {
    'win_name': 'Whiteboard Controls',
    'win_size': (700, 450),
    'zoom_window_margin': 0.1,  # fraction of window size, set zoom to whatever fits the current zoom_window_extent.

    # toolbox, strip in the middle of the right side of the window
    'tool_box': {'options':  # this defines the layout of the toolbox, each string
                 # should match something in tool_manager._TOOLS and icon artists.
                 [['pencil', 'line'], ['rectangle', 'circle'], ['select', 'pan']],
                 'loc': {'x': [.85, .95],
                         'y': [.3, .6]},
                 'line_widths': [1, 2, 3, 5, 8, 13]},

    # color box, strip below toolbox, 10% width, 5% separation
    'color_box': {'loc': {'x': [.05, .15],
                          'y': [.3, .6]},
                  'options': [['black', 'gray'],
                              ['red', 'orange'],
                              ['blue', 'yellow'],
                              ['purple', 'green']]},

    # command box (undo/redo, clear, grid, connect, etc.) is at the bottom left, next to the zoom slider
    'command_box': {'loc': {'x': [.15, .55],
                            'y': [.85, .95]},
                    # Should match something in icon_artists
                    'options': [['undo', 'redo', 'clear', 'thickness','text_size','snap_to_grid', 'grid'],],
                    'thickness_range': [1, 20]},


    # zoom slider-bar, horizontal, accros bottom.
    'zoom_slider': {'loc': {'x': [.55, .85],
                            'y': [.85, .95],
                            'orientation': 'horizontal'},
                    'label': 'Zoom: %.1f'},
}

VECTOR_DEF = {'ctrl_pts': {'color': 'neon green',
                           'radius': 10,
                           'max_click_dist': 10  # max distance from ctrl pt to select it
                           }}

SLIDERS = {'indent': .02,  # fraction of bounding box length (right margin determined by label length)
           'line_thickness': 2,  # fraction of bounding box width
           'line_width': 0.1,  # fraction of bounding box width
           'tab_width': 0.01,  # fraction of bounding box length
           'tab_height': 0.5,  # fraction of bounding box width
           'min_tab_width_px': 10,
           'min_tab_height_px': 20,
           'line_color': BOARD_LAYOUT['obj_color'],
           'label_color': BOARD_LAYOUT['obj_color'],
           'label_font': cv2.FONT_HERSHEY_SIMPLEX,
           'tab_color': 'gray',
           'tab_text_color': BOARD_LAYOUT['obj_color'],
           'tab_text_size': 1.0,  # fraction of tab height
           }
EMPTY_BBOX = {'x': [0, 1], 'y': [0, 1]}

COLOR_BUTTONS = {'circle_frac': 0.7,  # Circle fits in bbox with this margin
                 'outline_frac': .9,  # Fraction of bbox width for outline
                 'mouseover_color': 'neon green',  # ring around buttons when mouseover
                 'selected_color': BOARD_LAYOUT['obj_color'],  # or button has state True
                 'unselected_color': 'red'}

TOOL_BUTTONS = {'outline_frac': 1.0,  # Fraction of bbox width for outline
                'margin_frac': 0.1,  # Fraction of bbox width for margin in drawing
                }
SELECTION_BOX = {'color': 'neon green',
                 'line_thickness': 3}

ZOOM_BOX = {'color': 'neon green',
            'line_thickness': 2,
            'reize_corner_frac': 0.2}  # Fraction of box dims for resize corner
TEXT_TOOL = {'font_size_range': [1.0, 64.0],
             'font': cv2.FONT_HERSHEY_SIMPLEX,
             'thickness': 1,}