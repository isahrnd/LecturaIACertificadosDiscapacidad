import type { Analysis } from "../types/analysis";
import {
  formatCertificationDate,
  formatLocation,
  getInitials,
  toDisplayList,
} from "../utils/analysis";
import { DisabilityBadge } from "./DisabilityBadge";

interface ProfileHeaderCardProps {
  analysis: Analysis;
}

export function ProfileHeaderCard({ analysis }: ProfileHeaderCardProps) {
  const name =
    analysis.persona.nombre_completo.trim() || "Persona no identificada";
  const documentLabel =
    analysis.persona.documento.trim() || "Documento no disponible";
  const location = formatLocation(analysis);
  const certificationDate = formatCertificationDate(
    analysis.persona.fecha_certificacion,
  );
  const activeConditions = analysis.discapacidades_activas
    .map((item) => item.trim())
    .filter(Boolean);
  const badges = toDisplayList(
    activeConditions,
    "Sin condiciones identificadas",
  );
  const hasActiveConditions = activeConditions.length > 0;

  return (
    <section className="panel-card subtle-grid overflow-hidden bg-gradient-to-r from-white via-[#f7fdfc] to-[#ecf9f7]">
      <div className="space-y-6 p-6 sm:p-8">
        <div className="grid gap-6 lg:grid-cols-[1fr_auto] lg:items-start">
          <div className="flex gap-5">
            <div className="flex h-20 w-20 shrink-0 items-center justify-center rounded-[28px] bg-gradient-to-br from-almia-100 via-almia-200 to-almia-50 text-3xl font-extrabold text-almia-800 shadow-sm">
              {getInitials(name)}
            </div>
            <div className="space-y-1">
              <h2 className="text-3xl font-extrabold tracking-tight text-ink">
                {name}
              </h2>
              <p className="text-lg font-semibold text-slate-700">
                {documentLabel}
              </p>
              <p className="text-sm text-slate-500">
                {location} - Certificado: {certificationDate}
              </p>
              <p className="text-sm text-slate-500">
                IPS: {analysis.persona.ips_certificadora || "No disponible"}
              </p>
            </div>
          </div>

          <div className="flex flex-wrap gap-3 lg:justify-end">
            {badges.map((item) => (
              <DisabilityBadge key={item} label={item} />
            ))}
          </div>
        </div>

        <div className="rounded-[30px] border border-almia-100 bg-white/90 p-5 shadow-sm shadow-almia-100/40">
          <div className="flex flex-col gap-3 border-b border-almia-100/80 pb-4 sm:flex-row sm:items-start sm:justify-between">
            <div>
              <h3 className="text-xl font-extrabold tracking-tight text-ink">
                Discapacidad identificada
              </h3>
              <p className="mt-1 text-sm text-slate-500">
                Se muestran únicamente las condiciones identificadas en el
                certificado.
              </p>
            </div>
            <div className="inline-flex w-fit items-center rounded-full bg-almia-50 px-4 py-2 text-sm font-bold text-almia-700">
              {hasActiveConditions
                ? `${activeConditions.length} condición${activeConditions.length === 1 ? " activa" : "es activas"}`
                : "Sin condiciones activas"}
            </div>
          </div>

          <div
            className={[
              "mt-5",
              hasActiveConditions
                ? "grid gap-4 sm:grid-cols-2 xl:grid-cols-3"
                : "",
            ].join(" ")}
          >
            {hasActiveConditions ? (
              activeConditions.map((item) => (
                <div
                  key={item}
                  className="rounded-[26px] border border-almia-100 bg-gradient-to-br from-almia-50 via-white to-almia-100/80 p-4"
                >
                  <div className="mt-1">
                    <DisabilityBadge label={item} cardLike />
                  </div>
                </div>
              ))
            ) : (
              <div className="rounded-[26px] border border-dashed border-almia-200 bg-gradient-to-r from-almia-50 to-white px-5 py-5 text-sm text-slate-600">
                <p className="font-bold text-almia-700">
                  No se identificaron condiciones activas legibles en el
                  certificado.
                </p>
                <p className="mt-1">
                  El resumen conserva el resto de la información funcional y
                  laboral disponible para esta persona.
                </p>
              </div>
            )}
          </div>
        </div>
      </div>
    </section>
  );
}
