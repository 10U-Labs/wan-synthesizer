import hmac
import json
import os
import urllib.error
import urllib.parse
import urllib.request
from typing import Any

import boto3

TOKENINFO = "https://oauth2.googleapis.com/tokeninfo"
ISSUERS = frozenset({"accounts.google.com", "https://accounts.google.com"})
API_KEY_PRINCIPAL = "api-key"


class Unauthorized(Exception):
    def __init__(self) -> None:
        super().__init__("Unauthorized")


def _parameter(name: str) -> str:
    parameter = boto3.client("ssm", region_name="us-east-2").get_parameter(
        Name=os.environ[name], WithDecryption=True
    )
    return str(parameter["Parameter"]["Value"])


def _authorized_accounts() -> frozenset[str]:
    listed = _parameter("AUTHORIZED_ACCOUNTS_PARAMETER").split(",")
    return frozenset(account.strip().lower() for account in listed if account.strip())


def _bearer(event: dict[str, Any]) -> str:
    scheme, _, token = str(event.get("authorizationToken", "")).partition(" ")
    if scheme != "Bearer" or not token:
        raise Unauthorized()
    return token


def _claims(token: str) -> dict[str, Any]:
    request = urllib.request.Request(f"{TOKENINFO}?{urllib.parse.urlencode({'id_token': token})}")
    try:
        with urllib.request.urlopen(request, timeout=5) as response:
            claims: dict[str, Any] = json.loads(response.read())
    except urllib.error.HTTPError as refusal:
        raise Unauthorized() from refusal
    if claims.get("aud") != os.environ["GOOGLE_CLIENT_ID"] or claims.get("iss") not in ISSUERS:
        raise Unauthorized()
    return claims


def _verdict(event: dict[str, Any], principal: str, effect: str) -> dict[str, Any]:
    api, stage, *_ = str(event["methodArn"]).split("/")
    return {
        "principalId": principal,
        "policyDocument": {
            "Version": "2012-10-17",
            "Statement": [{
                "Action": "execute-api:Invoke",
                "Effect": effect,
                "Resource": f"{api}/{stage}/*",
            }],
        },
    }


def lambda_handler(event: dict[str, Any], _context: Any) -> dict[str, Any]:
    token = _bearer(event)
    if hmac.compare_digest(token.encode(), _parameter("API_KEY_PARAMETER").encode()):
        return _verdict(event, API_KEY_PRINCIPAL, "Allow")
    claims = _claims(token)
    email = str(claims.get("email", ""))
    admitted = (
        claims.get("hd") == os.environ["HOSTED_DOMAIN"]
        and claims.get("email_verified") == "true"
        and email.lower() in _authorized_accounts()
    )
    return _verdict(event, email, "Allow" if admitted else "Deny")
