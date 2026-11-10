"""The front seat on seat_side.png, read off gridded enlargements (zoom.py) in the photo's own pixels (x right,
y down). The seat faces right; the photo is from its side and a little above, so the cushion's top shows.
The outline itself is not here: seat_measure takes it from the backdrop to a fraction of a pixel. These are the
lines inside it. FIRST READING, to within about 3 px; snap() them before use (wheel_features.snap works on any photo).

The parts, top to bottom: the headrest (rows 20 to 280) on two bright posts (280 to 305); the backrest (305 to
about 900), with a black bracket on its upper rear edge (x 150 to 175, y 330 to 500); the cushion (750 to 960);
the plastic base under and behind it, with the controls in a sunk oval; the black rail (1126 to 1200). A belt
buckle with a red button stands behind the cushion at about (650..690, 720..770).

SCALE has no source: no photo gives the seat's size against a known length. It is set so that the seat is 1.08 m
from the rail's foot to the headrest's top (a game choice until the cabin's own measures check it)."""
HEIGHT = 1.08                      # metres from the rail's lowest point to the headrest's top: an assumption
# the plastic base's outline, clockwise from where it meets the backrest's lower rear
BASE = [(320, 894), (352, 873), (394, 872), (441, 891), (499, 929), (547, 950), (617, 962), (735, 959), (852, 953), (941, 950),
        (999, 953), (1007, 974), (994, 1021), (964, 1079), (935, 1121), (911, 1134), (676, 1143), (441, 1135), (388, 1121),
        (352, 1068), (329, 997), (320, 938), (317, 909)]
CONTROL_WELL = (676, 994, 932, 1074)            # the sunk oval: x0, y0, x1, y1
RECLINE_LEVER = (708, 1003, 749, 1059)
SLIDE_SWITCH = (765, 1021, 839, 1055)
LUMBAR_KNOB = (883, 1031, 26)                   # centre x, y and radius
RAIL = (320, 1126, 998, 1190)                   # the black rail's box; its feet run out to x 185 and 1000 at y 1165 to 1200
# the backrest's lower edge where it tucks into the base, rear to front, then up its front edge
BACK_FOOT = [(314, 856), (347, 851), (411, 859), (458, 877), (487, 891), (517, 821), (541, 791)]
BUCKLE = (650, 720, 690, 770)
