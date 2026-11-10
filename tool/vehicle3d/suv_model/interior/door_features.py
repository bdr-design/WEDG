"""What is on the front left door's trim in door_FL.png, read off gridded enlargements (zoom.py) in the photo's own
pixels (x right, y down). FIRST READING, to within about 3 px: snap them (wheel_features.snap) before use."""
# the recess round the inner handle: its rim, the cup inside it, the lever, the lock's tab, and three slats beside the cup
HANDLE_RIM = [(707, 194), (1076, 194), (1088, 205), (1089, 215), (1060, 250), (1010, 290), (960, 318), (700, 322), (690, 318), (680, 300), (680, 215), (690, 200)]
HANDLE_CUP = [(716, 214), (925, 214), (929, 222), (929, 300), (922, 304), (716, 304), (711, 296), (711, 222)]
LEVER = [(707, 285), (712, 300), (890, 302), (925, 280), (929, 266), (770, 268), (765, 285)]
LOCK_TAB = [(762, 236), (771, 236), (771, 265), (762, 265)]
SLATS = [[(1008, 214), (1060, 214), (1040, 232), (988, 232)], [(978, 242), (1032, 242), (1010, 266), (956, 266)], [(945, 274), (1000, 274), (980, 298), (925, 298)]]
# the switch panel on the sweep's edge, the mirror knob and the four window switches (each a slanted block)
SWITCH_PANEL = [(1186, 198), (1225, 223), (1220, 254), (970, 467), (951, 481), (904, 439), (920, 423), (1164, 214)]
MIRROR_KNOB = (1167, 268, 14)
SWITCHES = [[(1076, 290), (1118, 262), (1148, 300), (1104, 332)], [(1008, 342), (1050, 316), (1082, 352), (1040, 384)],
            [(960, 392), (1000, 366), (1026, 400), (986, 430)], [(905, 440), (945, 414), (968, 446), (930, 474)]]
# the wood strip between the upper panel and the armrest
WOOD = [(560, 432), (619, 438), (685, 464), (759, 473), (898, 474), (943, 479), (945, 526), (917, 545), (796, 538), (722, 523), (663, 497), (619, 468), (575, 442)]
# the seam that parts the armrest's pad from the band under it, and the stitching along the armrest's upper sweep
ARMREST_SEAM = [(93, 628), (500, 628), (972, 628), (1000, 600)]
STITCH = [(472, 409), (575, 468), (648, 526), (722, 552), (832, 563), (928, 567)]
# the map pocket's opening, the speaker's grille and the courtesy lamp in the lower panel
POCKET = [(531, 652), (1037, 646), (1104, 688), (1073, 742), (1013, 827), (953, 863), (580, 857), (561, 832), (519, 766), (489, 700)]
SPEAKER = [(1152, 688), (1441, 670), (1453, 887), (1440, 940), (1411, 962), (1013, 965), (1011, 887), (1037, 851), (1110, 766)]
LAMP = [(460, 958), (560, 958), (560, 982), (460, 982)]
