# Cline Agent Planning Initialization Protocol (Impetus-LLM-Server)

---

### 1. Load Essential Project Context

- **Start with `ai.md`**: This file is the canonical source for project overview, current status, and planning workflow. It defines the mission, key features, and immediate post-MVP focus (frontend with Ant Design/Vite, code signing, distribution).
- **Cross-reference `.clinerules/memory.md`**: This file provides critical technical context, known issues, current limitations (e.g., only GGUF is real, others are placeholders), and a prioritized list of post-release tasks. It also documents recent breakthroughs, MCP tool setup, and testing protocols.

---

### 2. Gather Supporting Resources

- **Check `todo.md`**: For the latest prioritized tasks, especially those related to frontend development, code signing, and distribution.
- **Review `docs/frontend_development_guidelines.md`**: For Ant Design best practices, dashboard component recommendations, and integration tips.
- **Consult `.clinerules/mcp_configuration.md`**: For MCP tool usage, context sharing, and efficient context loading (80%+ token reduction).
- **Leverage Ant Design resources**: Use the official docs and dashboard templates linked in ai.md for UI/UX planning.

---

### 3. Planning Workflow

**Follow this structured workflow:**
1. **Context Loading**: Use MCP tools to load summaries and critical context from ai.md, .clinerules/memory.md, and todo.md. Avoid reading large files directly—use smart search and memory recall tools.
2. **Task Identification**: Focus on post-MVP priorities:
   - Frontend rebuild with Ant Design and Vite (VectorDB/MCP dashboards)
   - Code signing, notarization, auto-updates
   - Distribution improvements (GitHub releases, download page, announcement)
3. **Solution Architecture**:
   - For frontend: Plan the component structure, dashboard layout, and API integration points using Ant Design guidelines.
   - For backend: Ensure all endpoints needed for the new UI are exposed and documented.
   - For distribution: Outline steps for code signing, notarization, and update mechanisms.
4. **Automated Testing**: Prioritize browser-based automated testing (Puppeteer, Playwright, Browser Tools MCP) for all new features and UI changes.
5. **Discussion & Clarification**: Use the planning phase to clarify any ambiguities, discuss resource needs, and identify potential blockers.
6. **Implementation Readiness**: Once the plan is complete and agreed upon, request the user to "toggle to Act mode" to begin execution.

---

### 4. Critical Technical Reminders

- **Always activate the Python virtual environment** before any backend work:  
  `source .venv/bin/activate`
- **Only GGUF inference is real**; all other model formats are placeholders.
- **Model Management UI is already implemented** in the React frontend; focus is now on advanced dashboards and post-MVP enhancements.
- **Use MCP tools for all context loading and testing** to maximize efficiency and minimize token usage.
- **Automated browser testing is mandatory** for all UI and API changes.

---

### 5. Success Criteria

- All planning is aligned with the mission: local, privacy-first, Apple Silicon-optimized LLM server with seamless VS Code/Cline integration.
- The plan addresses post-MVP priorities, especially frontend dashboard enhancements and distribution improvements.
- All context is loaded efficiently using MCP tools, and the workflow is documented for agent handoff and cross-agent collaboration.

---

**Summary:**  
To initialize a planning session for Impetus-LLM-Server, agents must load context from ai.md and .clinerules/memory.md, gather supporting resources, follow the structured planning workflow, use MCP tools for efficiency, and focus on post-MVP enhancements—especially frontend dashboard development with Ant Design and Vite. All plans should be validated with automated browser testing and prepared for seamless handoff to Act mode for implementation.

---

# AI Agent Initialization for Impetus-LLM-Server

## Purpose
This document serves as the initialization point for Cline plan agents working on the Impetus-LLM-Server project. It provides essential context, current status, and a structured workflow to ensure the planning phase is aligned with project goals. Use this file with the "initialize from ai.md" command to set up the planning environment correctly.

## Project Overview
Impetus-LLM-Server is a production-ready macOS application designed for managing Apple Silicon hardware optimization, machine learning models, and AI workloads with OpenAI-compatible API endpoints. Optimized specifically for Apple Silicon (M1-M4 series), it offers real-time hardware monitoring and VS Code extension compatibility.

- **Mission**: Create the premier local LLM inference server for developers, with flawless VS Code integration, universal model format support, and dynamically optimized performance across all Apple Silicon machines, maintaining complete privacy with zero cloud dependencies.
- **Key Features**: OpenAI API compatibility, dynamic hardware optimization, support for multiple model formats (GGUF, SafeTensors, MLX, etc.), and a modern frontend interface for management.

## Current Status (July 8, 2025)
- **MVP Status**: 100% COMPLETE - v1.0.0 released with a self-contained installer.
- **Completed Foundation**:
  - All 6 model format loaders implemented (GGUF, SafeTensors, MLX, CoreML, PyTorch, ONNX).
  - Model loader factory pattern with automatic format detection.
  - Unified inference interface (UnifiedInferenceEngine).
  - Native macOS Electron app "Impetus" built and installed.
  - Enhanced production server with progressive ML loading.
  - Real GGUF inference operational at 138.61 tokens/sec on M3 Ultra.
  - VS Code/Cline integration fully tested and validated.
- **Recent Updates**:
  - Comprehensive cleanup of non-essential files and directories to streamline project structure.
  - Dependency files updated to focus on core backend packages.
  - Frontend transition prepared from Next.js to Vite and Ant Design for a modern, enterprise-grade interface.
- **Current Focus**: Post-MVP enhancements including frontend development for VectorDB and MCP service dashboards, code signing, notarization, auto-updates, and distribution improvements.

## Key Goals for Planning Phase
The planning phase should focus on the following objectives to guide the next steps of development:
1. **Frontend Development with Ant Design and Vite**:
   - Set up a new frontend structure to create a modern UI for model management, hardware metrics visualization, and optimization settings.
   - Leverage Ant Design resources for dashboard development, especially for VectorDB and MCP services, ensuring intuitive data display and visualization.
2. **Post-Release Improvements**:
   - Plan for code signing and Apple notarization to facilitate easier installation and distribution.
   - Architect auto-update mechanisms (e.g., Sparkle or Electron updater) for seamless user experience.
   - Enhance performance dashboards with real-time graphs for hardware metrics.
3. **Distribution Strategy**:
   - Develop a plan for uploading to GitHub releases, creating a download page, and announcing the release to the community.

## Planning Workflow for Cline Agents
Follow this structured workflow during the planning phase to ensure alignment with project goals:
1. **Gather Context**:
   - Review this 'ai.md' for project overview, current status, and Ant Design resources for frontend development.
   - Check 'todo.md' for detailed task lists and recent updates.
   - Refer to '.clinerules/memory.md' for critical context, known issues, and recent breakthroughs.
   - Use 'docs/frontend_development_guidelines.md' for comprehensive Ant Design resources and frontend development guidelines.
2. **Identify Key Tasks**:
   - Focus on high-priority post-MVP tasks such as frontend development, code signing, and distribution.
   - Prioritize tasks that align with the goal of enhancing user experience and project accessibility, particularly the development of VectorDB and MCP service dashboards.
3. **Architect Solutions**:
   - For frontend development, plan the structure using Vite and Ant Design, identifying key components for VectorDB/MCP dashboards based on the provided component recommendations.
   - Outline integration points with backend APIs for model management and hardware metrics.
   - Consider best practices from Ant Design visualization guidelines to avoid information overload in dashboards, organizing information from summary to detail and limiting modules to 5-9.
4. **Engage in Discussion**:
   - Use the planning phase to discuss potential challenges, resource needs, or additional tools (like MCP servers) that could aid development.
   - Clarify any ambiguities in task prioritization or technical approaches with the user if necessary.
5. **Prepare for Implementation**:
   - Once a detailed plan is agreed upon, request to toggle to Act mode to execute the planned tasks, such as creating frontend structures or updating documentation.

## Critical Resources
- **Project Documentation**:
  - 'todo.md': Current tasks and progress tracking.
  - 'docs/frontend_development_guidelines.md': Guidelines and resources for frontend development with Ant Design.
  - '.clinerules/memory.md': Detailed project memory and critical updates.
- **Ant Design Resources for VectorDB and MCP Service Dashboards**:
  - **Official Documentation**:
    - **Main Ant Design Site**: [https://ant.design/](https://ant.design/) - The official documentation hub for Ant Design, the world's second most popular React UI framework.
    - **Component Overview**: [https://ant.design/components/overview/](https://ant.design/components/overview/) - Complete component library reference.
    - **Getting Started Guide**: [https://ant.design/docs/react/getting-started/](https://ant.design/docs/react/getting-started/) - Quick setup and installation instructions.
    - **Ant Design Pro**: [https://pro.ant.design/](https://pro.ant.design/) - Enterprise-ready templates and patterns.
    - **Visualization Guidelines**: [https://ant.design/docs/spec/visualization-page/](https://ant.design/docs/spec/visualization-page/) - Best practices for data dashboards, recommending organizing information from summary to detail, using filtering capabilities, and limiting modules to 5-9 to avoid information overload.
  - **Dashboard Examples & Templates**:
    - **Open Source Examples**:
      - **Ant Design Pro - GitHub**: Includes analytics, monitoring, and workspace dashboards with data tables, forms, and visualization components, perfect for enterprise-level applications.
      - **Antd Multipurpose Dashboard - GitHub**: Built with Vite, TypeScript, and Ant Design 5, includes Ant Design Charts for data visualization, and is well-documented with Storybook integration.
      - **Muse Ant Design Dashboard - Creative Tim**: Free React & Ant Design admin template with 120+ components and multiple theme options, good for quick prototyping.
    - **Live Demos**:
      - **Ant Design Pro Preview**: Official enterprise dashboard demo.
      - **Design Sparx Demo**: A dynamic and versatile multipurpose dashboard template utilizing React, Vite, Ant Design, and Storybook by Design Sparx, featuring multi-dashboard with data visualization.
  - **Components Most Relevant for VectorDB/MCP Dashboard**:
    - **Data Display**:
      - **Table**: Advanced features for displaying vector collections and search results.
      - **Descriptions**: Perfect for metadata display.
      - **Statistic**: For showing metrics like query latency and index size.
    - **Data Visualization**:
      - **Progress**: Indexing progress indicators.
      - **Charts (via Ant Design Charts)**: For embedding visualizations. Consider integrating D3.js or Three.js for vector space visualizations.
    - **Forms & Controls**:
      - **Form**: Complex configuration forms with validation.
      - **Select/Input**: Query interfaces.
      - **Slider**: Parameter tuning (dimensions, thresholds).
    - **Layout**:
      - **Layout with collapsible sidebar**: For navigation.
      - **Tabs**: Switching between indexes/collections.
      - **Drawer/Modal**: Detailed vector inspection.
    - **Feedback**:
      - **Alert/Notification**: System status and errors.
      - **Result**: Query results display.

## Notes for Agents
- Always start by loading context from this file to ensure alignment with project goals.
- Use MCP tools if available for efficient context loading and token reduction (refer to '.clinerules/mcp_configuration.md' for setup).
- Focus on planning for post-MVP enhancements, particularly frontend development for VectorDB and MCP service dashboards, to meet the project's current needs.
- Maintain a privacy-first approach, ensuring all solutions align with local-only processing and zero cloud dependencies.

This initialization sets the stage for effective planning, guiding the agent to focus on the Impetus-LLM-Server's immediate and long-term objectives with a strong emphasis on frontend development using Ant Design resources.
