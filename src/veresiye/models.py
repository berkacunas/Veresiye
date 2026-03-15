from pydantic import BaseModel, Field
from typing import List, Optional

class ReceiptItem(BaseModel):
    """Model of a single product line"""
    name: str
    quantity: float = 1.0
    unit_price: float = 0.0
    total_price: float
    tax_rate: Optional[str] = None # e.g., %1, %20

class ParsedReceipt(BaseModel):
    """The standard receipt model that all parsers will return"""
    market: str
    date: Optional[str] = None
    hour: Optional[str] = None
    receipt_no: Optional[str] = None
    total_amount: Optional[float] = None
    products: List[ReceiptItem] = Field(default_factory=list) # It starts with an empty list.
