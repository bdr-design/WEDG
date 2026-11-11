"""The downloaded model's textures with every brand name and logo taken out (the owner's rule: no badges or names).
thirdparty_tex.py <model's textures dir> <out dir>: writes cleaned copies; the model's own files are not touched.
- Wheel_baseColor: the tyre's sidewall carries the tyre maker's name, the tyre's line and the car maker's logo. Below
  the tread band (rows past TREAD of 2048) all of it is replaced by plain rubber: the plain corner's own colour and
  grain. The two discs that carry no lettering (rings only) are kept as they are.
- Textures_A_baseColor and its roughness map: the car's name in letters (unused by any face, 11 Nov, but not left in
  the files) is painted over with each texture's own background.
- Buttons_baseColor: the sound system maker's logo (on its button) and the "HDMI" label painted out with the black background; the three
  screen pictures below the buttons (a phone's app icons, each an app's logo) made the plain dark display the
  screens have (thirdparty_clean.py).
- Screens_emissive is the same sheet as Buttons (identical pixels), the screens' light: relink() points it at the
  cleaned Buttons sheet too (one texture in the phone's memory, not two), so the gauges, the climate's figures and the
  switches' symbols still glow and the centre screen is a dark display."""
import sys, os, numpy as np
from PIL import Image
from scipy import ndimage

TREAD = 300                                                # the tread band's lower edge (rows, of 2048)
DISCS = (((1240, 1070), 220), ((910, 1376), 220))          # the plain discs: (col, row) centre and radius (px, of 2048)
GRAIN = (slice(1750, 2040), slice(10, 300))                # a plain corner: the rubber's grain
NAME_BOX, NAME_BG = (slice(2536, 2644), slice(838, 1698)), 19      # the name's box on Textures_A (of 4096) and its background
LOGO_BOX = (slice(192, 240), slice(874, 942))                     # on Buttons (of 2048): the logo (lit pixels: rows 198-233, cols 880-936)
HDMI_BOX = (slice(612, 638), slice(552, 618))                     # the "HDMI" label (a trademark; lit pixels: rows 618-632, cols 559-611)
SCREENS_ROW, DISPLAY = 1610, (13, 17, 26)                         # the screens' pictures fill the rows below; the display's colour (sRGB of thirdparty_clean's)


def wheel(src, dst):
    a = np.asarray(Image.open(src).convert('RGB')).astype(float); H, W = a.shape[:2]
    shade = np.median(a[GRAIN].reshape(-1, 3), 0)[None, None, :]          # (the sidewall is flat rubber: its lettering's bands, blurred, read as smudges)
    g = a[GRAIN] - ndimage.gaussian_filter(a[GRAIN], (12, 12, 0)); gh, gw = g.shape[:2]
    grain = np.tile(g, (H // gh + 1, W // gw + 1, 1))[:H, :W]
    plain = np.clip(shade + grain[TREAD:], 0, 255)
    keep = np.zeros((H, W), bool); yy, xx = np.mgrid[:H, :W]
    for (cx, cy), r in DISCS: keep |= (xx - cx) ** 2 + (yy - cy) ** 2 < r * r
    out = a.copy(); sub = keep[TREAD:]; out[TREAD:][~sub] = plain[~sub]
    Image.fromarray(out.astype(np.uint8)).save(dst)


def textures_a(src, dst):
    im = Image.open(src); a = np.array(im); a[NAME_BOX][..., :3] = NAME_BG; Image.fromarray(a).save(dst)


def textures_a_mr(src, dst):
    """The same name is in the roughness map (also the occlusion), at the same place: painted over with the colour
    round it."""
    a = np.array(Image.open(src).convert('RGB')); r, c = NAME_BOX; a[NAME_BOX] = a[r.start - 6, c.start - 6]; Image.fromarray(a).save(dst)


def buttons(src, dst):
    im = Image.open(src); a = np.array(im); a[LOGO_BOX][..., :3] = 0; a[HDMI_BOX][..., :3] = 0; a[SCREENS_ROW:][..., :3] = DISPLAY; Image.fromarray(a).save(dst)


def relink(out_dir):
    """In the open .blend: the image nodes reading a texture cleaned here read the clean copy (packed into the file)."""
    import bpy
    for fn, olds in (('Wheel_baseColor.png', ('Wheel_baseColor',)), ('Textures_A_baseColor.png', ('Textures_A_baseColor',)),
                     ('Textures_A_metallicRoughness.png', ('Textures_A_metallicRoughness',)),
                     ('Buttons_baseColor.png', ('Buttons_baseColor', 'Screens_emissive'))):
        new = bpy.data.images.load(os.path.join(os.path.abspath(out_dir), fn)); new.pack()
        for m in bpy.data.materials:
            for n in (m.node_tree.nodes if m.node_tree else ()):
                if n.type == 'TEX_IMAGE' and n.image and n.image != new and n.image.name.split('.')[0] in olds:
                    new.colorspace_settings.name = n.image.colorspace_settings.name; n.image = new


def main(src_dir, out_dir):
    os.makedirs(out_dir, exist_ok=True)
    wheel(os.path.join(src_dir, 'Wheel_baseColor.png'), os.path.join(out_dir, 'Wheel_baseColor.png'))
    textures_a(os.path.join(src_dir, 'Textures_A_baseColor.png'), os.path.join(out_dir, 'Textures_A_baseColor.png'))
    buttons(os.path.join(src_dir, 'Buttons_baseColor.png'), os.path.join(out_dir, 'Buttons_baseColor.png'))
    textures_a_mr(os.path.join(src_dir, 'Textures_A_metallicRoughness.png'), os.path.join(out_dir, 'Textures_A_metallicRoughness.png'))


if __name__ == '__main__':
    main(*sys.argv[-2:])
