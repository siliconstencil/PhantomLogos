from pydantic import BaseModel, Field


class MCPServerConfig(BaseModel):
    command: str
    args: list[str] = Field(default_factory=list)
    env: dict[str, str] = Field(default_factory=dict)
    timeout: int = 30
    enabled: bool = True


class MCPRuntimeConfig(BaseModel):
    mcpServers: dict[str, MCPServerConfig] = Field(default_factory=dict)  # noqa: N815
