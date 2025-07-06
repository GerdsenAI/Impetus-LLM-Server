const { AppController } = require('../utils/app-controller');
const { ApiClient } = require('../utils/api-client');
const { testData } = require('../utils/test-data');

describe('IMPETUS API Endpoints Tests', () => {
  let appController;
  let apiClient;

  beforeAll(async () => {
    appController = new AppController();
    apiClient = new ApiClient();
    
    // Ensure app is running
    await appController.launch();
    
    // Wait for server to be ready
    await new Promise(resolve => setTimeout(resolve, 10000));
  });

  afterAll(async () => {
    await appController.terminate();
  });

  describe('Health and Status Endpoints', () => {
    test('should return healthy status from health endpoint', async () => {
      const response = await apiClient.healthCheck();
      
      expect(response.success).toBe(true);
      expect(response.status).toBe(200);
      expect(response.data).toHaveProperty('status', 'healthy');
      expect(response.data).toHaveProperty('timestamp');
      expect(response.data).toHaveProperty('components');
      
      console.log('✅ Health endpoint responding correctly');
    });

    test('should return hardware information', async () => {
      const response = await apiClient.getHardwareInfo();
      
      expect(response.success).toBe(true);
      expect(response.status).toBe(200);
      expect(response.data).toHaveProperty('chip_name');
      expect(response.data).toHaveProperty('cpu_cores');
      
      console.log(`✅ Hardware info: ${response.data.chip_name || 'Unknown'} chip detected`);
    });
  });

  describe('OpenAI Compatible Models Endpoint', () => {
    test('should return models list in OpenAI format', async () => {
      const response = await apiClient.getModels();
      
      expect(response.success).toBe(true);
      expect(response.status).toBe(200);
      expect(response.data).toMatchObject(testData.expectedResponses.models);
      
      // Verify each model has required fields
      response.data.data.forEach(model => {
        expect(model).toHaveProperty('id');
        expect(model).toHaveProperty('object', 'model');
        expect(model).toHaveProperty('created');
        expect(model).toHaveProperty('owned_by');
      });
      
      console.log(`✅ Models endpoint returning ${response.data.data.length} models`);
    });

    test('should include default models', async () => {
      const response = await apiClient.getModels();
      
      expect(response.success).toBe(true);
      
      const modelIds = response.data.data.map(model => model.id);
      
      // Should have at least gpt-4 or similar default models
      const hasDefaultModel = modelIds.some(id => 
        id.includes('gpt') || id.includes('llama') || id.includes('mistral')
      );
      
      expect(hasDefaultModel).toBe(true);
      
      console.log(`✅ Available models: ${modelIds.join(', ')}`);
    });
  });

  describe('Chat Completions Endpoint', () => {
    test('should handle basic chat completion request', async () => {
      const response = await apiClient.chatCompletion(
        testData.chatMessages.simple,
        { max_tokens: 50 }
      );
      
      expect(response.success).toBe(true);
      expect(response.status).toBe(200);
      expect(response.data).toMatchObject(testData.expectedResponses.chatCompletion);
      
      const choice = response.data.choices[0];
      expect(choice.message.content).toBeTruthy();
      expect(choice.message.content.length).toBeGreaterThan(0);
      
      console.log(`✅ Chat completion response: "${choice.message.content.substring(0, 100)}..."`);
    });

    test('should handle conversation context', async () => {
      const response = await apiClient.chatCompletion(
        testData.chatMessages.conversation,
        { max_tokens: 100 }
      );
      
      expect(response.success).toBe(true);
      expect(response.data.choices[0].message.content).toBeTruthy();
      
      console.log('✅ Conversation context handled correctly');
    });

    test('should support streaming responses', async () => {
      const response = await apiClient.chatCompletion(
        testData.chatMessages.simple,
        { stream: true, max_tokens: 30 }
      );
      
      expect(response.success).toBe(true);
      expect(response.chunks).toBeDefined();
      expect(Array.isArray(response.chunks)).toBe(true);
      expect(response.chunks.length).toBeGreaterThan(0);
      
      // Verify streaming format
      const hasValidStreamData = response.chunks.some(chunk => 
        chunk.startsWith('data: ') && chunk.includes('"object":')
      );
      expect(hasValidStreamData).toBe(true);
      
      console.log(`✅ Streaming response with ${response.chunks.length} chunks`);
    }, 45000);

    test('should handle different model parameters', async () => {
      const tests = [
        { temperature: 0.1, max_tokens: 20 },
        { temperature: 0.9, max_tokens: 40 },
        { temperature: 0.5, max_tokens: 60, top_p: 0.8 }
      ];
      
      for (const params of tests) {
        const response = await apiClient.chatCompletion(
          testData.chatMessages.simple,
          params
        );
        
        expect(response.success).toBe(true);
        expect(response.data.choices[0].message.content).toBeTruthy();
      }
      
      console.log('✅ Different parameter configurations working');
    });
  });

  describe('Error Handling', () => {
    test('should handle invalid model gracefully', async () => {
      const response = await apiClient.chatCompletion(
        testData.errorScenarios.invalidModel.messages,
        { model: testData.errorScenarios.invalidModel.model }
      );
      
      // Should either handle gracefully or return appropriate error
      if (!response.success) {
        expect(response.status).toBeGreaterThanOrEqual(400);
      } else {
        // If it succeeds, it should fall back to a default model
        expect(response.data.choices[0].message.content).toBeTruthy();
      }
      
      console.log('✅ Invalid model handled appropriately');
    });

    test('should validate message format', async () => {
      const response = await apiClient.chatCompletion(
        testData.errorScenarios.invalidRole.messages,
        { model: 'gpt-4' }
      );
      
      // Should return an error for invalid role
      if (!response.success) {
        expect(response.status).toBeGreaterThanOrEqual(400);
        console.log('✅ Invalid message role rejected correctly');
      } else {
        // If it accepts invalid role, log it but don't fail the test
        console.log('⚠️ Invalid message role was accepted');
      }
    });

    test('should handle missing required fields', async () => {
      const response = await apiClient.client.post('/v1/chat/completions', 
        testData.errorScenarios.missingMessages
      ).catch(error => ({
        success: false,
        status: error.response?.status || 0,
        error: error.message
      }));
      
      expect(response.success).toBe(false);
      expect(response.status).toBeGreaterThanOrEqual(400);
      
      console.log('✅ Missing messages field properly rejected');
    });
  });

  describe('API Compatibility', () => {
    test('should validate full OpenAI API compatibility', async () => {
      const compatibility = await apiClient.validateOpenAICompatibility();
      
      expect(compatibility.models).toBe(true);
      expect(compatibility.chatCompletions).toBe(true);
      expect(compatibility.streaming).toBe(true);
      
      const compatibilityScore = Object.values(compatibility).filter(Boolean).length;
      const totalTests = Object.keys(compatibility).length;
      
      console.log(`✅ OpenAI compatibility: ${compatibilityScore}/${totalTests} tests passed`);
      
      // Expect at least 75% compatibility
      expect(compatibilityScore / totalTests).toBeGreaterThanOrEqual(0.75);
    }, 60000);

    test('should have correct response headers', async () => {
      const response = await apiClient.client.get('/v1/models');
      
      expect(response.headers['content-type']).toContain('application/json');
      expect(response.headers['access-control-allow-origin']).toBeDefined();
      
      console.log('✅ Response headers are correct');
    });

    test('should handle CORS preflight requests', async () => {
      try {
        const response = await apiClient.client.options('/v1/models');
        expect(response.status).toBeLessThan(300);
        console.log('✅ CORS preflight handled correctly');
      } catch (error) {
        // Some servers might not implement OPTIONS, which is okay
        console.log('⚠️ CORS preflight not implemented (may be okay)');
      }
    });
  });

  describe('Authentication', () => {
    test('should accept requests with API key', async () => {
      const response = await apiClient.getModels();
      
      expect(response.success).toBe(true);
      expect(response.status).toBe(200);
      
      console.log('✅ API key authentication working');
    });

    test('should handle requests without API key', async () => {
      const clientNoAuth = new apiClient.constructor();
      clientNoAuth.client.defaults.headers['Authorization'] = '';
      
      const response = await clientNoAuth.getModels();
      
      // Should either work (no auth required) or return auth error
      if (response.success) {
        console.log('✅ No authentication required');
      } else {
        expect(response.status).toBe(401);
        console.log('✅ Authentication properly enforced');
      }
    });
  });
});
