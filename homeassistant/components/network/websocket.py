"""The Network Configuration integration websocket commands."""
from __future__ import annotations

import voluptuous as vol

from homeassistant.components import websocket_api
from homeassistant.components.websocket_api.connection import ActiveConnection
from homeassistant.core import HomeAssistant, callback

from .const import (
    ATTR_ADAPTERS,
    ATTR_CONFIGURED_ADAPTERS,
    DOMAIN,
    NETWORK_CONFIG_SCHEMA,
)
from .network import Network


@callback
def async_register_websocket_commands(hass: HomeAssistant) -> None:
    """Register network websocket commands."""
    websocket_api.async_register_command(hass, websocket_network_adapters)
    websocket_api.async_register_command(hass, websocket_network_adapters_configure)


@websocket_api.require_admin
@websocket_api.websocket_command({vol.Required("type"): "network"})
@websocket_api.async_response
async def websocket_network_adapters(
    hass: HomeAssistant,
    connection: ActiveConnection,
    msg: dict,
) -> None:
    """Return network preferences."""
    network: Network = hass.data[DOMAIN]
    connection.send_result(
        msg["id"],
        {
            ATTR_ADAPTERS: network.adapters,
            ATTR_CONFIGURED_ADAPTERS: network.configured_adapters,
        },
    )


@websocket_api.require_admin
@websocket_api.websocket_command(
    {
        vol.Required("type"): "network/configure",
        vol.Required("config", default={}): NETWORK_CONFIG_SCHEMA,
    }
)
@websocket_api.async_response
async def websocket_network_adapters_configure(
    hass: HomeAssistant,
    connection: ActiveConnection,
    msg: dict,
) -> None:
    """Update network config."""
    network: Network = hass.data[DOMAIN]

    await network.async_reconfig(msg["config"])

    connection.send_result(
        msg["id"],
        {ATTR_CONFIGURED_ADAPTERS: network.configured_adapters},
    )
