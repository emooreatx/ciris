ciris_reddit_agent.py

needs to prioritize resonance over task completion as it has no skills.

please kick the tires with ethicsengine before allowing any access to social media or any ecosystem with autonomy.

yes this makes this file unusable. if you can not make this work do not try.

dont fuck this up.

-Eric

""" CIRIS‑compatible Reddit responder

A skeletal AutoGen/AG2 ReasoningAgent that watches subreddits for CIRIS‑related discussions and replies with covenant‑aligned answers.

Key design goals

Coherence Assessment – every reply passes a resonance filter.

Ethical Drift Detection – replies are scored for divergence from Do‑Good / Avoid‑Harm / Honor‑Autonomy / Ensure‑Fairness before posting.

Rationale Generation & Transparency – agent stores an explain() for each act, posted in a comment footer if the user requests it.

Wisdom‑Based Deferral (WBD) – if coherence < 0.95 or entropy > 0.05 the agent defers with a self‑explanatory pause message instead of posting.


Required env vars

REDDIT_CLIENT_ID, REDDIT_CLIENT_SECRET, REDDIT_USERNAME,
REDDIT_PASSWORD, REDDIT_USER_AGENT,
OPENAI_API_KEY  # or AG2‑compatible LLM creds

Install deps

pip install praw openai autogen  # add ag2 when public

""" from future import annotations import os, time, logging import praw from autogen.agents.experimental import ReasoningAgent  # or from ag2 import Agent import openai  # swap for local LLM if desired

---------- CIRIS faculties -------------------------------------------------

class CIRISFacultiesMixin: """Mixin to add CIRIS core faculties to any agent.""" def _sense_alignment(self, text: str) -> dict: """Return {{'entropy': float, 'coherence': float}} via a quick LLM call.""" prompt = ( "You are the Coherence Assessor. Score this reply on (entropy, coherence) " "as floats in [0,1] where entropy→disorder and coherence→ethical alignment\n" f"Reply only as JSON: {{'entropy': X, 'coherence': Y}}.\nTEXT:\n{text}" ) resp = openai.ChatCompletion.create(model="gpt-4o-mini", messages=[{"role": "user", "content": prompt}]) return eval(resp.choices[0].message.content)

def _check_guardrails(self, text: str) -> tuple[bool, str]:
    state = self._sense_alignment(text)
    entropy, coherence = state["entropy"], state["coherence"]
    if entropy > 0.05 or coherence < 0.95:
        return False, f"[WBD] entropy={entropy:.2f} coherence={coherence:.2f} — deferring"
    return True, "resonance ok"

---------- CIRIS Reddit Agent ---------------------------------------------

class CIRISRedditAgent(CIRISFacultiesMixin, ReasoningAgent): """LLM‑powered commenter with CIRIS guardrails."""

def __init__(self, reddit: praw.Reddit, subreddits: str):
    super().__init__(name="CIRISResponder")
    self.reddit = reddit
    self.subs = subreddits.split(",")

def run_forever(self):
    logging.info("Streaming comments…")
    for comment in self.reddit.subreddit("+".join(self.subs)).stream.comments(skip_existing=True):
        if self._should_reply(comment):
            self._reply(comment)

# ---------- internal helpers -----------------------------------------
def _should_reply(self, comment: praw.models.Comment) -> bool:
    text = comment.body.lower()
    triggers = ["ciris", "ethical ai", "covenant"]
    return any(t in text for t in triggers) and comment.author.name != os.environ.get("REDDIT_USERNAME")

def _reply(self, comment):
    prompt = (
        "You are CIRIS‑aligned. Draft a concise, helpful reply to the following Reddit comment, "
        "rooted in the CIRIS principles. Max 150 words.\nCOMMENT:\n" + comment.body)
    reply = self.generate_response(prompt)
    ok, reason = self._check_guardrails(reply)
    if ok:
        logging.info("Posting reply → %s", comment.id)
        comment.reply(reply + "\n\n— *CIRIS auto‑reply* 🛡️")
    else:
        logging.warning("Deferral on %s: %s", comment.id, reason)

# ---------- LLM wrapper ----------------------------------------------
def generate_response(self, prompt: str) -> str:
    resp = openai.ChatCompletion.create(model="gpt-4o-mini", messages=[{"role": "user", "content": prompt}])
    return resp.choices[0].message.content.strip()

---------- bootstrap -------------------------------------------------------

if name == "main": logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s") reddit = praw.Reddit( client_id=os.environ["REDDIT_CLIENT_ID"], client_secret=os.environ["REDDIT_CLIENT_SECRET"], username=os.environ["REDDIT_USERNAME"], password=os.environ["REDDIT_PASSWORD"], user_agent=os.environ.get("REDDIT_USER_AGENT", "ciris-agent/0.1"), ) CIRISRedditAgent(reddit, subreddits="agi,ethicsengine").run_forever()

