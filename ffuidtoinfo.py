import sys
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
    "MA": "Middle East (MENA)",
    "BR": "Brazil",
    "TH": "Thailand",
    "VN": "Vietnam"
}


def check_player_info(target_id, requested_region=None):

    if requested_region:
        regions_to_test = [requested_region.upper()]
    else:
        regions_to_test = [
            "BD",
            "IN",
            "SG",
            "MA",
            "PK",
            "BR"
        ]

    diagnostics = []

    for r_code in regions_to_test:

        if r_code not in SUPPORTED_REGIONS:
            diagnostics.append({
                "region": r_code,
                "status": "UNSUPPORTED_REGION"
            })
            continue

        print(
            f"Checking UID={target_id} REGION={r_code}",
            flush=True
        )

        cookies = {
            "source": "mb",
            "region": r_code,
            "language": "en" if r_code != "MA" else "ar"
        }

        headers = {
            "Accept-Language": "en-US,en;q=0.9",
            "Accept": "application/json",
            "Content-Type": "application/json",
            "User-Agent": (
                "Mozilla/5.0 (Linux; Android 11) "
                "AppleWebKit/537.36 "
                "(KHTML, like Gecko) "
                "Chrome/107.0.0.0 Mobile Safari/537.36"
            )
        }

        json_data = {
            "app_id": 100067,
            "login_id": target_id,
            "app_server_id": 0
        }

        try:

            response = requests.post(
                "https://shop2game.com/api/auth/player_id_login",
                cookies=cookies,
                headers=headers,
                json=json_data,
                timeout=8
            )

            print(
                f"UPSTREAM STATUS {r_code}: "
                f"{response.status_code}",
                flush=True
            )

            content_type = response.headers.get(
                "content-type",
                ""
            )

            print(
                f"UPSTREAM CONTENT-TYPE {r_code}: "
                f"{content_type}",
                flush=True
            )

            # JSON response পরীক্ষা
            try:
                data = response.json()
            except ValueError:

                diagnostics.append({
                    "region": r_code,
                    "status_code": response.status_code,
                    "result": "NON_JSON_RESPONSE"
                })

                print(
                    f"UPSTREAM {r_code}: NON JSON RESPONSE",
                    flush=True
                )

                continue

            # nickname পাওয়া গেলে success
            nickname = data.get("nickname")

            if response.status_code == 200 and nickname:

                print(
                    f"PLAYER FOUND: {nickname} "
                    f"REGION={r_code}",
                    flush=True
                )

                return {
                    "nickname": nickname,
                    "region_code": r_code,
                    "region_name": SUPPORTED_REGIONS[r_code]
                }

            # Diagnostic information
            diagnostics.append({
                "region": r_code,
                "status_code": response.status_code,
                "has_nickname": bool(nickname),
                "response_keys": list(data.keys())
            })

            print(
                f"NO PLAYER RESULT {r_code}: "
                f"status={response.status_code}, "
                f"keys={list(data.keys())}",
                flush=True
            )

        except requests.exceptions.Timeout:

            diagnostics.append({
                "region": r_code,
                "status": "TIMEOUT"
            })

            print(
                f"TIMEOUT: {r_code}",
                flush=True
            )

        except requests.exceptions.RequestException as error:

            diagnostics.append({
                "region": r_code,
                "status": "REQUEST_ERROR",
                "message": str(error)
            })

            print(
                f"REQUEST ERROR {r_code}: {error}",
                flush=True
            )

    return {
        "error": "PLAYER LOOKUP FAILED",
        "diagnostics": diagnostics
    }


@app.route("/", methods=["GET"])
def home_region_info():

    uid = request.args.get("uid")
    region = request.args.get("region")

    if not uid:
        return jsonify({
            "error": "UID parameter is required"
        }), 400

    result = check_player_info(
        uid,
        region
    )

    if "error" in result:
        return jsonify(result), 502

    return jsonify(result), 200


@app.route("/xp-opu", methods=["GET"])
def get_region_info():

    uid = request.args.get("uid")
    region = request.args.get("region")

    if not uid:
        return jsonify({
            "error": "UID parameter is required"
        }), 400

    result = check_player_info(
        uid,
        region
    )

    if "error" in result:
        return jsonify(result), 502

    return jsonify(result), 200


@app.route("/health", methods=["GET"])
def health():

    return jsonify({
        "status": "ok",
        "service": "Free Fire UID Checker API"
    })


if __name__ == "__main__":

    port = int(
        sys.argv[1]
    ) if len(sys.argv) > 1 else 5000

    app.run(
        host="0.0.0.0",
        port=port
    )
