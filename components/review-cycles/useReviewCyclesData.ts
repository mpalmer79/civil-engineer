"use client";

import { useCallback, useEffect, useMemo, useState } from "react";

import type { ApiFailure } from "@/lib/api/client";
import {
  getApplicantResponses,
  getCadFiles,
  getCadParseRuns,
  getCarryForwards,
  getResubmittalPackages,
  getResponseResolutionRecords,
  getReviewCycleDashboard,
  getReviewCycles,
  type ApplicantResponse,
  type ApplicantResponseMapping,
  type CadFileUpload,
  type CadParseRun,
  type IssueCarryForward,
  type NextCyclePreparation,
  type ResponseResolutionRecord,
  type ResubmittalPackage,
  type RevisionChangeRecord,
  type RevisionComparisonRun,
  type ReviewCycle,
  type ReviewCycleDashboard as ReviewCycleDashboardData,
} from "@/lib/api";

// Backend-canonical state for the multi-round review cycle experience. The
// browser does not simulate review cycle data.
export function useReviewCyclesData() {
  const [loaded, setLoaded] = useState(false);
  const [cycles, setCycles] = useState<ReviewCycle[]>([]);
  const [activeCycleId, setActiveCycleId] = useState<string | null>(null);
  const [dashboard, setDashboard] = useState<ReviewCycleDashboardData | null>(
    null,
  );
  const [resubmittals, setResubmittals] = useState<ResubmittalPackage[]>([]);
  const [selectedResubmittalId, setSelectedResubmittalId] = useState<
    string | null
  >(null);
  const [responses, setResponses] = useState<ApplicantResponse[]>([]);
  const [mappings, setMappings] = useState<ApplicantResponseMapping[]>([]);
  const [cadFiles, setCadFiles] = useState<CadFileUpload[]>([]);
  const [parseRuns, setParseRuns] = useState<CadParseRun[]>([]);
  const [comparison, setComparison] = useState<RevisionComparisonRun | null>(
    null,
  );
  const [changes, setChanges] = useState<RevisionChangeRecord[]>([]);
  const [carryForwards, setCarryForwards] = useState<IssueCarryForward[]>([]);
  const [resolutions, setResolutions] = useState<ResponseResolutionRecord[]>([]);
  const [preparation, setPreparation] = useState<NextCyclePreparation | null>(
    null,
  );
  const [busy, setBusy] = useState(false);
  const [failure, setFailure] = useState<ApiFailure | null>(null);
  const [message, setMessage] = useState<string | null>(null);
  const [carryMessage, setCarryMessage] = useState<string | null>(null);

  const activeCycle = useMemo(
    () => cycles.find((c) => c.reviewCycleId === activeCycleId) ?? null,
    [cycles, activeCycleId],
  );

  const responsesById = useMemo(() => {
    const map: Record<string, ApplicantResponse> = {};
    for (const response of responses) map[response.applicantResponseId] = response;
    return map;
  }, [responses]);

  const refreshCycleData = useCallback(async (cycleId: string | null) => {
    const [resubsResult, respsResult, resolsResult, cfsResult, dashboardResult] =
      await Promise.all([
        getResubmittalPackages(),
        getApplicantResponses(),
        getResponseResolutionRecords(),
        getCarryForwards(),
        getReviewCycleDashboard(),
      ]);
    const results = [resubsResult, respsResult, resolsResult, cfsResult, dashboardResult];
    const firstFailure = results.find((r) => !r.ok);
    setFailure(firstFailure && !firstFailure.ok ? firstFailure : null);
    const resubs = resubsResult.ok ? resubsResult.data : [];
    const resps = respsResult.ok ? respsResult.data : [];
    const resols = resolsResult.ok ? resolsResult.data : [];
    const cfs = cfsResult.ok ? cfsResult.data : [];
    setResubmittals(resubs);
    setResponses(
      cycleId ? resps.filter((r) => r.reviewCycleId === cycleId) : resps,
    );
    setResolutions(
      cycleId ? resols.filter((r) => r.reviewCycleId === cycleId) : resols,
    );
    setCarryForwards(
      cycleId ? cfs.filter((c) => c.reviewCycleId === cycleId) : cfs,
    );
    setDashboard(dashboardResult.ok ? dashboardResult.data : null);
  }, []);

  useEffect(() => {
    (async () => {
      const [cycResult, filesResult, runsResult] = await Promise.all([
        getReviewCycles(),
        getCadFiles(),
        getCadParseRuns(),
      ]);
      const cyc = cycResult.ok ? cycResult.data : [];
      setCycles(cyc);
      setCadFiles(filesResult.ok ? filesResult.data : []);
      setParseRuns(runsResult.ok ? runsResult.data : []);
      const loadFailure = [cycResult, filesResult, runsResult].find((r) => !r.ok);
      if (loadFailure && !loadFailure.ok) setFailure(loadFailure);
      const active =
        cyc.find((c) => c.status === "active")?.reviewCycleId ??
        (cyc.length > 0 ? cyc[cyc.length - 1].reviewCycleId : null);
      setActiveCycleId(active);
      await refreshCycleData(active);
      setLoaded(true);
    })();
  }, [refreshCycleData]);

  return {
    loaded,
    cycles,
    setCycles,
    activeCycleId,
    setActiveCycleId,
    dashboard,
    resubmittals,
    setResubmittals,
    selectedResubmittalId,
    setSelectedResubmittalId,
    responses,
    mappings,
    setMappings,
    cadFiles,
    parseRuns,
    comparison,
    setComparison,
    changes,
    setChanges,
    carryForwards,
    resolutions,
    preparation,
    setPreparation,
    busy,
    setBusy,
    failure,
    setFailure,
    message,
    setMessage,
    carryMessage,
    setCarryMessage,
    activeCycle,
    responsesById,
    refreshCycleData,
  };
}

export type ReviewCyclesData = ReturnType<typeof useReviewCyclesData>;
