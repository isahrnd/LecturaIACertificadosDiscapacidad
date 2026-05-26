import { toDisplayList } from "../utils/analysis";

interface HrRecommendationsPanelProps {
  items: string[];
}

export function HrRecommendationsPanel({
  items,
}: HrRecommendationsPanelProps) {
  const displayItems = toDisplayList(
    items,
    "No se identificaron recomendaciones específicas para RRHH y SST.",
  );

  return (
    <section className="panel-card overflow-hidden">
      <header className="border-b border-almia-100 bg-gradient-to-r from-[#f1fbf9] via-almia-50 to-[#e9f6f8] px-6 py-4">
        <h3 className="panel-title text-almia-700">Recomendaciones para RRHH y SST</h3>
      </header>
      <div className="p-6">
        <ul className="bullet-list text-blue-700">
          {displayItems.map((item) => (
            <li key={item}>{item}</li>
          ))}
        </ul>
      </div>
    </section>
  );
}
