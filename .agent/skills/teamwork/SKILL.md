---
name: teamwork
description: Multi-agent teamwork mode. Hand over complex, multi-step engineering tasks to a parallel multi-agent swarm (orchestrator, interviewer, explorers, workers, reviewers, challenger, sentinel).
---

# /teamwork — MULTI-AGENT SWARM TEAMWORK MODE

## MISSION

Delegate complex, multi-part, or large-scale tasks to the parallel multi-agent team (`teamwork`).

## INSTRUCTIONS FOR AGENT

1. **Do not attempt the task yourself** when the user calls `/teamwork`. Hand it over directly to the teamwork multi-agent team.
2. **If the user's request is empty** (or only contains `/teamwork`), ask the user what specific task or milestone they want the team to execute.
3. **Invoke Teamwork:**
   - Call the `invoke_subagent` tool with:
     - `TypeName`: `"teamwork"`
     - `Model`: `"inherit"` (uses current active model: Gemini 3.8 Flash High)
     - `Role`: Appropriate coordinator title (e.g. `"Full Stack Coordinator"`)
     - `Prompt`: The user's request without the `/teamwork` slash command, keeping any leading bracket parameters such as `[skip-interview]` at the start exactly as typed.
     - Include any relevant context or file paths from the current conversation if needed.
4. **Relay Updates:**
   - When the `teamwork` subagent or its `interviewer` sends updates, clarification questions, or drafts for the user, present them to the user faithfully.
   - If the user asks for progress, message the active teamwork subagent.

