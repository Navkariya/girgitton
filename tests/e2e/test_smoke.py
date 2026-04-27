"""End-to-end smoke testlar — loyiha modullari tashkilotini tekshirish (v3.1)."""

from __future__ import annotations

import importlib

import pytest


@pytest.mark.e2e
def test_top_level_package() -> None:
    pkg = importlib.import_module("girgitton")
    assert pkg.__version__.startswith("3.")


@pytest.mark.e2e
def test_core_modules_import() -> None:
    for name in (
        "girgitton.core.config",
        "girgitton.core.constants",
        "girgitton.core.errors",
        "girgitton.core.logging_setup",
        "girgitton.core.models",
        "girgitton.shared.crypto",
        "girgitton.shared.media",
        "girgitton.shared.repositories",
    ):
        importlib.import_module(name)


@pytest.mark.e2e
def test_storage_modules_import() -> None:
    for name in (
        "girgitton.storage.base",
        "girgitton.storage.factory",
        "girgitton.storage.json_store",
        "girgitton.storage.redis_store",
    ):
        importlib.import_module(name)


@pytest.mark.e2e
def test_bot_modules_import() -> None:
    for name in (
        "girgitton.bot.client",
        "girgitton.bot.handlers",
        "girgitton.bot.handlers.help",
        "girgitton.bot.handlers.enrollment",
        "girgitton.bot.handlers.status",
        "girgitton.bot.handlers.access",
        "girgitton.bot.api.server",
        "girgitton.bot.api.routes",
        "girgitton.bot.api.middleware",
        "girgitton.bot.api.schemas",
    ):
        importlib.import_module(name)


@pytest.mark.e2e
def test_app_modules_import() -> None:
    for name in (
        "girgitton.app.api_client",
        "girgitton.app.config_store",
        "girgitton.app.connect_flow",
        "girgitton.app.upload.batch",
        "girgitton.app.upload.engine",
        "girgitton.app.upload.worker_pool",
        "girgitton.app.upload.rate_limit",
    ):
        importlib.import_module(name)
