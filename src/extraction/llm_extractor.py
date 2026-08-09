"""LLM Structured Fact Extractor with Gemini & OpenAI support, Pydantic validation, & graceful fallback."""

import json
import os
import uuid
from typing import List, Optional, Any, Dict
from pydantic import BaseModel, Field, SecretStr

from src.config import settings
from src.models.domain import DocumentMetadata, ExtractedFact, SourceCitation
from src.extraction.normalizer import (
    normalize_currency, normalize_date, normalize_percentage, normalize_quantity
)
from src.extraction.grounding import verify_grounding
from src.logging_config import get_logger

logger = get_logger("documesh.extraction.llm")


class ExtractedFactLLMItem(BaseModel):
    entity_type: str = Field(description="Canonical entity type, e.g. CONTRACT_VALUE, HANDOVER_DATE, EXPENDITURE, PROGRESS_PCT, PENALTY_RATE")
    entity_key: str = Field(description="Canonical key, e.g. project:total_contract_value, project:handover_date, phase:3:progress_pct")
    attribute: str = Field(description="Attribute name, e.g. value, date, percentage, status")
    raw_value: str = Field(description="Raw string value extracted from document")
    unit: Optional[str] = Field(None, description="Unit if applicable, e.g. INR, date, percentage, cum, MT")
    location: str = Field(description="Section or table location in document")
    exact_quote: str = Field(description="Exact verbatim quote from the document supporting this fact")


class LLMExtractionSchema(BaseModel):
    facts: List[ExtractedFactLLMItem] = Field(default_factory=list)


async def extract_facts_llm_async(doc: DocumentMetadata) -> List[ExtractedFact]:
    """Extract facts using LLM structured output (Gemini / OpenAI) with fallback to heuristic extractor."""
    gemini_key = settings.gemini_api_key or settings.google_api_key or os.getenv("GEMINI_API_KEY", "") or os.getenv("GOOGLE_API_KEY", "")
    openai_key = settings.openai_api_key or os.getenv("OPENAI_API_KEY", "")

    if not gemini_key and not openai_key:
        logger.info("llm_keys_missing_using_heuristic_extractor", filename=doc.filename)
        from src.extraction.extractor import extract_facts_heuristic
        return extract_facts_heuristic(doc)

    try:
        from langchain_core.prompts import ChatPromptTemplate

        if gemini_key:
            from langchain_google_genai import ChatGoogleGenerativeAI
            logger.info("using_gemini_llm_provider", filename=doc.filename, model=settings.default_gemini_model)
            model = ChatGoogleGenerativeAI(
                model=settings.default_gemini_model,
                google_api_key=gemini_key,
                temperature=0.0
            ).with_structured_output(LLMExtractionSchema)
        else:
            from langchain_openai import ChatOpenAI
            logger.info("using_openai_llm_provider", filename=doc.filename, model=settings.default_model)
            model = ChatOpenAI(
                model=settings.default_model,
                api_key=SecretStr(openai_key),
                temperature=0.0
            ).with_structured_output(LLMExtractionSchema)

        prompt = ChatPromptTemplate.from_messages([
            ("system",
             "You are an expert construction document analyst. Extract all key facts from the document text.\n"
             "For EVERY fact you extract, you MUST provide an exact_quote containing verbatim text from the document.\n"
             "DO NOT hallucinate or summarize in exact_quote. Ground every fact strictly in the document text."),
            ("user", "Document Filename: {filename}\nDocument Type: {doc_type}\n\nText:\n{text}")
        ])

        chain = prompt | model

        raw_result = await chain.ainvoke({
            "filename": doc.filename,
            "doc_type": doc.doc_type.value,
            "text": (doc.extracted_text or "")[:12000]
        })

        if isinstance(raw_result, dict):
            result = LLMExtractionSchema(**raw_result)
        elif isinstance(raw_result, LLMExtractionSchema):
            result = raw_result
        else:
            result = LLMExtractionSchema()

        extracted_facts: List[ExtractedFact] = []
        full_text = doc.extracted_text or ""

        for item in result.facts:
            norm_val: Any = item.raw_value
            if item.unit == "INR" or "crore" in item.raw_value.lower() or "lakh" in item.raw_value.lower() or "," in item.raw_value:
                curr = normalize_currency(item.raw_value)
                if curr is not None:
                    norm_val = curr
            elif item.unit == "date" or any(month in item.raw_value.lower() for month in ["jan", "feb", "mar", "apr", "may", "jun", "jul", "aug", "sep", "oct", "nov", "dec"]):
                d = normalize_date(item.raw_value)
                if d is not None:
                    norm_val = d
            elif item.unit == "percentage" or "%" in item.raw_value:
                p = normalize_percentage(item.raw_value)
                if p is not None:
                    norm_val = p
            elif item.unit in ["cum", "mt"]:
                q, _ = normalize_quantity(item.raw_value)
                if q is not None:
                    norm_val = q

            is_grounded = verify_grounding(item.exact_quote, full_text)

            if not is_grounded:
                logger.warning("ungrounded_claim_rejected", filename=doc.filename, quote=item.exact_quote)
                continue

            extracted_facts.append(ExtractedFact(
                fact_id=str(uuid.uuid4())[:8],
                project_id=doc.project_id,
                doc_id=doc.doc_id,
                entity_type=item.entity_type,
                entity_key=item.entity_key,
                attribute=item.attribute,
                raw_value=item.raw_value,
                normalized_value=norm_val,
                unit=item.unit,
                grounded=True,
                citation=SourceCitation(
                    doc_id=doc.doc_id,
                    filename=doc.filename,
                    location=item.location,
                    exact_quote=item.exact_quote
                )
            ))

        logger.info("llm_extraction_success", filename=doc.filename, fact_count=len(extracted_facts))
        return extracted_facts

    except Exception as e:
        logger.error("llm_extraction_error_falling_back_to_heuristic", filename=doc.filename, error=str(e))
        from src.extraction.extractor import extract_facts_heuristic
        return extract_facts_heuristic(doc)
