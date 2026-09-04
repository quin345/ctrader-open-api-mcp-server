"""Live end-to-end smoke test: connect, auth, fetch trader info. Prints no secrets."""
import asyncio
import os
import sys

sys.path.insert(0, "src")

from dotenv import load_dotenv

load_dotenv()


async def main() -> None:
    from ctrader_mcp_server.config import load_config
    from ctrader_mcp_server.oauth import OAuthManager
    from ctrader_mcp_server.session import CTraderSession

    cfg = load_config()
    oauth = OAuthManager(cfg.client_id, cfg.client_secret, cfg.redirect_uri, cfg.token_path)
    session = CTraderSession(cfg, oauth)

    await session.connect()
    # give the Twisted client a moment to establish TLS
    for _ in range(50):
        if session.state.connected:
            break
        await asyncio.sleep(0.1)
    print("connected:", session.state.connected)

    await session.authenticate_application()
    print("app authenticated:", session.state.application_authenticated)

    accounts = await session.discover_accounts()
    print("accounts discovered:", len(accounts))
    for a in accounts:
        print("  account id:", a.get("ctidTraderAccountId"), "login:", a.get("traderLogin"))

    target = cfg.account_id or str(accounts[0]["ctidTraderAccountId"])
    await session.authenticate_account(target)
    print("account authenticated:", session.state.account_authenticated, target)

    version = await session.get_protocol_version()
    print("protocol version:", version)

    # symbols count as a cheap authenticated data call
    symbols = await session.get_symbols()
    print("symbols:", len(symbols), "first:", symbols[0]["symbolName"] if symbols else None)

    await session.disconnect()
    print("LIVE TEST PASSED")


asyncio.run(main())
