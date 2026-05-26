import { splitIntoColumns, toDisplayList } from "../utils/analysis";

interface NotRecommendedPanelProps {
  items: string[];
}

export function NotRecommendedPanel({ items }: NotRecommendedPanelProps) {
  const displayItems = toDisplayList(
    items,
    "No se identificaron restricciones laborales específicas.",
  );
  const columns = splitIntoColumns(displayItems, 3);

  return (
    <section className="panel-card overflow-hidden">
      <header className="border-b border-terracotta-100 bg-gradient-to-r from-terracotta-50 via-[#f9f0f0] to-terracotta-100/70 px-6 py-4">
        <h3 className="panel-title text-terracotta-700">Tareas a evitar o revisar</h3>
      </header>
      <div className="grid gap-6 p-6 md:grid-cols-2 xl:grid-cols-3">
        {columns.map((column, index) => (
          <ul key={index} className="bullet-list text-terracotta-700">
            {column.map((item) => (
              <li key={item}>{item}</li>
            ))}
          </ul>
        ))}
      </div>
    </section>
  );
}
