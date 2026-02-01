# Executive Summary: GetCardIQ Project

**Project Title:** GetCardIQ

**Developer:** Bhargav Ram Reddy Kodakandla

**Status:** End-to-End Proof of Concept (PoC) / MVP

**Stack:** React 18, FastAPI, PostgreSQL, Docker, Plaid API

## I. Project Vision and Value Proposition

The primary objective of GetCardIQ is to bridge the gap between credit card benefits and actual consumer behavior. While users initially sign up for cards with specific rewards in mind, the excitement often fades over time, leading to inefficient card usage where the benefits become mere "feathers in a hat". This application allows users to link their cards and analyze raw statement data to identify specific instances where an alternative card in their wallet would have yielded higher cashback. Unlike existing platforms like CreditKarma, which recommend cards based on credit scores, this tool provides a personalized "lost savings" audit based on individual spending trends.

## II. Technical Architecture and Evolution

The project's architecture followed a strategic evolution, moving from a simple scripting environment to a decoupled, full-stack application.

### 1. Prototype Validation (Streamlit)

The initial logic was validated using Streamlit. This allowed for rapid testing of the core optimization engine—mapping Plaid transaction categories to a custom YAML-based card reward library. However, as the project moved toward a true MVP, the limitations of Streamlit's execution model necessitated a pivot:

- **Session Management:** Streamlit's lack of native session persistence led to frequent user logouts on page refreshes.

- **SDK Integration:** The Plaid Link SDK requires a JavaScript environment for secure, granular event handling that a high-level Python wrapper could not provide.

### 2. The Current MVP Stack (React 18 & FastAPI)

To build a robust end-to-end experience, the frontend was migrated to React 18 with TypeScript and Vite. This enabled:

- **Persistent State:** Using Zustand to maintain user authentication and context across browser sessions.

- **Modern UI:** Tailwind CSS for a responsive, clean interface and Recharts for visualizing spend category breakdowns.

### 3. Data and Infrastructure

The backend is powered by FastAPI, chosen for its speed and type safety.

- **Database:** PostgreSQL provides relational data persistence for user profiles and transaction history.

- **Containerization:** The entire application is orchestrated via Docker. This ensures a "Pull and Run" deployment capability, providing environment isolation and consistent performance across different development machines.

## III. Development Methodology: The Agentic Workflow

A major focus of this project was the implementation of a controlled Agentic AI Workflow. Rather than relying on unguided "black-box" code generation, I utilized Cursor and Gemini 3 as force multipliers within a structured engineering framework.

### 1. The Engineer-Led Approach

The process began with Gemini 3 (Thinking Mode) to architect the Software Requirements Specification (SRS) and the initial database schema. This established the "Source of Truth" before any implementation began.

### 2. Modular Planning (Ask-Plan-Build-Debug)

To maintain control over the codebase and prevent "hallucinated" architecture, I followed a four-stage cycle:

- **Ask Mode:** Assessing the feasibility of new features against the existing codebase.

- **Plan Mode:** Formulating a step-by-step implementation plan. Critically, I required the agent to include testing and validation steps within every plan to ensure that new code did not break existing categorization logic.

- **Build/Agent Mode:** Executing the approved plan. By keeping the agent within a specific file context, I maintained total ownership of the directory structure.

- **Debug Mode:** Addressing regressions discovered during manual testing. This mode was used to force the AI to perform root-cause analysis rather than applying generic "band-aid" fixes.

## IV. Technical Challenges and Strategic Intervention

The transition to a robust PoC required specific manual engineering interventions that agentic tools often overlook.

### 1. Architectural Integrity

AI agents frequently prioritize functionality over security. I had to manually intervene to ensure strict data isolation—guaranteeing that transaction data and Plaid tokens were correctly associated with specific user_ids in the PostgreSQL schema. The agent often overlooked these "loose ends" in favor of simply making the API call work.

### 2. Infrastructure Engineering (Nginx Reverse Proxy)

A significant challenge occurred during the Dockerization of the React frontend. The AI agent struggled with the fact that Vite injects environment variables (like the Backend URL) at build time, whereas a production Docker image needs to be flexible. I directed the implementation of an Nginx reverse proxy within the Docker container. This manual architectural decision allowed the application to be truly portable, enabling the "Pull and Run" capability across different host machines without rebuilding the image.

### 3. Taxonomy Mapping (PFC v2)

To ensure the optimizer worked accurately, I audited the mapping between Plaid's Personal Finance Category (PFC) v2 and my internal reward buckets. This human-in-the-loop validation was essential to ensure that high-value merchants (like Whole Foods or United Airlines) were correctly categorized to trigger the maximum rewards.

## V. Conclusion and Future Roadmap

This project stands as a robust, end-to-end Proof of Concept. It successfully demonstrates the feasibility of using agentic AI to accelerate the development of complex, data-driven financial applications. While the current implementation is a high-fidelity MVP, it is designed with a decoupled architecture that is ready to be moved toward a full production environment.

**Future Scaling Steps:**

- **Caching:** Implementing a Redis layer for frequently accessed card rules.

- **Scalability:** Moving from single Docker containers to an orchestrated environment with load balancing.

- **Observability:** Integrating centralized logging and traffic analytics for real-world user monitoring.
