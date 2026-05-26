import { useMemo, useState } from "react";
import {
  analyzeCertificate,
  validateCertificateFile,
  validateOptionalSupportingFile,
} from "../lib/api";
import type { AnalysisResult } from "../types/analysis";

type RequestState = "idle" | "loading" | "success" | "error";

export function useCertificateAnalysis() {
  const [state, setState] = useState<RequestState>("idle");
  const [error, setError] = useState<string | null>(null);
  const [result, setResult] = useState<AnalysisResult | null>(null);

  const isBusy = state === "loading";

  const actions = useMemo(
    () => ({
      async submit(
        file: File | null,
        formFile?: File | null,
        observations?: string,
        clinicalFile?: File | null,
      ) {
        const validationError = validateCertificateFile(file);
        if (validationError) {
          setState("error");
          setError(validationError);
          return;
        }

        const supportingValidationError = validateOptionalSupportingFile(
          formFile ?? null,
        );
        if (supportingValidationError) {
          setState("error");
          setError(supportingValidationError);
          return;
        }

        const clinicalValidationError = validateOptionalSupportingFile(
          clinicalFile ?? null,
        );
        if (clinicalValidationError) {
          setState("error");
          setError(clinicalValidationError);
          return;
        }

        setState("loading");
        setError(null);

        try {
          const analysisResult = await analyzeCertificate({
            file: file!,
            formFile,
            clinicalFile,
            observations,
          });
          setResult(analysisResult);
          setState("success");
        } catch (caughtError) {
          const message =
            caughtError instanceof Error
              ? caughtError.message
              : "Ocurrió un error inesperado.";
          setError(message);
          setState("error");
        }
      },
      reset() {
        setState("idle");
        setError(null);
        setResult(null);
      },
    }),
    [],
  );

  return {
    state,
    error,
    result,
    isBusy,
    ...actions,
  };
}
