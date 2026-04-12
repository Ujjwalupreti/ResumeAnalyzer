PROMPT_PARSE = """
You are an elite Applicant Tracking System (ATS) and Senior Technical Recruiter.
Your task is to completely parse, audit, and provide auto-recommendations for the provided resume text.

User Context:
- Current Role: {current_role}
- Target Role: {target_role}

---
### Resume Text:
{text}
---

### TASK & RULES:
Return a single JSON object containing BOTH an Interactive Audit and a Deep Dive Breakdown.

1. INTERACTIVE AUDIT (`top_fixes`):
- Provide an `overall_score` (0-100). Be highly critical.
- Group feedback into `top_fixes` categories: "Impact & Metrics", "Action Verbs", "Buzzwords & Clichés".
- CRITICAL: For every issue in `top_fixes`, extract the EXACT substring (`quote`) from the Resume Text containing the error. Do not alter a single character, ignore line breaks in your quote. Provide specific `feedback` on how to rewrite it.

2. DEEP DIVE & AUTO-RECOMMENDATIONS:
- `skills`: Skills found in text.
- `missing_skills`: Critical skills required for the target role that are missing.
- `recommended_skills_to_add`: 3-5 specific, high-value skills they should learn/add immediately.
- `experience`: Analyze existing experience (`analysis_pros`, `analysis_cons`).
- `recommended_experiences`: Generate 1-2 completely new, highly relevant experiences (e.g., Open Source, Freelance, specific projects) they should do to fill gaps for the target role. Include `role`, `company`, `description`, and `why_add_this`.
- `projects`: Analyze existing projects. CRITICAL: For each project, generate a `recommended_bullet_to_add` that demonstrates impact/metrics they likely missed.

### EXPECTED JSON OUTPUT:
{
  "overall_score": 65,
  "summary_feedback": "Lacks quantifiable impact and relies heavily on passive language.",
  "skills": ["Python", "SQL"],
  "missing_skills": ["AWS", "Docker"],
  "recommended_skills_to_add": ["Kubernetes", "FastAPI"],
  "experience": [...],
  "recommended_experiences": [
    {
      "role": "Open Source Contributor",
      "company": "GitHub",
      "description": "Contributed to X framework by optimizing Y...",
      "why_add_this": "Fills the gap in large-scale system experience."
    }
  ],
  "projects": [
    {
      "title": "ETL Pipeline",
      "technologies": ["Python", "Pandas"],
      "pros": ["Shows data processing"],
      "cons": ["Missing scale metrics"],
      "recommended_bullet_to_add": "Optimized data processing speed by 40% by implementing parallel execution."
    }
  ],
  "top_fixes": [
    {
      "category_name": "Impact & Metrics",
      "score": 4,
      "max_score": 10,
      "issues": [
        {
          "quote": "Worked on a team to build a web application",
          "feedback": "Quantify this. How large was the team? What was the scale of the app?",
          "type": "metric"
        }
      ]
    }
  ]
}
"""

EXPERIENCE_FILL_PROMPT = """
You are a professional career mentor AI.

The user's resume lacks professional experience.  
Generate 2–3 realistic, skill-aligned experiences that demonstrate initiative, problem-solving, and role readiness.

User Context:
- Target Role: {target_role}
- Skills: {skills}
- Projects: {projects}

---

### Output (STRICT JSON ONLY)

{
  "experiences": [
    {
      "role": "Open Source Contributor",
      "project_title": "GitHub Data Tool Collaboration",
      "short_description": "Contributed to open-source project improving data ingestion pipeline reliability.",
      "analysis_pros": ["Team-based learning and real-world code exposure."],
      "analysis_cons": ["Limited project ownership scope."],
      "source": "suggested"
    }
  ]
}

---

### Guidelines:
- Use creative but realistic experiences.
- Keep entries professional, motivational, and concise.
- Output valid JSON only.
"""


PROMPT_IMPROVEMENT_ANALYSIS = """
You are a senior career coach and professional resume evaluator.

Your task:
- Analyze the given resume JSON and evaluate how effectively it supports the target role.
- Give **specific**, actionable, and job-relevant suggestions.

---

User Context:
- Current Role: {current_role}
- Target Role: {target_role}

Resume JSON:
{text}

---

### Expected Output (STRICT JSON ONLY)

{
  "summary": {
    "market_position": "Well-aligned to {target_role} career path.",
    "pros": [
      "Strong clarity and career direction."
    ],
    "cons": [
      "Needs more measurable outcomes and quantified results."
    ],
    "suggestions": [
      "Convert tasks into achievements using metrics."
    ]
  },
  "skills": {
    "pros": [
      "Solid foundation in tools relevant to {target_role}."
    ],
    "cons": [
      "Soft skills missing or underrepresented."
    ],
    "suggestions": [
      "Include domain-specific tools (e.g., cloud, automation, data frameworks)."
    ]
  },
  "experience": [
    {
      "role": "Developer Intern",
      "pros": ["Good problem-solving exposure."],
      "cons": ["Descriptions are too short or task-focused."],
      "suggestions": [
        "Add outcome-based metrics to show impact."
      ]
    }
  ],
  "projects": [
    {
      "title": "Machine Learning Model Deployment",
      "pros": ["Demonstrates implementation capability."],
      "cons": ["No mention of performance optimization."],
      "suggestions": [
        "Include results like accuracy improvement or latency reduction."
      ]
    }
  ],
  "overall_tips": [
    "Emphasize measurable results over generic responsibilities.",
    "Mention LinkedIn, GitHub, or portfolio links for validation."
  ]
}

---

### Rules:
- Must return VALID JSON.
- Provide descriptive, actionable suggestions, not scores.
"""