"""
FastAPI Application for OFIP
"""

from fastapi import FastAPI, UploadFile, File
from pydantic import BaseModel
from typing import Dict, Any
import json

from core.engine import RuleEngine, SuspiciousAmountRule
from core.plugin_manager import PluginManager
from ocr.processor import OCRProcessor

app = FastAPI(title="Open Fraud Intelligence Platform", version="0.1.0")

# Initialize components
rule_engine = RuleEngine()
rule_engine.add_rule(SuspiciousAmountRule())

plugin_manager = PluginManager()
plugin_manager.load_plugins()

ocr_processor = OCRProcessor()

class TransactionData(BaseModel):
    amount: float
    description: str
    # Add more fields as needed

@app.get("/")
def read_root():
    return {"message": "Welcome to OFIP API"}

@app.post("/analyze")
def analyze_transaction(data: TransactionData):
    input_data = data.dict()
    results = rule_engine.evaluate_all(input_data)
    return {"results": results, "data": input_data}

@app.post("/ocr")
async def process_ocr(file: UploadFile = File(...)):
    content = await file.read()
    text = ocr_processor.extract_text(content)
    return {"extracted_text": text}

@app.get("/plugins")
def list_plugins():
    return {"plugins": plugin_manager.list_plugins()}

@app.post("/plugin/{plugin_name}")
def run_plugin(plugin_name: str, data: Dict[str, Any]):
    result = plugin_manager.process_with_plugin(plugin_name, data)
    return {"result": result}