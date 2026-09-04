# Asset Manifest

## Images
| File | Source comp | Purpose |
|---|---|---|
| `verdent-design/images/hero-map-background.png` | `verdent-design/stage1/comp-2-gece-navigasyon.png` | Night-mode Istanbul map background (full-screen, no text) |

## Icons
| File | Source | Purpose |
|---|---|---|
| `frontend/src/icons/index.tsx` | hand-authored SVG components from `comp-2` + `comp-1` | Pin, swap, bus, metro, walk, car, sparkle, send, close, globe, clock, route, wallet, weather icons |
| `frontend/public/favicon.svg` | hand-authored | App favicon + logo mark |

## Logo
| File | Background | Purpose |
|---|---|---|
| `frontend/src/icons/index.tsx` (`IconLogo`) | vector, `currentColor`-independent | Header wordmark mark; scales cleanly, no raster logo needed |

## Notes
- The map background is the only raster asset on the primary screen; all other visuals are CSS/SVG.
- intentionally skipped: raster logo variants (logo is hand-authored SVG), OG share image (not needed before publish), below-the-fold thumbnails (single-screen app).
