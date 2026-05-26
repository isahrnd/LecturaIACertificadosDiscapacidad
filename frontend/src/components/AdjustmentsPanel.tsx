import type { AjusteRazonable } from "../types/analysis";

interface AdjustmentsPanelProps {
  adjustments: AjusteRazonable[];
}

export function AdjustmentsPanel({ adjustments }: AdjustmentsPanelProps) {
  const items =
    adjustments.length > 0
      ? adjustments
      : [
          {
            titulo: "Ajustes razonables por definir",
            descripcion:
              "No se identificaron ajustes específicos. Se recomienda una revisión conjunta entre RRHH, SST y el liderazgo del cargo.",
            fundamento:
              "La información disponible no permite confirmar ajustes concretos por ahora.",
          },
        ];

  return (
    <section className="panel-card overflow-hidden">
      <header className="border-b border-almia-100 bg-gradient-to-r from-[#f7fbfa] via-almia-50 to-[#eef8f6] px-6 py-4">
        <h3 className="panel-title text-almia-700">Con ajustes razonables</h3>
      </header>
      <div className="space-y-4 p-6">
        {items.map((item) => (
          <article
            key={`${item.titulo}-${item.descripcion}`}
            className="rounded-[22px] border border-almia-100 bg-gradient-to-br from-white via-almia-50 to-almia-100/55 p-5"
          >
            <h4 className="text-lg font-extrabold text-almia-700">
              {item.titulo}
            </h4>
            <p className="mt-2 text-sm leading-7 text-slate-700">
              {item.descripcion}
            </p>
          </article>
        ))}
      </div>
    </section>
  );
}
