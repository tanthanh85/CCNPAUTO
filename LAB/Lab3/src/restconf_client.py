"""Basic and resilient RESTCONF clients for Lab 3."""

import random
import time
from urllib.parse import quote

import requests
import urllib3


INTERFACES_PATH = "/restconf/data/Cisco-IOS-XE-interfaces-oper:interfaces"
INTERFACE_PATH = INTERFACES_PATH + "/interface={}"


class APIError(RuntimeError):
    def __init__(self, status_code, message):
        self.status_code = status_code
        super().__init__(message)


class AuthenticationError(APIError):
    pass


class AuthorizationError(APIError):
    pass


class NotFoundError(APIError):
    pass


class RESTCONFClient:
    def __init__(self, settings):
        self.settings = settings
        self.session = requests.Session()
        self.session.auth = (settings.username, settings.password)
        self.session.headers.update({"Accept": "application/yang-data+json"})
        self.session.verify = settings.verify_tls

        if not settings.verify_tls:
            urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

    def get_response(self, path, headers=None):
        return self.session.get(
            self.settings.base_url + path,
            headers=headers,
            timeout=(self.settings.connect_timeout, self.settings.read_timeout),
        )

    def get_json(self, path):
        response = self.get_response(path)
        self._raise_for_status(response, path)

        try:
            return response.json()
        except requests.JSONDecodeError as error:
            raise APIError(response.status_code, "The response was not valid JSON") from error

    def get_interface(self, interface_name):
        encoded_name = quote(interface_name, safe="")
        return self.get_json(INTERFACE_PATH.format(encoded_name))

    @staticmethod
    def _raise_for_status(response, path):
        if response.status_code == 401:
            raise AuthenticationError(401, "Authentication failed")
        if response.status_code == 403:
            raise AuthorizationError(403, "Access is forbidden")
        if response.status_code == 404:
            raise NotFoundError(404, f"Resource not found: {path}")
        if response.status_code >= 400:
            raise APIError(response.status_code, f"HTTP {response.status_code}: {path}")


class ResilientRESTCONFClient(RESTCONFClient):
    def __init__(self, settings):
        super().__init__(settings)
        self.attempts = 0
        self.retries = 0
        self.status_codes = {}

    def get_json(self, path):
        attempts_allowed = self.settings.max_retries + 1

        for attempt in range(1, attempts_allowed + 1):
            self.attempts += 1

            try:
                response = self.get_response(path)
            except (requests.Timeout, requests.ConnectionError) as error:
                if attempt == attempts_allowed:
                    raise APIError(0, f"Connection failed after {attempt} attempts") from error
                self._wait_before_retry(attempt, None)
                continue

            status = response.status_code
            self.status_codes[status] = self.status_codes.get(status, 0) + 1

            if status == 200:
                try:
                    return response.json()
                except requests.JSONDecodeError as error:
                    raise APIError(200, "The response was not valid JSON") from error

            if status in [401, 403, 404]:
                self._raise_for_status(response, path)

            if status == 429 or status >= 500:
                if attempt == attempts_allowed:
                    raise APIError(status, f"HTTP {status}: retry limit reached")
                self._wait_before_retry(attempt, response)
                continue

            self._raise_for_status(response, path)

        raise APIError(0, "Request failed")

    def _wait_before_retry(self, attempt, response):
        wait_time = None

        if response is not None:
            retry_after = response.headers.get("Retry-After", "")
            if retry_after.isdigit():
                wait_time = min(int(retry_after), 60)

        if wait_time is None:
            wait_time = 0.5 * (2 ** (attempt - 1)) + random.uniform(0, 0.25)

        self.retries += 1
        print(f"Retrying in {wait_time:.2f} seconds...")
        time.sleep(wait_time)
