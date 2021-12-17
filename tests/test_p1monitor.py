"""Basic tests for the P1Monitor device."""
import asyncio
from unittest.mock import patch

import aiohttp
import pytest

from p1monitor import P1Monitor
from p1monitor.exceptions import P1MonitorConnectionError, P1MonitorError

from . import load_fixtures


@pytest.mark.asyncio
async def test__json_request(aresponses):
    """Test JSON response is handled correctly."""
    aresponses.add(
        "example.com",
        "/api/test",
        "GET",
        aresponses.Response(
            status=200,
            headers={"Content-Type": "application/json"},
            text='{"status": "ok"}',
        ),
    )
    async with aiohttp.ClientSession() as session:
        p1monitor = P1Monitor("example.com", session=session)
        await p1monitor.request("test")
        await p1monitor.close()


@pytest.mark.asyncio
async def test_internal_session(aresponses):
    """Test JSON response is handled correctly."""
    aresponses.add(
        "example.com",
        "/api/test",
        "GET",
        aresponses.Response(
            status=200,
            headers={"Content-Type": "application/json"},
            text='{"status": "ok"}',
        ),
    )
    async with P1Monitor("example.com") as p1monitor:
        await p1monitor.request("test")


@pytest.mark.asyncio
async def test_timeout(aresponses):
    """Test request timeout from P1 Monitor."""
    # Faking a timeout by sleeping
    async def reponse_handler(_):
        await asyncio.sleep(0.2)
        return aresponses.Response(
            body="Goodmorning!", text=load_fixtures("smartmeter.json")
        )

    aresponses.add("example.com", "/api/test", "GET", reponse_handler)

    async with aiohttp.ClientSession() as session:
        client = P1Monitor(host="example.com", session=session, request_timeout=0.1)
        with pytest.raises(P1MonitorConnectionError):
            assert await client.smartmeter()


@pytest.mark.asyncio
async def test_client_error():
    """Test request client error from P1 Monitor."""
    async with aiohttp.ClientSession() as session:
        client = P1Monitor(host="example.com", session=session)
        with patch.object(
            session, "request", side_effect=aiohttp.ClientError
        ), pytest.raises(P1MonitorConnectionError):
            assert await client.request("test")


@pytest.mark.asyncio
@pytest.mark.parametrize("status", [401, 403])
async def test_http_error401(aresponses, status):
    """Test HTTP 401 response handling."""
    aresponses.add(
        "example.com",
        "/api/v1/smartmeter",
        "GET",
        aresponses.Response(text="Give me energy!", status=status),
    )

    async with aiohttp.ClientSession() as session:
        client = P1Monitor(host="example.com", session=session)
        with pytest.raises(P1MonitorConnectionError):
            assert await client.request("test")


@pytest.mark.asyncio
async def test_http_error400(aresponses):
    """Test HTTP 404 response handling."""
    aresponses.add(
        "example.com",
        "/api/v1/smartmeter",
        "GET",
        aresponses.Response(text="Give me energy!", status=404),
    )

    async with aiohttp.ClientSession() as session:
        client = P1Monitor(host="example.com", session=session)
        with pytest.raises(P1MonitorError):
            assert await client.request("test")


@pytest.mark.asyncio
async def test_http_error500(aresponses):
    """Test HTTP 500 response handling."""
    aresponses.add(
        "example.com",
        "/api/v1/smartmeter",
        "GET",
        aresponses.Response(
            body=b'{"status":"nok"}',
            status=500,
        ),
    )

    async with aiohttp.ClientSession() as session:
        client = P1Monitor(host="example.com", session=session)
        with pytest.raises(P1MonitorError):
            assert await client.request("test")


@pytest.mark.asyncio
async def test_no_success(aresponses):
    """Test a message without a success message throws."""
    aresponses.add(
        "example.com",
        "/api/v1/smartmeter",
        "GET",
        aresponses.Response(
            status=200,
            text='{"message": "no success"}',
        ),
    )

    async with aiohttp.ClientSession() as session:
        client = P1Monitor(host="example.com", session=session)
        with pytest.raises(P1MonitorError):
            assert await client.request("test")
