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

# on the dashboard's faces either side of the stack (first readings off the whole photo and one enlargement)
DASH = [
    ('flat', 'screen', 'display', 0.3, box(709, 300, 1000, 403)),                  # the screen's display
    ('flat', 'cluster', 'display', 0.0, [(330, 440), (345, 395), (420, 368), (560, 363), (568, 440), (560, 466), (345, 466)]),      # the instruments' display, behind the wheel
    ('flat', 'upper', 'gloss', 0.5, box(150, 370, 229, 424)), ('flat', 'upper', 'gloss', 0.5, box(1400, 370, 1530, 424)),             # the outer vents
    ('prism', 'upper', 'silver', 12.0, circle(659, 391, 20)), ('prism', 'upper', 'black', 14.0, circle(659, 391, 15)),                # the round switch right of the instruments
    ('prism', 'lower', 'black', 2.0, box(603, 550, 655, 564)), ('prism', 'lower', 'black', 2.0, box(603, 568, 655, 582)), ('prism', 'lower', 'black', 2.0, box(603, 586, 655, 600)),
    ('flat', 'lower', 'dark', 0.3, box(1056, 444, 1480, 447)), ('flat', 'lower', 'dark', 0.3, box(1056, 657, 1480, 660)),             # the glovebox's upper and lower seams
    ('flat', 'lower', 'dark', 0.3, box(1056, 444, 1059, 660)), ('flat', 'lower', 'dark', 0.3, box(1477, 444, 1480, 660)),
    ('flat', 'lower', 'dark', 0.5, box(1112, 474, 1198, 506)), ('prism', 'lower', 'silver', 1.5, circle(1132, 490, 9)),              # its latch
]
