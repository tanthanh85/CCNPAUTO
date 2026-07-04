import pytest

from fmc_client import FMCClient, FMCError
from fmc_lab import lab_settings


def test_lab_settings_accepts_owned_canonical_network(monkeypatch):
    monkeypatch.setenv("LAB_OBJECT_NAME", "LAB15-BRANCH")
    monkeypatch.setenv("LAB_OBJECT_VALUE", "198.18.15.0/24")
    assert lab_settings()[:2] == ("LAB15-BRANCH", "198.18.15.0/24")


def test_lab_settings_rejects_foreign_name(monkeypatch):
    monkeypatch.setenv("LAB_OBJECT_NAME", "PRODUCTION-NETWORK")
    with pytest.raises(FMCError):
        lab_settings()


def test_safe_url_rejects_other_origin(monkeypatch):
    monkeypatch.setenv("FMC_HOST", "fmc.lab.local")
    monkeypatch.setenv("FMC_USERNAME", "learner")
    monkeypatch.setenv("FMC_PASSWORD", "secret")
    client = FMCClient()
    with pytest.raises(FMCError):
        client._safe_url("https://attacker.example/api/next")

