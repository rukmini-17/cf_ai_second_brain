# Interview Prep Companion (`cf_ai_second_brain`)

A full-stack RAG (Retrieval Augmented Generation) agent built on Cloudflare Workers, Durable Objects, and Vectorize. It serves as a personalized "Interview Prep Companion" that helps students store and recall behavioral stories, algorithm patterns, and system design notes.

## 🚀 Live Demo
**[https://cf-ai-second-brain.rnazre.workers.dev](https://cf-ai-second-brain.rnazre.workers.dev)**

## 🛠️ Tech Stack
* **LLM:** Llama 3.3 70B (via Workers AI)
* **Coordination:** Durable Objects (managing chat state and agent logic)
* **Memory:** Cloudflare Vectorize (Vector Database) + BGE-M3 Embeddings
* **Frontend:** React + Vite (served via Worker Assets)
* **Language:** TypeScript

## ✨ Features
1.  **Mock Interviewer:** Real-time streaming chat with Llama 3.3, customized to act as a supportive technical interviewer.
2.  **Study Guide Mode:** Users can save specific notes (STAR method stories, LeetCode patterns) using the `/learn` command.
3.  **RAG / Memory:** The agent converts `/learn` inputs into vector embeddings (1024 dimensions) and stores them in Cloudflare Vectorize. When asked a question later, it retrieves the user's *specific* saved examples rather than generic advice.
4.  **Persistent History:** Chat sessions are managed by Durable Objects, ensuring state consistency.

## 🏃‍♂️ How to Run Locally

### Prerequisites
* Node.js & npm
* Cloudflare Wrangler CLI (`npm install -g wrangler`)

### Installation
1.  **Clone the repository:**
    ```bash
    git clone [https://github.com/rukmini-17/cf_ai_second_brain.git](https://github.com/rukmini-17/cf_ai_second_brain.git)
    cd cf_ai_second_brain
    ```

2.  **Install dependencies:**
    ```bash
    npm install
    ```

3.  **Login to Cloudflare:**
    ```bash
    npx wrangler login
    ```

4.  **Setup Vector Database:**
    ```bash
    npx wrangler vectorize create second-brain-index --dimensions=1024 --metric=cosine
    ```

5.  **Run Development Server:**
    ```bash
    npm run dev
    ```

## 🧠 Example Usage

**1. Save a Behavioral Story (STAR Method):**
> `/learn For the 'Conflict' question: I resolved a git merge dispute during the Hackathon by setting up a daily standup. Result: We shipped on time.`

**2. Recall for Interview:**
> **User:** "Give me a story about conflict resolution."
>
> **Agent:** "Here is your saved example: During the Hackathon, you resolved a git merge dispute by instituting daily standups, which ensured the project shipped on time."

**3. Save a Technical Concept:**
> `/learn The difference between TCP and UDP is that TCP guarantees delivery (handshake) while UDP is connectionless and faster (video streaming).`

## 📂 Project Structure
* `src/server.ts`: Main Worker and Durable Object logic (RAG implementation).
* `src/client.tsx`: React frontend.
* `wrangler.jsonc`: Cloudflare configuration (Vectorize bindings, Assets).

## 🤖 AI Assistance
Prompts used during development are documented in [PROMPTS.md](./PROMPTS.md).