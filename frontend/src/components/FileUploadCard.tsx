import { useRef } from "react";
import { CheckIcon, PlusIcon, UploadArrowIcon } from "./Icons";

interface FileUploadCardProps {
  file: File | null;
  formFile: File | null;
  clinicalFile: File | null;
  observations: string;
  onFileChange: (file: File | null) => void;
  onFormFileChange: (file: File | null) => void;
  onClinicalFileChange: (file: File | null) => void;
  onObservationsChange: (value: string) => void;
  onAnalyze: () => void;
  isBusy: boolean;
}

export function FileUploadCard({
  file,
  formFile,
  clinicalFile,
  observations,
  onFileChange,
  onFormFileChange,
  onClinicalFileChange,
  onObservationsChange,
  onAnalyze,
  isBusy,
}: FileUploadCardProps) {
  const certificateInputRef = useRef<HTMLInputElement | null>(null);
  const formInputRef = useRef<HTMLInputElement | null>(null);
  const clinicalInputRef = useRef<HTMLInputElement | null>(null);

  const renderFileSummary = (selectedFile: File | null, emptyState: string) =>
    selectedFile
      ? `${selectedFile.name} - ${(selectedFile.size / 1024 / 1024).toFixed(2)} MB`
      : emptyState;

  return (
    <section className="panel-card overflow-hidden bg-white">
      <div className="bg-gradient-hero px-8 py-10 lg:px-10 lg:py-12">
        <div className="mx-auto max-w-4xl space-y-4 text-center lg:text-left">
          <span className="inline-flex rounded-full bg-primary-foam px-4 py-1 text-sm font-bold text-almia-700">
            Lector inclusivo
          </span>
          <div className="space-y-3">
            <h1 className="max-w-3xl text-4xl font-extrabold tracking-tight text-ink sm:text-5xl">
              Lectura IA de certificados de discapacidad
            </h1>
            <p className="max-w-3xl text-base leading-8 text-slate-600 sm:text-lg">
              Carga el certificado, complementa con formulario de especialista
              si lo tienes y agrega observaciones específicas para generar un
              perfil funcional con análisis procesado con IA.
            </p>
          </div>
          <div className="flex flex-wrap gap-3 text-sm text-slate-500">
            <span className="rounded-full bg-sage-50 px-3 py-1 font-semibold text-sage-700">
              PDF, JPG, PNG o WEBP
            </span>
            <span className="rounded-full bg-primary-foam px-3 py-1 font-semibold text-almia-700">
              Análisis procesado con IA
            </span>
            <span className="rounded-full bg-terracotta-50 px-3 py-1 font-semibold text-terracotta-700">
              Certificado obligatorio, extras opcionales
            </span>
          </div>
        </div>
      </div>

      <div className="p-6 md:p-8 lg:p-10">
        <div className="rounded-3xl border border-line/80 bg-white p-6 shadow-card md:p-8">
          <div className="grid gap-6 md:grid-cols-2 xl:grid-cols-3">
            <button
              type="button"
              onClick={() => certificateInputRef.current?.click()}
              className="group flex min-h-[220px] flex-col items-center justify-center rounded-[22px] border-2 border-dashed border-almia-200 bg-gradient-soft px-6 py-10 text-center transition hover:border-almia-400 hover:bg-primary-foam/60"
            >
              <div className="mb-4 flex h-14 w-14 items-center justify-center rounded-2xl bg-primary-foam text-almia-700 transition group-hover:scale-105">
                <UploadArrowIcon className="h-7 w-7" aria-hidden="true" />
              </div>
              <h2 className="text-lg font-extrabold text-ink">
                Subir certificado de discapacidad
              </h2>
              <p className="mt-2 max-w-sm text-sm leading-6 text-slate-500">
                {renderFileSummary(
                  file,
                  "Formatos permitidos: PDF, JPG, PNG o WEBP.",
                )}
              </p>
              <span className="mt-4 inline-flex rounded-full bg-white px-4 py-1 text-xs font-bold text-almia-700 shadow-sm">
                {file ? "Certificado cargado" : "Seleccionar archivo"}
              </span>
            </button>

            <input
              ref={certificateInputRef}
              type="file"
              accept=".pdf,.png,.jpg,.jpeg,.webp"
              className="hidden"
              onChange={(event) => onFileChange(event.target.files?.[0] ?? null)}
            />

            <button
              type="button"
              onClick={() => formInputRef.current?.click()}
              className="group flex min-h-[220px] flex-col items-center justify-center rounded-[22px] border-2 border-dashed border-almia-200 bg-gradient-soft px-6 py-10 text-center transition hover:border-almia-400 hover:bg-primary-foam/60"
            >
              <div className="mb-4 flex h-14 w-14 items-center justify-center rounded-2xl bg-primary-foam text-almia-700 transition group-hover:scale-105">
                <PlusIcon className="h-7 w-7" aria-hidden="true" />
              </div>
              <h2 className="text-lg font-extrabold text-ink">
                Subir formulario con especialista de Almia (opcional)
              </h2>
              <p className="mt-2 max-w-sm text-sm leading-6 text-slate-500">
                {renderFileSummary(
                  formFile,
                  "Adjunta este formulario solo si la persona ya tuvo una entrevista o valoración funcional con una especialista de Almia. Este documento ayuda a precisar apoyos, ajustes razonables y recomendaciones laborales.",
                )}
              </p>
              <span className="mt-4 inline-flex rounded-full bg-white px-4 py-1 text-xs font-bold text-almia-700 shadow-sm">
                {formFile ? "Formulario cargado" : "Seleccionar archivo"}
              </span>
            </button>

            <input
              ref={formInputRef}
              type="file"
              accept=".pdf,.png,.jpg,.jpeg,.webp"
              className="hidden"
              onChange={(event) => onFormFileChange(event.target.files?.[0] ?? null)}
            />

            <button
              type="button"
              onClick={() => clinicalInputRef.current?.click()}
              className="group flex min-h-[220px] flex-col items-center justify-center rounded-[22px] border-2 border-dashed border-almia-200 bg-gradient-soft px-6 py-10 text-center transition hover:border-almia-400 hover:bg-primary-foam/60"
            >
              <div className="mb-4 flex h-14 w-14 items-center justify-center rounded-2xl bg-primary-foam text-almia-700 transition group-hover:scale-105">
                <PlusIcon className="h-7 w-7" aria-hidden="true" />
              </div>
              <h2 className="text-lg font-extrabold text-ink">
                Subir historia clínica (opcional)
              </h2>
              <p className="mt-2 max-w-sm text-sm leading-6 text-slate-500">
                {renderFileSummary(
                  clinicalFile,
                  "Adjunta la historia clínica solo si cuentas con autorización para usarla en este análisis. Este documento puede complementar diagnósticos, evolución, tratamientos, apoyos técnicos y pronóstico funcional.",
                )}
              </p>
              <span className="mt-4 inline-flex rounded-full bg-white px-4 py-1 text-xs font-bold text-almia-700 shadow-sm">
                {clinicalFile ? "Historia clínica cargada" : "Seleccionar archivo"}
              </span>
            </button>

            <input
              ref={clinicalInputRef}
              type="file"
              accept=".pdf,.png,.jpg,.jpeg,.webp"
              className="hidden"
              onChange={(event) => onClinicalFileChange(event.target.files?.[0] ?? null)}
            />
          </div>

          <div className="mt-6">
            <label
              htmlFor="observations"
              className="text-sm font-semibold text-ink"
            >
              Observaciones específicas
            </label>
            <textarea
              id="observations"
              value={observations}
              onChange={(event) => onObservationsChange(event.target.value)}
              rows={5}
              placeholder="Ej: persona oralizada, usa audífonos, requiere intérprete, movilidad conservada en miembros superiores, restricciones de desplazamiento, apoyos familiares, etc."
              className="mt-2 min-h-[128px] w-full rounded-2xl border border-line bg-white px-4 py-3 text-sm text-slate-700 shadow-sm outline-none transition placeholder:text-slate-400 focus:border-almia-300 focus:ring-2 focus:ring-almia-100"
            />
          </div>

          <div className="mt-8 flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between">
            <div className="space-y-2">
              <div className="inline-flex items-center gap-2 text-xs font-medium text-slate-500">
                <span className="inline-flex h-5 w-5 items-center justify-center rounded-full bg-primary-foam text-almia-700">
                  <CheckIcon className="h-3.5 w-3.5" aria-hidden="true" />
                </span>
                Tus datos se procesan de forma segura y confidencial.
              </div>
              <p className="text-xs leading-6 text-slate-500">
                El certificado sigue siendo obligatorio. El formulario y las
                observaciones enriquecen la lectura del caso, pero no
                reemplazan la informacion contenida en el certificado.
              </p>
            </div>

            <div className="flex flex-col gap-3 sm:min-w-[280px]">
              <button
                type="button"
                onClick={onAnalyze}
                disabled={isBusy}
                className="inline-flex items-center justify-center rounded-2xl bg-gradient-to-r from-almia-400 to-almia-500 px-6 py-3 text-sm font-bold text-white transition hover:from-almia-500 hover:to-almia-700 disabled:cursor-not-allowed disabled:opacity-60"
              >
                {isBusy
                  ? "Procesando..."
                  : "Generar perfil laboral inclusivo"}
              </button>
              <button
                type="button"
                onClick={() => {
                  onFileChange(null);
                  onFormFileChange(null);
                  onClinicalFileChange(null);
                  onObservationsChange("");
                }}
                disabled={(!file && !formFile && !clinicalFile && !observations.trim()) || isBusy}
                className="inline-flex items-center justify-center rounded-2xl border border-line bg-white px-5 py-3 text-sm font-bold text-slate-600 transition hover:bg-slate-50 disabled:cursor-not-allowed disabled:opacity-50"
              >
                Limpiar campos
              </button>
            </div>
          </div>
        </div>
      </div>
    </section>
  );
}
