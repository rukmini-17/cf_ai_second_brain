import requests
import time
import statistics
import csv
from sentence_transformers import SentenceTransformer, util

# ---------------------------------------------------------
# CONFIGURATION
# ---------------------------------------------------------

# HISTORY_ENDPOINT = "https://YOUR_WORKER_URL_HERE/agents/chat/default/get-messages"
# (Uncomment and add your URL locally to run, do not commit your personal URL)
import os
HISTORY_ENDPOINT = os.getenv("AGENT_URL", "https://replace-me-in-local-env/agents/chat/default/get-messages")

print("⏳ Loading Embedding Model (all-MiniLM-L6-v2)...")
eval_model = SentenceTransformer('all-MiniLM-L6-v2')

# ---------------------------------------------------------
# THE GOLDEN DATASET (12 Questions)
# ---------------------------------------------------------
test_suite = [
    # --- BEHAVIORAL ---
    {"cat": "Behavioral", "q": "Tell me about a time you handled a conflict.", "truth": "I resolved a git merge dispute during the Hackathon by setting up a daily standup. Result: We shipped on time."},
    {"cat": "Behavioral", "q": "What is your greatest weakness?", "truth": "I sometimes focus too much on details. I am working on this by using time-boxing techniques to prioritize shipping."},
    {"cat": "Behavioral", "q": "Describe a leadership experience.", "truth": "I led the frontend team for the Capstone project, organizing sprint planning and code reviews."},

    # --- TECHNICAL: ML/AI ---
    {"cat": "ML/AI", "q": "Define Big O Notation.", "truth": "Big O measures algorithm performance relative to input size growth. O(1) is constant, O(n) is linear."},
    {"cat": "ML/AI", "q": "What is Overfitting?", "truth": "Overfitting happens when a model learns the training data too well, including noise, and fails to generalize to new data."},
    {"cat": "ML/AI", "q": "Explain Gradient Descent.", "truth": "Gradient Descent is an optimization algorithm used to minimize the loss function by iteratively moving in the direction of steepest descent."},

    # --- TECHNICAL: SECURITY ---
    {"cat": "Security", "q": "Difference between TCP and UDP?", "truth": "TCP guarantees delivery via handshake (reliable), while UDP is connectionless and faster but unreliable (video streaming)."},
    {"cat": "Security", "q": "What is SQL Injection?", "truth": "SQL Injection is a vulnerability where an attacker interferes with the queries an application makes to its database, often to access unauthorized data."},
    {"cat": "Security", "q": "Explain XSS (Cross-Site Scripting).", "truth": "XSS allows attackers to inject malicious scripts into web pages viewed by other users, often stealing cookies or session tokens."},

    # --- PERSONAL / RESUME ---
    {"cat": "Resume", "q": "Where did you intern in Summer 2024?", "truth": "I interned at TCS Research from May to July 2024."},
    {"cat": "Resume", "q": "What is TERRA-CD?", "truth": "TERRA-CD is a benchmark dataset for Semantic Change Detection I created for my final year project."},
    {"cat": "Resume", "q": "What master's degree are you pursuing?", "truth": "I am pursuing a Master of Science in Computer Science (MS CS) at UMass Amherst."}
]

def get_text(msg):
    """Robust text extractor"""
    text = ""
    if 'parts' in msg:
        for p in msg['parts']:
            if isinstance(p, dict) and 'text' in p:
                text += p['text'] + " "
    elif 'content' in msg:
        c = msg['content']
        if isinstance(c, str): text = c
        elif isinstance(c, list): 
            text = " ".join([str(x.get('text','')) for x in c if isinstance(x, dict)])
    return text.strip()

def fetch_latest_answer(query):
    """Fetches history and finds the answer to the specific query"""
    try:
        response = requests.get(HISTORY_ENDPOINT)
        data = response.json()
        messages = []
        if isinstance(data, list): messages = data
        elif 'messages' in data: messages = data['messages']
        elif 'result' in data: messages = data['result']['messages']
        
        # Search backwards for the question
        q_idx = -1
        for i in range(len(messages) - 1, -1, -1):
            if messages[i].get('role') == 'user' and query.lower() in get_text(messages[i]).lower():
                q_idx = i
                break
        
        if q_idx == -1: return None

        # Look forward for the answer
        search_limit = min(len(messages), q_idx + 6)
        for j in range(q_idx + 1, search_limit):
            msg = messages[j]
            txt = get_text(msg)
            if msg.get('role') == 'assistant':
                # Apply filters (Skip "Saved" and short noise)
                if "Saved to your Study Guide" in txt or len(txt) < 25:
                    continue
                return txt
    except:
        return None
    return None

def run_bulk_benchmark():
    print(f"\n🚀 STARTING BULK EVALUATION (n={len(test_suite)})")
    print("Note: This script attempts to verify answers found in the logs.")
    print("-" * 75)
    print(f"{'CATEGORY':<12} | {'QUERY (truncated)':<30} | {'SCORE':<6} | {'STATUS'}")
    print("-" * 75)

    results = []
    
    for item in test_suite:
        # Analyze Logs
        ai_ans = fetch_latest_answer(item['q'])
        
        score = 0.0
        status = "MISSING"
        
        if ai_ans:
            truth_emb = eval_model.encode(item['truth'], convert_to_tensor=True)
            ans_emb = eval_model.encode(ai_ans, convert_to_tensor=True)
            score = util.cos_sim(truth_emb, ans_emb).item()
            status = "✅ PASS" if score > 0.6 else "❌ FAIL"
        else:
            status = "⚠️ NOT FOUND"

        # Print Row
        q_short = (item['q'][:28] + '..') if len(item['q']) > 28 else item['q']
        print(f"{item['cat']:<12} | {q_short:<30} | {score:.3f}  | {status}")
        
        results.append({
            "Category": item['cat'],
            "Question": item['q'],
            "Score": score,
            "Status": status
        })

    # Summary Stats
    print("-" * 75)
    valid_scores = [r['Score'] for r in results if r['Status'] != "⚠️ NOT FOUND"]
    if valid_scores:
        avg = statistics.mean(valid_scores)
        print(f"🏆 OVERALL ACCURACY: {avg:.1%}")
        
        # Category Breakdown
        cats = set(r['Category'] for r in results)
        for c in cats:
            c_scores = [r['Score'] for r in results if r['Category'] == c and r['Status'] != "⚠️ NOT FOUND"]
            if c_scores:
                print(f"   🔹 {c:<10}: {statistics.mean(c_scores):.1%}")
    else:
        print("❌ No answers found. Did you chat with the bot first?")

    # CSV Export (FIXED ENCODING HERE)
    with open("benchmark_results.csv", "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=["Category", "Question", "Score", "Status"])
        writer.writeheader()
        writer.writerows(results)
    print(f"\n📄 Results exported to 'benchmark_results.csv'")

if __name__ == "__main__":
    run_bulk_benchmark()