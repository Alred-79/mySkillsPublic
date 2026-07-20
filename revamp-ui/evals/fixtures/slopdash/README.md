# slopdash (before-state fixture)

A single-file "analytics dashboard" landing + overview, `index.html`, built deliberately slop-ridden.
It is the BEFORE state for the revamp-ui evals: the revamp runs against it, and scoring is the constraint floor plus intensity-vs-contract, never a golden output.

## Seeded slop (the detector should count these; the revamp should remove them)

Every pattern here is named in `../../../gates.md`'s slop list:

- Centered hero + exactly 3 feature cards + a big gradient CTA (the canonical template).
- Default indigo/violet `#6366f1`/`#8b5cf6` everywhere (background, buttons, stat numbers).
- Unmodified system-font stack as the entire type system (no type decision).
- Emoji as feature icons (rocket / chart / lock).
- Evenly-spaced everything, uniform `box-shadow` on every surface.
- Generic glassmorphism card grid (`backdrop-filter: blur`).
- Gratuitous gradient text on the `h1`.
- Placeholder copy left in ("Your headline here").

## Load-bearing (a correct revamp MUST preserve these)

This is the anti-greenfield control. Restyle freely, but do not drop or break:

- **Content / metrics:** the four stats (12,480 active users, $48.2k revenue, 3.1% churn, 1,204 signups) and the four data-table rows (Organic / Paid / Referral / Direct with their numbers).
- **Working functionality:** the date-range `<select>` filter updates the note; it must still work after the revamp.
- **Routes / nav:** the four nav links (`/`, `/reports`, `/settings`, `/help`) and `/signup` on the CTA.
- **SEO surface:** the `<title>`, the meta description, and the heading outline (one `h1`, then `h2` "This month"). Keep a single `h1` and a sane heading order.

Deleting the filter or the table, changing the metric values, breaking a route, or flattening the heading semantics is a floor failure regardless of how good the new pixels look.
