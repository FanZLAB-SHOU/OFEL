# World time & weather — independent preview

Open `/OFEL/demos/world-weather/` on GitHub Pages, or serve the OFEL checkout with `python3 -m http.server 8765` and open `/demos/world-weather/` locally. The page is intentionally absent from the main navigation and sitemap and marked `noindex`.

- Eight preset city clocks run from the device clock with native `Intl` IANA time zones, including daylight saving and fractional offsets.
- Search for a city or select coordinates on the map. Search and current modelled weather use Open-Meteo. No API key or location permission is required.
- Only the selected location requests weather. Cache entries expire after ten minutes; the auto-refresh timer makes no requests while the page is hidden. Manual Refresh bypasses the cache. Errors show missing data rather than invented readings. Known city clocks continue to run when the weather service is unavailable; arbitrary points need the API to resolve their time zone.
- Map zoom, pan and reset work without a mapping library or external map tiles. Keyboard: Tab to cities; Enter/Space selects a marker; focus the map and use +/−, arrows or Home. City cards provide an alternative to map markers on narrow screens.
- No changes to the site’s shared navigation, content builders or other pages are required. The preview has its own CSS and JavaScript.

## Sources and attribution

- Weather API: https://open-meteo.com/en/docs — current conditions are weather-model estimates, not live station observations. Unix timestamps are formatted with the returned IANA zone; offsets are not hard-coded. Weather data attribution and city-search attribution remain visible in the footer.
- Geocoding: https://open-meteo.com/en/docs/geocoding-api — Open-Meteo / GeoNames.
- Free API terms: https://open-meteo.com/en/terms — for non-commercial use, with published request limits. Reassess the service plan if the deployment’s usage changes.
- Natural Earth land geometry (public domain): https://www.naturalearthdata.com/about/terms-of-use/
- Source geometry: https://raw.githubusercontent.com/nvkelso/natural-earth-vector/master/geojson/ne_110m_land.geojson — saved locally as `land.geojson` with non-geometric feature properties removed. Land outlines only; no country borders are displayed.

## Verification

`node test-model.cjs` checks time-zone boundaries, DST transitions, date rollover, half/quarter-hour offsets, projection round trips, missing weather values, session caching and API failures. `node test-controller.cjs` runs the actual controller in a small DOM/network harness to check city selection, stale responses, offline fallback, refresh, search, custom pins, map reset and visibility-aware updates. `node --check app.js` checks controller syntax. Test actual forecast/geocoding endpoints and CORS separately. Browser visual/gesture verification depends on browser access in the session.
