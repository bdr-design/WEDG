# In-game UI designs approved by the owner (2026-11-09)

These mockups were reviewed by agents and approved by the owner. Only the information comes from the reference game; the look is our own.

| File | What it shows |
|---|---|
| `hud.html`, `hud_portrait.jpg`, `hud_landscape.jpg` | The map HUD. |
| `phone.html`, `phone_1.jpg`, `phone_2.jpg`, `phone_3.jpg` | The in-game phone, light and clean like iOS. |
| `phone_supplies.html`, `phone_supplies_water.jpg`, `phone_supplies_feed.jpg` | الوايت and العلف in the phone, and the home screen's date and season (approved 2026-11-12). Add `&big=1` to see a screen as the game enlarges it. |
| `phone_start_home.jpg`, `phone_start_milk.jpg`, `phone_start_build.jpg` (drawn by `phone_start.cjs`) | The new start (one nursing she-camel and her calf, SAR 20,000): the home screen with الحليب, العزبة and الحراج, the milk app (sold every day; how much is left for the calf) and the farm app (what you have, and the facilities you can buy and their prices), approved 2026-11-13. |
| `phone_haraj.jpg` (drawn by `phone_haraj.cjs` with `phone_haraj.css`) | الحراج on the engine: the listings, a camel's page (buy, or haggle three times a seller), selling one's own camel (listed at one's price or to the broker now), and one's listings with their offers; the old design's «على السوم» tab and live auction left out (every listing takes offers; the auctions come later), approved 2026-11-13. |
| `phone_bank.jpg` (drawn by `phone_bank.cjs` with `phone_bank.css`, its figures from `phone_bank_data.dart`, dumped to `phone_bank.json`) | البنك on the engine's own ledger (a new game, seed 4242, played forward by the engine): the main screen on day one, on 22 October after a day of money both ways (the net in the home widget's words, the split under it) and six and a half months in (each month's net and its biggest movement, «أكبرها: …»), and a month opened by kind: October, November (a camel bought and trucked) and February (the calf sold, shown as what reached the player with its price and السعي; no milk). Approved 2026-11-13 with the month rows by their biggest movement (option B; the in-and-out rows dropped) and السعي folded into its sale; built in the phone. The approved mock's تحويل, طلب مبلغ, الرواتب and الكشف are left out: the engine has no transfers, wages are taken on the 1st by themselves, and the months are the statement. |

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
