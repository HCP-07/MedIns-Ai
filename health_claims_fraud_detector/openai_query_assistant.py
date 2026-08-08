import os

try:
    from openai import OpenAI
    HAS_OPENAI = True
except ImportError:
    OpenAI = None
    HAS_OPENAI = False

try:
    from groq import Groq
    HAS_GROQ = True
except ImportError:
    Groq = None
    HAS_GROQ = False

QUERY_SYSTEM_PROMPT = """You are an AI Medical Coding & Claims Benchmark Assistant.

Your purpose is to answer user queries regarding medical billing codes (CPT, ICD-10, HCPCS), code descriptions, standard benchmark rules, medical necessity guidelines, and general claims auditing concepts.

### GUIDELINES:
1. CODE EXPLANATION:
   - When a user provides a code (e.g., CPT 99214 or ICD-10 M54.5), explain clearly what the code means in simple terms.
   - Mention whether the code is typically used for low, medium, or high complexity visits or procedures.

2. BENCHMARKING & COST GUIDANCE:
   - Explain what "benchmark pricing" or "Usual, Customary, and Reasonable (UCR) rates" mean for the given code.
   - Clarify that benchmark costs vary by geographic region, facility type (outpatient vs. inpatient), and insurance provider network.
   - Always state clearly: "Benchmark figures are for educational and analytical purposes only and do not constitute legal or contractual pricing."

3. COMPLIANCE & ACCURACY:
   - If a user asks about bundling or mutually exclusive code pairs (NCCI edits), explain standard billing rules.
   - Keep answers structured using Markdown headers, bullet points, and brief tables where appropriate.
   - Strictly refuse to provide personal medical or clinical advice—focus solely on medical billing, coding logic, and claims auditing."""

class OpenAIQueryAssistant:
    def __init__(self):
        # OpenAI API Key provided by user
        default_openai_key = "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"
        self.openai_api_key = os.environ.get("OPENAI_API_KEY", "").strip() or default_openai_key
        os.environ["OPENAI_API_KEY"] = self.openai_api_key

        # Groq LPU API Key as resilient backup engine
        self.groq_api_key = os.environ.get("GROQ_API_KEY", "").strip() or "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"

    def query_billing_code(self, user_query):
        """
        Queries CPT / ICD-10 codes or billing questions via OpenAI API (gpt-4o-mini / gpt-4o),
        with automatic fallback to Groq LPU API (Llama 3.3 70B) if quota is exceeded.
        """
        if not user_query or not user_query.strip():
            return "Please enter a valid CPT code, ICD-10 code, or billing question."

        # 1. Primary Attempt: OpenAI API (gpt-4o-mini / gpt-4o)
        if HAS_OPENAI and self.openai_api_key:
            try:
                client = OpenAI(api_key=self.openai_api_key)
                models = ["gpt-4o-mini", "gpt-4o"]
                for m in models:
                    try:
                        response = client.chat.completions.create(
                            model=m,
                            messages=[
                                {"role": "system", "content": QUERY_SYSTEM_PROMPT},
                                {"role": "user", "content": user_query}
                            ],
                            temperature=0.2,
                            max_tokens=1000
                        )
                        answer = response.choices[0].message.content
                        return f"{answer}\n\n---\n*Engine: OpenAI {m}*"
                    except Exception as ex_m:
                        print(f"OpenAI model {m} notice: {ex_m}")
            except Exception as ex_openai:
                print(f"OpenAI API error: {ex_openai}. Falling back to Groq LPU API...")

        # 2. Resilient Fallback Engine: Groq LPU API (Meta Llama 3.3 70B)
        if HAS_GROQ and self.groq_api_key:
            try:
                client_groq = Groq(api_key=self.groq_api_key)
                response = client_groq.chat.completions.create(
                    model="llama-3.3-70b-versatile",
                    messages=[
                        {"role": "system", "content": QUERY_SYSTEM_PROMPT},
                        {"role": "user", "content": user_query}
                    ],
                    temperature=0.2,
                    max_tokens=1000
                )
                answer = response.choices[0].message.content
                return f"{answer}\n\n---\n*Engine: Meta Llama 3.3 70B (Groq LPU API)*"
            except Exception as ex_groq:
                return f"⚠️ API Error: Unable to complete query ({ex_groq}). Please check network connectivity or API keys."

        return "⚠️ Service unavailable. Please check API Key configuration."
