import type { TareasRecomendadas } from "../types/analysis";
import { toDisplayList } from "../utils/analysis";

interface RecommendedTasksPanelProps {
  tasks: TareasRecomendadas;
}

export function RecommendedTasksPanel({
  tasks,
}: RecommendedTasksPanelProps) {
  const sections = [
    {
      title: "Administrativo / oficina",
      items: toDisplayList(
        tasks.administrativo_oficina,
        "No se identificaron tareas administrativas específicas.",
      ),
    },
    {
      title: "Operativo / manual liviano",
      items: toDisplayList(
        tasks.operativo_manual_liviano,
        "No se identificaron tareas operativas livianas específicas.",
      ),
    },
    {
      title: "Relacional / apoyo",
      items: toDisplayList(
        tasks.relacional_apoyo,
        "No se identificaron tareas de apoyo relacional específicas.",
      ),
    },
  ];

  return (
    <section className="panel-card overflow-hidden">
      <header className="border-b border-almia-100 bg-gradient-to-r from-almia-50 via-[#edf9f7] to-almia-100/90 px-6 py-4">
        <h3 className="panel-title text-almia-700">Tareas recomendadas</h3>
      </header>
      <div className="space-y-6 p-6">
        {sections.map((section, index) => (
          <div
            key={section.title}
            className={index < sections.length - 1 ? "border-b border-line pb-6" : ""}
          >
            <h4 className="mb-3 text-xl font-extrabold text-almia-700">
              {section.title}
            </h4>
            <ul className="bullet-list text-slate-700">
              {section.items.map((item) => (
                <li key={item}>{item}</li>
              ))}
            </ul>
          </div>
        ))}
      </div>
    </section>
  );
}
