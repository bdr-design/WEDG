# Scale brief: 1,000,000 camels per player

Verdict: the planned direction holds, with one change. SQLite, compact rows and event sampling are all correct, but the daily changes must **not** be written as in-place updates to camel rows. Write them to an append-only event table and fold that table into the camel rows in one batch. Measured here, that is about 1 ms per simulated day instead of about 66 ms.

Fetch notes: drift.simonbinder.eu, sqlite.org and dart.googlesource.com failed with ENOTFOUND, so claims from those hosts come from search snippets. The GitHub API was blocked, but the github.com release page loaded.

The figures marked **[M]** I measured in this sandbox. Setup: Dart 3.13.7 AOT via `dart build cli`, package:sqlite3 3.9.0 with `source: system` (SQLite 3.45.1), on a 2.3 GHz Xeon VM running Linux. Phones will be slower. The bench code is in `/tmp/claude-0/-home-user-WEDG/d6dbc15a-e910-5754-8d25-3b30bd9632e4/scratchpad/scale-bench/`.

## A1. Native store

**Use package:sqlite3 3.9.x directly in the engine isolate.**
- **Why it fits:**
  - It is a synchronous FFI API, so calls make no extra isolate hop.
  - Since 3.0, build hooks bundle SQLite for Android, iOS, macOS, Linux and Windows. `sqlite3_flutter_libs` is no longer needed [1][2][3].
  - It works as plain Dart. I built and ran it with `dart build cli` and no Flutter [M], so the same engine package can run on a Dart server later.
- **Recent additions:** 3.7.0 added `Database.releaseMemory()`. 3.9.0 added `interrupt()` [1].

**Alternatives:**
- **drift:** It moved onto sqlite3 3.x in 2.33.0 [10]. It is optional on the UI side, where its reactive queries and web-worker plumbing help. Its docs say a background isolate trades total throughput for less UI jank, and that WAL is required when several isolates share a database [11].
- **Rejected:**
  - sqflite is a Flutter plugin: no server, and web support is experimental [5].
  - ObjectBox has no web build [6].
  - The original Isar is discontinued, and its community forks get bug fixes only [8][9].
  - Realm SDKs were deprecated in September 2024, with end-of-life on 30 September 2025 [7].
- **Batching:** PowerSync's benchmark found that transactions and batching matter more than which database you pick [12].

**Measured, 1M rows [M]:**

| Operation | Result |
|---|---|
| Insert in 1 transaction with a prepared statement | 1.6 s (about 630k rows/s) |
| Build 3 indexes | 0.7 s |
| File size, no indexes | 57.7 B/row |
| File size with `(farm,id)`, partial `due`, partial `sick` indexes | 73.9 B/row (74 MB) |
| File size with names added | 86 MB |
| Keyset page of 50 rows (`WHERE farm=? AND id>? ORDER BY id LIMIT 50`) | 0.1 ms |
| Point lookup | 6.4 µs |
| `GROUP BY farm` count | 33 ms |
| Due-today read through a partial index | 0.16 ms |
| Process RSS (8 MB page cache) | 24 MB |

**Row layout matters [M]:**
- 20 REAL trait columns take 224 B/row.
- One 20-byte BLOB takes 56 B/row.
- Adding a byte-quantised body condition brings it to 49 B/row.

**Daily writes [M]:**
- 3,000 random in-place updates take 64–70 ms per simulated day. Neither sorting the ids, a 64 MB cache nor dropping the index helped, because each update dirties its own 4 KB page.
- At that rate a 300-day catch-up costs about 20 s on desktop.
- Appending 3,000 events per day to an event table takes **1.0 ms**.
- The fold step, one sorted transaction updating 300k distinct camels, takes **0.47 s**.

**Phones:** Older Android measurements through the Java API reached about 17k inserts/s [25]. FFI avoids that overhead. Plan on 50–200k rows/s and test on a low-end device (this is my estimate).

**Design:**
- Use `INTEGER PRIMARY KEY` with dense ids, so births are appends.
- Settings: WAL, `synchronous=NORMAL`, and keyset paging (never OFFSET).
- Put contest placings, illness episodes and an archive of dead or sold camels in side tables.
- Commit catch-up in chunks of one day or ≤10k rows, then fold.
- The engine isolate owns the single write connection. Optionally add a read-only WAL connection in a query isolate, so screens can page while catch-up runs.

## A2. Web

- **dart:isolate is native-only [17].** OPFS synchronous access handles work only in **dedicated workers** (Chrome 108, Firefox 111, Safari 16.4) [14]. So the current time-sliced main-thread engine cannot use durable OPFS. Move the engine and the database into a dedicated Web Worker, compiled separately to JS or wasm.
- **Storage options:**
  - sqlite3's `SimpleOpfsFileSystem` runs in dedicated workers only and persists a single database at `/database` [13].
  - drift's `opfsLocks` needs COOP/COEP headers [11].
  - The IndexedDB VFS makes "no guarantees on durability" [15].
- **Bundle size:** `sqlite3.wasm` is 741 KB in the sqlite3.dart 3.9.0 release [4]. The official build is 879 KB raw and 406 KB gzipped [M][16].
- **1M rows on web:** That is about 75–90 MB on disk, which is feasible. Call `navigator.storage.persist()` [18] and plan for eviction. Treat the web build as the slow tier: throughput is unmeasured, so benchmark it.

## A3. Memory

**Per-camel cost, 1M camels, x64 AOT [M]:**

| Layout | Per camel | 1M camels |
|---|---|---|
| One object per camel, `List<double>` traits | 607 B | 607 MB |
| One object per camel, `Uint8List(20)` traits | 125 B | 125 MB |
| Struct-of-arrays in typed columns | 42 B | 42 MB |

Mobile builds use compressed pointers. That saves only 20–30% of heap and puts all isolate groups in one 4 GB region [19].

**iOS limits:**
- The limit is a dirty-memory limit that can change over the app's lifetime. Apple says to read `os_proc_available_memory()` and not cache it [20].
- Measured kill points:

| Device class | Kill point |
|---|---|
| 3 GB iPhones (e.g. iPhone X) | about 1.39 GB [22] |
| 4 GB devices | 2.04–2.10 GB [21][22] |
| 8–12 GB Pro Max | about 6 GB [23] |

**Android:** Cached processes are killed by the low-memory killer, and `onTrimMemory` warns you first [24]. Dart heap is native memory, so Java's `memoryClass` does not cap it; that is my inference.

**Budget:**
- Engine isolate ≤150 MB steady, ≤250 MB peak.
- Keep the app under about 1 GB on 3 GB phones.
- Never materialise 1M camel objects.
- In RAM, keep only:
  - per-stratum counts;
  - one `Int32List` of member ids per stratum (4 MB in total);
  - optionally, typed columns the samplers need (20 MB for traits).
- Load the 50 camels a screen shows on demand.

## A4. Event sampling

1. **Strata:** Group camels by farm × sex × age class × health × pregnancy, for example 200 farms × 12 classes ≈ 2,400 strata.
2. **Counts:** For each stratum, day and event, draw k ~ Binomial(n, p) exactly.
   - Use inversion when np < 14–30.
   - Use BTPE above that. R switches at np ≥ 30 and GSL at 14 [26][27].
   - BTRD is an alternative, needing 1.4–2.5 uniforms per draw [28].
   - Do not use Poisson. Le Cam bounds the error by d_TV ≤ np² [29], which is 0.05 at n = 50,000, p = 0.001: not negligible.
3. **Competing risks:** Draw deaths, then draw illness from the survivors with p/(1−p_death).
4. **Choosing individuals:** Floyd's algorithm picks k distinct indices with exactly k RNG calls [30]. Index into the stratum's id array, and swap-remove ids as camels leave it.
5. **Risk that varies by camel** (genes, condition): use thinning. Draw candidates at p_max and accept each with p_i/p_max [32]. This is exact and touches only the candidates.
6. **Determinism:**
   - Use a counter-based RNG (Philox or Threefry [31]) keyed by (worldSeed, day, stratum, eventType). Results then do not depend on catch-up batching or iteration order.
   - Implement it with 32-bit operations. On web, Dart ints are JS doubles with 53 bits, and bitwise operations truncate to 32 bits [33].
   - Native and web can still differ in the last bits of exp/log. If online play needs bit-identical results, make the server authoritative.
7. **Body condition:** Use the closed form c(t) = target + (c₀−target)·e^(−k(t−t₀)) on read, anchored per camel. A policy change writes the farm's policy timeline, not 1M rows.

**Load at 1M camels (my estimate from Part B rates):**
- About 840 births/day (1M × ~45% breeding females × 0.68 calvings/year ÷ 365).
- About 110–190 adult deaths/day.
- About 575 sales or slaughters/day.
- That is roughly 2–3k events/day.
- A 300-day catch-up is about 3M binomial draws (mostly cheap inversion) plus about 0.8M event appends. Expect a few seconds on a phone if events are journalled; this needs measuring.

## B5. Real large operations

- **National herd:** GASTAT counted 2.2M camels in 2023, 68% of them aged ≥4 years [34]. The 2024 count was 2.24M, up 1% [35]. The ministry census put it at about 2.2M at the end of 2024: Riyadh 656k, Eastern Province 361k, Makkah 281k [36].
- **Rates:**
  - A Qassim survey found a typical herd of 27 head, a **68% calving rate**, first calving at 4 years 4 months, a 20-month calving interval, and **17% mortality from birth to 1 year** [37].
  - Adult or whole-herd mortality runs 4–6% a year in pastoral studies elsewhere [38][39].
  - Saudi slaughter of about 470k head in 2022 [40] implies about **21% offtake** a year.
- **Staff:**
  - In 115 Saudi herds (7,122 camels), pregnancy rates were 95% at 1 herder per <25 camels, 80% at 1:25–50, and 73% at 1:>50 [41].
  - Farm types range from desert-based herds to urban multi-activity owners [42].
  - Shepherds are excluded from the Saudi labour code [43].
  - I found no published vet-to-camel ratio.
- **Records:**
  - Electronic neck microchips have been mandatory since 2020. More than 1.4M camels were chipped at the time, registered through the ministry's "Naama" portal [44].
  - A Camel Passport launched in February 2026. It records microchip number, name, birth date and place, breed, sex and colour [45].

## B6. Framing 1M honestly

- The largest documented single operations are 7,000–10,000 head [46][47][48]. A 1996 report described a sheikh with about 5,000 racing camels [49].
- **1M is about 45% of the Kingdom's camels and about 2.4% of the world's** (41.8M per FAOSTAT 2023 [50]).
- **Suggested framing:** a fictional national-scale holding company. At 1:25–50 herders, it would need about 100–150 sites of 7–10k head, or thousands of عزب, and 20–40k herders.

## Sources
1. https://pub.dev/packages/sqlite3/changelog
2. https://pub.dev/packages/sqlite3
3. https://pub.dev/documentation/sqlite3_flutter_libs
4. https://github.com/simolus3/sqlite3.dart/releases/expanded_assets/sqlite3-3.9.0
5. https://pub.dev/packages/sqflite
6. https://pub.dev/packages/objectbox
7. https://www.mongodb.com/docs/atlas/device-sdks/deprecation.md
8. https://pub.dev/packages/isar_db/changelog
9. https://dinkomarinac.dev/blog/best-local-database-for-flutter-apps-a-complete-guide/
10. https://github.com/simolus3/drift/releases
11. https://pub.dev/documentation/drift/latest/wasm/WasmStorageImplementation.html ; https://drift.simonbinder.eu/platforms/vm (search snippet)
12. https://powersync.com/blog/flutter-database-comparison-sqlite-async-sqflite-objectbox-isar
13. https://pub.dev/documentation/sqlite3/latest/wasm/SimpleOpfsFileSystem-class.html
14. https://developer.mozilla.org/en-US/docs/Web/API/FileSystemSyncAccessHandle ; https://blog.openreplay.com/sqlite-browser-opfs/
15. https://pub.dev/documentation/sqlite3/latest/wasm/IndexedDbFileSystem-class.html
16. https://registry.npmjs.org/@sqlite.org/sqlite-wasm (3.54.1-build1 tarball)
17. https://api.dart.dev/dart-isolate
18. https://web.dev/articles/persistent-storage
19. https://dart.googlesource.com/sdk/+/stable/runtime/docs/compressed-pointers.md (search snippet)
20. https://developer.apple.com/documentation/os/os_proc_available_memory
21. https://developer.apple.com/forums/thread/688973
22. https://cloud.tencent.com/developer/article/1383264
23. https://developer.apple.com/forums/thread/834805
24. https://developer.android.com/topic/performance/memory
25. https://medium.com/@suhail.ali/android-sqlite-insertions-performance-8f9cea05348f
26. https://svn.r-project.org/R/tags/R-4-6-1/src/nmath/rbinom.c
27. https://accserv.classe.cornell.edu/svn/packages/gsl/randist/binomial_tpe.c
28. https://statmath.wu.ac.at/papers/92-04-07.wh.abs.html
29. https://en.wikipedia.org/wiki/Le_Cam%27s_theorem
30. https://blog.acolyer.org/2018/01/30/a-sample-of-brilliance/
31. https://users.cs.utah.edu/~hari/teaching/bigdata/random123sc11.pdf
32. https://ideas.repec.org/a/wly/navlog/v26y1979i3p403-413.html
33. https://dart.dev/articles/dart-vm/numeric-computation
34. https://www.spa.gov.sa/en/N2210890 ; https://www.stats.gov.sa/documents/20117/1400941/Livestock+Statistics+2023+EN_0.pdf/068908eb-802b-6e4f-1daf-fe1ffeabf487?t=1734123531614
35. https://stats.gov.sa/documents/20117/2435281/Livestock+Statistics+2024+-+EN.pdf/8035d1ec-8565-16ab-e37a-4acc2d81212e
36. https://saudipedia.com/ar/كم-عدد-الإبل-في-السعودية؟
37. https://doaj.org/article/cf0cc8134f2542dbb791e62a0cf38371
38. https://agritrop.cirad.fr/550942
39. https://njap.org.ng/index.php/njap/article/download/412/360
40. https://www.helgilibrary.com/indicators/meat-camel-producing-animals-slaughtered
41. https://link.springer.com/doi/10.1007/s11250-018-1545-3
42. https://ejfa.me/index.php/journal/article/view/838
43. https://www.migrant-rights.org/2018/05/death-and-desolation-shepherds-and-farmworkers-in-saudi-arabia/
44. https://ajel.sa/local/krbsv4 ; https://www.mewa.gov.sa/ar/MediaCenter/News/Pages/News1062020.aspx
45. https://www.zawya.com/en/economy/gcc/saudi-arabia-launches-camel-passport-to-regulate-and-digitize-camel-sector-o9kq277g
46. https://camelicious.ae/pages/farm-tour
47. https://phys.org/news/2024-04-camels-cows-megafarms-camel-industrial.html
48. https://www.argaam.com/en/article/articledetail/id/1834390
49. https://www.worldpressphoto.org/collection/photo-contest/1996/manfred-linke/7
50. https://cgspace.cgiar.org/server/api/core/bitstreams/230aa52c-0e94-4488-a73d-c75670e39160/content ; https://link.springer.com/doi/10.1186/s13570-020-00176-z
