# API Key Configuration Summary for GerdsenAI Projects

## Overview
This document summarizes the API key configuration files created for the Azure resources associated with three GerdsenAI projects: Impetus-LLM-Server, Samson-AI, and Socrates-MCP-Server. These configurations are stored within the /.azure folder and reference the endpoints and deployment details for Azure OpenAI and Azure AI Search resources. API keys are securely stored in the `gerdsenai-kv` Key Vault, and instructions for secure access are provided below.

**Last Updated:** July 6, 2025

## Configuration Files
The following configuration files have been created in the /.azure folder:

- **Impetus_LLM_Server_API_Config.json**: Contains endpoint and deployment details for Impetus-LLM-Server.
  - Azure OpenAI Endpoint: `https://eastus2.api.cognitive.microsoft.com/`
  - Deployment Name: `impetus-gpt4o-mini`
  - Azure AI Search Endpoint: `https://impetus-search.search.windows.net/`

- **Samson_AI_API_Config.json**: Contains endpoint and deployment details for Samson-AI.
  - Azure OpenAI Endpoint: `https://eastus2.api.cognitive.microsoft.com/`
  - Deployment Name: `samson-gpt4o-mini`
  - Azure AI Search Endpoint: `https://samson-search.search.windows.net/`

- **Socrates_MCP_Server_API_Config.json**: Contains endpoint and deployment details for Socrates-MCP-Server.
  - Azure OpenAI Endpoint: `https://eastus2.api.cognitive.microsoft.com/`
  - Deployment Name: `socrates-gpt4o-mini`
  - Azure AI Search Endpoint: `https://socrates-search.search.windows.net/`

## Secure API Key Access Instructions
API keys for the Azure resources are stored in the `gerdsenai-kv` Key Vault (URI: `https://gerdsenai-kv.vault.azure.net/`). To ensure security, follow these best practices for accessing the keys:

- **Use Azure Managed Identities**: Whenever possible, configure your applications to use Azure Managed Identities for seamless and secure access to Key Vault resources without hardcoding API keys.
- **Dynamic Key Retrieval with Azure CLI**: If Managed Identities are not feasible, retrieve keys dynamically using Azure CLI commands. Ensure you have the necessary permissions (e.g., "Key Vault Secrets Officer" role). Example command:
  ```bash
  az keyvault secret show --vault-name gerdsenai-kv --name <secret-name>
  ```
- **Environment Variables**: Store retrieved keys in environment variables within your application runtime, avoiding storage in source code or configuration files.
- **Integration with Development Environments**: For tools like Cline, configure the API endpoints and deployment names as specified in the configuration files. Use the retrieved keys or Managed Identities for authentication.

## Notes
- All configurations are restricted to the /.azure folder as per the project guidelines.
- Ensure that any application or script accessing these resources adheres to Zero Trust security principles, validating access permissions and using secure communication channels.

## Enabling API Configurations for Your Project
To enable these API configurations for your project, follow these steps to securely integrate the Azure resources into your application or development environment:

1. **Identify the Relevant Configuration File**:
   - Locate the JSON configuration file for your project in the /.azure folder (e.g., `Impetus_LLM_Server_API_Config.json` for Impetus-LLM-Server).
   - Note the Azure OpenAI endpoint, deployment name, and Azure AI Search endpoint specified in the file.

2. **Securely Access API Keys from Key Vault**:
   - **Using Azure Managed Identities (Recommended)**:
     - Configure your application to use Azure Managed Identities for authentication. This allows your app to access the Key Vault without hardcoding credentials.
     - Assign the appropriate role to your application’s identity (e.g., "Key Vault Secrets Officer") in the Azure portal under the Key Vault’s Access Control (IAM) settings.
     - In your application code, use the Azure SDK to authenticate and retrieve secrets. Example for Python using `azure-identity`:
       ```python
       from azure.identity import DefaultAzureCredential
       from azure.keyvault.secrets import SecretClient
       
       credential = DefaultAzureCredential()
       client = SecretClient(vault_url="https://gerdsenai-kv.vault.azure.net/", credential=credential)
       secret = client.get_secret("<secret-name>")
       api_key = secret.value
       ```
   - **Using Azure CLI (Alternative)**:
     - If Managed Identities are not feasible, use Azure CLI to retrieve the API key dynamically. Ensure you are logged in with an account that has the necessary permissions.
     - Run the following command to get the secret value:
       ```bash
       az keyvault secret show --vault-name gerdsenai-kv --name <secret-name> --query value --output tsv
       ```
     - Store the retrieved key in an environment variable for temporary use within your session or script:
       ```bash
       export OPENAI_API_KEY=$(az keyvault secret show --vault-name gerdsenai-kv --name <secret-name> --query value --output tsv)
       ```

3. **Configure Your Application or Development Tool**:
   - **For VS Code Extensions like Cline**:
     - Open the extension settings in VS Code.
     - Set the API endpoint to the one specified in your project’s configuration file (e.g., `https://eastus2.api.cognitive.microsoft.com/`).
     - Specify the deployment name (e.g., `impetus-gpt4o-mini`) and model (e.g., `gpt-4o-mini`).
     - Use the API key retrieved from the Key Vault for authentication, ensuring it is not hardcoded but passed via an environment variable or secure configuration.
   - **For Custom Applications**:
     - Update your application’s configuration to use the endpoints and deployment names from the JSON file.
     - Implement secure API key handling using the methods described above to authenticate requests to Azure OpenAI and AI Search services.

4. **Test the Integration**:
   - Verify connectivity by making a test API call to the Azure OpenAI endpoint using the specified deployment. For example, using `curl`:
     ```bash
     curl -X POST "${OPENAI_ENDPOINT}openai/deployments/${DEPLOYMENT_NAME}/chat/completions?api-version=2024-07-18" \
       -H "Content-Type: application/json" \
       -H "Authorization: Bearer ${OPENAI_API_KEY}" \
       -d '{"messages": [{"role": "user", "content": "Hello, world!"}]}'
     ```
   - Ensure that responses are received correctly and troubleshoot any authentication or connectivity issues by checking permissions and network settings.

5. **Adhere to Security Best Practices**:
   - Never store API keys in source code or version control.
   - Regularly rotate keys in the Key Vault and update your application configurations accordingly.
   - Monitor access logs in Azure to detect any unauthorized access attempts to the Key Vault or API endpoints.

By following these steps, you can enable the API configurations for your project, ensuring secure and efficient integration with Azure resources.

## Conclusion
The API key configurations for the three GerdsenAI projects have been documented and are ready for use. Refer to the individual JSON files for specific endpoint and deployment details, and follow the secure access instructions and integration steps provided above to enable these resources in your applications.
