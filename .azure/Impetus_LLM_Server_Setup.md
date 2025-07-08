# Impetus-LLM-Server Setup Documentation

## Overview
This document provides a detailed record of the Azure setup specific to the `Impetus-LLM-Server` project under GerdsenAI, a premium distributed artificial intelligence company focused on privacy-first, cross-platform AI solutions. `Impetus-LLM-Server` is designed as a dedicated language model server to support advanced AI capabilities for specific use cases within the GerdsenAI ecosystem. The setup follows a serverless-first, cost-optimized architecture aligned with the broader project guides (`GerdsenAI_Azure_setup_guide.md` and `GerdsenAI_Azure_Recommendations.md`).

**Document Last Updated:** July 6, 2025

## Project Context and Objectives
`Impetus-LLM-Server` aims to provide robust language model inference capabilities, potentially for internal tools, customer-facing applications, or specialized AI tasks. The Azure setup for this project focuses on:
- Ensuring isolation from other GerdsenAI projects to prevent data or model overlap.
- Leveraging Azure AI services for scalable, secure model deployment.
- Supporting integration with development environments like Cline for real-time AI assistance.

## Current Azure Setup for Impetus-LLM-Server

### 1. Azure OpenAI Resource and Model Deployment
- **Status:** Completed
- **Details:**
  - Resource Name: `impetus-llm-server-openai` (shared resource due to quota limitations)
  - Location: `East US 2`
  - Resource Group: `gerdsenai-rg`
  - Resource ID: `/subscriptions/8bf993b3-39d9-4d78-a533-5140cce5cee7/resourceGroups/gerdsenai-rg/providers/Microsoft.CognitiveServices/accounts/impetus-llm-server-openai`
  - Endpoint: `https://eastus2.api.cognitive.microsoft.com/`
  - Specific Model Deployment for Impetus-LLM-Server:
    - Deployment Name: `impetus-gpt4o-mini`
    - Model: `gpt-4o-mini`
    - Version: `2024-07-18`
    - SKU: `Standard`
    - Capacity: 1
  - Created: July 6, 2025
- **Purpose:** Provides a dedicated model deployment for `Impetus-LLM-Server` within a shared OpenAI resource, ensuring isolated inference capabilities for this project.
- **Notes:** API keys are securely stored in `gerdsenai-kv` Key Vault. Use Azure Managed Identities or retrieve keys dynamically for secure access in applications.

### 2. Azure AI Search Resource for RAG Isolation
- **Status:** Completed
- **Details:**
  - Resource Name: `impetus-search`
  - Location: `East US 2`
  - Resource Group: `gerdsenai-rg`
  - Resource ID: `/subscriptions/8bf993b3-39d9-4d78-a533-5140cce5cee7/resourceGroups/gerdsenai-rg/providers/Microsoft.Search/searchServices/impetus-search`
  - Endpoint: `https://impetus-search.search.windows.net/`
  - SKU: Basic
  - Created: July 6, 2025
- **Purpose:** Enables retrieval-augmented generation (RAG) specific to `Impetus-LLM-Server`, ensuring that search data and indexes are isolated from other projects to prevent overlap.
- **Notes:** Admin keys are stored in `gerdsenai-kv` Key Vault. Indexes need to be configured for project-specific data sources.

## Integration with Cline or Development Environments
- **Azure OpenAI Model Access**:
  - Configure Cline to use the OpenAI API with the endpoint `https://eastus2.api.cognitive.microsoft.com/` and specify the deployment name `impetus-gpt4o-mini` for API calls.
  - Example in a Node.js environment using `@azure/openai`:
    ```javascript
    const { OpenAIClient } = require('@azure/openai');
    const { DefaultAzureCredential } = require('@azure/identity');
    const client = new OpenAIClient('https://eastus2.api.cognitive.microsoft.com/', new DefaultAzureCredential());
    const deploymentName = 'impetus-gpt4o-mini';
    // Use deploymentName in API calls for model inference
    ```
  - Retrieve API keys from `gerdsenai-kv` Key Vault if Managed Identities are not used.
- **Azure AI Search for RAG**:
  - Set up indexes under `impetus-search` for project-specific documentation or data.
  - Use the endpoint `https://impetus-search.search.windows.net/` for search queries, ensuring RAG responses are tailored to `Impetus-LLM-Server`.
  - Example in Node.js using `@azure/search-documents`:
    ```javascript
    const { SearchClient } = require('@azure/search-documents');
    const endpoint = 'https://impetus-search.search.windows.net/';
    const apiKey = 'retrieve-from-key-vault';
    const indexName = 'impetus-docs';
    const client = new SearchClient(endpoint, indexName, { key: apiKey });
    // Use client to search for RAG data
    ```
  - Combine search results with model outputs for enhanced AI responses in Cline.

## Setup Log and Command History
- **July 6, 2025 - Azure OpenAI Resource Creation:**
  - Command: `az cognitiveservices account create --name impetus-llm-server-openai --resource-group gerdsenai-rg --kind OpenAI --sku S0 --location eastus2`
  - Result: Created OpenAI resource `impetus-llm-server-openai` in `East US 2`.
- **July 6, 2025 - Model Deployment for Impetus-LLM-Server:**
  - Command: `az cognitiveservices account deployment create --name impetus-llm-server-openai --resource-group gerdsenai-rg --deployment-name impetus-gpt4o-mini --model-name gpt-4o-mini --model-version "2024-07-18" --model-format OpenAI --sku-name Standard --sku-capacity 1`
  - Result: Deployed `gpt-4o-mini` model under deployment name `impetus-gpt4o-mini`.
- **July 6, 2025 - Azure AI Search Resource Creation:**
  - Command: `az search service create --name impetus-search --resource-group gerdsenai-rg --sku Basic --location eastus2`
  - Result: Created Azure AI Search resource `impetus-search` for RAG isolation.

## Best Practices and Notes
- **Isolation:** Resources and deployments are configured to ensure `Impetus-LLM-Server` operates independently from other GerdsenAI projects, preventing data or model overlap.
- **Security:** Follow Zero Trust principles by using managed identities or securely stored keys in `gerdsenai-kv` Key Vault for access to Azure resources.
- **Documentation Maintenance:** This file will be updated with significant milestones or changes specific to `Impetus-LLM-Server` to maintain a complete record.

## Conclusion
This documentation outlines the Azure setup for `Impetus-LLM-Server` as of July 6, 2025, with dedicated model deployment and search resources established to support isolated AI capabilities within the GerdsenAI ecosystem. Future updates will include index configurations for RAG and further integration details as the project evolves.
