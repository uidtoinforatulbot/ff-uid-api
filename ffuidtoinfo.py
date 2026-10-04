import os
import requests
from flask import Flask, request, jsonify

app = Flask(__name__)

SUPPORTED_REGIONS = {
    "BD": "Bangladesh",
    "IN": "India",
    "SG": "Singapore",
    "MY": "Malaysia",
    "ID": "Indonesia",
    "PK": "Pakistan",
    "MA": "Middle East / MENA",
    "BR": "Brazil",
    "TH": "Thailand",
    "VN": "Vietnam",
}

# IMPORTANT:
# এখানে শুধুমাত্র তোমার অনুমোদিত/বৈধ player lookup API-এর URL বসাবে।
# Render Environment Variable থেকে নেওয়া হবে।
UPSTREAM_API_URL = os.environ.get("PLAYER_LOOKUP_API_URL", "").strip()
UPSTREAM_API_KEY = os.environ.get("PLAYER_LOOKUP_API_KEY", "").strip()


def check_player_info(uid, requested_region=None):
    if not uid.isdigit():
        return {
            "error": "UID must contain only numbers"
        }, 400

    if requested_region:
        regions = [requested_region.upper()]
    else:
        regions = list(SUPPORTED_REGIONS.keys())

    if not UPSTREAM_API_URL:
        return {
            "error": "Player lookup API is not configured on the server."
        }, 503

    for region in regions:

        if region not in SUPPORTED_REGIONS:
            continue

        print(
            f"Checking UID={uid} REGION={region}",
            flush=True
        )

        params = {
            "uid": uid,
            "region": region
        }

        headers = {
            "Accept": "application/json",
            "User-Agent": "RED-TOUR-UID-Checker/1.0"
        }

        if UPSTREAM_API_KEY:
            headers["Authorization"] = f"Bearer {UPSTREAM_API_KEY}"

        try:
            response = requests.get(
                UPSTREAM_API_URL,
                params=params,
                headers=headers,
                timeout=10
            )

            content_type = response.headers.get(
                "content-type",
                ""
            )

            print(
                f"UPSTREAM STATUS {region}: {response.status_code}",
                flush=True
            )

            print(
                f"UPSTREAM CONTENT-TYPE {region}: {content_type}",
                flush=True
            )

            if response.status_code == 403:
                print(
                    f"UPSTREAM FORBIDDEN {region}",
                    flush=True
                )
                continue

            if response.status_code == 404:
                continue

            response.raise_for_status()

            try:
                data = response.json()
            except ValueError:
                print(
                    f"INVALID JSON RESPONSE {region}",
                    flush=True
                )
                continue

            nickname = (
                data.get("nickname")
                or data.get("name")
                or data.get("player_name")
            )

            if nickname:
                print(
                    f"PLAYER FOUND {region}: {nickname}",
                    flush=True
                )

                return {
                    "nickname": nickname,
                    "region_code": region,
                    "region_name": SUPPORTED_REGIONS[region]
                }, 200

        except requests.exceptions.Timeout:
            print(
                f"UPSTREAM TIMEOUT {region}",
                flush=True
            )

        except requests.exceptions.RequestException as exc:
            print(
                f"UPSTREAM ERROR {region}: {exc}",
                flush=True
            )

    return {
        "error": "Player information could not be retrieved from the configured lookup service."
    }, 502


@app.route("/", methods=["GET"])
def home():
    uid = request.args.get("uid", "").strip()
    region = request.args.get("region", "").strip()

    if not uid:
        return jsonify({
            "error": "UID parameter is required"
        }), 400

    result, status = check_player_info(
        uid,
        region or None
    )

    return jsonify(result), status


@app.route("/xp-opu", methods=["GET"])
def xp_opu():
    uid = request.args.get("uid", "").strip()
    region = request.args.get("region", "").strip()

    if not uid:
        return jsonify({
            "error": "UID parameter is required"
        }), 400

    result, status = check_player_info(
        uid,
        region or None
    )

    return jsonify(result), status


@app.route("/health", methods=["GET"])
def health():
    return jsonify({
        "status": "ok",
        "service": "Free Fire UID Checker"
    })


if __name__ == "__main__":
    port = int(os.environ.get("PORT", "10000"))

    print(
        f"Starting server on 0.0.0.0:{port}",
        flush=True
    )

    app.run(
        host="0.0.0.0",
        port=port
    )
