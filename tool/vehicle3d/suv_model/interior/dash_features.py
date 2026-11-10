"""What is on the dashboard's centre stack and the console in dash_front.png, read off gridded enlargements
(zoom.py) in the photo's own pixels (x right, y down). FIRST READING, to within about 3 px.
Each entry: (kind, plane, material, how far it stands out of its plane in mm, shape), where the plane is one of
dash.PARTS' names (the thing lies on that part's face) and the shape is a box (col0, row0, col1, row1), a list of
(col, row) corners, or a circle ('circle', col, row, radius across in px, radius up in px)."""
def box(x0, y0, x1, y1): return [(x0, y0), (x1, y0), (x1, y1), (x0, y1)]
def circle(cx, cy, rx, ry=None, n=28):
    import math
    return [(cx + rx * math.cos(2 * math.pi * k / n), cy + (ry or rx) * math.sin(2 * math.pi * k / n)) for k in range(n)]
FRAME_OUT = [(688, 426), (1025, 426), (1025, 548), (1005, 572), (708, 572), (688, 548)]
FRAME_IN = [(701, 434), (1012, 434), (1012, 545), (996, 560), (717, 560), (701, 545)]
STACK = [
    ('ring', 'stack', 'silver', 4.0, (FRAME_OUT, FRAME_IN)),                       # the silver frame round the upper module
    ('flat', 'stack', 'gloss', 0.5, box(723, 438, 992, 493)),                      # the vents' block
    ('prism', 'stack', 'gloss', 3.0, box(843, 439, 873, 491)),                     # the hazard switch
    ('flat', 'stack', 'red', 3.3, [(858, 455), (866, 470), (850, 470)]),           # its triangle
    ('prism', 'stack', 'silver', 2.5, box(768, 459, 799, 463)), ('prism', 'stack', 'silver', 2.5, box(913, 459, 944, 463)),      # the vents' tabs
    ('prism', 'stack', 'silver', 3.0, box(705, 446, 720, 478)), ('prism', 'stack', 'silver', 3.0, box(995, 446, 1010, 478)),     # the wheels beside the vents
    ('flat', 'stack', 'gloss', 0.5, box(723, 496, 992, 556)),                      # the heater panel
    ('prism', 'stack', 'silver', 4.0, box(753, 527, 965, 534)),                    # its row of switch tips
    ('prism', 'stack_low', 'silver', 3.0, box(688, 572, 703, 748)), ('prism', 'stack_low', 'silver', 3.0, box(983, 572, 1023, 748)),     # the silver posts either side
    ('prism', 'stack_low', 'silver', 14.0, circle(719, 638, 26)), ('prism', 'stack_low', 'black', 16.0, circle(719, 638, 20)),             # the big knob
    ('flat', 'stack_low', 'gloss', 0.5, box(764, 591, 803, 659)),                  # the small panel beside it
    ('flat', 'stack_low', 'dark', 0.5, box(805, 583, 975, 661)),                   # the tray
    ('prism', 'stack_low', 'black', 2.0, box(705, 578, 733, 613)), ('prism', 'stack_low', 'black', 2.0, box(705, 670, 733, 739)),         # switches on the left post
]
CONSOLE = [
    ('flat', 'console', 'gloss', 0.5, box(736, 713, 1001, 809)),                   # the plate the shifter stands on
    ('prism', 'console', 'silver', 2.0, box(766, 740, 793, 743)),
    ('ring', 'console', 'silver', 3.0, (circle(792, 872, 65, 46), circle(792, 872, 57, 40))), ('ring', 'console', 'silver', 3.0, (circle(964, 872, 65, 46), circle(964, 872, 57, 40))),
    ('flat', 'console', 'dark', -60.0, circle(792, 872, 57, 40)), ('flat', 'console', 'dark', -60.0, circle(964, 872, 57, 40)),            # the cup holders' floors
]
SHIFTER = {'foot': (855, 775), 'knob': (825, 626, 903, 687), 'boot': (810, 687, 901, 817)}        # where it stands on the console, and its knob and boot as boxes on the photo
