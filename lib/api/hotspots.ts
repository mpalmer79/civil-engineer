import { PROJECT_ID, safeFetch } from "./client";
import { hotspots as staticHotspots, type Hotspot } from "@/data/hotspots";

type ApiHotspot = {
  hotspot_id: string;
  name: string;
  category: Hotspot["category"];
  short_description: string;
  civil_purpose: string;
  related_checklist_items: string[];
  related_planted_issues: string[];
  future_drilldown: string;
  position_x_percent: number;
  position_y_percent: number;
};

export async function getHotspots(): Promise<Hotspot[]> {
  const data = await safeFetch<ApiHotspot[]>(
    `/api/v1/projects/${PROJECT_ID}/hotspots`,
  );
  if (!data) return staticHotspots;
  return data.map((h) => ({
    id: h.hotspot_id,
    name: h.name,
    category: h.category,
    shortDescription: h.short_description,
    civilPurpose: h.civil_purpose,
    relatedChecklistItems: h.related_checklist_items,
    relatedPlantedIssues: h.related_planted_issues,
    futureDrilldown: h.future_drilldown,
    position: { xPercent: h.position_x_percent, yPercent: h.position_y_percent },
  }));
}
