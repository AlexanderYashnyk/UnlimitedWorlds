# Changelog

All notable changes to this project will be documented in this file.

This project follows Semantic Versioning (SemVer) and the changelog format is based on
"Keep a Changelog".

## [Unreleased]
### Added
- (nothing yet)

### Changed
- (nothing yet)

### Fixed
- (nothing yet)

### Removed
- (nothing yet)

## [0.1.0] - 2026-01-02
### Added
- Initial grid engine core: Grid/Tile, World, Agent, Action, tick().
- Smoke tests for basic movement and blocking.

### Changed
- Internal refactor: split core into modules (no public API changes).
- Formalized tick contract: implicit wait, last-write-wins, deterministic uid order.
- Added CollisionPolicy.BLOCK (swap blocked) + tests.
- Added system hooks (pre/resolve/post) + TickContext + tests.
- Added seeded RNG injection via world.rng + tests.
