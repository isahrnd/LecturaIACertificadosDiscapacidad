import type { AnalysisResult, BackendAnalyzeResponse } from "../types/analysis";

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL?.replace(/\/$/, "") ?? "";
const ALLOWED_FILE_TYPES = [
  "application/pdf",
  "image/png",
  "image/jpeg",
  "image/webp",
];
const MAX_SIZE_BYTES = 10 * 1024 * 1024;

export interface CertificateAnalysisInput {
  file: File;
  formFile?: File | null;
  clinicalFile?: File | null;
  observations?: string;
}

function buildUrl(path: string): string {
  if (!API_BASE_URL) {
    throw new Error(
      "La plataforma no tiene configurada la conexion necesaria para procesar certificados.",
    );
  }
  return `${API_BASE_URL}${path}`;
}

export async function downloadCompanyReportPdf(analysisId: string): Promise<void> {
  if (!analysisId || analysisId === "sin-id") {
    throw new Error(
      "No se encontro un identificador valido del analisis para generar el reporte.",
    );
  }

  let response: Response;
  try {
    response = await fetch(buildUrl(`/api/v1/analyses/${analysisId}/pdf`), {
      headers: {
        Accept: "application/pdf",
      },
    });
  } catch {
    throw new Error(
      "No fue posible generar el informe PDF en este momento.",
    );
  }

  if (!response.ok) {
    throw new Error(
      "No fue posible preparar el informe PDF para este certificado.",
    );
  }

  const blob = await response.blob();
  const contentDisposition = response.headers.get("Content-Disposition") || "";
  const filenameMatch = contentDisposition.match(/filename=\"?([^\"]+)\"?/i);
  const filename = filenameMatch?.[1] || "informe-laboral-inclusivo.pdf";

  const objectUrl = window.URL.createObjectURL(blob);
  const link = window.document.createElement("a");
  link.href = objectUrl;
  link.download = filename;
  window.document.body.appendChild(link);
  link.click();
  link.remove();
  window.URL.revokeObjectURL(objectUrl);
}

export function validateCertificateFile(file: File | null): string | null {
  if (!file) {
    return "Selecciona un archivo para continuar.";
  }

  if (!ALLOWED_FILE_TYPES.includes(file.type)) {
    return "Solo se permiten archivos PDF, PNG, JPG o WEBP.";
  }

  if (file.size > MAX_SIZE_BYTES) {
    return "El archivo supera el limite recomendado de 10 MB.";
  }

  return null;
}

export function validateOptionalSupportingFile(file: File | null): string | null {
  if (!file) {
    return null;
  }

  if (!ALLOWED_FILE_TYPES.includes(file.type)) {
    return "El formulario opcional debe estar en PDF, PNG, JPG o WEBP.";
  }

  if (file.size > MAX_SIZE_BYTES) {
    return "El formulario opcional supera el limite recomendado de 10 MB.";
  }

  return null;
}

export async function analyzeCertificate({
  file,
  formFile,
  clinicalFile,
  observations,
}: CertificateAnalysisInput): Promise<AnalysisResult> {
  const formData = new FormData();
  formData.append("file", file);
  if (formFile) {
    formData.append("form_file", formFile);
  }
  if (clinicalFile) {
    formData.append("clinical_file", clinicalFile);
  }
  if (observations?.trim()) {
    formData.append("observations", observations.trim());
  }

  let response: Response;
  try {
    response = await fetch(buildUrl("/api/v1/analyses"), {
      method: "POST",
      body: formData,
    });
  } catch {
    throw new Error(
      "No fue posible conectar el frontend con el backend de analisis. Verifica que la API este activa en VITE_API_BASE_URL.",
    );
  }

  let payload: BackendAnalyzeResponse | { detail?: string };
  try {
    payload = await response.json();
  } catch {
    throw new Error("La respuesta del servicio no pudo interpretarse correctamente.");
  }

  if (!response.ok) {
    const detail =
      typeof payload === "object" && payload && "detail" in payload
        ? payload.detail
        : undefined;
    throw new Error(detail || "No fue posible analizar el certificado.");
  }

  const data = payload as BackendAnalyzeResponse;
  return {
    analysisId: data.analysis_id || data.id || "sin-id",
    analysis: data.analysis,
  };
}
