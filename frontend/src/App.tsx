import { useState } from "react";
import { AnalysisDashboard } from "./components/AnalysisDashboard";
import { ErrorView } from "./components/ErrorView";
import { FileUploadCard } from "./components/FileUploadCard";
import { CheckIcon } from "./components/Icons";
import { LoadingView } from "./components/LoadingView";
import { useCertificateAnalysis } from "./hooks/useCertificateAnalysis";

export default function App() {
  const [file, setFile] = useState<File | null>(null);
  const [formFile, setFormFile] = useState<File | null>(null);
  const [clinicalFile, setClinicalFile] = useState<File | null>(null);
  const [observations, setObservations] = useState("");
  const { state, error, result, isBusy, submit, reset } = useCertificateAnalysis();

  const handleReset = () => {
    setFile(null);
    setFormFile(null);
    setClinicalFile(null);
    setObservations("");
    reset();
  };

  return (
    <main className="min-h-screen px-4 py-8 sm:px-6 lg:px-8 lg:py-10">
      <div className="mx-auto max-w-7xl space-y-6">
        <FileUploadCard
          file={file}
          formFile={formFile}
          clinicalFile={clinicalFile}
          observations={observations}
          onFileChange={setFile}
          onFormFileChange={setFormFile}
          onClinicalFileChange={setClinicalFile}
          onObservationsChange={setObservations}
          onAnalyze={() => void submit(file, formFile, observations, clinicalFile)}
          isBusy={isBusy}
        />

        {state === "idle" && (
          <section className="panel-card border-dashed bg-white/70 p-12 text-center">
            <div className="mx-auto flex h-16 w-16 items-center justify-center rounded-[24px] bg-sage-50 text-sage-700">
              <CheckIcon className="h-9 w-9" aria-hidden="true" />
            </div>
            <h2 className="mt-5 text-2xl font-extrabold tracking-tight text-ink">
              Todo listo para comenzar
            </h2>
            <p className="mx-auto mt-3 max-w-2xl text-sm leading-7 text-slate-500">
              Cuando subas un certificado, aqui aparecera un resumen visual con
              el perfil funcional, tareas sugeridas, ajustes razonables y
              recomendaciones para el entorno laboral.
            </p>
          </section>
        )}

        {state === "loading" && <LoadingView />}

        {state === "error" && error && (
          <ErrorView
            message={error}
            onRetry={() => void submit(file, formFile, observations, clinicalFile)}
          />
        )}

        {state === "success" && result && (
          <AnalysisDashboard
            analysisId={result.analysisId}
            analysis={result.analysis}
            onReset={handleReset}
          />
        )}
      </div>
    </main>
  );
}
