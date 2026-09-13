---
name: the-api-admits-a-google-account-or-the-seed-key
description: "Every API operation but a preflight sits behind the routing stack's Lambda authorizer, which admits a Google ID token for a 10ulabs.com account named in /wan-synthesizer/authorized-accounts to every operation, or the API key CI reads from SSM to every read and the writes seed.py makes"
metadata: 
  node_type: memory
  type: project
  originSessionId: dffa3dbf-1048-4f91-a52f-2f1eba1888a3
  modified: 2026-09-12T16:18:56.209Z
---

# The API admits a Google account or the seed key

## Table of Contents

- [Overview](#overview)
- [Conventions](#conventions)
  - [A Google account is admitted by its hosted domain and the authorized list](#a-google-account-is-admitted-by-its-hosted-domain-and-the-authorized-list)
  - [The page opens on the sign-in screen and nothing else](#the-page-opens-on-the-sign-in-screen-and-nothing-else)
  - [CI presents the key the routing stack generated](#ci-presents-the-key-the-routing-stack-generated)
  - [The key is granted every read and the writes the seed makes](#the-key-is-granted-every-read-and-the-writes-the-seed-makes)
  - [A route the map fetches answers a preflight](#a-route-the-map-fetches-answers-a-preflight)
  - [Nothing here is a Cognito pool or a Lambda layer](#nothing-here-is-a-cognito-pool-or-a-lambda-layer)

## Overview

Since September 2026 (issue 176) the map at `www.10ulabs.com/wan-synthesizer/` asks for a Google sign-in, and `api.10ulabs.com/wan-synthesizer` answers only a request carrying a bearer token the authorizer in `src/api/common/routing/lambdas/authorizer.py` admits. The page is static files, so the login is enforced at the API, not the page; a client-side gate alone would have left every tenant's WAN one `curl` away. The authorizer is declared in `authorizer.tf` and attached through `components.securitySchemes.bearer` and a top-level `security` in `src/www/api/openapi.json`, with `security: []` on every `options` operation because a browser sends a preflight with no token.

The precedent is in `../10ulabs.com` history, not its tree: `1bf50323 Add Google authentication to simulation/soc` (December 2025, deleted in `18320684` with the SOC simulator) had the same shape — Google Sign-In in the page, the token in `sessionStorage`, the Lambda asking `tokeninfo`. It differed in taking the client ID from a GitHub secret, in checking `aud` alone with no hosted domain, and in verifying inside one handler rather than at the gateway.

## Conventions

### A Google account is admitted by its hosted domain and the authorized list

The 10ulabs.com mail is hosted on Google Workspace, so the accounts that exist are `@10ulabs.com` Google accounts and no user store is kept here. Which of them may use this system is the StringList parameter `/wan-synthesizer/authorized-accounts` (GitHub issue #194, September 2026), whose value the routing deploy passes as `TF_VAR_authorized_accounts` from the repository variable `WAN_SYNTHESIZER_AUTHORIZED_ACCOUNTS`, comma-separated; adding, reviewing (quarterly) and removing an account is `gh variable set WAN_SYNTHESIZER_AUTHORIZED_ACCOUNTS` followed by a routing deploy, and the authorizer reads the list on each cold verdict beside the key. A verified domain account off the list is a 403 like one off the domain, so the page's 403 note says "not authorized" rather than naming the domain. The page uses Google Identity Services with the OAuth client `846587722064-qjou8en4tk96n12ii3rgnpjshnbqovok.apps.googleusercontent.com` (created in Google Cloud Console with `https://www.10ulabs.com` as an authorized JavaScript origin; a second one would need the same). The authorizer sends the ID token to `oauth2.googleapis.com/tokeninfo`, which vouches for the signature, and then holds the claims to that client (`aud`), a Google issuer, a verified address, `hd == 10ulabs.com`, and `email` on the list. A token that fails the first three is a 401; an account off the domain or off the list is a 403 (`Deny`), so the page can tell the user which happened. `app.js` and `authorizer.tf` both spell the client and the domain, and `test/www/spa/pre_deployment/unit/test_login.py` fails when they disagree.

### The page opens on the sign-in screen and nothing else

`index.html` opens on `#sign-in` and keeps the header and map inside `<div id="app" hidden>` until `showApp()` reveals them after a credential arrives, as the SOC simulator did; the first cut drew the map under a translucent card and was sent back. The screen is a centred white card over a dark ground with two glows, the Google button rendered as a 300px pill, and no One Tap `prompt()`, which put a bubble beside the card. The name Google shows in its chooser is the OAuth consent screen's *App name* in the Cloud project numbered `846587722064` (Google Auth Platform → Branding), not anything in this tree; it said "SoC Simulator" until renamed. `test_login.py` holds `#sign-in` to being visible and `#map` and `#tenants` to a hidden ancestor.

### CI presents the key the routing stack generated

`random_password.api_key` is kept as the SecureString parameter `/wan-synthesizer/api-key`, and the authorizer reads it from SSM on each cold verdict rather than caching it, because API Gateway remembers a verdict for five minutes per token. The `seeding` and `e2e-tests` jobs in `seed.yml` assume the OIDC role, read the parameter with `aws ssm get-parameter --with-decryption`, mask it, and export `WAN_SYNTHESIZER_API_KEY`, which `scripts/seed.py` sends as `Authorization: Bearer` on every request; without the variable it sends no header and the API says 401. `test_every_job_that_reaches_the_api_reads_the_key_the_authorizer_holds` in `test/scripts/seed/pre_deployment/integration/test_contracts.py` holds the two jobs to that. The routing post-deployment tests read the key through the `api_key` fixture and prove the CloudFront path forwards the header by getting a 200 with it and a 401 without.

### The key is granted every read and the writes the seed makes

An admitted Google account's verdict covers `{stage}/*`; the key's verdict (GitHub issue #195, September 2026) lists `GET/wan-synthesizer/*` and then one `execute-api:Invoke` resource per row of `SEED_WRITES` in `authorizer.py`, the table of every `PUT`, `POST` and `DELETE` that `scripts/seed.py` makes with a path parameter spelled `*`. A write the table lacks is a 403 to CI, so a route the seed starts calling is added to the table in the same commit, and `test_the_api_key_verdict_writes_exactly_what_the_seed_writes` runs the seed against a recorder and fails when the two drift either way. Every read is granted because `e2e-tests` and `wait-for-every-wan` read the published collections with the same key and reading is CI's task; `DELETE /carriers/{carrier}` and `DELETE /providers/regions` are what the key cannot do, and `test_the_key_is_refused_the_delete_of_a_carrier` asks the live gateway. The verdict lists every resource at once rather than only the one asked for because the gateway caches it per token for five minutes and applies it to every later request.

### A route the map fetches answers a preflight

A fetch carrying `Authorization` is preflighted, so every route `app.js` fetches has an `options` mock in the spec allowing that header, and `x-amazon-apigateway-gateway-responses` gives the gateway's own 4XX and 5XX answers the CORS origin so the browser can read a 401. A new fetch in `app.js` without an `options` on its route fails `test_every_route_the_map_fetches_answers_the_browsers_preflight`. Every `Access-Control-Allow-Origin` — the seven mocks, the two gateway responses, and `_HEADERS` in each of the six handlers — names `https://www.10ulabs.com` and nothing wider (GitHub issue #196, September 2026): the apex `10ulabs.com` is a 301 to `www`, so that is the page's one origin, spelled once as `SPA_ORIGIN` in `lib/python/test_handler_contracts`. `test_cors.py` in the routing unit tests walks the spec for every value of the header, `ReaderContract` and the merge and prune handler tests read it off a response, and the routing post-deployment tests read it off a live preflight, a keyed GET and a 401. A second origin is a commit that adds it in every one of those places.

### Nothing here is a Cognito pool or a Lambda layer

A Cognito user pool federated to Google was the alternative, and was not taken: it would need a Google client secret kept somewhere, a hosted UI, and a trigger to restrict the domain, for one hosted domain. Verifying the JWT locally would need `cryptography` shipped as a layer per [third-party-code-ships-as-a-layer](third-party-code-ships-as-a-layer.md); the tokeninfo call keeps the authorizer on the standard library and boto3.

## The stage admits twenty requests a second and a burst of forty

Since 2026-09-13 (GitHub issue #199) `aws_api_gateway_method_settings.throttle`
in the routing stack holds `*/*` of the `prod` stage to
`throttling_rate_limit = 20` and `throttling_burst_limit = 40`; a caller
past that gets `429` until the bucket refills. That is the limit on
unsuccessful logon attempts NIST SP 800-171r3 03.01.08 asks for, since
a refused token is re-evaluated on every request and the account default
of 10,000 a second would let a caller try tokens as fast as the gateway
accepts them.

**How to apply:** anything in CI that talks to the API stays under that
rate; `seed.py` writes sequentially and `wait-for-every-wan` polls one
tenant every twenty seconds. A load test against the live API is a
change to those two numbers first.
