import { PROJECT_ID, safeFetch } from "./client";
import { brookside, type BrooksideProject } from "@/data/brookside";

// Backend payload shapes (snake_case), kept local to the mapping layer.

type ApiProject = {
  project_id: string;
  project_name: string;
  project_type: string;
  location_context: string;
  jurisdiction: string;
  review_type: string;
  review_domain: string;
  acreage: number;
  disturbed_area: number;
  proposed_lots: number;
  status: string;
  summary: string;
  site_conditions: { type: string; label: string; description: string }[];
  proposed_improvements: {
    type: string;
    label: string;
    aliases: string[];
    description: string;
  }[];
  known_constraints: string[];
};

export async function getProject(): Promise<BrooksideProject> {
  const data = await safeFetch<ApiProject>(`/api/v1/projects/${PROJECT_ID}`);
  if (!data) return brookside;
  return {
    projectId: data.project_id,
    projectName: data.project_name,
    projectType: data.project_type,
    locationContext: data.location_context,
    jurisdiction: data.jurisdiction,
    reviewType: data.review_type,
    reviewDomain: data.review_domain,
    acreage: data.acreage,
    disturbedAcres: data.disturbed_area,
    proposedLots: data.proposed_lots,
    status: data.status,
    hasInfiltrationPractice: brookside.hasInfiltrationPractice,
    hasDetentionBasin: brookside.hasDetentionBasin,
    summary: data.summary,
    siteConditions: data.site_conditions,
    proposedImprovements: data.proposed_improvements,
    knownConstraints: data.known_constraints,
  };
}
