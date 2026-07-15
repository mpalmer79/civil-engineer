"""SQLAlchemy models for the Civil Engineer AI backend.

The models are organized into domain modules (ADR 0005): identity, billing,
cad, command_center, projects, documents, evidence, checklists, findings,
evaluation, plans, review_packets, workflow, response_packages, review_cycles,
responses, and audit. Every class is re-exported here so both import styles
keep working unchanged:

    from app.db import models; models.Project
    from app.db.models import Project

Table names, columns, constraints, and relationships are unchanged by the
module split; no migration accompanies it."""

from app.db.database import Base
from app.db.models.shared import _utcnow

from app.db.models.identity import (
    Actor,
    Organization,
    OrganizationInvitation,
    OrganizationMembership,
    PasswordResetToken,
    PilotRequest,
    ProjectAccess,
    UserAccount,
)
from app.db.models.billing import (
    BillingEvent,
    OrganizationSubscription,
    UsageEvent,
)
from app.db.models.cad import (
    CadBlockExtract,
    CadEntityExtract,
    CadFileUpload,
    CadLayerExtract,
    CadParseRun,
    CadReferenceCandidate,
    CadReviewFinding,
    CadTextExtract,
)
from app.db.models.command_center import (
    DashboardReviewerNote,
    ProjectCommandCenterSnapshot,
    ProjectHealthMetric,
    ProjectTimelineEvent,
    ReviewReadinessCheck,
    ReviewerAttentionItem,
)
from app.db.models.projects import Project
from app.db.models.documents import (
    ChunkEmbedding,
    Document,
    DocumentChunk,
    DocumentPage,
    Hotspot,
)
from app.db.models.evidence import (
    EvidenceCandidate,
    EvidenceCitation,
    RetrievalQuery,
)
from app.db.models.checklists import (
    ChecklistEvidenceLink,
    ChecklistItem,
    ProjectChecklist,
    ProjectChecklistItem,
    RulePack,
    RulePackItem,
)
from app.db.models.findings import (
    AIDraftFinding,
    AIReviewRun,
    Finding,
    FindingSource,
    HumanReviewAction,
    TraceabilityReviewAction,
)
from app.db.models.evaluation import (
    AIEvaluationMatch,
    AIEvaluationResult,
    EvaluationCase,
)
from app.db.models.plans import (
    CadMetadata,
    PlanConsistencyFinding,
    PlanConsistencyReviewAction,
    PlanReference,
    PlanSheet,
    PlanSheetHotspot,
)
from app.db.models.review_packets import (
    ReviewPacket,
    ReviewPacketEvidenceLink,
    ReviewPacketItem,
    ReviewPacketReviewerAction,
    ReviewPacketSection,
)
from app.db.models.workflow import (
    WorkflowAction,
    WorkflowFollowUpRequest,
    WorkflowItem,
)
from app.db.models.response_packages import (
    ResponsePackage,
    ResponsePackageAction,
    ResponsePackageAttachment,
    ResponsePackageEvidenceLink,
    ResponsePackageItem,
    ResponsePackageSection,
)
from app.db.models.review_cycles import (
    ApplicantResponse,
    ApplicantResponseMapping,
    IssueCarryForward,
    NextCyclePreparation,
    ResponseResolutionRecord,
    ResubmittalDocument,
    ResubmittalPackage,
    ResubmittalRound,
    ReviewCycle,
    RevisionChangeRecord,
    RevisionComparisonRun,
)
from app.db.models.responses import (
    CommentLetterDraft,
    MatrixItemDocumentLink,
    ResponseMatrix,
    ResponseMatrixItem,
    ReviewerResponsePackage,
    ReviewerResponsePackageItem,
    ReviewerResponsePackageRevision,
)
from app.db.models.audit import AuditEvent

__all__ = [
    "AIDraftFinding",
    "AIEvaluationMatch",
    "AIEvaluationResult",
    "AIReviewRun",
    "Actor",
    "ApplicantResponse",
    "ApplicantResponseMapping",
    "AuditEvent",
    "BillingEvent",
    "CadBlockExtract",
    "CadEntityExtract",
    "CadFileUpload",
    "CadLayerExtract",
    "CadMetadata",
    "CadParseRun",
    "CadReferenceCandidate",
    "CadReviewFinding",
    "CadTextExtract",
    "ChecklistEvidenceLink",
    "ChecklistItem",
    "ChunkEmbedding",
    "CommentLetterDraft",
    "DashboardReviewerNote",
    "Document",
    "DocumentChunk",
    "DocumentPage",
    "EvaluationCase",
    "EvidenceCandidate",
    "EvidenceCitation",
    "Finding",
    "FindingSource",
    "Hotspot",
    "HumanReviewAction",
    "IssueCarryForward",
    "MatrixItemDocumentLink",
    "NextCyclePreparation",
    "Organization",
    "OrganizationInvitation",
    "OrganizationMembership",
    "OrganizationSubscription",
    "PasswordResetToken",
    "PilotRequest",
    "PlanConsistencyFinding",
    "PlanConsistencyReviewAction",
    "PlanReference",
    "PlanSheet",
    "PlanSheetHotspot",
    "Project",
    "ProjectAccess",
    "ProjectChecklist",
    "ProjectChecklistItem",
    "ProjectCommandCenterSnapshot",
    "ProjectHealthMetric",
    "ProjectTimelineEvent",
    "ResponseMatrix",
    "ResponseMatrixItem",
    "ResponsePackage",
    "ResponsePackageAction",
    "ResponsePackageAttachment",
    "ResponsePackageEvidenceLink",
    "ResponsePackageItem",
    "ResponsePackageSection",
    "ResponseResolutionRecord",
    "ResubmittalDocument",
    "ResubmittalPackage",
    "ResubmittalRound",
    "RetrievalQuery",
    "ReviewCycle",
    "ReviewPacket",
    "ReviewPacketEvidenceLink",
    "ReviewPacketItem",
    "ReviewPacketReviewerAction",
    "ReviewPacketSection",
    "ReviewReadinessCheck",
    "ReviewerAttentionItem",
    "ReviewerResponsePackage",
    "ReviewerResponsePackageItem",
    "ReviewerResponsePackageRevision",
    "RevisionChangeRecord",
    "RevisionComparisonRun",
    "RulePack",
    "RulePackItem",
    "TraceabilityReviewAction",
    "UsageEvent",
    "UserAccount",
    "WorkflowAction",
    "WorkflowFollowUpRequest",
    "WorkflowItem",
    "Base",
    "_utcnow",
]
