"""http2_config configuration."""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any, TYPE_CHECKING
from .enums import HTTPProtocol, PushPriority
from .models import ConnectionStats

if TYPE_CHECKING:
    from .service import PushResource


@dataclass
class MultiplexConfig:
    """HTTP/2 multiplexing configuration."""

    max_concurrent_streams: int = 100
    initial_window_size: int = 65535
    max_frame_size: int = 16384
    max_header_list_size: int = 8192
    enable_connect_protocol: bool = False

    def validate(self) -> list[str]:
        """Validate configuration values."""
        errors: list[str] = []
        if self.max_concurrent_streams < 1:
            errors.append("max_concurrent_streams must be >= 1")
        if self.max_concurrent_streams > 2147483647:
            errors.append("max_concurrent_streams exceeds max value")
        if self.initial_window_size < 0:
            errors.append("initial_window_size must be >= 0")
        if self.initial_window_size > 2147483647:
            errors.append("initial_window_size exceeds max value")
        if self.max_frame_size < 16384:
            errors.append("max_frame_size must be >= 16384")
        if self.max_frame_size > 16777215:
            errors.append("max_frame_size exceeds max value")
        if self.max_header_list_size < 0:
            errors.append("max_header_list_size must be >= 0")
        return errors

@dataclass
class HTTP3Config:
    """HTTP/3 (QUIC) specific configuration."""

    max_idle_timeout_ms: int = 30000
    max_udp_payload_size: int = 65527
    initial_max_data: int = 10485760
    initial_max_stream_data_bidi_local: int = 1048576
    initial_max_stream_data_bidi_remote: int = 1048576
    initial_max_stream_data_uni: int = 1048576
    initial_max_streams_bidi: int = 100
    initial_max_streams_uni: int = 100
    disable_active_migration: bool = False

    def validate(self) -> list[str]:
        """Validate HTTP/3 configuration."""
        errors: list[str] = []
        if self.max_idle_timeout_ms < 0:
            errors.append("max_idle_timeout_ms must be >= 0")
        if self.max_udp_payload_size < 1200:
            errors.append("max_udp_payload_size must be >= 1200")
        if self.initial_max_data < 0:
            errors.append("initial_max_data must be >= 0")
        return errors

@dataclass
class HTTP2Config:
    """Complete HTTP/2 configuration."""

    enabled: bool = True
    multiplex: MultiplexConfig = field(default_factory=MultiplexConfig)
    server_push_enabled: bool = True
    push_resources: list[Any] = field(default_factory=list)  # list[PushResource]
    preload_hints: bool = True
    prioritization_enabled: bool = True

    def add_push_resource(
        self,
        path: str,
        content_type: str,
        priority: PushPriority = PushPriority.NORMAL,
    ) -> None:
        """Add a resource for server push."""
        from .service import PushResource
        resource = PushResource(path=path, content_type=content_type, priority=priority)
        self.push_resources.append(resource)

    def get_link_headers(self) -> list[str]:
        """Get Link headers for all push resources."""
        return [r.to_link_header() for r in self.push_resources]

    def validate(self) -> list[str]:
        """Validate complete configuration."""
        return self.multiplex.validate()

@dataclass
class ProtocolConfig:
    """Combined protocol configuration."""

    http2: HTTP2Config = field(default_factory=HTTP2Config)
    http3: HTTP3Config = field(default_factory=HTTP3Config)
    preferred_protocol: HTTPProtocol = HTTPProtocol.HTTP_2
    fallback_enabled: bool = True
    alpn_protocols: list[str] = field(
        default_factory=lambda: ["h2", "http/1.1"]
    )

    def get_supported_protocols(self) -> list[HTTPProtocol]:
        """Get list of supported protocols."""
        protocols: list[HTTPProtocol] = []
        if self.http2.enabled:
            protocols.append(HTTPProtocol.HTTP_2)
        if "h3" in self.alpn_protocols:
            protocols.append(HTTPProtocol.HTTP_3)
        if self.fallback_enabled:
            protocols.append(HTTPProtocol.HTTP_1_1)
        return protocols

    def validate(self) -> list[str]:
        """Validate all protocol configurations."""
        errors: list[str] = []
        errors.extend(self.http2.validate())
        errors.extend(self.http3.validate())
        if not self.alpn_protocols:
            errors.append("alpn_protocols cannot be empty")
        return errors
