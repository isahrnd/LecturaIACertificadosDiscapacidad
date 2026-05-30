import { useState } from "react";
import type { Analysis } from "../types/analysis";
import { ProfileHeaderCard } from "./ProfileHeaderCard";
import { RecommendedTasksPanel } from "./RecommendedTasksPanel";
import { AdjustmentsPanel } from "./AdjustmentsPanel";
import { NotRecommendedPanel } from "./NotRecommendedPanel";
import { HrRecommendationsPanel } from "./HrRecommendationsPanel";
import { downloadCompanyReportPdf } from "../lib/api";

interface AnalysisDashboardProps {
  analysisId: string;
  analysis: Analysis;
  onReset: () => void;
}

export function AnalysisDashboard({
  analysisId,
  analysis,
  onReset,
}: AnalysisDashboardProps) {
  const [isDownloading, setIsDownloading] = useState(false);
  const [downloadError, setDownloadError] = useState<string | null>(null);

  const handleDownloadPdf = async () => {
    setIsDownloading(true);
    setDownloadError(null);
    try {
      await downloadCompanyReportPdf(analysisId);
    } catch (error) {
      setDownloadError(
        error instanceof Error
          ? error.message
          : "No fue posible descargar el informe PDF.",
      );
    } finally {
      setIsDownloading(false);
    }
  };

  return (
    <div className="space-y-6">
      <div className="flex flex-wrap items-center justify-between gap-3">
        <div>
          <p className="text-sm font-semibold uppercase tracking-[0.18em] text-almia-700/60">
            Resultado del análisis
          </p>
          <h2 className="mt-1 text-2xl font-extrabold tracking-tight text-ink">
            Resumen laboral del certificado
          </h2>
        </div>

        <div className="flex flex-wrap gap-3">
          <button
            type="button"
            onClick={() => void handleDownloadPdf()}
            disabled={isDownloading}
            className="rounded-2xl border border-almia-100 bg-white px-4 py-2 text-sm font-bold text-almia-700 transition hover:bg-almia-50 disabled:cursor-not-allowed disabled:opacity-60"
          >
            {isDownloading ? "Generando PDF..." : "Descargar informe PDF"}
          </button>
          <button
            type="button"
            onClick={onReset}
            className="rounded-2xl bg-gradient-to-r from-almia-400 to-almia-500 px-4 py-2 text-sm font-bold text-white transition hover:from-almia-500 hover:to-almia-700"
          >
            Analizar otro certificado
          </button>
        </div>
      </div>

      {downloadError && (
        <section className="rounded-2xl border border-terracotta-100 bg-terracotta-50/80 px-4 py-3 text-sm text-terracotta-700">
          {downloadError}
        </section>
      )}

      <ProfileHeaderCard analysis={analysis} />

      <section className="grid gap-5 xl:grid-cols-2">
        <RecommendedTasksPanel tasks={analysis.analisis.tareas_recomendadas} />
        <AdjustmentsPanel
          adjustments={analysis.analisis.ajustes_razonables}
          activeConditions={analysis.discapacidades_activas}
        />
      </section>

      <NotRecommendedPanel items={analysis.analisis.tareas_no_recomendadas} />

      <HrRecommendationsPanel items={analysis.analisis.recomendaciones_rrhh_sst} />
    </div>
  );
}
