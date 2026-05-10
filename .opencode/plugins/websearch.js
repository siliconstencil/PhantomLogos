import { tool } from "@opencode-ai/plugin";

export const WebSearchPlugin = async ({ directory }) => {
  return {
    tool: {
      websearch: tool({
        description: "Search the web using DuckDuckGo (free, no API key). Returns results with titles, URLs, and snippets.",
        args: {
          query: tool.schema.string().describe("Search query"),
          max_results: tool.schema.number().optional().describe("Max results (default 8)"),
        },
        async execute(args, context) {
          const scriptPath = `${context.directory}/src/tools/websearch.py`;
          const proc = Bun.spawn(["python", scriptPath, args.query], {
            env: { ...process.env },
          });
          const out = await new Response(proc.stdout).text();
          const err = await new Response(proc.stderr).text();
          const exitCode = await proc.exited;
          if (exitCode !== 0) {
            return `Search failed (exit ${exitCode}): ${err || out}`;
          }
          try {
            const data = JSON.parse(out);
            if (data.error) return `Search error: ${data.error}`;
            if (!data.results || data.results.length === 0) return "No results found.";
            return data.results.map((r, i) =>
              `[${i + 1}] ${r.title}\n    URL: ${r.url}\n    ${r.snippet}`
            ).join("\n\n");
          } catch (e) {
            return `Failed to parse results: ${e.message}\nRaw: ${out.slice(0, 500)}`;
          }
        },
      }),
    },
  };
};
