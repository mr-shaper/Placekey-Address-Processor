"""地址公寓识别与门禁码提取工具

基于Placekey API的智能地址处理工具，专门用于识别公寓地址并提取门禁码(access_code)。
"""

__version__ = "1.0.0"
__author__ = "Apartment AccessCode Team"
__email__ = "support@apartment-accesscode.com"

from .config import config
from .placekey_client import PlacekeyClient
from .address_processor import AddressProcessor
from .apartment_handler import ApartmentHandler
from .batch_processor import BatchProcessor
from .integration_processor import ExistingApartmentClassifier
from .main import main

__all__ = [
    "config",
    "PlacekeyClient",
    "AddressProcessor", 
    "ApartmentHandler",
    "BatchProcessor",
    "ExistingApartmentClassifier",
    "main"
]