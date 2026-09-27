"""
SIH 26090: Base Ingestion Adapter Interface
Abstract base class defining the standard ingestion lifecycle.
"""

from abc import ABC, abstractmethod
from typing import List, Dict, Any, Tuple
from scripts.ingestion.common.manifest import IngestionManifest


class BaseIngestionAdapter(ABC):
    """Abstract interface implemented by all data source ingestion adapters."""

    @property
    @abstractmethod
    def source_id(self) -> str:
        """Unique identifier of the data source."""
        pass

    @property
    @abstractmethod
    def source_name(self) -> str:
        """Official name of the data provider."""
        pass

    @property
    @abstractmethod
    def source_url(self) -> str:
        """Official public URL where data originates."""
        pass

    @property
    @abstractmethod
    def custodian(self) -> str:
        """Government department or custodian agency."""
        pass

    @property
    @abstractmethod
    def license_type(self) -> str:
        """Open Government Data License or public domain notice."""
        pass

    @abstractmethod
    def load_raw_data(self) -> Tuple[str, str]:
        """Loads or downloads pristine raw data. Returns (raw_content_str, raw_file_path)."""
        pass

    @abstractmethod
    def parse_raw(self, raw_content: str) -> List[Dict[str, Any]]:
        """Parses raw content into intermediate Python dictionary records."""
        pass

    @abstractmethod
    def validate_records(self, records: List[Dict[str, Any]]) -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]]]:
        """Validates records. Returns (valid_records, rejected_records)."""
        pass

    @abstractmethod
    def deduplicate(self, records: List[Dict[str, Any]]) -> Tuple[List[Dict[str, Any]], int]:
        """Deduplicates records. Returns (unique_records, duplicate_count)."""
        pass

    @abstractmethod
    def transform(self, records: List[Dict[str, Any]], manifest_id: str) -> List[Dict[str, Any]]:
        """Transforms validated records into database-ready entity dictionaries with provenance headers."""
        pass
