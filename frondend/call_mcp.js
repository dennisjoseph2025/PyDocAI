import { Client } from "@modelcontextprotocol/sdk/client/index.js";
import { StdioClientTransport } from "@modelcontextprotocol/sdk/client/stdio.js";

async function main() {
  const transport = new StdioClientTransport({
    command: "node",
    args: ["D:/DENNIS/AI/Proxima/src/mcp-server-v3.js"],
  });

  const client = new Client(
    { name: "test-client", version: "1.0.0" },
    { capabilities: {} }
  );

  await client.connect(transport);

  const result = await client.callTool({
    name: "get_ui_reference",
    arguments: {
      description: "A premium technical documentation page for a Django project. It should have a sidebar with project metadata and a main area for Markdown content. Use glassmorphism, smooth transitions, and syntax highlighting for code blocks. The colors should be deep purple and neon violet.",
      style: "modern dark glassmorphism"
    }
  });

  console.log(JSON.stringify(result, null, 2));
  process.exit(0);
}

main().catch(console.error);
