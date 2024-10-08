# Fixed params for app, dimensions are pixels or relative to w/h of window.

COLORS_RGB = {'black': (0, 0, 0),
              'white': (255, 255, 255),
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


LAYOUT = {'win_size': (1200, 800),

          'ctrl_pts': {'color': 'neon green',
                       'radius': 10},

          # equation box, centered on lower half of window, 90% width
          'eqn_box': {'loc': {'x': (0.05, 0.95),
                              'y': (0.55, 0.85)},
                      'move_tab_corner': 'lower_right', },

          # toolbox, strip on upper-right side of window, 10% width
          'toolbox': {'loc': {'x': [.85, .95],
                              'y': [.05, .40]},
                      'line_widths': [1, 2, 3, 5, 8, 13]},
          # color box, strip below toolbox, 10% width, 5% separation
          'color_box_': {'loc': {'x': [.85, .95],
                                 'y': [.45, .65]},
                         'options': [['black', 'white'],
                                     ['red', 'orange'],
                                     ['blue', 'yellow'],
                                     ['purple', 'green']]},
          # zoom slider-bar, vertical, left side of window
          'zoom_bar': {'loc': {'x': [.05, .15],
                               'y': [.05, .40],
                               'orientation': 'vertical'}, },

          # Rewind/fast-forward style undo/redo buttons, horizontal strip at bottom
          'undo_bar': {'loc': {'x': [.1, .9],
                               'y': [.85, .95],
                               'orientation': 'horizontal'}, }, }
