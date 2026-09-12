---
name: the-api-admits-a-google-account-or-the-seed-key
description: "Every API operation but a preflight sits behind the routing stack's Lambda authorizer, which admits a Google ID token for a 10ulabs.com account or the API key CI reads from SSM"
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
  - [A Google account is admitted by its hosted domain](#a-google-account-is-admitted-by-its-hosted-domain)
  - [CI presents the key the routing stack generated](#ci-presents-the-key-the-routing-stack-generated)
  - [A route the map fetches answers a preflight](#a-route-the-map-fetches-answers-a-preflight)
  - [Nothing here is a Cognito pool or a Lambda layer](#nothing-here-is-a-cognito-pool-or-a-lambda-layer)

## Overview

Since September 2026 (issue 176) the map at `www.10ulabs.com/wan-synthesizer/` asks for a Google sign-in, and `api.10ulabs.com/wan-synthesizer` answers only a request carrying a bearer token the authorizer in `src/api/common/routing/lambdas/authorizer.py` admits. The page is static files, so the login is enforced at the API, not the page; a client-side gate alone would have left every tenant's WAN one `curl` away. The authorizer is declared in `authorizer.tf` and attached through `components.securitySchemes.bearer` and a top-level `security` in `src/www/api/openapi.json`, with `security: []` on every `options` operation because a browser sends a preflight with no token.

## Conventions

### A Google account is admitted by its hosted domain

The 10ulabs.com mail is hosted on Google Workspace, so the accounts that exist are `@10ulabs.com` Google accounts and no user store is kept here. The page uses Google Identity Services with the OAuth client `846587722064-qjou8en4tk96n12ii3rgnpjshnbqovok.apps.googleusercontent.com` (created in Google Cloud Console with `https://www.10ulabs.com` as an authorized JavaScript origin; a second one would need the same). The authorizer sends the ID token to `oauth2.googleapis.com/tokeninfo`, which vouches for the signature, and then holds the claims to that client (`aud`), a Google issuer, a verified address, and `hd == 10ulabs.com`. A token that fails the first three is a 401; an account off the domain is a 403 (`Deny`), so the page can tell the user which happened. `app.js` and `authorizer.tf` both spell the client and the domain, and `test/www/spa/pre_deployment/unit/test_login.py` fails when they disagree.

### CI presents the key the routing stack generated

`random_password.api_key` is kept as the SecureString parameter `/wan-synthesizer/api-key`, and the authorizer reads it from SSM on each cold verdict rather than caching it, because API Gateway remembers a verdict for five minutes per token. The `seeding` and `e2e-tests` jobs in `seed.yml` assume the OIDC role, read the parameter with `aws ssm get-parameter --with-decryption`, mask it, and export `WAN_SYNTHESIZER_API_KEY`, which `scripts/seed.py` sends as `Authorization: Bearer` on every request; without the variable it sends no header and the API says 401. `test_every_job_that_reaches_the_api_reads_the_key_the_authorizer_holds` in `test/scripts/seed/pre_deployment/integration/test_contracts.py` holds the two jobs to that. The routing post-deployment tests read the key through the `api_key` fixture and prove the CloudFront path forwards the header by getting a 200 with it and a 401 without.

### A route the map fetches answers a preflight

A fetch carrying `Authorization` is preflighted, so every route `app.js` fetches has an `options` mock in the spec allowing that header, and `x-amazon-apigateway-gateway-responses` gives the gateway's own 4XX and 5XX answers the CORS origin so the browser can read a 401. A new fetch in `app.js` without an `options` on its route fails `test_every_route_the_map_fetches_answers_the_browsers_preflight`.

### Nothing here is a Cognito pool or a Lambda layer

A Cognito user pool federated to Google was the alternative, and was not taken: it would need a Google client secret kept somewhere, a hosted UI, and a trigger to restrict the domain, for one hosted domain. Verifying the JWT locally would need `cryptography` shipped as a layer per [third-party-code-ships-as-a-layer](third-party-code-ships-as-a-layer.md); the tokeninfo call keeps the authorizer on the standard library and boto3.
