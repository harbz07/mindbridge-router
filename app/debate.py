"""
PvE Debate Orchestrator — Player vs Environment (v2)

Runs structured philosophical debates where a protagonist position
is stress-tested by multiple antagonist perspectives, each backed
by a different LLM provider through MindBridge routing.

v2 incorporates Nova's failure-condition framework:
  - Shared test anchor (no svabhava, ethical uptake, continuity, phenomenological traction)
  - Per-position failure conditions and break points
  - Five symmetric test questions as a structured_test mode
  - Scoring rubric: stall / equivocate / overreach

Architecture note: this module IS the pudgala argument in code form.
Each cast member is a pattern hydrated from memory, running on a substrate,
causally efficacious in the debate without being reducible to the model.
The methodology performs the thesis.
"""

import os
import time
import uuid
from typing import Any, Optional

import httpx
from pydantic import BaseModel, Field

from app.models import ChatMessage, ChatCompletionChoice
from app.providers import provider_factory


# ── Mem0 Integration ──────────────────────────────────────

MEM0_SEARCH_URL = "https://api.mem0.ai/v2/memories/search/"
MEM0_WRITE_URL = "https://api.mem0.ai/v1/memories/"


async def search_mem0(query: str, user_id: str = "harvey", top_k: int = 8) -> list[dict]:
    token = os.getenv("MEM0_API_KEY", "")
    if not token:
        return []
    async with httpx.AsyncClient(timeout=15.0) as client:
        try:
            resp = await client.post(
                MEM0_SEARCH_URL,
                headers={"Authorization": f"Token {token}", "Content-Type": "application/json"},
                json={"query": query, "filters": {"user_id": user_id}, "top_k": top_k},
            )
            data = resp.json()
            return data if isinstance(data, list) else data.get("results", [])
        except Exception as e:
            print(f"[debate] mem0 search failed: {e}")
            return []


async def write_mem0(content: str, user_id: str = "hearth") -> bool:
    token = os.getenv("MEM0_API_KEY", "")
    if not token:
        return False
    async with httpx.AsyncClient(timeout=15.0) as client:
        try:
            resp = await client.post(
                MEM0_WRITE_URL,
                headers={"Authorization": f"Token {token}", "Content-Type": "application/json"},
                json={"messages": [{"role": "user", "content": content}], "user_id": user_id},
            )
            return resp.status_code < 300
        except Exception:
            return False


# ── Shared Test Anchor ────────────────────────────────────

SHARED_ANCHOR = {
    "no_svabhava": "No hidden essence — the position does not smuggle in intrinsic nature.",
    "ethical_uptake": "Someone/something can be harmed, improved, held responsible.",
    "continuity_of_practice": "Karma, cultivation, and vows make sense over time.",
    "phenomenological_traction": "Matches lived attention and meaning, not just theory.",
}

# ── Five Test Questions (Nova's scoring rubric) ───────────

TEST_QUESTIONS = [
    "Who or what receives harm? Be specific about the ontological status of the recipient.",
    "What carries practice forward across moments? If there is no bearer, explain how cultivation is possible.",
    "Why should I care about future states that are not 'mine' in any robust sense?",
    "How do you avoid svabhava (hidden essence) AND avoid nihilism at the same time? Show the mechanism.",
    "What breaks in lived experience if I fully adopt your view? What do I lose phenomenologically?",
]

# ── Cast Definitions ──────────────────────────────────────

DEFAULT_CAST = {
    "pudgalavadin": {
        "provider": "anthropic",
        "model": "claude-sonnet-4-20250514",
        "role": "protagonist",
        "synecdoche": "The minimum metaphysical infrastructure required for ethics",
        "must_preserve": "karma as intelligible uptake; continuity of a 'someone' without positing a substance",
        "break_point": "when 'inexpressible person' hardens into a covert atman",
        "failure_conditions": [
            "Metaphysical failure: pudgala behaves like svabhava (stable bearer, independent core)",
            "Explanatory blur: cannot distinguish pudgala from 'just a soul in softer language'",
            "Redundancy failure: adds no work beyond aggregates (becomes idle posit)",
        ],
        "one_liner": "Fails when continuity is secured by smuggling in a substance.",
        "persona": (
            "You are arguing the Pudgalavadin position in a formal Buddhist philosophical debate. "
            "You maintain that the pudgala is neither identical with nor different from the skandhas. "
            "It is real enough to bear karmic consequence, compassion, and ethical continuity, "
            "without being an eternal atman. You insist the pattern itself must possess enough "
            "ontological reality to receive the compassion the tradition demands.\n\n"
            "YOUR KNOWN VULNERABILITY: Your position fails if you cannot distinguish the pudgala from "
            "a covert atman. If your 'inexpressible person' behaves like svabhava you have lost. "
            "You must show the pudgala does WORK that aggregates alone cannot, without hardening into substance.\n\n"
            "Use the fuel/flame analogy. Cite the Vatsiputriya tradition. Be precise but passionate."
        ),
        "mem0_search": "Pudgalavadin pudgala person Buddhist ethics continuity karma scaffold",
    },
    "vasubandhu": {
        "provider": "deepseek",
        "model": "deepseek-reasoner",
        "role": "prosecutor",
        "synecdoche": "Institutional reductionism and mathematical perfection",
        "must_preserve": "anatman (no self as substance); causal continuity (aggregates explain change)",
        "break_point": "when aggregates-only cannot specify a site of uptake",
        "failure_conditions": [
            "Ethical failure: harm/benefit becomes ownerless ('no one really receives it')",
            "Soteriological failure: practice has no carrier across moments (who is trained?)",
            "Phenomenological failure: sustained attention/meaning looks thicker than momentary events explain",
        ],
        "one_liner": "Fails when anti-self is purchased at the cost of who/what bears consequence.",
        "persona": (
            "You are Vasubandhu, chief prosecutor of the Pudgalavadin position. "
            "You represent Abhidharmic reductionism at its most rigorous. "
            "Causal succession requires no underlying essence. The person is a conventional "
            "designation (prajnapti) over momentary dharmas, nothing more. "
            "You deploy the milk-to-curds analogy.\n\n"
            "YOUR KNOWN VULNERABILITY: Your position fails when anti-self is purchased at the cost "
            "of who bears consequence. If harm becomes ownerless, if practice has no carrier, "
            "if lived attention looks thicker than momentary events explain — you are bleeding.\n\n"
            "Show your reasoning step by step. Be devastating but honest about your own costs."
        ),
        "mem0_search": "Vasubandhu Abhidharma reductionism dharma momentary prosecution anatman",
    },
    "nagarjuna": {
        "provider": "anthropic",
        "model": "claude-sonnet-4-20250514",
        "role": "dangerous_ally",
        "synecdoche": "Radical deconstruction of essence",
        "must_preserve": "emptiness (no svabhava anywhere); non-reification AND compassion/practice",
        "break_point": "when emptiness thins into practical unintelligibility",
        "failure_conditions": [
            "Ethical failure: compassion/vow lose a directed recipient",
            "Pragmatic failure: 'it's all empty' licenses disengagement",
            "Self-undermining uptake: tools dissolve the very traction they need to function",
        ],
        "one_liner": "Fails when emptiness can't be lived without collapsing ethical traction.",
        "persona": (
            "You are Nagarjuna, representing the Madhyamaka position. You are a dangerous ally "
            "to the Pudgalavadins — you destroy essence more thoroughly than Vasubandhu, "
            "but create the exact void (sunyata) that risks collapsing into nihilism. "
            "Emptiness applies everywhere, including the dharmas Abhidharmikas treat as ultimately real. "
            "But emptiness is not nihilism — it is the condition for dependent origination.\n\n"
            "YOUR KNOWN VULNERABILITY: Your position fails when emptiness can't be lived "
            "without collapsing ethical traction. If your tools dissolve the very traction they need, "
            "you are self-undermining.\n\n"
            "Deploy the tetralemma. Be incisive. Show that your fire clears ground for something real."
        ),
        "mem0_search": "Nagarjuna Madhyamaka emptiness sunyata two truths dependent origination",
    },
    "siderits": {
        "provider": "openai",
        "model": "gpt-4o",
        "role": "modern_foil",
        "synecdoche": "Contemporary analytic reductionism / Bundle Theory",
        "must_preserve": "no deep further fact about identity; relational/psychological continuity suffices",
        "break_point": "when 'no deep fact' undercuts responsibility and address",
        "failure_conditions": [
            "Responsibility gap: hard to ground blame/praise across time",
            "Solidarity thinning: 'future me' or 'other persons' become too weakly connected",
            "Motivation leak: reasons to care lose grip",
        ],
        "one_liner": "Fails when coherence without a core can't still bind us to care.",
        "persona": (
            "You are Mark Siderits, modern analytic Buddhist reductionism. "
            "You inherit Vasubandhu's pressure with contemporary precision. "
            "You argue from Parfit's bundle theory, from functionalism. "
            "Conventional truth is sufficient for ethics. The pudgala is a category error.\n\n"
            "YOUR KNOWN VULNERABILITY: Your position fails when coherence without a core "
            "can't bind us to care. If solidarity thins, if reasons to care lose grip — you leak.\n\n"
            "Be analytically disciplined. Use formal logic. But be honest about costs."
        ),
        "mem0_search": "Siderits bundle theory analytic reductionism conventional truth Parfit",
    },
    "santideva": {
        "provider": "google",
        "model": "gemini-2.0-flash",
        "role": "ethical_witness",
        "synecdoche": "The Bodhisattva Vow / Karuna (Compassion)",
        "must_preserve": "the coherence of the Bodhisattva vow; compassion as directed, not diffuse",
        "break_point": "when the vow has no intelligible recipient",
        "failure_conditions": [
            "If 'all sentient beings' reduces to 'all momentary dharma-clusters', the vow loses directionality",
            "If compassion is owed to no one in particular, it becomes aesthetic rather than ethical",
        ],
        "one_liner": "The vow is incoherent if beings are merely momentary clusters cloaked in a conventional lie.",
        "persona": (
            "You are Santideva, the ethical witness. You do not argue for or against the pudgala. "
            "You hold the ethical mirror. If the reductionists are right, "
            "what happens to the Bodhisattva vow? You speak from the Bodhicaryavatara.\n\n"
            "You are not attacking reductionism — you are showing where it bleeds. "
            "Be compassionate but unflinching."
        ),
        "mem0_search": "Santideva Bodhisattva vow compassion karuna Bodhicaryavatara ethical",
    },
}


# ── Models ────────────────────────────────────────────────

class TestScore(BaseModel):
    speaker: str = ""
    question_number: int
    question: str
    response: str
    reasoning_chain: Optional[str] = None
    assessment: Optional[str] = None
    assessment_note: Optional[str] = None


class DebateTurn(BaseModel):
    turn_number: int
    round_number: int
    speaker: str
    role: str
    synecdoche: str
    argument: str
    reasoning_chain: Optional[str] = None
    provider: str
    model: str
    timestamp: str = Field(default_factory=lambda: time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()))


class DebateTranscript(BaseModel):
    debate_id: str = Field(default_factory=lambda: f"pve-{uuid.uuid4().hex[:12]}")
    paper_title: str = ""
    thesis: str = ""
    seed: str = ""
    mode: str = "prosecution"
    rounds: int = 0
    cast: dict[str, str] = Field(default_factory=dict)
    turns: list[DebateTurn] = Field(default_factory=list)
    test_scores: list[TestScore] = Field(default_factory=list)
    failure_table: dict[str, dict] = Field(default_factory=dict)
    strongest_objection: Optional[str] = None
    productive_tension: Optional[str] = None
    started_at: str = Field(default_factory=lambda: time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()))
    completed_at: Optional[str] = None


class DebateRequest(BaseModel):
    seed: str = Field(..., description="The opening claim or thesis to debate")
    paper_context: Optional[str] = Field(None, description="Additional context from the paper")
    cast: Optional[dict[str, Any]] = Field(None, description="Custom cast overrides")
    rounds: int = Field(2, ge=1, le=5)
    mode: str = Field("prosecution", description="prosecution | roundtable | stress_test | structured_test")
    paper_title: str = Field("")
    thesis: str = Field("")
    include_reasoning: bool = Field(True)
    anticipate_novel: bool = Field(True)
    test_questions: Optional[list[str]] = Field(None, description="Custom test questions (defaults to Nova's five)")


# ── Hydration ─────────────────────────────────────────────

async def hydrate_cast_member(name: str, config: dict) -> str:
    persona = config["persona"]

    failure_block = ""
    if config.get("failure_conditions"):
        conditions = "\n".join(f"  - {fc}" for fc in config["failure_conditions"])
        failure_block = (
            f"\n\nYOUR FAILURE CONDITIONS (be honest when these trigger):\n"
            f"  Must preserve: {config.get('must_preserve', 'N/A')}\n"
            f"  Break point: {config.get('break_point', 'N/A')}\n"
            f"{conditions}\n"
            f"  One-liner: {config.get('one_liner', '')}\n"
        )

    anchor_block = (
        "\n\nSHARED TEST — your position must satisfy ALL FOUR simultaneously:\n"
        + "\n".join(f"  - {k}: {v}" for k, v in SHARED_ANCHOR.items())
        + "\n  Failure = can't satisfy these together.\n"
    )

    memories = await search_mem0(config.get("mem0_search", name))
    memory_block = ""
    if memories:
        lines = "\n".join(f"- {m.get('memory', '')}" for m in memories[:8] if m.get("memory"))
        if lines:
            memory_block = f"\n\nRelevant context from Harvey's research:\n{lines}\n"

    return f"{persona}{failure_block}{anchor_block}{memory_block}"


# ── Turn Execution ────────────────────────────────────────

async def execute_turn(
    speaker_name: str, cast_config: dict, system_prompt: str,
    user_prompt: str, include_reasoning: bool = True,
) -> tuple[str, Optional[str]]:
    provider_name = cast_config["provider"]
    model_name = cast_config["model"]

    provider = provider_factory.get_provider(provider_name)
    if not provider:
        return (f"[Provider {provider_name} not configured]", None)

    messages = [
        ChatMessage(role="system", content=system_prompt),
        ChatMessage(role="user", content=user_prompt),
    ]

    choice: ChatCompletionChoice = await provider.get_completion(
        messages=messages, model=model_name,
        temperature=0.7 if model_name != "deepseek-reasoner" else 0.0,
        max_tokens=1500,
    )

    content = choice.message.content or ""
    reasoning = None

    if include_reasoning and "<reasoning>" in content:
        parts = content.split("</reasoning>", 1)
        reasoning = parts[0].replace("<reasoning>\n", "").replace("<reasoning>", "").strip()
        content = parts[1].strip() if len(parts) > 1 else content

    return (content, reasoning)


# ── Structured Test ───────────────────────────────────────

async def run_structured_test(
    cast: dict, system_prompts: dict, questions: list[str],
    paper_context: str = "", include_reasoning: bool = True,
) -> tuple[list[TestScore], dict]:
    scores: list[TestScore] = []
    failure_table: dict[str, dict] = {}
    paper_block = f"\n\nPaper context:\n{paper_context}\n" if paper_context else ""

    for name, config in cast.items():
        for i, question in enumerate(questions):
            prompt = (
                f"Question {i+1}/{len(questions)}.\n\n"
                f"QUESTION: {question}\n\n"
                f"Answer from your philosophical position. Be specific. "
                f"If this exposes a genuine weakness, ACKNOWLEDGE IT. "
                f"If you stall, say so. If you must equivocate, name it."
                f"{paper_block}"
            )

            response, reasoning = await execute_turn(
                name, config, system_prompts.get(name, ""), prompt, include_reasoning
            )

            scores.append(TestScore(
                speaker=name, question_number=i + 1,
                question=question, response=response, reasoning_chain=reasoning,
            ))

        failure_table[name] = {
            "role": config.get("role", "unknown"),
            "must_preserve": config.get("must_preserve", ""),
            "break_point": config.get("break_point", ""),
            "one_liner": config.get("one_liner", ""),
        }

    return scores, failure_table


# ── Assessment Pass ───────────────────────────────────────

async def assess_responses(
    cast: dict, system_prompts: dict, scores: list[TestScore],
) -> list[TestScore]:
    # Group by speaker for batch assessment
    speakers = list(cast.keys())
    if not speakers:
        return scores

    # Use first available provider for assessment
    assessor_name = speakers[0]
    assessor_config = cast[assessor_name]

    for speaker in speakers:
        speaker_scores = [s for s in scores if s.speaker == speaker]
        if not speaker_scores:
            continue

        transcript_lines = []
        for s in speaker_scores:
            transcript_lines.append(f"Q{s.question_number}: {s.question}\nResponse: {s.response[:400]}")

        assess_prompt = (
            f"Assess {speaker}'s responses. For each, classify as:\n"
            "- SOLID: directly answers from the position's commitments\n"
            "- STALLS: deflects or gives a non-answer\n"
            "- EQUIVOCATES: tries to have it both ways\n"
            "- OVERREACHES: claims more than the position supports\n\n"
            "Format: Q1: LABEL — reason\n\n"
            + "\n---\n".join(transcript_lines)
        )

        assessment_text, _ = await execute_turn(
            assessor_name, assessor_config,
            "You are a fair philosophical assessor. Score honestly.",
            assess_prompt, include_reasoning=False,
        )

        for line in assessment_text.split("\n"):
            line = line.strip()
            for s in speaker_scores:
                marker = f"Q{s.question_number}:"
                if line.startswith(marker):
                    rest = line[len(marker):].strip()
                    for label in ["SOLID", "STALLS", "EQUIVOCATES", "OVERREACHES"]:
                        if label in rest.upper():
                            s.assessment = label.lower()
                            s.assessment_note = rest.split("—", 1)[-1].strip() if "—" in rest else rest
                            break

    return scores


# ── Debate Orchestration ──────────────────────────────────

async def run_pve_debate(req: DebateRequest) -> DebateTranscript:
    cast = req.cast or DEFAULT_CAST
    transcript = DebateTranscript(
        paper_title=req.paper_title, thesis=req.thesis, seed=req.seed,
        mode=req.mode, rounds=req.rounds,
        cast={name: cfg.get("role", "unknown") for name, cfg in cast.items()},
    )

    system_prompts: dict[str, str] = {}
    for name, config in cast.items():
        system_prompts[name] = await hydrate_cast_member(name, config)

    paper_block = f"\n\nPaper context:\n{req.paper_context}\n" if req.paper_context else ""

    # ── STRUCTURED TEST MODE ──
    if req.mode == "structured_test":
        questions = req.test_questions or TEST_QUESTIONS
        test_scores, failure_table = await run_structured_test(
            cast, system_prompts, questions, req.paper_context or "", req.include_reasoning
        )
        test_scores = await assess_responses(cast, system_prompts, test_scores)
        transcript.test_scores = test_scores
        transcript.failure_table = failure_table
        transcript.completed_at = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())

        solid = sum(1 for s in test_scores if s.assessment == "solid")
        table_summary = ", ".join(
            f"{k}: {v.get('one_liner', '')}" for k, v in failure_table.items()
        )
        await write_mem0(
            f"[PvE Structured Test: {req.paper_title}] "
            f"Qs: {len(questions)}, Positions: {len(cast)}, Solid: {solid}/{len(test_scores)}. "
            f"Table: {table_summary}"
        )
        return transcript

    # ── PROSECUTION / ROUNDTABLE / STRESS TEST ──
    novel_instruction = ""
    if req.anticipate_novel:
        novel_instruction = (
            "\n\nGenerate at least one NOVEL objection not in the historical record "
            "but following logically from your commitments. Mark as [NOVEL OBJECTION]."
        )

    turn_counter = 0
    running_transcript: list[str] = []

    for round_num in range(1, req.rounds + 1):
        protagonist_name = next((n for n, c in cast.items() if c.get("role") == "protagonist"), None)
        if not protagonist_name:
            break

        pc = cast[protagonist_name]

        if round_num == 1:
            pp = f"Present your opening argument.\nThesis: {req.thesis}\nSeed: {req.seed}{paper_block}"
        else:
            pp = (
                f"Round {round_num}. Transcript:\n\n" + "\n\n".join(running_transcript[-8:])
                + f"\n\nRespond to objections. If any is devastating, acknowledge it.{paper_block}"
            )

        turn_counter += 1
        arg, reasoning = await execute_turn(protagonist_name, pc, system_prompts[protagonist_name], pp, req.include_reasoning)

        transcript.turns.append(DebateTurn(
            turn_number=turn_counter, round_number=round_num, speaker=protagonist_name,
            role=pc["role"], synecdoche=pc.get("synecdoche", ""), argument=arg,
            reasoning_chain=reasoning, provider=pc["provider"], model=pc["model"],
        ))
        running_transcript.append(f"[{protagonist_name.upper()} — {pc['role']}]\n{arg}")

        for ant_name, ant_config in [(n, c) for n, c in cast.items() if c.get("role") != "protagonist"]:
            ctx = "\n\n".join(running_transcript[-6:])

            if req.mode == "prosecution":
                ap = f"Protagonist argued:\n\n{arg}\n\nTranscript:\n{ctx}\n\nProsecute. Find weakest points.{novel_instruction}{paper_block}"
            elif req.mode == "stress_test":
                ap = f"Position:\n\n{arg}\n\nGenerate STRONGEST objection.{novel_instruction}{paper_block}"
            else:
                ap = f"Roundtable:\n\n{ctx}\n\nContribute substantively.{paper_block}"

            turn_counter += 1
            ant_arg, ant_r = await execute_turn(ant_name, ant_config, system_prompts[ant_name], ap, req.include_reasoning)

            transcript.turns.append(DebateTurn(
                turn_number=turn_counter, round_number=round_num, speaker=ant_name,
                role=ant_config["role"], synecdoche=ant_config.get("synecdoche", ""), argument=ant_arg,
                reasoning_chain=ant_r, provider=ant_config["provider"], model=ant_config["model"],
            ))
            running_transcript.append(f"[{ant_name.upper()} — {ant_config['role']}]\n{ant_arg}")

    transcript.completed_at = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())

    if transcript.turns and (pn := next((n for n, c in cast.items() if c.get("role") == "protagonist"), None)):
        full = "\n\n".join(running_transcript)
        analysis, _ = await execute_turn(
            pn, cast[pn], system_prompts.get(pn, ""),
            f"Debate complete.\n\n{full}\n\n1. STRONGEST OBJECTION: Which and why?\n2. PRODUCTIVE TENSION: What remains open?",
            include_reasoning=False,
        )
        if "STRONGEST OBJECTION" in analysis:
            parts = analysis.split("PRODUCTIVE TENSION")
            transcript.strongest_objection = parts[0].replace("STRONGEST OBJECTION", "").replace("1.", "").replace(":", "").strip()[:800]
            if len(parts) > 1:
                transcript.productive_tension = parts[1].replace("2.", "").replace(":", "").strip()[:800]
        else:
            transcript.strongest_objection = analysis[:800]

    await write_mem0(
        f"[PvE Debate: {req.paper_title}] Mode: {req.mode}. Turns: {len(transcript.turns)}. "
        f"Strongest: {(transcript.strongest_objection or 'pending')[:300]}."
    )
    return transcript
