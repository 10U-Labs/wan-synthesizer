---
name: the-spa-signs-in-with-a-google-account
description: "The map at 10ulabs.com/wan-synthesizer/ opens on a Google sign-in card for a 10ulabs.com account, sends the ID token as a bearer to api.10ulabs.com, ends a session through one endSession on sign-out, at the token's exp, or after 15 idle minutes, and is served with 10ulabs.com's security headers and its own meta CSP; the API side of the login lives in api.10ulabs.com"
metadata:
  type: project
---

# The SPA signs in with a Google account

Since September 2026 (GitHub issue #176) the map at
`www.10ulabs.com/wan-synthesizer/` asks for a Google sign-in and sends
the ID token as `Authorization: Bearer` on every fetch of
`https://api.10ulabs.com`. The page is static files, so the login is
enforced at the API, not the page; which accounts are admitted, the
authorizer, the API key and its rotation, the CORS answers and the
stage's throttle all live in `10U-Labs/api.10ulabs.com` and its
memories since the API migration.

**How to apply:**

- `app.js` spells the OAuth client
  `846587722064-qjou8en4tk96n12ii3rgnpjshnbqovok.apps.googleusercontent.com`
  (created in Google Cloud Console with `https://www.10ulabs.com` as an
  authorized JavaScript origin) and the hosted domain `10ulabs.com`;
  the API's authorizer must spell the same client. The name Google
  shows in its chooser is the Cloud project's OAuth consent-screen
  branding, not anything in this tree.
- `index.html` opens on `#sign-in` and keeps the header and map inside
  `<div id="app" hidden>` until a credential arrives; a 403 note says
  "not authorized" rather than naming the domain, since a domain
  account off the API's list is refused the same way.
  `test/www/spa/pre_deployment/unit/test_login.py` holds all of it.
- A session ends through one function, `endSession(note)`: a `401` or
  `403` from the API, the `Sign out` control (which also calls
  `google.accounts.id.disableAutoSelect()`), a timer set to the `exp`
  decoded from the token, and an inactivity timer of
  `INACTIVITY_LIMIT_MINUTES` (15, NIST SP 800-171r3 03.01.11 and
  03.13.09) restarted by every event in `ACTIVITY_EVENTS`.
  `test_session.py` holds each path by reading the source, since
  nothing runs the SPA in CI.
- The distribution that serves the page is `10U-Labs/10ulabs.com`'s
  website distribution, which sends HSTS for a year with subdomains,
  `X-Content-Type-Options: nosniff`, `Referrer-Policy:
  strict-origin-when-cross-origin` and `X-Frame-Options: DENY`; a
  header the SPA needs is declared there, not in a `<meta>` tag.
  `test/www/spa/post_deployment/e2e/test_headers.py` reads them off
  the served page after every deploy, and holds the served page to
  the tree's byte for byte, which the deploy's `aws cloudfront wait
  invalidation-completed` makes sound.
- The page's own `Content-Security-Policy` is a `<meta>` in
  `index.html`: scripts from `'self'` and `https://accounts.google.com`
  (Google's `gsi/client` carries no stable hash, so it is admitted by
  origin), connections to `'self'`, `https://api.10ulabs.com` and
  `https://accounts.google.com`, and nothing else.
  `test_content_security_policy.py` holds each directive to exactly
  its sources. A new origin the page needs is added to the directive,
  the test's `POLICY`, and the API's CORS answers where it is a fetch.
