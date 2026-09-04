"""
cTrader MCP Server - Open API Integration for Model Context Protocol

This package provides a comprehensive MCP server implementation for the
cTrader Open API, enabling natural language trading operations through
AI assistants. It uses the cTrader Twisted/protobuf client for transport.

Key Features:
- OAuth authorization-code flow with refresh-token rotation
- Account discovery and account authentication
- Market orders, limit orders, stop orders, and amendments
- Position management and closing
- Historical trendbars and tick data
- Live spot-price and trendbar subscriptions
- Trader state, cash flow, margin, and dynamic leverage
- Protocol diagnostics
"""

__version__ = "0.1.0"
__author__ = "cTrader MCP Server Contributors"
__license__ = "MIT"
__description__ = "cTrader Open API integration for Model Context Protocol (MCP)"

__all__ = ["__version__"]
