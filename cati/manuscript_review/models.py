"""Data models for the manuscript review system."""
from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Literal


class AgentRole(str, Enum):
    """Review agent roles (Phase 1)."""

    HOOK_SPECIALIST = "hook_specialist"
    STRUCTURE_EDITOR = "structure_editor"
    NARRATIVE_EDITOR = "narrative_editor"
    TARGET_AUDIENCE = "target_audience"
    FACT_CHECKER = "fact_checker"


class ExpertRole(str, Enum):
    """Expert editor roles (Phase 2)."""

    OPENING_ARCHITECT = "opening_architect"
    FLOW_SURGEON = "flow_surgeon"
    VOICE_POLISHER = "voice_polisher"


class Priority(str, Enum):
    """Review finding priority."""

    P1_CRITICAL = "P1"
    P2_SIGNIFICANT = "P2"
    P3_POLISH = "P3"


class FindingCategory(str, Enum):
    """Category of a review finding."""

    CRITICAL = "critical"
    SIGNIFICANT = "significant"
    OBSERVATION = "observation"


@dataclass
class Finding:
    """A single review finding from an agent."""

    location: str
    problem: str
    suggestion: str
    category: FindingCategory
    priority: Priority | None = None


@dataclass
class AgentReview:
    """Output from a single review agent."""

    agent_role: AgentRole
    agent_name: str
    overall_assessment: str
    critical_findings: list[Finding]
    significant_findings: list[Finding]
    observations: list[Finding]
    summary_points: list[str]
    raw_output: str
    extra_data: dict = field(default_factory=dict)


@dataclass
class SynthesizedFinding:
    """A finding after synthesis with assigned priority."""

    finding: Finding
    source_agents: list[AgentRole]
    priority: Priority
    action: str


@dataclass
class ReviewSynthesis:
    """Combined and prioritized output from all review agents."""

    p1_critical: list[SynthesizedFinding]
    p2_significant: list[SynthesizedFinding]
    p3_polish: list[SynthesizedFinding]
    raw_output: str


@dataclass
class ExpertEdit:
    """Output from an expert editor."""

    expert_role: ExpertRole
    expert_name: str
    changes: list[dict]
    editor_notes: str
    raw_output: str


@dataclass
class ManuscriptChunk:
    """A chunk of the manuscript for processing."""

    chapter: str
    content: str
    word_count: int
    chunk_index: int
    total_chunks: int


@dataclass
class ReviewSession:
    """Complete review session tracking."""

    manuscript_path: str
    chunks: list[ManuscriptChunk] = field(default_factory=list)
    agent_reviews: dict[str, AgentReview] = field(default_factory=dict)
    synthesis: ReviewSynthesis | None = None
    expert_edits: dict[str, ExpertEdit] = field(default_factory=dict)
    status: Literal["pending", "reviewing", "synthesizing", "editing", "complete"] = "pending"
