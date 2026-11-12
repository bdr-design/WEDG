# The 3D prototype as an iPhone app

A test harness, not the game: it shows `design/prototype3d` (the three.js
prototype) inside an iPhone app, so the owner can try it on a phone, full
screen and landscape only, with the frame meter (`#fps`) on. The game itself
is `apps/marah`.

- **How it works:** a small HTTP server on the loopback address serves the
  bundled files to a WKWebView. Module scripts do not load from `file://`
  URLs, and `NSAllowsLocalNetworking` lets the web view reach it.
- **The bundle:** `assemble.py` copies the prototype into `assets/web/`, which
  is not committed, and compiles the rules engine for its worker (it needs
  `dart`). It includes the terrain, the models in
  `design/prototype3d/models/` and three.js r170, with the import map
  rewritten from the CDN to the local copy. Only the web fonts come from the
  network.
- **The game's save:** the page's rules engine (`design/prototype3d/engine.js`,
  in a Web Worker) keeps its save as files in the app's Documents folder
  through the same server (`GET /save`, `PUT` and `DELETE /save/KEY`, the
  three keys `marah.save`, `.prev` and `.broken` only, 64 MB at most), each
  write whole and then renamed into place. A random key for each launch, in
  the page's address, must come with every request. The page's own storage
  would not last: its origin, which holds the port, changes every launch.
- **Performance:** the same as Safari on that phone. WKWebView uses Safari's
  engine.

## Building

`.github/workflows/ios-proto.yml` builds it on a macOS runner, on a push that
touches the prototype or this app, or by hand from the Actions tab. The IPA is
the run's artifact.

- **Signed:** when the repository has these secrets (Settings > Secrets and
  variables > Actions):
  - `IOS_P12_BASE64`: the certificate and its private key (`.p12`), base64.
  - `IOS_P12_PASSWORD`: the `.p12`'s password.
  - `IOS_PROFILE_BASE64`: the provisioning profile, base64.
- **What comes from the profile:** the bundle ID (a wildcard profile gets
  `…marahproto`), the team and the export method (development, ad-hoc,
  app-store or enterprise). The run's summary lists them.
- **Unsigned:** without the secrets, the IPA is unsigned, to sign and install
  with your own Apple ID (for example with Sideloadly).

Locally (Linux works for everything but the iOS build):

```
python3 tool/proto_app/assemble.py      # THREE_DIR=<unpacked three@0.170.0> skips the npm download
cd tool/proto_app && flutter test
```
