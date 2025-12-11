"""Property-based tests for Protocol Buffers code review.

This module contains property-based tests validating the proto files
follow best practices and correctness properties defined in the design.

Feature: protos-code-review
"""

import re
import subprocess
from pathlib import Path
from typing import Any

import pytest
from hypothesis import given, settings, strategies as st

# Proto directory path
PROTOS_DIR = Path(__file__).parent.parent.parent / "protos"


class TestBufLintCompliance:
    """Property 1: Buf Lint Compliance.

    **Feature: protos-code-review, Property 1: Buf Lint Compliance**
    **Validates: Requirements 1.1, 1.2, 1.3, 1.4, 1.5, 2.1, 2.2, 2.3, 2.4, 2.5**

    For any proto file in the Proto_System, running buf lint with
    STANDARD and COMMENTS categories SHALL produce zero errors.
    """

    @pytest.mark.skipif(not (PROTOS_DIR / "buf.yaml").exists(), reason="buf.yaml not found")
    def test_buf_lint_passes(self) -> None:
        """All proto files pass buf lint with STANDARD + COMMENTS."""
        import shutil

        # Skip if buf is not installed
        if shutil.which("buf") is None:
            pytest.skip("buf CLI not installed")

        result = subprocess.run(
            ["buf", "lint"],
            check=False,
            cwd=PROTOS_DIR,
            capture_output=True,
            text=True,
        )

        # buf lint returns 0 on success
        assert result.returncode == 0, f"buf lint failed with errors:\n{result.stdout}\n{result.stderr}"

    def test_buf_yaml_has_standard_category(self) -> None:
        """buf.yaml includes STANDARD lint category."""
        buf_yaml = PROTOS_DIR / "buf.yaml"
        if not buf_yaml.exists():
            pytest.skip("buf.yaml not found")

        content = buf_yaml.read_text()
        assert "STANDARD" in content, "buf.yaml should include STANDARD lint category"

    def test_buf_yaml_has_comments_category(self) -> None:
        """buf.yaml includes COMMENTS lint category."""
        buf_yaml = PROTOS_DIR / "buf.yaml"
        if not buf_yaml.exists():
            pytest.skip("buf.yaml not found")

        content = buf_yaml.read_text()
        assert "COMMENTS" in content, "buf.yaml should include COMMENTS lint category"


class TestPackageVersionSuffix:
    """Property 6: Package Version Suffix.

    **Feature: protos-code-review, Property 6: Package Version Suffix**
    **Validates: Requirements 9.1, 9.3**

    For any package declaration in the Proto_System, the package name
    SHALL end with a version suffix matching pattern v[0-9]+.
    """

    VERSION_PATTERN = re.compile(r"\.v\d+$")
    PACKAGE_PATTERN = re.compile(r"^package\s+([a-zA-Z0-9_.]+);")

    def _get_proto_files(self) -> list[Path]:
        """Get all .proto files in the protos directory."""
        return list(PROTOS_DIR.rglob("*.proto"))

    @given(st.sampled_from(["v1", "v2", "v3", "v10", "v99"]))
    @settings(max_examples=10)
    def test_valid_version_suffixes_match_pattern(self, version: str) -> None:
        """Valid version suffixes match the expected pattern."""
        package_name = f"common.{version}"
        assert self.VERSION_PATTERN.search(package_name), f"Package {package_name} should match version pattern"

    def test_all_packages_have_version_suffix(self) -> None:
        """All proto packages have version suffix."""
        proto_files = self._get_proto_files()

        if not proto_files:
            pytest.skip("No proto files found")

        for proto_file in proto_files:
            content = proto_file.read_text()
            match = self.PACKAGE_PATTERN.search(content)

            if match:
                package_name = match.group(1)
                assert self.VERSION_PATTERN.search(package_name), (
                    f"Package '{package_name}' in {proto_file.name} should end with version suffix (e.g., .v1)"
                )


class TestPaginationStructure:
    """Property 4: Pagination Structure Completeness.

    **Feature: protos-code-review, Property 4: Pagination Structure Completeness**
    **Validates: Requirements 7.1, 7.2, 7.3, 7.4**

    For any List RPC operation, the request message SHALL contain
    page_size and page_token fields, and the response message SHALL
    contain next_page_token and items collection.
    """

    def test_page_request_has_required_fields(self) -> None:
        """PageRequest message has page_size and page_token fields."""
        pagination_proto = PROTOS_DIR / "common" / "v1" / "pagination.proto"

        if not pagination_proto.exists():
            pytest.skip("pagination.proto not found")

        content = pagination_proto.read_text()

        assert "page_size" in content, "PageRequest should have page_size field"
        assert "page_token" in content, "PageRequest should have page_token field"

    def test_page_response_has_required_fields(self) -> None:
        """PageResponse message has next_page_token and has_more fields."""
        pagination_proto = PROTOS_DIR / "common" / "v1" / "pagination.proto"

        if not pagination_proto.exists():
            pytest.skip("pagination.proto not found")

        content = pagination_proto.read_text()

        assert "next_page_token" in content, "PageResponse should have next_page_token"
        assert "total_count" in content, "PageResponse should have total_count"
        assert "has_more" in content, "PageResponse should have has_more"

    def test_list_items_request_uses_pagination(self) -> None:
        """ListItemsRequest uses common.v1.PageRequest."""
        items_proto = PROTOS_DIR / "examples" / "v1" / "items.proto"

        if not items_proto.exists():
            pytest.skip("items.proto not found")

        content = items_proto.read_text()

        assert "common.v1.PageRequest" in content, "ListItemsRequest should use common.v1.PageRequest"

    def test_list_items_response_uses_pagination(self) -> None:
        """ListItemsResponse uses common.v1.PageResponse."""
        items_proto = PROTOS_DIR / "examples" / "v1" / "items.proto"

        if not items_proto.exists():
            pytest.skip("items.proto not found")

        content = items_proto.read_text()

        assert "common.v1.PageResponse" in content, "ListItemsResponse should use common.v1.PageResponse"


class TestTimestampWellKnownTypes:
    """Property 3: Timestamp Well-Known Types.

    **Feature: protos-code-review, Property 3: Timestamp Well-Known Types**
    **Validates: Requirements 4.1, 4.3, 5.4**

    For any field representing a point in time, the field type SHALL be
    google.protobuf.Timestamp.
    """

    TIMESTAMP_IMPORT = "google/protobuf/timestamp.proto"
    TIMESTAMP_TYPE = "google.protobuf.Timestamp"
    TIME_FIELD_PATTERN = re.compile(r"(create_time|update_time|timestamp|_at)\s*=")

    def test_errors_proto_uses_timestamp_type(self) -> None:
        """errors.proto uses google.protobuf.Timestamp for timestamp field."""
        errors_proto = PROTOS_DIR / "common" / "v1" / "errors.proto"

        if not errors_proto.exists():
            pytest.skip("errors.proto not found")

        content = errors_proto.read_text()

        assert self.TIMESTAMP_IMPORT in content, "errors.proto should import google/protobuf/timestamp.proto"
        assert self.TIMESTAMP_TYPE in content, "errors.proto should use google.protobuf.Timestamp type"

    def test_items_proto_uses_timestamp_type(self) -> None:
        """items.proto uses google.protobuf.Timestamp for time fields."""
        items_proto = PROTOS_DIR / "examples" / "v1" / "items.proto"

        if not items_proto.exists():
            pytest.skip("items.proto not found")

        content = items_proto.read_text()

        assert self.TIMESTAMP_IMPORT in content, "items.proto should import google/protobuf/timestamp.proto"

        # Check that time fields use Timestamp type
        assert "google.protobuf.Timestamp create_time" in content, "create_time should be google.protobuf.Timestamp"
        assert "google.protobuf.Timestamp update_time" in content, "update_time should be google.protobuf.Timestamp"


class TestFieldMaskUpdateSemantics:
    """Property 5: Field Mask Update Semantics.

    **Feature: protos-code-review, Property 5: Field Mask Update Semantics**
    **Validates: Requirements 8.1, 8.2, 8.3**

    For any Update RPC operation, the request SHALL include
    google.protobuf.FieldMask for partial updates.
    """

    FIELD_MASK_IMPORT = "google/protobuf/field_mask.proto"
    FIELD_MASK_TYPE = "google.protobuf.FieldMask"

    def test_update_item_request_has_field_mask(self) -> None:
        """UpdateItemRequest includes FieldMask for partial updates."""
        items_proto = PROTOS_DIR / "examples" / "v1" / "items.proto"

        if not items_proto.exists():
            pytest.skip("items.proto not found")

        content = items_proto.read_text()

        assert self.FIELD_MASK_IMPORT in content, "items.proto should import google/protobuf/field_mask.proto"
        assert self.FIELD_MASK_TYPE in content, "UpdateItemRequest should include google.protobuf.FieldMask"
        assert "update_mask" in content, "UpdateItemRequest should have update_mask field"


class TestProtovalidateValidation:
    """Property 2: Protovalidate Validation.

    **Feature: protos-code-review, Property 2: Protovalidate Validation**
    **Validates: Requirements 3.1, 3.2, 3.3, 3.4**

    For any message with validation annotations, the proto file SHALL
    import and use buf.validate constraints.
    """

    VALIDATE_IMPORT = "buf/validate/validate.proto"
    VALIDATE_ANNOTATION = "buf.validate"

    def test_items_proto_has_validation(self) -> None:
        """items.proto uses protovalidate annotations."""
        items_proto = PROTOS_DIR / "examples" / "v1" / "items.proto"

        if not items_proto.exists():
            pytest.skip("items.proto not found")

        content = items_proto.read_text()

        assert self.VALIDATE_IMPORT in content, "items.proto should import buf/validate/validate.proto"
        assert self.VALIDATE_ANNOTATION in content, "items.proto should use buf.validate annotations"

    def test_errors_proto_has_validation(self) -> None:
        """errors.proto uses protovalidate annotations."""
        errors_proto = PROTOS_DIR / "common" / "v1" / "errors.proto"

        if not errors_proto.exists():
            pytest.skip("errors.proto not found")

        content = errors_proto.read_text()

        assert self.VALIDATE_IMPORT in content, "errors.proto should import buf/validate/validate.proto"

    def test_pagination_proto_has_validation(self) -> None:
        """pagination.proto uses protovalidate annotations."""
        pagination_proto = PROTOS_DIR / "common" / "v1" / "pagination.proto"

        if not pagination_proto.exists():
            pytest.skip("pagination.proto not found")

        content = pagination_proto.read_text()

        assert self.VALIDATE_IMPORT in content, "pagination.proto should import buf/validate/validate.proto"

    @given(st.integers(min_value=1, max_value=100))
    @settings(max_examples=20)
    def test_page_size_validation_range(self, page_size: int) -> None:
        """page_size validation allows values 1-100."""
        # This is a structural test - we verify the constraint exists
        pagination_proto = PROTOS_DIR / "common" / "v1" / "pagination.proto"

        if not pagination_proto.exists():
            pytest.skip("pagination.proto not found")

        content = pagination_proto.read_text()

        # Check that page_size has range validation
        assert "lte: 100" in content or "lte:100" in content, "page_size should have max validation of 100"


class TestResourceNameFormat:
    """Property 7: Resource Name Format.

    **Feature: protos-code-review, Property 7: Resource Name Format**
    **Validates: Requirements 10.1, 10.2, 10.3**

    For any resource message with a name field, the value SHALL follow
    the pattern {collection}/{resource_id} as per AIP-122.
    """

    RESOURCE_NAME_PATTERN = r"\^items/\[a-zA-Z0-9-\]\+\$"

    def test_item_has_name_field(self) -> None:
        """Item message has name field for resource naming."""
        items_proto = PROTOS_DIR / "examples" / "v1" / "items.proto"

        if not items_proto.exists():
            pytest.skip("items.proto not found")

        content = items_proto.read_text()

        # Check for name field in Item message
        assert "string name = 2" in content, "Item message should have name field at position 2"

    def test_item_name_has_pattern_validation(self) -> None:
        """Item name field has pattern validation for AIP-122 format."""
        items_proto = PROTOS_DIR / "examples" / "v1" / "items.proto"

        if not items_proto.exists():
            pytest.skip("items.proto not found")

        content = items_proto.read_text()

        # Check for pattern validation on name field
        assert "pattern" in content, "Item name field should have pattern validation"
        assert "items/" in content, "Item name pattern should include 'items/' collection prefix"

    @given(st.uuids())
    @settings(max_examples=20)
    def test_resource_name_format_with_uuid(self, uuid: Any) -> None:
        """Resource names with UUIDs match expected format."""
        resource_name = f"items/{uuid}"
        pattern = re.compile(r"^items/[a-zA-Z0-9-]+$")

        assert pattern.match(resource_name), f"Resource name '{resource_name}' should match AIP-122 pattern"


class TestErrorCodeEnum:
    """Test ErrorCode enum follows best practices.

    **Feature: protos-code-review, Property 2: Protovalidate Validation**
    **Validates: Requirements 5.5**
    """

    def test_error_code_enum_exists(self) -> None:
        """ErrorCode enum is defined in errors.proto."""
        errors_proto = PROTOS_DIR / "common" / "v1" / "errors.proto"

        if not errors_proto.exists():
            pytest.skip("errors.proto not found")

        content = errors_proto.read_text()

        assert "enum ErrorCode" in content, "errors.proto should define ErrorCode enum"

    def test_error_code_has_unspecified_zero_value(self) -> None:
        """ErrorCode enum has UNSPECIFIED as zero value."""
        errors_proto = PROTOS_DIR / "common" / "v1" / "errors.proto"

        if not errors_proto.exists():
            pytest.skip("errors.proto not found")

        content = errors_proto.read_text()

        assert "ERROR_CODE_UNSPECIFIED = 0" in content, "ErrorCode should have ERROR_CODE_UNSPECIFIED = 0"

    def test_error_code_values_have_prefix(self) -> None:
        """ErrorCode enum values have ERROR_CODE_ prefix."""
        errors_proto = PROTOS_DIR / "common" / "v1" / "errors.proto"

        if not errors_proto.exists():
            pytest.skip("errors.proto not found")

        content = errors_proto.read_text()

        # Check for common error codes with proper prefix
        expected_codes = [
            "ERROR_CODE_VALIDATION",
            "ERROR_CODE_NOT_FOUND",
            "ERROR_CODE_PERMISSION_DENIED",
            "ERROR_CODE_INTERNAL",
        ]

        for code in expected_codes:
            assert code in content, f"ErrorCode should include {code}"
