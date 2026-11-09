# In-game UI designs approved by the owner (2026-11-09)

These mockups were reviewed by agents and approved by the owner. Only the information comes from the reference game; the look is our own.

| File | What it shows |
|---|---|
| `hud.html`, `hud_portrait.jpg`, `hud_landscape.jpg` | The map HUD. |
| `phone.html`, `phone_1.jpg`, `phone_2.jpg`, `phone_3.jpg` | The in-game phone, light and clean like iOS. |

## The map HUD

- **Top:** small glass capsules. The farm's وسم and name, the time of day and the season; the money; water and feed as rings, with the days left.
- **Bottom:** a floating tab bar (حلالي، المسراح، الحراج، المزاين) and a camera button.
- **Pens:** each pen's name is printed into its green shade cloth, so nothing floats over the farm. The isolation pen's shade is tinted orange when it needs attention.
- **Water tank:** an orange ring on the ground when water runs low.
- **Places:** a tap opens a one-line glass card beside the thing.
- **Names in the far view:** hidden when they would be under 11 pt.

## The phone

Apps: the bank (transfers and shepherds' wages), الحراج (priced, on-bid and my listings), a live auction, chats with traders (haggling, with a sale summary: السعي, vaccination, health certificate, chip and passport transfer, transport permit), weather with grazing, and more.

**Weight:**
- The 3D view stops drawing while the phone is open; behind it is the last frame, dimmed, with no blur.
- Lists are lazy, and the thumbnails are small and made in advance.

`proj.js` is the camera projection used to place the roof prints in the mockup.
