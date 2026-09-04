"""
Foundation tests — verify the ctrader-open-api transport layer is importable.

The protobuf session layer depends on this package; if it is missing the
server builds but every live connection fails. Kept as a fast, no-network
smoke test so dependency drift is caught at test time.
"""

import ctrader_open_api  # noqa: F401


def test_ctrader_open_api_importable():
    """The cTrader transport package must be importable."""
    import ctrader_open_api

    assert hasattr(ctrader_open_api, "__path__")


def test_protobuf_messages_available():
    """The generated protobuf message modules must load."""
    from ctrader_open_api.messages.OpenApiMessages_pb2 import (  # noqa: F401
        ProtoOAAccountAuthReq,
        ProtoOAApplicationAuthReq,
        ProtoOANewOrderReq,
    )

    assert ProtoOANewOrderReq is not None
