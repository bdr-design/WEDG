# In-game UI designs approved by the owner (2026-11-09)

These mockups were reviewed by agents and approved by the owner. Only the information comes from the reference game; the look is our own.

| File | What it shows |
|---|---|
| `hud.html`, `hud_portrait.jpg`, `hud_landscape.jpg` | The map HUD. |
| `phone.html`, `phone_1.jpg`, `phone_2.jpg`, `phone_3.jpg` | The in-game phone, light and clean like iOS. |
| `phone_supplies.html`, `phone_supplies_water.jpg`, `phone_supplies_feed.jpg` | الوايت and العلف in the phone, and the home screen's date and season (approved 2026-11-12). Add `&big=1` to see a screen as the game enlarges it. |
| `phone_start_home.jpg`, `phone_start_milk.jpg`, `phone_start_build.jpg` (drawn by `phone_start.cjs`) | The new start (one nursing she-camel and her calf, SAR 20,000): the home screen with الحليب, العزبة and الحراج, the milk app (sold every day; how much is left for the calf) and the farm app (what you have, and the facilities you can buy and their prices), approved 2026-11-13. |
| `phone_haraj.jpg` (drawn by `phone_haraj.cjs` with `phone_haraj.css`) | الحراج on the engine: the listings, a camel's page (buy, or haggle three times a seller), selling one's own camel (listed at one's price or to the broker now), and one's listings with their offers; the old design's «على السوم» tab and live auction left out (every listing takes offers; the auctions come later), approved 2026-11-13. |
| `phone_mazayen.jpg` (drawn by `phone_mazayen.cjs`) | **Approved by the owner 2026-11-13 for building.** Cheating lives in a secret dealer's chat, reached through a new «المحادثات» app (he messages after a registration; the festival's own app never offers it), and the round's day is told stage by stage through the day with a notice at each stage (the hours a game choice). المزاين on the festival engine (GDD 7 and 7.1, the owner's festival decisions of 2026-11-13), in nine views from real games on seed 4242 (1 October 2026; copies played on a fast clock to the round's day): the festivals (the one open, the player's entry and its withdrawal, the coming ones by their days and the highest first prize a player can enter for); a festival in two views (its individual rounds and first prizes, each colour's day, free then late registration closing 72 hours before the round, the group rounds only as coming later, the rules); registering (each camel with its round or the engine's refusal, and the cost); the secret treatment in a dealer's chat (the seven kinds, then light, middle or strong with each one's price, fine and risk in words; kinds stack and the risk adds up; the examination at a sale); the round's day (the six stages from الشريحة والشاهد, told one by one); the results (placings and prizes only, no scores); and the day a treatment is found, played in a game, not drawn from rules (the fine, the ban from every festival, the balance below zero, the account for feed, water and the vet). Every figure is the engine's; what is still copied or a placeholder is listed in the session's report. |

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

## الوايت and العلف (approved 2026-11-12)

Drawn from the rules engine's own numbers (a new farm six weeks in), and as the game enlarges the phone.
- **الوايت:** the tank in litres and the days it lasts at the herd's drinking; a 19 t tanker (SAR 200) and a 6 t one
  (SAR 120) to top up a tank the large one does not fit, each greyed with the level at which it will fit; when the
  herd is thirsty, the days without water against the days it can last (10 in winter on dry feed, 17 on green
  pasture) and how many are left before it starts to die.
- **العلف:** each feed's stock and days left, a warning the day before it runs out, the ration (خفيفة, عادية, قوية)
  with each one's cost a day and the condition it reaches, an order for three weeks by bags and bales, the order on
  its way and the days it will give, and, short of money, a week's order the balance covers.
- **The home screen:** the date and season (الأحد 15 نوفمبر · الوسم · وقت الضراب) in a line above the widgets; the
  widgets as approved; red badges count the supplies running low.
- **Build notes:** a count's word follows the counting rule as the count changes (كيس واحد، كيسين، 3–10 أكياس، 11
  كيس); the app checks the whole order's total before sending its parts.
