# Fixed params for app, dimensions are pixels or relative to w/h of window.
import cv2

PREC_BITS = 7  # number of bits to use for precision in fixed-point numbers
PREC_SCALE = 2 ** PREC_BITS  # for cv2 draw commands

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
              'light_gray': (192, 192, 192),
              'orange': (255, 165, 0),
              'purple': (128, 0, 128),
              'brown': (165, 42, 42),
              'pink': (255, 192, 203),
              'olive': (128, 128, 0),
              'teal': (0, 128, 128),
              'navy': (0, 0, 128)}

UI_LINE_THICKNESS = 2

# Board is the main display window
CANVAS_LAYOUT = {'win_size': (1200, 800),
                 'win_name': 'Whiteboard Board',
                 'bkg_color': COLORS_RGB['off_white'],
                 'init_zoom': 1.0,  
                 'init_origin': (0, 0),
                 'zoom_bar': {'loc': {'x': [.85, .95],
                                      'y': [.05, .475],
                                      'orientation': 'vertical'}, }, }

# Control is the user input window.
CONTROL_LAYOUT = {
    'win_name': 'Whiteboard Controls',
    'win_size': (800, 600),
    'init_zoom': 2.0,  # wrt canvas window
    'init_origin': (0, 0), # wrt canvas window


    # toolbox, strip in the middle of the right side of the window
    'toolbox': {'loc': {'x': [.85, .3],
                        'y': [.05, .6]},
                'line_widths': [1, 2, 3, 5, 8, 13]},

    # color box, strip below toolbox, 10% width, 5% separation
    'color_box': {'loc': {'x': [.05, .3],
                           'y': [.15, .6]},
                   'options': [['black', 'white'],
                               ['red', 'orange'],
                               ['blue', 'yellow'],
                               ['purple', 'green']]},

    # zoom slider-bar, vertical, left side of window
    'zoom_bar': {'loc': {'x': [.05, .15],
                         'y': [.05, .40],
                         'orientation': 'vertical'}, },
}

VECTORS = {'ctrl_pts': {'color': 'neon green',
                        'radius': 10,
                        'max_click_dist': 10  # max distance from ctrl pt to select it
                        }}

SLIDERS = {'indent': .05,  # fraction of bounding box length (right margin determined by label length)
           'line_thickness': 2,  # fraction of bounding box width
           'line_width': 0.1,  # fraction of bounding box width
           'tab_width': 0.01,  # fraction of bounding box length
           'tab_height': 0.5,  # fraction of bounding box width
           'min_tab_width_px': 10,
           'min_tab_height_px': 20,
           'line_color': 'black',
           'label_color': 'white',
           'label_font': cv2.FONT_HERSHEY_SIMPLEX,
           'tab_color': 'dark_gray',
           'tab_text_color': 'light_gray',
           'tab_text_size': 1.0,  # fraction of tab height
           }
