# Resume Analyzer 

## Key Features

* **AI-Driven ATS Audit:** Utilizes Google Gemini to simulate a "Senior Technical Recruiter," identifying weak metrics, buzzwords, and passive language with high precision.
* **Actionable Rewrite Suggestions:** Beyond identifying issues, the system generates 2-3 professional, high-impact rewrite versions for every problematic line that users can directly copy-paste.
* **Deep Dive Breakdown:**
    * **Skills Mapping:** Automatically detects existing skills and highlights critical missing gaps based on the user's target role.
    * **Experience & Project Audit:** Provides a detailed "Pros & Cons" analysis for every entry, ensuring bullets are optimized for impact.
    * **AI Auto-Recommendations:** Suggests entirely new experiences or specific bullet points to add to existing projects to boost ATS scores.
* **Smart Retrieval & Caching:** Implements a SHA-256 content hashing system. Re-uploading the same resume returns instant results from the database, saving API costs and ensuring consistent feedback.
* **Interactive Professional UI:** A sleek, responsive Indigo-themed dashboard built with pure CSS and Vanilla JS for a fast, lightweight, and modern user experience.

---

## Technical Stack

### **Backend**
* **Framework:** FastAPI (Python)
* **AI Engine:** Google Gemini Fleet (`flash-2.5`, `flash-2.0`, `pro-1.5`)
* **Database:** MySQL with Connection Pooling
* **Data Validation:** Pydantic (Strict JSON Schema enforcement)
* **Parsing:** PyPDF2 & python-docx

### **Frontend**
* **Core:** HTML5 & Vanilla JavaScript (Modular ES6 Architecture)
* **Styling:** Semantic CSS3 (Modularly partitioned into Globals, Auth, and Dashboard)
* **Authentication:** JWT (JSON Web Tokens) with Secure LocalStorage management
* **Icons:** FontAwesome 6
