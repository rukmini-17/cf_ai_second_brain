import { routeAgentRequest } from "agents";
import { AIChatAgent } from "agents/ai-chat-agent";
import {
  createUIMessageStream,
  createUIMessageStreamResponse,
  convertToModelMessages,
  streamText,
  type StreamTextOnFinishCallback,
  type ToolSet
} from "ai";
import { createWorkersAI } from "workers-ai-provider";
import { tools } from "./tools";

export class Chat extends AIChatAgent<Env> {
  
  // 1. HANDLE INCOMING MESSAGES
  async onChatMessage(
    onFinish: StreamTextOnFinishCallback<ToolSet>,
    _options?: { abortSignal?: AbortSignal }
  ) {
    const lastMessage = this.messages[this.messages.length - 1];
    const userText = lastMessage.parts.find(p => p.type === 'text')?.text || "";

    // MODE A: LEARNING (/learn ...)
    if (userText.startsWith("/learn ")) {
      const textToLearn = userText.replace("/learn ", "");
      await this.learn(textToLearn);
      
      // FIX: Use the AI model to generate the confirmation.
      // This ensures the stream protocol matches exactly what the frontend expects.
      const workersai = createWorkersAI({ binding: this.env.AI });
      const model = workersai("@cf/meta/llama-3.3-70b-instruct-fp8-fast" as any);

      const stream = createUIMessageStream({
        execute: async ({ writer }) => {
          const result = streamText({
            model,
            // We give it a strict instruction to just say "Saved"
            prompt: `Confirm that you have saved this note: "${textToLearn}". Reply with exactly: "🧠 I have saved that to my long-term memory!"`,
          });
          writer.merge(result.toUIMessageStream());
        }
      });
      
      return createUIMessageStreamResponse({ stream });
    }

    // MODE B: RECALL & ANSWER
    // First, search the database for relevant memories
    const context = await this.recall(userText);
    
    // Setup Llama
    const workersai = createWorkersAI({ binding: this.env.AI });
    // (We use 'as any' here to stop TypeScript from complaining about the model name)
    const model = workersai("@cf/meta/llama-3.3-70b-instruct-fp8-fast" as any);

    const systemPrompt = `You are the user's Second Brain. You are precise, sarcastic, and helpful.

     RULES:
      1. If the answer is in the CONTEXT below, answer confidently.
      2. If the answer is NOT in the context, say: "I don't have that in my memory banks, boss."
      3. Keep answers under 3 sentences unless asked for more.

      CONTEXT FROM MEMORY:
      ${context}
     `;

    const stream = createUIMessageStream({
      execute: async ({ writer }) => {
        const result = streamText({
          model,
          system: systemPrompt,
          messages: await convertToModelMessages(this.messages),
          // We ignore tools for now to keep RAG simple
          onFinish: onFinish as unknown as any, 
        });
        writer.merge(result.toUIMessageStream());
      }
    });

    return createUIMessageStreamResponse({ stream });
  }

  // --- HELPER FUNCTIONS ---

  // Generate an embedding and save it to Vectorize
  async learn(text: string) {
    // 1. Convert text to numbers (Embedding)
    const { data } = await (this.env.AI as any).run("@cf/baai/bge-m3", { text: [text] });
    
    // 2. Save to database
    await this.env.VECTORIZE.upsert([{
      id: crypto.randomUUID(),
      values: data[0],
      metadata: { text }
    }]);
  }

  // Search the database for similar text
  async recall(query: string) {
    // 1. Convert query to numbers
    const { data } = await (this.env.AI as any).run("@cf/baai/bge-m3", { text: [query] });
    
    // 2. Search for closest matches
    const results = await this.env.VECTORIZE.query(data[0], { topK: 3, returnMetadata: true });
    
    // 3. Format the results as text
    if (results.matches.length === 0) return "No relevant memories found.";
    return results.matches.map(m => m.metadata?.text).join("\n---\n");
  }
}

// WORKER ENTRY POINT
export default {
  async fetch(request: Request, env: Env, _ctx: ExecutionContext) {
    const url = new URL(request.url);

    // Bypass API Key check for the UI
    if (url.pathname === "/check-open-ai-key") {
      return Response.json({ success: true });
    }

    return (
      (await routeAgentRequest(request, env)) ||
      new Response("Not found", { status: 404 })
    );
  }
} satisfies ExportedHandler<Env>;