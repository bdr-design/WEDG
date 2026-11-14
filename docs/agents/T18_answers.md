# T18 part A: answers to the reviewer's phase-1 questions (14 Nov 2026)

The reviewer's rules table raised 28 places where the documents disagree or are silent
($SC/t18_review/rules_table.md, Q-1 to Q-28). Each is answered here one of three ways:

- **Source**: the sources settle it; build to the source.
- **Game choice (director)**: the sources are silent and the point is a detail inside the design the owner approved;
  built as stated, written in the GDD as a game choice, and listed for the owner in the report so he can overturn it.
  One constant each, so overturning is a one-line change.
- **Owner**: his to decide. Build the provisional answer given here behind one switch; it is being put to him.

## Dates and hours

- Q-1 Hunting hours: **Source** [135]: from one hour after sunrise to one hour before sunset. Sun times: the game's
  own sun for the date if the engine has one; otherwise a table by month for the farm's latitude, each row sourced or
  computed by the standard formula and marked so.
- Q-2 Trapping at midday: **Game choice**: lawful all day; the hour is one of the weights of the odds (the design:
  "the hour"), highest from dawn to 10:00 and in the evening hour [204], low between. Nothing is refused for the hour
  in daylight. Night: refused (the hunting rules' ban on night and lights is taken to bind trapping: the conservative
  reading; marked unconfirmed in the GDD as the design note does).
- Q-3 The breeders' auction: **Source** [158]: 5–25 August.
- Q-4 Releasing a kept trapped peregrine: **Owner** (his item 19 says from February or keep). Provisional: any day
  from 1 February to 30 April (the spring passage north; mark the end date a game choice unless the research dates
  it), in any later year too.
- Q-5 The trapping permit: **Game choice**: bought on any day; valid for one trapping season (the one open or the
  next to open); lapses on 30 November. The hunting permit likewise, one season (1 Sep–31 Jan).

## Permits and papers

- Q-6 The hunting permit's fee: **Game choice**: 100 riyals as the money page has it, marked "weak source".
- Q-7 A trapped bird he keeps: **Source** [190][191][192]: the club's team checks the bird and documents the
  trapping, and that registration leads to the passport. So keeping is also done through the club (the same check,
  no sale), and the kept bird has its registration and passport before it may be flown under the hunting permit.

## Grounds and quarry

- Q-8 الحماد: north-west of Arar, toward Turaif and the Jordanian border (the director's own knowledge, not opened
  on this machine: mark it so). If the research's sources put the trapping ground itself elsewhere, give both and
  keep the distance from the farm a marked estimate.
- Q-9 "Around the farm": the research's figure for the distance from dwellings and farms if it has one; otherwise a
  **game choice** stated in the GDD.
- Q-10 The quarry's dates: **Source**, strictly: each species may be flown at only on the dates its source lists; a
  species or a date the sources do not list is refused. Say in the report what that leaves huntable, by month.
- Q-11 The Empty Quarter: as the design has it (a trapping ground); the old hunting rule noted in the GDD.

## The net, the room, the auction

- Q-12 A saker قرناس takes the saker's line (the species' rule is tested first; the قرناس line is for a peregrine
  older than a فرخ).
- Q-13 and Q-15 A bird with nowhere to go, and holding an unsold bird: **Owner.** Provisional: a sellable bird may
  be held at camp and at the farm without a room until it is sold; it may be entered on any night the auction is
  open; to keep it as his own he needs a free place in the falcons' room; a bird still unsold and unkept when the
  auction closes is released, with a line. A bird in the net when the auction has already closed for the year
  cannot happen (the season and the auction end the same day): assert it.
- Q-14 Selling: from the phone, as the approved view draws it; no trip to Malham (the club carries the cost [184]
  [189]); the hammer falls that night.
- Q-16 A lot with no bid: **Game choice**: a bird the club accepted always sells (no unsold lot was found in the
  sales read). The price is drawn from the distribution; it has no floor below the lowest sale read.
- Q-17 Buying at the trapping auction: the engine offers the night's lots and a buy command at the hammer price the
  lot will reach (no bidding game); the phone's view for it is drawn in part B and shown to the owner before it is
  built. Say in the report what the view will need.
- Q-18 Cash or account: **Owner.** Provisional: everything in hunting is cash only (a falcon, the gear, the room,
  the permits, the tracker), refused in debt, as rushing is.
- Q-19 Buying a falcon with no room, or with the room full: refused, with words (yours; list them for the owner).
- Q-20 Reselling a bought falcon: **Owner.** Provisional: no command for it (as for a kept trapped bird); the older
  GDD lines about selling a trained falcon at a higher price are withdrawn until he says.

## Being away and الدعو

- Q-21 Landing minutes: **Game choice**: trapping lands at first light (civil dawn by the sun table); falconry at the
  hour the hunting day opens (one hour after sunrise).
- Q-22 The falconCare hook: build it as a state-based stop of the away call, like the others: a jump stops on the
  morning of the day a falcon left at the farm would step back, so he can go to the room. No loop callback (N3).
- Q-23 One falcons' room (4 falcons) for now: **Game choice**; a second room is a later question.
- Q-24 الدعو: one tap is today's care for every falcon in the room; neglect is counted by the days since each
  falcon was last cared for or flown; a falcon with him on a trip counts as cared for on a day it flew. The design's
  thresholds stand.
- Q-25 Upkeep: 20 riyals a day for each falcon, as the money page has it (a game choice there): a daily system, the
  bank's own kind.

## Falconry

- Q-26 "Parked, not moving": the cast command carries the car's state from the map (on foot; or in the car and
  whether it is moving) and the engine refuses a cast from a moving car with the reason's words. No fine follows a
  refusal.
- Q-27 The tracker: one for each falcon (each bird wears its own); its price a **game choice**.

## The odds

- Q-28 A second bird in one season: **Owner.** Provisional: the target is his own words, counted as he said them:
  the share of seasons with at least one sellable bird (about 1 in 6 to 2 in 3). A second bird in the same season is
  possible by the same daily chance, with no cap and no help; report the mean birds a season beside it. If he
  answers "one bird a season at most" it is one switch.

## The two oddities

- `Facility.room` (the sitting room) stays; the falcons' room is a new value.
- season.cjs's header line about selling at the next autumn's auction is stale: decision 8 governs; correct the
  comment when you next touch the file.

## The owner's answers (14 Nov 2026, the same day)

Q-13/Q-15, Q-18, Q-20 and Q-28 were put to him and he chose the provisional answer in each
(docs/agents/owner_decisions_2026-11-14.md items 22–25): they are now his word, not provisional; the switches may
be removed where they cost anything to keep. Q-4 is still provisional.
