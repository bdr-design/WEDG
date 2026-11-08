# مراح (Marah)

لعبة واقعية لملاك الإبل: العزبة، والسوق، والتلقيح، ومزاين الإبل.
A realistic camel-owner game for iOS, Android and the web.

- Architecture: [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md)
- Decisions: [docs/adr/](docs/adr/)

## Develop

Flutter 3.47.8 (Dart 3.13). The repo is a Dart pub workspace.

```sh
flutter pub get                                   # whole workspace
(cd packages/marah_domain && dart test)           # rules
(cd packages/marah_data && dart test)             # save format
(cd apps/marah && flutter test)                   # app
(cd packages/marah_domain && dart run marah_domain:simulate 10 4)   # 10-year simulation
```
