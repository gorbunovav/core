"""Test the SiteSage Emonitor config flow."""
from unittest.mock import MagicMock, patch

from aioemonitor.monitor import EmonitorNetwork, EmonitorStatus
import aiohttp

from homeassistant import config_entries
from homeassistant.components.dhcp import HOSTNAME, IP_ADDRESS, MAC_ADDRESS
from homeassistant.components.emonitor.const import DOMAIN
from homeassistant.const import CONF_HOST

from tests.common import MockConfigEntry


def _mock_emonitor():
    return EmonitorStatus(
        MagicMock(), EmonitorNetwork("AABBCCDDEEFF", "1.2.3.4"), MagicMock()
    )


async def test_form(hass):
    """Test we get the form."""

    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )
    assert result["type"] == "form"
    assert result["errors"] == {}

    with patch(
        "homeassistant.components.emonitor.config_flow.Emonitor.async_get_status",
        return_value=_mock_emonitor(),
    ), patch(
        "homeassistant.components.emonitor.async_setup_entry",
        return_value=True,
    ) as mock_setup_entry:
        result2 = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            {
                "host": "1.2.3.4",
            },
        )
        await hass.async_block_till_done()

    assert result2["type"] == "create_entry"
    assert result2["title"] == "Emonitor DDEEFF"
    assert result2["data"] == {
        "host": "1.2.3.4",
    }
    assert len(mock_setup_entry.mock_calls) == 1


async def test_form_unknown_error(hass):
    """Test we handle unknown error."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )

    with patch(
        "homeassistant.components.emonitor.config_flow.Emonitor.async_get_status",
        side_effect=Exception,
    ):
        result2 = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            {
                "host": "1.2.3.4",
            },
        )

    assert result2["type"] == "form"
    assert result2["errors"] == {"base": "unknown"}


async def test_form_cannot_connect(hass):
    """Test we handle cannot connect error."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )

    with patch(
        "homeassistant.components.emonitor.config_flow.Emonitor.async_get_status",
        side_effect=aiohttp.ClientError,
    ):
        result2 = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            {
                "host": "1.2.3.4",
            },
        )

    assert result2["type"] == "form"
    assert result2["errors"] == {CONF_HOST: "cannot_connect"}


async def test_dhcp_can_confirm(hass):
    """Test DHCP discovery flow can confirm right away."""

    with patch(
        "homeassistant.components.emonitor.config_flow.Emonitor.async_get_status",
        return_value=_mock_emonitor(),
    ):
        result = await hass.config_entries.flow.async_init(
            DOMAIN,
            context={"source": config_entries.SOURCE_DHCP},
            data={
                HOSTNAME: "emonitor",
                IP_ADDRESS: "1.2.3.4",
                MAC_ADDRESS: "aa:bb:cc:dd:ee:ff",
            },
        )
        await hass.async_block_till_done()

    assert result["type"] == "form"
    assert result["step_id"] == "confirm"
    assert result["description_placeholders"] == {
        "host": "1.2.3.4",
        "name": "Emonitor DDEEFF",
    }

    with patch(
        "homeassistant.components.emonitor.async_setup_entry",
        return_value=True,
    ) as mock_setup_entry:
        result2 = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            {},
        )
        await hass.async_block_till_done()

    assert result2["type"] == "create_entry"
    assert result2["title"] == "Emonitor DDEEFF"
    assert result2["data"] == {
        "host": "1.2.3.4",
    }
    assert len(mock_setup_entry.mock_calls) == 1


async def test_dhcp_fails_to_connect(hass):
    """Test DHCP discovery flow that fails to connect."""

    with patch(
        "homeassistant.components.emonitor.config_flow.Emonitor.async_get_status",
        side_effect=aiohttp.ClientError,
    ):
        result = await hass.config_entries.flow.async_init(
            DOMAIN,
            context={"source": config_entries.SOURCE_DHCP},
            data={
                HOSTNAME: "emonitor",
                IP_ADDRESS: "1.2.3.4",
                MAC_ADDRESS: "aa:bb:cc:dd:ee:ff",
            },
        )
        await hass.async_block_till_done()

    assert result["type"] == "form"
    assert result["step_id"] == "user"


async def test_dhcp_already_exists(hass):
    """Test DHCP discovery flow that fails to connect."""

    entry = MockConfigEntry(
        domain=DOMAIN,
        data={CONF_HOST: "1.2.3.4"},
        unique_id="aa:bb:cc:dd:ee:ff",
    )
    entry.add_to_hass(hass)

    with patch(
        "homeassistant.components.emonitor.config_flow.Emonitor.async_get_status",
        return_value=_mock_emonitor(),
    ):
        result = await hass.config_entries.flow.async_init(
            DOMAIN,
            context={"source": config_entries.SOURCE_DHCP},
            data={
                HOSTNAME: "emonitor",
                IP_ADDRESS: "1.2.3.4",
                MAC_ADDRESS: "aa:bb:cc:dd:ee:ff",
            },
        )
        await hass.async_block_till_done()

    assert result["type"] == "abort"
    assert result["reason"] == "already_configured"


async def test_user_unique_id_already_exists(hass):
    """Test creating an entry where the unique_id already exists."""

    entry = MockConfigEntry(
        domain=DOMAIN,
        data={CONF_HOST: "1.2.3.4"},
        unique_id="aa:bb:cc:dd:ee:ff",
    )
    entry.add_to_hass(hass)

    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )
    assert result["type"] == "form"
    assert result["errors"] == {}

    with patch(
        "homeassistant.components.emonitor.config_flow.Emonitor.async_get_status",
        return_value=_mock_emonitor(),
    ), patch(
        "homeassistant.components.emonitor.async_setup_entry",
        return_value=True,
    ):
        result2 = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            {
                "host": "1.2.3.4",
            },
        )
        await hass.async_block_till_done()

    assert result2["type"] == "abort"
    assert result2["reason"] == "already_configured"
