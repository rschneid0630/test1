# Holiday Lights — Falcon Controller Reference

Starter overview for an outdoor pixel display driven by a Falcon controller.

## Pixel Lights (Outdoor)

**Standard choice:** WS2811 12V bullet pixels, IP68 rated.

- **12V vs 5V:** Use 12V outdoors — less voltage drop over long runs, fewer power injection points.
- **Spacing:** 4" pitch is most common for outlines/matrices; 6" for trees/mega-trees.
- **Form factor:** Bullet (most common, hides well), square nodes (for P10-style matrices), or strip (for wrapped props).
- **Reputable sources:** Wally's Lights, Your Pixel Store (YPS), BoscoeP, Ray Wu (AliExpress), HolidayCoro, Pixels Plus. Look for xConnect-compatible pigtails to standardize cabling.
- **Count:** Strings of 50 or 100. Standard color order is BGR or RGB — confirm before bulk-ordering.

## Receivers for Falcon Controllers

Falcon controllers (F16V3, F16V4, F48) support **differential / long-range output** over Cat5e/Cat6, which is the key advantage. Common receiver pairings:

- **Falcon F16V3R / F16V4-NS** — 16 differential ports, matches the main controller.
- **Falcon F4V3 / F4V4** — 4-port receiver, good for smaller prop clusters in the yard.
- **HinksPix Long Range Receivers** — also compatible if using DMX/sACN.
- **SanDevices E682 / E6804** — alternative if you want Ethernet-fed satellites instead of differential.

Place receivers near prop clusters so the **short, lossy pixel data run** stays under ~50 ft, and feed them with **long Cat5e** from the main controller.

## Cabling & Power

### Data
- Controller → Receiver: **shielded Cat5e/Cat6** for differential. Up to ~300 ft reliably.
- Receiver → Pixels: 3-conductor (V+, GND, Data). Keep under 50 ft.
- Use **xConnect** (3-pin waterproof) as your standard — saves enormous time year over year.

### Power
- **PSU:** Meanwell LRS-350-12 (12V, 29A) is the workhorse. One per ~700–1000 pixels with margin.
- **Power injection:** Every ~50 pixels on 12V (every ~25 on 5V). End-injection minimum for 100-count strings.
- **Wire gauge:** 18 AWG for short pigtails, 14 AWG for trunk runs, 12 AWG for PSU-to-distribution.
- Use a **fused distribution board** (CG-1500 or similar) at each PSU.

### Enclosures
- Outdoor PSU + controller in a vented, weather-resistant enclosure (DIYLightAnimation sells kits, or use a sealed plastic toolbox with passive vents on the bottom).
- All connectors face down, drip loops on every cable.
