# Frontend Development Guidelines for Impetus-LLM-Server

## Purpose
This document provides guidelines and resources for the frontend development of the Impetus-LLM-Server project. With the transition to Vite and Ant Design, the focus is on creating a modern, enterprise-grade interface for LLM management, specifically targeting VectorDB and MCP service dashboards. Additionally, it outlines the integration with a lightweight backend web server service to support the frontend.

## Technology Stack
- **Vite**: A fast, modern frontend tooling framework for building React applications.
- **Ant Design**: A popular React UI framework offering a comprehensive set of components for enterprise-level applications.
- **React**: The JavaScript library for building user interfaces, used in conjunction with Vite and Ant Design.

## Development Goals
The frontend development aims to:
- Provide an intuitive interface for model management, hardware metrics visualization, and optimization settings.
- Integrate seamlessly with the existing OpenAI-compatible API endpoints provided by the backend.
- Support dashboards for VectorDB and MCP services with advanced data display and visualization capabilities.
- Ensure efficient communication with a lightweight backend web server service designed specifically for frontend support.

## Backend Integration with Lightweight Web Server Service
To support the frontend, a lightweight web server service will be developed using the existing Flask backend in 'gerdsen_ai_server/src'. This service will:
- Focus on efficient API delivery for VectorDB and MCP dashboards, minimizing resource usage while maintaining OpenAI API compatibility.
- Support static file serving for the Vite-built frontend, ensuring fast loading of UI assets.
- Handle API requests for model management, hardware metrics, and optimization settings, providing a seamless interaction between frontend and backend.
- Be optimized for lightweight operation, potentially using a simplified server configuration (e.g., a lighter version of 'production_main.py') to reduce overhead.

### Development Steps for Backend Integration
1. **Create Lightweight Service**: Develop a new Flask-based service or modify an existing server script to focus on frontend support, ensuring it can serve static files and handle API requests efficiently.
2. **Configure API Endpoints**: Ensure all necessary API endpoints (e.g., model management, hardware metrics) are accessible through this lightweight service.
3. **Test Integration**: Validate that the frontend can communicate with the backend service without performance bottlenecks, using tools like Puppeteer for automated testing.
4. **Document Setup**: Update project documentation to include setup and configuration instructions for the lightweight web server service, enabling developers to deploy and test the integrated solution easily.

## Ant Design Resources and Examples
For the development of the VectorDB and MCP service dashboards, the following Ant Design resources and examples are particularly useful:

### Official Documentation
- **Main Ant Design Site**: [https://ant.design/](https://ant.design/) - The official documentation hub for Ant Design, the world's second most popular React UI framework.
- **Component Overview**: [https://ant.design/components/overview/](https://ant.design/components/overview/) - Complete component library reference.
- **Getting Started Guide**: [https://ant.design/docs/react/getting-started/](https://ant.design/docs/react/getting-started/) - Quick setup and installation instructions.
- **Ant Design Pro**: [https://pro.ant.design/](https://pro.ant.design/) - Enterprise-ready templates and patterns.
- **Visualization Guidelines**: [https://ant.design/docs/spec/visualization-page/](https://ant.design/docs/spec/visualization-page/) - Best practices for data dashboards, recommending organizing information from summary to detail, using filtering capabilities, and limiting modules to 5-9 to avoid information overload.

### Dashboard Examples & Templates
- **Open Source Examples**:
  - **Ant Design Pro - GitHub**: Includes analytics, monitoring, and workspace dashboards with data tables, forms, and visualization components, perfect for enterprise-level applications.
  - **Antd Multipurpose Dashboard - GitHub**: Built with Vite, TypeScript, and Ant Design 5, includes Ant Design Charts for data visualization, and is well-documented with Storybook integration.
  - **Muse Ant Design Dashboard - Creative Tim**: Free React & Ant Design admin template with 120+ components and multiple theme options, good for quick prototyping.
- **Live Demos**:
  - **Ant Design Pro Preview**: Official enterprise dashboard demo.
  - **Design Sparx Demo**: A dynamic and versatile multipurpose dashboard template utilizing React, Vite, Ant Design, and Storybook by Design Sparx, featuring multi-dashboard with data visualization.

### Components Most Relevant for VectorDB/MCP Dashboard
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

## Development Workflow
1. **Setup Project Structure**: Initialize the frontend project using Vite, following the Getting Started Guide from Ant Design for setup instructions.
2. **Component Development**: Develop UI components for model management, hardware metrics, and optimization settings, leveraging the relevant Ant Design components listed above.
3. **API Integration**: Connect the frontend to backend API endpoints for model management, hardware metrics, and other services, ensuring the lightweight web server service is operational for efficient communication.
4. **Testing and Validation**: Ensure the UI is responsive and accessible, using tools like Storybook for component testing and following Ant Design's visualization guidelines.

## Best Practices
- Adhere to Ant Design's visualization guidelines to avoid information overload in dashboards, organizing information from summary to detail and limiting modules to 5-9.
- Use the provided dashboard examples as references for layout and functionality, adapting them to the specific needs of VectorDB and MCP service dashboards.
- Regularly review the Ant Design documentation for updates or new components that could enhance the dashboard functionality.
- Ensure the frontend is optimized for performance, leveraging Vite's fast build times and hot module replacement for efficient
