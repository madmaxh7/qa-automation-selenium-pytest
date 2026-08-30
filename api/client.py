"""Thin API client for the betting app. Owns transport details so tests never touch raw HTTP.

Every call is an Allure step with the request and response attached, so a failure shows
the exact exchange. All endpoints go through one private `_request`, because the timeout
is a safety property: a forgotten one does not fail loudly, it hangs the suite on a
stalled connection.
"""
import allure
import requests

import config

DEFAULT_TIMEOUT = 10


def _attach(response: requests.Response) -> requests.Response:
    """Attach the request payload (if any) and the response body to the current Allure step."""
    if response.request.body:
        allure.attach(
            response.request.body,
            name="request body",
            attachment_type=allure.attachment_type.JSON,
        )
    allure.attach(
        response.text,
        name=f"response {response.status_code}",
        attachment_type=allure.attachment_type.JSON,
    )
    return response


class BettingApiClient:
    def __init__(self) -> None:
        self._session = requests.Session()
        self._session.headers.update({"x-user-id": config.USER_ID})
        self._base = config.BASE_URL

    def _request(self, method: str, path: str, **kwargs) -> requests.Response:
        """Send one request and report it. The single place that owns base URL and timeout."""
        response = self._session.request(
            method, f"{self._base}{path}", timeout=DEFAULT_TIMEOUT, **kwargs
        )
        return _attach(response)

    @allure.step("GET /api/matches")
    def get_matches(self) -> requests.Response:
        return self._request("GET", "/api/matches")

    @allure.step("GET /api/balance")
    def get_balance(self) -> requests.Response:
        return self._request("GET", "/api/balance")

    @allure.step("POST /api/place-bet: {selection} on {match_id} for stake {stake}")
    def place_bet(self, match_id: str, selection: str, stake) -> requests.Response:
        payload = {"matchId": match_id, "selection": selection, "stake": stake}
        return self._request("POST", "/api/place-bet", json=payload)

    @allure.step("POST /api/reset-balance")
    def reset_balance(self) -> requests.Response:
        return self._request("POST", "/api/reset-balance")
