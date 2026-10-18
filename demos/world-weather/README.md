# World time & weather — independent preview

Open `/OFEL/demos/world-weather/` on GitHub Pages, or serve the OFEL checkout with `python3 -m http.server 8765` and open `/demos/world-weather/` locally. The page is intentionally absent from the main navigation and sitemap and marked `noindex`.

- City clocks run from the device clock with native `Intl` IANA time zones, including daylight saving and fractional offsets. Eight example cities appear on the first visit; every card can be removed. Select a search result (or a map point with a resolved time zone), then use **Add to city clocks**. Duplicate locations are not added again.
- The editable city list and its map pins persist in browser `localStorage`, including an intentionally empty list. It is personal to that browser, with no account or server storage. If browser storage is unavailable, edits still work for the current visit and the save message explains the limitation. Deleting a clock leaves its current weather available until another location is selected.
- Search for a city or select coordinates on the map. Search and current modelled weather use Open-Meteo. No API key or location permission is required.
- Search results throughout Taiwan use the site's administrative label `Taiwan, China`; API coordinates and IANA time zones are preserved.
- Hong Kong and Macao searches accept common spellings (`hongkong`, `Hong Kong`, `Macao`, `Macau`) and simplified/traditional Chinese names. The query sent to the geocoder uses its recognized English name. HK/MO results display `Hong Kong, China` / `Macao, China` even when the geocoder omits a country name; other places with similar names keep their API region.
- Major Taiwan city searches also accept Hanyu Pinyin, established English spellings and simplified/traditional Chinese names: Taipei/Taibei, New Taipei/Xinbei, Taichung/Taizhong, Kaohsiung/Gaoxiong, Keelung/Jilong, Hsinchu/Xinzhu, Chiayi/Jiayi, Changhua/Zhanghua, Pingtung/Pingdong, Hualien/Hualian, Taitung/Taidong, plus Tainan, Taoyuan, Miaoli, Nantou and Yilan. Known aliases ignore case, accents, spaces and hyphens, and accept city suffixes (`市`, `shi`, `City`). They query the API's matching geographic code to avoid unrelated places with the same name. Labels still use the site's `Taiwan, China` convention; alternate spellings share the same location and saved-clock identity. Other searches pass through unchanged.
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

`node test-model.cjs` checks time-zone boundaries, DST transitions, date rollover, half/quarter-hour offsets, projection round trips, missing weather values, caching, API failures, city-list restoration and unavailable storage. `node test-controller.cjs` runs the actual controller in a small DOM/network harness to check city selection, stale responses, offline fallback, refresh, search aliases, custom pins, map reset, visibility-aware updates, add/remove actions, duplicate prevention, reload persistence and empty lists. `node --check app.js` checks controller syntax. Test actual forecast/geocoding endpoints and CORS separately. Browser visual/gesture verification depends on browser access in the session.
