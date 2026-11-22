"""Early TLS ClientHello Server Name Indication (SNI) snooper and pre-wake dispatcher.

Governed by ADR-010 (TP-08), BRD-008 (BRU-008-01..02), FDD-008 (§1.1..1.2),
and Epic 008 Story 8.1 (WBS 9.1 / AC-8.1.1..2).
"""

from __future__ import annotations

import struct
import threading
import time
from typing import Any, Dict, Optional, Tuple


def parse_tls_sni(raw_bytes: bytes) -> Optional[str]:
    """Parse a binary TLS ClientHello frame and extract the SNI hostname (AC-8.1.1).

    Executes in <= 5.0 ms. Returns None defensively for non-TLS, truncated,
    or plain HTTP payloads without raising exceptions.
    """
    if not raw_bytes or len(raw_bytes) < 9:
        return None

    try:
        # Check TLS Record Header: 0x16 is Handshake
        content_type = raw_bytes[0]
        if content_type != 0x16:
            return None

        # Protocol version check (TLS 1.0 - 1.3: 0x0301 .. 0x0304)
        major_ver = raw_bytes[1]
        minor_ver = raw_bytes[2]
        if major_ver != 0x03 or minor_ver not in (0x01, 0x02, 0x03, 0x04):
            return None

        record_len = struct.unpack("!H", raw_bytes[3:5])[0]
        if len(raw_bytes) < 5 + record_len:
            # Truncated record
            return None

        # Handshake Header: 0x01 is ClientHello
        handshake_type = raw_bytes[5]
        if handshake_type != 0x01:
            return None

        handshake_len = struct.unpack("!I", b"\x00" + raw_bytes[6:9])[0]
        if len(raw_bytes) < 9 + handshake_len:
            return None

        # ClientHello fields:
        # Client Version (2 bytes) + Random (32 bytes) = 34 bytes
        offset = 9 + 34
        if offset >= len(raw_bytes):
            return None

        # Session ID
        session_id_len = raw_bytes[offset]
        offset += 1 + session_id_len
        if offset + 2 > len(raw_bytes):
            return None

        # Cipher Suites
        cipher_suites_len = struct.unpack("!H", raw_bytes[offset : offset + 2])[0]
        offset += 2 + cipher_suites_len
        if offset + 1 > len(raw_bytes):
            return None

        # Compression Methods
        compression_len = raw_bytes[offset]
        offset += 1 + compression_len
        if offset + 2 > len(raw_bytes):
            return None

        # Extensions
        extensions_len = struct.unpack("!H", raw_bytes[offset : offset + 2])[0]
        offset += 2
        ext_end = offset + extensions_len

        while offset + 4 <= ext_end and offset + 4 <= len(raw_bytes):
            ext_type = struct.unpack("!H", raw_bytes[offset : offset + 2])[0]
            ext_len = struct.unpack("!H", raw_bytes[offset + 2 : offset + 4])[0]
            offset += 4

            if ext_type == 0x0000:  # server_name extension (SNI)
                if offset + ext_len > len(raw_bytes):
                    return None
                ext_data = raw_bytes[offset : offset + ext_len]
                if len(ext_data) < 5:
                    return None
                # Server name list length (2 bytes), name type (1 byte), name len (2 bytes)
                name_type = ext_data[2]
                if name_type == 0x00:  # host_name
                    name_len = struct.unpack("!H", ext_data[3:5])[0]
                    if len(ext_data) >= 5 + name_len:
                        return ext_data[5 : 5 + name_len].decode("utf-8")
                return None

            offset += ext_len

    except Exception:
        return None

    return None


def build_test_client_hello(sni_hostname: str) -> bytes:
    """Build a valid binary TLS 1.2/1.3 ClientHello frame containing the SNI extension."""
    host_bytes = sni_hostname.encode("utf-8")
    server_name_ext_data = (
        struct.pack("!H", len(host_bytes) + 3)  # server_name_list length
        + b"\x00"                               # name_type: host_name
        + struct.pack("!H", len(host_bytes))    # host_name length
        + host_bytes
    )

    sni_extension = struct.pack("!HH", 0x0000, len(server_name_ext_data)) + server_name_ext_data
    extensions_block = struct.pack("!H", len(sni_extension)) + sni_extension

    client_version = b"\x03\x03"  # TLS 1.2
    random_bytes = b"\xaa" * 32
    session_id = b"\x00"          # session_id_len = 0
    cipher_suites = struct.pack("!H", 2) + b"\xc0\x2f"  # TLS_ECDHE_RSA_WITH_AES_128_GCM_SHA256
    compression_methods = b"\x01\x00"                   # null compression

    client_hello_body = (
        client_version
        + random_bytes
        + session_id
        + cipher_suites
        + compression_methods
        + extensions_block
    )

    handshake_header = b"\x01" + struct.pack("!I", len(client_hello_body))[1:]  # 3 bytes len
    handshake_payload = handshake_header + client_hello_body

    record_header = b"\x16\x03\x01" + struct.pack("!H", len(handshake_payload))
    return record_header + handshake_payload


class TLSSnooper:
    """Asynchronous TLS ClientHello snooper and predictive pre-wake dispatcher."""

    def __init__(
        self,
        pool_manager: Any,
        tenant_vm_map: Optional[Dict[str, str]] = None,
    ) -> None:
        self.pool_manager = pool_manager
        self.tenant_vm_map = tenant_vm_map or {}
        self._lock = threading.Lock()

    def snoop_and_pre_wake(self, raw_payload: bytes) -> Tuple[Optional[str], bool, float]:
        """Snoop initial TCP packet, extract SNI, and dispatch pre-wake (AC-8.1.1, AC-8.1.2)."""
        t0 = time.perf_counter()
        sni_host = parse_tls_sni(raw_payload)
        latency_ms = (time.perf_counter() - t0) * 1000.0

        if not sni_host:
            return None, False, latency_ms

        wake_dispatched = False
        with self._lock:
            if sni_host in self.tenant_vm_map:
                vm_name = self.tenant_vm_map[sni_host]
                # Dispatch non-blocking background wake/promotion
                try:
                    if hasattr(self.pool_manager, "promote_cold_to_warm"):
                        # Promote cold instance if currently cold
                        instance = self.pool_manager._guests.get(vm_name)
                        if instance and instance.state.value == "ColdSaved":
                            self.pool_manager.promote_cold_to_warm(vm_name)
                            wake_dispatched = True
                        elif instance:
                            wake_dispatched = True
                except Exception:
                    wake_dispatched = False

        return sni_host, wake_dispatched, latency_ms
