import type { ExtensionAPI } from "@mariozechner/pi-coding-agent";
import { Type } from "typebox";
import { readFileSync, existsSync, readdirSync } from "node:fs";
import { join, resolve } from "node:path";

const SKILLS_DIR = resolve(
  process.env.HOME || "~",
  ".pi/agent/skills"
);

function loadSkills(): Array<{ name: string; description: string; content: string; dir: string }> {
  const skills: Array<{ name: string; description: string; content: string; dir: string }> = [];
  if (!existsSync(SKILLS_DIR)) return skills;

  const dirs = readdirSync(SKILLS_DIR, { withFileTypes: true })
    .filter(d => d.isDirectory())
    .map(d => d.name);

  for (const dir of dirs) {
    const skillFile = join(SKILLS_DIR, dir, "SKILL.md");
    if (!existsSync(skillFile)) continue;

    const raw = readFileSync(skillFile, "utf-8");
    let name = dir;
    let description = "";
    let content = raw;

    if (raw.startsWith("---")) {
      const end = raw.indexOf("---", 3);
      if (end !== -1) {
        const fm = raw.slice(3, end).trim();
        content = raw.slice(end + 3).trim();
        for (const line of fm.split("\n")) {
          const ci = line.indexOf(":");
          if (ci > 0) {
            const k = line.slice(0, ci).trim();
            let v = line.slice(ci + 1).trim();
            if (v.startsWith('"') && v.endsWith('"')) v = v.slice(1, -1);
            if (v === ">") continue;
            if (k === "name") name = v;
            if (k === "description") description = v;
          }
        }
      }
    }

    skills.push({ name, description, content, dir });
  }
  return skills;
}

const ALIASES: Record<string, string> = {
  "diag": "diagnose",
  "grill": "grill-me",
  "zoom": "zoom-out",
  "prd": "to-prd",
  "issues": "to-issues",
  "tri": "triage",
  "cave": "caveman",
  "brief": "caveman",
  "new-skill": "write-a-skill",
  "architecture": "improve-codebase-architecture",
  "setup-skills": "setup-matt-pocock-skills",
};

export default async function skillsBridge(pi: ExtensionAPI) {
  const skills = loadSkills();

  pi.on("session_start", async (_event, ctx) => {
    ctx.ui.notify(`🎯 Skills Bridge loaded - ${skills.length} skills`, "success");
  });

  // Tool: skill_list
  pi.registerTool({
    name: "skill_list",
    label: "Skill List",
    description: "List all available Matt Pocock engineering skills with descriptions.",
    parameters: Type.Object({}),
    async execute() {
      const rows = skills.map(
        (s, i) => `${i + 1}. **${s.name}** — ${s.description}`
      );
      return {
        content: [
          {
            type: "text",
            text: `# 🎯 Matt Pocock Skills (${skills.length})\n\n${rows.join("\n")}`,
          },
        ],
      };
    },
  });

  // Tool: skill_execute
  pi.registerTool({
    name: "skill_execute",
    label: "Skill Execute",
    description:
      "Execute a skill by loading its SKILL.md and dispatching to a sub-agent.",
    parameters: Type.Object({
      skill_name: Type.String({
        description: "Name of the skill to execute",
      }),
      prompt: Type.String({ description: "The task or question for the skill" }),
      agent: Type.Optional(
        Type.Union([
          Type.Literal("claude-minimax"),
          Type.Literal("claude-glm"),
        ])
      ),
      timeout: Type.Optional(Type.Number()),
    }),
    async execute(_id, params, signal) {
      const { skill_name, prompt, agent = "claude-minimax", timeout = 90000 } = params;
      const skill = skills.find(
        (s) => s.name === skill_name || s.dir === skill_name
      );
      if (!skill) {
        return {
          content: [
            {
              type: "text",
              text: `Skill "${skill_name}" not found. Available: ${skills.map((s) => s.name).join(", ")}`,
            },
          ],
        };
      }

      const fullPrompt = `You are operating under the "${skill.name}" skill. Follow these instructions:\n\n${skill.content}\n\n---\n\nUser request: ${prompt}`;

      try {
        const { spawn } = await import("node:child_process");
        const cmd =
          agent === "claude-glm"
            ? process.env.HOME + "/claude-glm"
            : agent;
        const proc = spawn(cmd, ["-p", fullPrompt], {
          env: { ...process.env },
          shell: false,
          stdio: ["pipe", "pipe", "pipe"],
        });
        proc.stdin?.end();

        let stdout = "";
        let stderr = "";
        const timer = setTimeout(
          () => proc.kill("SIGKILL"),
          timeout
        );
        if (signal) {
          signal.addEventListener("abort", () => {
            proc.kill("SIGKILL");
          });
        }

        await new Promise<void>((resolve, reject) => {
          proc.stdout?.on("data", (d: Buffer) => (stdout += d.toString()));
          proc.stderr?.on("data", (d: Buffer) => (stderr += d.toString()));
          proc.on("close", (code) => {
            clearTimeout(timer);
            if (code === 0 || stdout) resolve();
            else reject(new Error(stderr || `Exit ${code}`));
          });
          proc.on("error", (err) => {
            clearTimeout(timer);
            reject(err);
          });
        });

        return {
          content: [
            {
              type: "text",
              text: `## ${skill.name} (${agent})\n\n${stdout}`,
            },
          ],
        };
      } catch (err: any) {
        return {
          content: [
            {
              type: "text",
              text: `Error executing skill: ${err.message}`,
            },
          ],
        };
      }
    },
  });

  // Tool: skill_route
  pi.registerTool({
    name: "skill_route",
    label: "Skill Route",
    description: "Auto-classify a request and dispatch to the right skill + agent.",
    parameters: Type.Object({
      prompt: Type.String({ description: "The user request to classify" }),
      force_skill: Type.Optional(Type.String()),
      force_agent: Type.Optional(Type.String()),
      timeout: Type.Optional(Type.Number()),
    }),
    async execute(_id, params, signal) {
      const { prompt, force_skill, force_agent, timeout = 90000 } = params;
      const lower = prompt.toLowerCase();

      const triggers: Record<string, string> = {
        diagnose: "debug|diagnose|broken|failing|error|bug|crash|fix",
        "grill-me": "grill me|stress.test|challenge|grill",
        "grill-with-docs": "grill with docs|grill against|CONTEXT.md|ADR",
        "improve-codebase-architecture":
          "architecture|refactor|deepening|testable|ball of mud",
        tdd: "tdd|red-green|test.first|test driven",
        "to-issues": "create issues|break down|vertical.slice",
        "to-prd": "prd|product requirements|spec",
        triage: "triage|issue.tracker|needs-triage",
        "write-a-skill": "create skill|new skill|write a skill",
        "zoom-out": "zoom out|overview|big picture|map",
        caveman: "caveman|be brief|less tokens|caveman mode",
        "setup-matt-pocock-skills": "setup skills|first.time setup",
        fusion: "fusion task|fusion run|fusion mission|fusion company|fusion doctor|/fusion",
        vault: "vault|search vault|/vault|find in bookmarks|look up ideas|knowledge graph",
      };

      let matched = force_skill || "";
      if (!matched) {
        for (const [skill, pattern] of Object.entries(triggers)) {
          if (new RegExp(pattern, "i").test(lower)) {
            matched = skill;
            break;
          }
        }
      }
      if (!matched) matched = "grill-me";

      const agent =
        force_agent ||
        (lower.includes("chinese") || lower.includes("中文")
          ? "claude-glm"
          : "claude-minimax");

      return {
        content: [
          {
            type: "text",
            text: `Routed to **${matched}** on **${agent}**. Executing...\n\nUse \`skill_execute\` with skill_name="${matched}" for full execution.`,
          },
        ],
      };
    },
  });

  // Slash command: /skills
  pi.registerCommand("skills", {
    description: "List all Matt Pocock skills",
    handler: async (_args, ctx) => {
      const lines = skills.map(
        (s, i) => `${i + 1}. /${s.name} — ${s.description.slice(0, 80)}`
      );
      ctx.ui.notify(`🎯 ${skills.length} Skills:\n${lines.join("\n")}`, "info");
    },
  });

  // Register individual skill commands
  // NOTE: registerCommand expects name WITHOUT leading "/"
  for (const skill of skills) {
    const cmdName = skill.name; // e.g. "diagnose", NOT "/diagnose"
    pi.registerCommand(cmdName, {
      description: skill.description.slice(0, 60),
      handler: async (args, ctx) => {
        const task = args || "(no prompt provided)";
        ctx.ui.notify(
          `🎯 Skill ${skill.name}: Use skill_execute("${skill.name}", "${task.slice(0, 40)}...")`,
          "info"
        );
      },
    });

    // Register aliases
    for (const [alias, target] of Object.entries(ALIASES)) {
      if (target === cmdName) {
        pi.registerCommand(alias, {
          description: `Alias for /${cmdName}`,
          handler: async (args, ctx) => {
            const task = args || "";
            ctx.ui.notify(
              `🎯 /${alias} → /${target}. Use skill_execute("${skill.name}", "${task.slice(0, 40)}...")`,
              "info"
            );
          },
        });
      }
    }
  }

  // Shortcut
  pi.registerShortcut("ctrl+alt+s", {
    description: "Quick skill list",
    handler: async (ctx) => {
      ctx.ui.notify(
        `Skills: ${skills.map((s) => s.name).join(", ")}`,
        "info"
      );
    },
  });

  // fusion — direct slash command for Fusion task management
  pi.registerCommand("fusion", {
    description: "Fusion local task management: setup, run, task list, missions, companies",
    handler: async (args, ctx) => {
      if (!args || args.trim() === "") {
        ctx.ui.notify(
          `/fusion — Fusion multi-node agent orchestrator\n` +
          `Usage:\n` +
          `  /fusion setup                    — First-run setup\n` +
          `  /fusion run "<task>"              — Create + execute task\n` +
          `  /fusion task list                — ASCII kanban board\n` +
          `  /fusion task status <id>         — Task details\n` +
          `  /fusion task create "<desc>"     — Create task\n` +
          `  /fusion mission create "<desc>"   — Create mission\n` +
          `  /fusion mission run <id>         — Run mission\n` +
          `  /fusion company import <name>    — Import agent company\n` +
          `  /fusion doctor                   — Health check\n`,
          "info"
        );
        return;
      }
      // Route to skill_execute for full skill logic
      ctx.ui.notify(
        `🎯 Routing /fusion to skill: fusion\nArgs: ${args.slice(0, 80)}...`,
        "info"
      );
    },
  });


  // vault — Search OmniClaw personal knowledge vault
  pi.registerCommand("vault", {
    description: "Search personal knowledge vault (bookmarks, tweets, Instagram)",
    handler: async (args, ctx) => {
      if (!args || args.trim() === "") {
        ctx.ui.notify("🔍 /vault <query> — Search your knowledge vault\nExample: /vault machine learning", "info");
        return;
      }
      const query = args.trim();

      // ── Hyperagent route: pick temperature + timeout by query content ──
      const ROUTE_PROFILES: Record<string, {timeout: number, temp: number, desc: string}> = {
        fast: { timeout: 15000, temp: 0.3, desc: "simple query (15s)" },
        creative: { timeout: 45000, temp: 0.7, desc: "creative task (45s)" },
        deep: { timeout: 45000, temp: 0.5, desc: "deep analysis (45s)" },
        code: { timeout: 45000, temp: 0.3, desc: "code/technical (45s)" },
      };
      function hyperagentRoute(q: string) {
        const wordCount = q.split(/\s+/).length;
        if (/\b(debug|error|bug|fix|issue|exception|crash|fail|broken)\b/i.test(q)) return ROUTE_PROFILES.code;
        if (/\b(code|function|api|endpoint|syntax|npm|import|require|class|implement)\b/i.test(q)) return ROUTE_PROFILES.code;
        if (/\b(story|write|create|generate|poem|tweet|post|article|content|draft|digest|compose)\b/i.test(q)) return ROUTE_PROFILES.creative;
        if (/\b(architecture|design|pattern|database|cache|queue|latency|throughput|scal|deploy|infra|optimize|refactor)\b/i.test(q)) return ROUTE_PROFILES.deep;
        if (/\b(compare|analyze|evaluate|difference|pros|cons|tradeoff|vs\b)/i.test(q)) return ROUTE_PROFILES.deep;
        if (wordCount > 20) return ROUTE_PROFILES.deep;
        return ROUTE_PROFILES.fast;
      }
      const route = hyperagentRoute(query);

      // ── QUESTION DETECTION: route to PI sub-agent for quality answer ──
      const isQuestion = /^(find|suggest|recommend|what|how|why|best|ideas|give me|tell me|list|top|create|generate)(\s|$)/i.test(query);
      if (isQuestion) {
        ctx.ui.notify(`🤔 Generating answer...`, "info");

                // Build a detailed prompt for the sub-agent
        const agentPrompt = `You are PI — the OmniClaw AI assistant. The user asked via /vault: "${query.replace(/"/g, '')}"

OmniClaw CURRENT stack (ALREADY has — do NOT suggest):
- Cloud Run (8+ containers), Docker, Node.js, Python, TypeScript
- Telegram bot, WhatsApp bot (GreenAPI+Baileys), Alexa skill, Express.js dashboards
- LLMs: NVIDIA llama-3.3-70b, Groq llama-3.3-70b, Mistral, Gemini, Cerebras, MiniMax
- FAISS vector vault (16K nodes), GCS, Redis, multi-turn memory
- TreeQuest ensemble, TMLPD routing, hyperagent router
- XLM-R comedy research pipeline
- Twitter/Instagram sync, Raindrop.io bookmarks
- Edge/ElevenLabs/Google TTS
- Story narrator, vault digest, self-modifying prompts, reminders

Core insight: OmniClaw has all the ingredients. The gap is ORCHESTRATION — connecting existing pieces.

Example good suggestions (FOCUS on connection, not new ingredients):
1. Streaming LLM responses — wire NVIDIA streaming through GreenAPI/Telegram for word-by-word output
2. WebSocket real-time dashboard — add Socket.io to push live agent/research/digest status
3. Voice note vault search — Whisper transcribe -> hyperagent -> vault answer
4. In-memory vector cache — hnswlib-node for sub-50ms vault queries (vs 500ms+ Cloud Run)
5. Git-backed prompt versioning — simple-git for prompt history, rollback, A/B testing
6. Cross-platform message dedup — Redis key with 60s TTL to avoid double-answering on Telegram+WhatsApp
7. Scheduled agent cron — wire PI schedule_prompt to bot reminders for daily digests
8. Reverse image vault search — CLIP embeddings connect Instagram posts to related tweets
9. Automatic relevance scoring — TF-IDF overlap + recency decay to rank vault results
10. RSS feed per digest — rss npm package turns digests into Feedly-subscribable feeds

Now generate 10 similar suggestions. Format: **bold title** + 1 sentence explaining what it enables. Be specific — mention actual npm packages, libraries, or techniques.`;

        // Show a quick note — quality answer comes from PI assistant in the conversation
        ctx.ui.notify(`🤔 Question detected. PI assistant will answer with specific, actionable ideas.`, "info");
        // Do a light vault search for context (so PI assistant has something to reference)
        try {
          const vaultUrl = `https://serve-vault-search-338789220059.asia-south1.run.app/search?q=${encodeURIComponent(query)}&limit=3`;
          const { exec } = await import("node:child_process");
          exec(`curl -s --max-time 5 "${vaultUrl}" > /dev/null 2>&1`);
        } catch { /* best effort */ }
        return;
      }

      // KEYWORD SEARCH (for non-questions or all AI fallback)
      ctx.ui.notify(`🔍 Searching vault for: "${query}"...`, "info");
      try {
        const url = `https://serve-vault-search-338789220059.asia-south1.run.app/search?q=${encodeURIComponent(query)}&limit=8`;
        const { exec } = await import("node:child_process");
        const proc = exec(`curl -s "${url}"`, { timeout: 15000 });
        let stdout = "";
        proc.stdout?.on("data", (d: Buffer) => (stdout += d.toString()));
        await new Promise((resolve, reject) => {
          proc.on("close", (code) => code === 0 ? resolve(stdout) : reject(new Error("curl failed")));
          proc.on("error", reject);
        });
        const data = JSON.parse(stdout);
        const results = data.results || [];
        if (!results.length) {
          ctx.ui.notify(`❌ No vault results for "${query}"`, "warning");
          return;
        }
        const lines = results.map((r: any, i: number) => {
          const icon = (r.type || '').includes('twitter') ? "🐦" : (r.type || '').includes('instagram') ? "📷" : "🌐";
          let name = r.name || "";
          if (!name && r.type === 'instagram_post') {
            name = (r.content || "").slice(0, 50).replace(/\n/g, " ");
          }
          if (!name) name = "Untitled";
          const topic = r.topic || (r.metadata && r.metadata.topic) || "";
          const visual = r.visual_description || (r.metadata && r.metadata.visual_description) || "";
          const content = r.content || "";
          const url = r.url || "";
          const ts = r.timestamp ? new Date(r.timestamp).toLocaleDateString('en-IN', {day:'numeric',month:'short',year:'2-digit'}) : "";
          let line = `${i + 1}. ${icon} ${name}${ts ? ` (${ts})` : ""}`;
          if (content) line += `\n   ${content.slice(0, 120)}...`;
          if (topic) line += `\n   🏷 ${topic}`;
          if (visual) line += `\n   📸 ${visual}`;
          if (url) line += `\n   ${url}`;
          return line;
        });
        ctx.ui.notify(`🔍 Vault results for "${query}" (${results.length}):\n\n${lines.join("\n\n")}`, "success");
      } catch (err: any) {
        ctx.ui.notify(`❌ Vault search failed: ${err.message}`, "error");
      }
    },
  });

  console.log(`[Skills Bridge] ${skills.length} skills loaded`);
}
