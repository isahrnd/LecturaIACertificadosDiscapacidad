from __future__ import annotations

import re
from datetime import datetime, timezone
from typing import Any

from dotenv import load_dotenv
from fastapi import HTTPException, status
from openai import (
    APIConnectionError,
    APIError,
    APITimeoutError,
    AsyncOpenAI,
    AuthenticationError,
    BadRequestError,
    RateLimitError,
)

from app.core.config import Settings, get_settings
from app.core.logging import logger
from app.prompts.certificate_analysis_prompt import (
    SYSTEM_PROMPT as GENERAL_SYSTEM_PROMPT,
    build_user_prompt as build_general_user_prompt,
)
from app.prompts.disability_table_prompt import (
    SYSTEM_PROMPT as DISABILITY_TABLE_SYSTEM_PROMPT,
    build_user_prompt as build_disability_table_user_prompt,
)
from app.utils.analysis_guardrails import normalize_analysis_for_certificate
from app.schemas.analysis import CertificateAnalysisSchema
from app.schemas.document import OpenAIAnalysisRequest
from app.utils.analysis_fallback import fallback_build_analysis, is_analysis_empty
from app.utils.disability_parser import clean_disabilities, normalize_token, parse_disability_table
from app.utils.json_utils import extract_json_object

load_dotenv()

EXPECTED_DOMAIN_KEYS = (
    "cognicion",
    "movilidad",
    "cuidado_personal",
    "relaciones",
    "vida_diaria",
    "participacion",
)


def _format_certificate_date(day: int, month: int, year: int) -> str:
    return f"{day:02d}/{month:02d}/{year:04d}"


def _extract_section_22_date(extracted_text: str) -> str:
    normalized_text = normalize_token(extracted_text or "")
    if not normalized_text:
        return ""

    section_match = re.search(
        r"2\s*\.?\s*2\s+FECHA DE LA CERTIFICACION(?P<section>.*?)(?:\b2\s*\.?\s*3\b|\b3\s*\.?\b|$)",
        normalized_text,
        flags=re.DOTALL,
    )
    section_text = section_match.group("section") if section_match else normalized_text

    year_match = re.search(r"\bANO\b\s*[:=\-]?\s*(\d{4})", section_text)
    month_match = re.search(r"\bMES\b\s*[:=\-]?\s*(\d{1,2})", section_text)
    day_match = re.search(r"\bDIA\b\s*[:=\-]?\s*(\d{1,2})", section_text)
    if not (year_match and month_match and day_match):
        return ""

    year = int(year_match.group(1))
    month = int(month_match.group(1))
    day = int(day_match.group(1))
    if year < 1900 or not 1 <= month <= 12 or not 1 <= day <= 31:
        return ""
    return _format_certificate_date(day, month, year)


def _normalize_certificate_date_value(raw_value: str) -> str:
    text = (raw_value or "").strip()
    if not text:
        return ""

    normalized = normalize_token(text)
    labeled_year = re.search(r"\bANO\b\s*[:=\-]?\s*(\d{4})", normalized)
    labeled_month = re.search(r"\bMES\b\s*[:=\-]?\s*(\d{1,2})", normalized)
    labeled_day = re.search(r"\bDIA\b\s*[:=\-]?\s*(\d{1,2})", normalized)
    if labeled_year and labeled_month and labeled_day:
        return _format_certificate_date(
            int(labeled_day.group(1)),
            int(labeled_month.group(1)),
            int(labeled_year.group(1)),
        )

    year_first = re.fullmatch(r"(\d{4})[\/\-\. ](\d{1,2})[\/\-\. ](\d{1,2})", normalized)
    if year_first:
        return _format_certificate_date(
            int(year_first.group(3)),
            int(year_first.group(2)),
            int(year_first.group(1)),
        )

    day_first = re.fullmatch(r"(\d{1,2})[\/\-\. ](\d{1,2})[\/\-\. ](\d{4})", normalized)
    if day_first:
        day = int(day_first.group(1))
        month = int(day_first.group(2))
        year = int(day_first.group(3))
        if 1 <= month <= 12 and 1 <= day <= 31:
            return _format_certificate_date(day, month, year)

    return text


def normalize_certificate_persona(
    payload: dict[str, Any],
    *,
    extracted_text: str,
    settings: Settings | None = None,
) -> dict[str, Any]:
    settings = settings or get_settings()
    persona = payload.get("persona")
    if not isinstance(persona, dict):
        return payload

    section_date = _extract_section_22_date(extracted_text)
    current_date = str(persona.get("fecha_certificacion") or "")
    if settings.analysis_debug:
        logger.info(
            "[ANALYSIS_DEBUG][openai_service] persona.fecha_certificacion raw_model=%s source_text_preview=%s extracted_section_22_date=%s",
            current_date,
            (extracted_text or "")[:500].replace("\n", " "),
            section_date,
        )
    persona["fecha_certificacion"] = section_date or _normalize_certificate_date_value(current_date)
    if settings.analysis_debug:
        logger.info(
            "[ANALYSIS_DEBUG][openai_service] persona.fecha_certificacion normalized=%s",
            persona["fecha_certificacion"],
        )
    payload["persona"] = persona
    return payload


class OpenAIAnalysisService:
    def __init__(self, settings: Settings | None = None) -> None:
        self.settings = settings or get_settings()
        self._client: AsyncOpenAI | None = None

    @property
    def client(self) -> AsyncOpenAI:
        if self._client is None:
            self._client = AsyncOpenAI(
                api_key=self.settings.openai_api_key,
                timeout=self.settings.request_timeout_seconds,
            )
        return self._client

    async def analyze_certificate(
        self, request: OpenAIAnalysisRequest, *, used_vision: bool, clinical_text: str | None = None
    ) -> CertificateAnalysisSchema:
        if not self.settings.openai_api_key:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="La variable OPENAI_API_KEY no está configurada.",
            )

        general_payload = await self._run_general_analysis(
            request=request,
            used_vision=used_vision,
            clinical_text=clinical_text,
        )
        general_payload = normalize_certificate_persona(
            general_payload,
            extracted_text=request.text,
            settings=self.settings,
        )
        general_payload["dominios"] = normalize_dominios(general_payload)

        disability_result = await self._run_specialized_disability_extraction(
            request=request,
            used_vision=used_vision,
            fallback_raw=general_payload.get("discapacidades_raw"),
        )
        general_payload["discapacidades_raw"] = disability_result.discapacidades_raw
        general_payload["discapacidades_activas"] = disability_result.discapacidades_activas
        general_payload["analisis"] = self._resolve_analysis(general_payload)
        general_payload["analisis"] = normalize_analysis_for_certificate(
            general_payload,
            used_vision=used_vision,
            observations=request.observations,
        )

        general_payload.setdefault("metadata", {})
        general_payload["metadata"]["modelo_usado"] = self.settings.openai_model
        general_payload["metadata"]["fecha_procesamiento"] = datetime.now(
            timezone.utc
        ).isoformat()
        general_payload["metadata"]["estado"] = "success"
        if self.settings.analysis_debug:
            logger.info(
                "[ANALYSIS_DEBUG][openai_service] final_response model=%s final_fecha_certificacion=%s final_tareas_no=%s final_recomendaciones=%s",
                self.settings.openai_model,
                (
                    general_payload.get("persona", {}).get("fecha_certificacion")
                    if isinstance(general_payload.get("persona"), dict)
                    else ""
                ),
                (
                    general_payload.get("analisis", {}).get("tareas_no_recomendadas")
                    if isinstance(general_payload.get("analisis"), dict)
                    else []
                ),
                (
                    general_payload.get("analisis", {}).get("recomendaciones_rrhh_sst")
                    if isinstance(general_payload.get("analisis"), dict)
                    else []
                ),
            )
        return CertificateAnalysisSchema.model_validate(general_payload)

    async def _run_general_analysis(
        self,
        *,
        request: OpenAIAnalysisRequest,
        used_vision: bool,
        clinical_text: str | None = None,
    ) -> dict[str, Any]:
        if self.settings.analysis_debug:
            logger.info(
                "[ANALYSIS_DEBUG][openai_service] calling_general_analysis model=%s image_count=%s used_vision=%s",
                self.settings.openai_model,
                len(request.image_data_urls),
                used_vision,
            )
        messages = self._build_messages(
            system_prompt=GENERAL_SYSTEM_PROMPT,
            user_prompt=build_general_user_prompt(
                extracted_text=request.text,
                filename=request.filename,
                used_vision=used_vision,
                form_text=request.form_text,
                observations=request.observations,
                clinical_text=clinical_text,
            ),
            image_data_urls=request.image_data_urls,
        )
        return await self._call_json_completion(messages)

    async def _run_specialized_disability_extraction(
        self,
        *,
        request: OpenAIAnalysisRequest,
        used_vision: bool,
        fallback_raw: Any,
    ):
        if self.settings.analysis_debug:
            logger.info(
                "[ANALYSIS_DEBUG][openai_service] calling_disability_extraction model=%s image_count=%s used_vision=%s",
                self.settings.openai_model,
                len(request.image_data_urls),
                used_vision,
            )
        messages = self._build_messages(
            system_prompt=DISABILITY_TABLE_SYSTEM_PROMPT,
            user_prompt=build_disability_table_user_prompt(
                extracted_text=request.text,
                filename=request.filename,
                used_vision=used_vision,
            ),
            image_data_urls=request.image_data_urls,
        )

        try:
            table_payload = await self._call_json_completion(messages)
            result = parse_disability_table(table_payload)
            if any(item["marcado"] != "ILEGIBLE" for item in result.discapacidades_raw):
                logger.info(
                    "La tabla especializada tuvo prioridad sobre la lectura general. activas=%s",
                    ", ".join(result.discapacidades_activas) or "ninguna",
                )
            logger.info(
                "Extracción especializada de discapacidad completada. activas=%s",
                ", ".join(result.discapacidades_activas) or "ninguna",
            )
            return result
        except HTTPException:
            logger.warning(
                "La extracción especializada de discapacidad falló. Se usará la lectura general saneada."
            )
            return clean_disabilities(fallback_raw)

    async def _call_json_completion(
        self,
        messages: list[dict[str, Any]],
    ) -> dict[str, Any]:
        try:
            response = await self.client.chat.completions.create(
                model=self.settings.openai_model,
                response_format={"type": "json_object"},
                temperature=0.1,
                messages=messages,
            )
        except AuthenticationError as exc:
            logger.exception("OpenAI rechazó la autenticación.")
            raise HTTPException(
                status_code=status.HTTP_502_BAD_GATEWAY,
                detail="OpenAI rechazó la autenticación. Verifica OPENAI_API_KEY.",
            ) from exc
        except RateLimitError as exc:
            logger.exception("OpenAI respondió con rate limit.")
            raise HTTPException(
                status_code=status.HTTP_502_BAD_GATEWAY,
                detail="OpenAI rechazó la solicitud por límite de tasa. Intenta nuevamente.",
            ) from exc
        except BadRequestError as exc:
            logger.exception("OpenAI rechazó la solicitud por parámetros inválidos.")
            raise HTTPException(
                status_code=status.HTTP_502_BAD_GATEWAY,
                detail=f"OpenAI rechazó la solicitud: {exc}",
            ) from exc
        except (APIConnectionError, APITimeoutError) as exc:
            logger.exception("Fallo de red o timeout llamando a OpenAI.")
            raise HTTPException(
                status_code=status.HTTP_502_BAD_GATEWAY,
                detail="No fue posible comunicarse con OpenAI.",
            ) from exc
        except APIError as exc:
            logger.exception("OpenAI devolvió un error de API.")
            raise HTTPException(
                status_code=status.HTTP_502_BAD_GATEWAY,
                detail="OpenAI devolvió un error procesando la solicitud.",
            ) from exc

        content = self._extract_message_content(response)
        return extract_json_object(content)

    def _build_messages(
        self,
        *,
        system_prompt: str,
        user_prompt: str,
        image_data_urls: list[str],
    ) -> list[dict[str, Any]]:
        user_content: list[dict[str, Any]] = [{"type": "text", "text": user_prompt}]
        for image_data_url in image_data_urls:
            user_content.append(
                {
                    "type": "image_url",
                    "image_url": {"url": image_data_url},
                }
            )

        return [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_content},
        ]

    def _extract_message_content(self, response_payload: Any) -> str:
        choices = getattr(response_payload, "choices", None) or []
        if not choices:
            raise HTTPException(
                status_code=status.HTTP_502_BAD_GATEWAY,
                detail="OpenAI no devolvió opciones de respuesta.",
            )

        message = getattr(choices[0], "message", None)
        if message is None:
            raise HTTPException(
                status_code=status.HTTP_502_BAD_GATEWAY,
                detail="La respuesta de OpenAI no incluyó un mensaje válido.",
            )

        content = getattr(message, "content", None)
        if isinstance(content, str):
            return content

        if isinstance(content, list):
            parts: list[str] = []
            for item in content:
                item_type = (
                    item.get("type") if isinstance(item, dict) else getattr(item, "type", None)
                )
                item_text = (
                    item.get("text") if isinstance(item, dict) else getattr(item, "text", None)
                )
                if item_type == "text" and item_text:
                    parts.append(item_text)
            if parts:
                return "\n".join(parts)

        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="La respuesta de OpenAI llegó en un formato no soportado.",
        )

    def _resolve_analysis(self, payload: dict[str, Any]) -> dict[str, Any]:
        if is_analysis_empty(payload):
            logger.warning(
                "El bloque 'analisis' llegó vacío o incompleto. Se aplicará fallback local."
            )
            return fallback_build_analysis(payload)

        analisis = payload.get("analisis")
        if not isinstance(analisis, dict):
            logger.warning(
                "El bloque 'analisis' no llegó como objeto. Se aplicará fallback local."
            )
            return fallback_build_analysis(payload)

        return analisis


def normalize_dominios(payload: dict[str, Any]) -> dict[str, float]:
    raw_dominios = payload.get("dominios")
    if not isinstance(raw_dominios, dict):
        logger.warning("El campo 'dominios' no llegó como objeto. Se usarán valores 0.0.")
        raw_dominios = {}

    normalized: dict[str, float] = {}
    for key in EXPECTED_DOMAIN_KEYS:
        raw_value = raw_dominios.get(key)
        try:
            if raw_value is None or raw_value == "":
                raise ValueError("empty")
            value = float(raw_value)
        except (TypeError, ValueError):
            logger.warning(
                "Dominio '%s' llegó con valor inválido %r. Se reemplaza por 0.0.",
                key,
                raw_value,
            )
            value = 0.0

        value = max(0.0, min(100.0, value))
        normalized[key] = value

    return normalized


def get_openai_service() -> OpenAIAnalysisService:
    return OpenAIAnalysisService()
