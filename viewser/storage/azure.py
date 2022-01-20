
def connection_string(
        account_name: str,
        account_key: str,
        protocol: str = "https",
        endpoint_suffix: str = "core.windows.net") -> str:
    return ";".join([
            f"DefaultEndpointsProtocol={protocol}",
            f"EndpointSuffix={endpoint_suffix}",
            f"AccountName={account_name}",
            f"AccountKey={account_key}",
        ])
