from src.architrave import GatewayArchitrave

_gateway_instance = None


def get_gateway():
    global _gateway_instance
    if _gateway_instance is None:
        _gateway_instance = GatewayArchitrave()
    return _gateway_instance
