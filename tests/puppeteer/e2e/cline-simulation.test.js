const { AppController } = require('../utils/app-controller');
const { ApiClient } = require('../utils/api-client');
const { testData } = require('../utils/test-data');

describe('VS Code Cline Integration Tests', () => {
  let appController;
  let apiClient;

  beforeAll(async () => {
    appController = new AppController();
    apiClient = new ApiClient();
    
    // Ensure app is running
    await appController.launch();
    await new Promise(resolve => setTimeout(resolve, 10000));
  });

  afterAll(async () => {
    await appController.terminate();
  });

  describe('Cline Extension Compatibility', () => {
    test('should handle typical Cline file creation request', async () => {
      console.log('📝 Testing Cline file creation scenario...');
      
      const response = await apiClient.chatCompletion(
        testData.clineScenarios.fileCreation,
        {
          model: 'gpt-4',
          max_tokens: 500,
          temperature: 0.7,
          stream: false
        }
      );
      
      expect(response.success).toBe(true);
      expect(response.data.choices[0].message.content).toBeTruthy();
      
      const content = response.data.choices[0].message.content;
      
      // Should contain code-like response
      const hasCodeIndication = content.includes('function') || 
                               content.includes('const') || 
                               content.includes('```') ||
                               content.toLowerCase().includes('javascript');
      
      expect(hasCodeIndication).toBe(true);
      
      console.log(`✅ File creation request handled: ${content.substring(0, 100)}...`);
    }, 45000);

    test('should handle code review requests like Cline', async () => {
      console.log('🔍 Testing Cline code review scenario...');
      
      const response = await apiClient.chatCompletion(
        testData.clineScenarios.codeReview,
        {
          model: 'gpt-4',
          max_tokens: 400,
          temperature: 0.3,
          stream: false
        }
      );
      
      expect(response.success).toBe(true);
      
      const content = response.data.choices[0].message.content;
      
      // Should provide suggestions or improvements
      const hasReviewContent = content.toLowerCase().includes('improve') ||
                              content.toLowerCase().includes('suggest') ||
                              content.toLowerCase().includes('better') ||
                              content.toLowerCase().includes('async');
      
      expect(hasReviewContent).toBe(true);
      
      console.log('✅ Code review request handled appropriately');
    }, 45000);

    test('should support streaming for real-time Cline responses', async () => {
      console.log('🌊 Testing streaming for Cline compatibility...');
      
      const response = await apiClient.chatCompletion(
        testData.clineScenarios.debugging,
        {
          model: 'gpt-4',
          max_tokens: 300,
          temperature: 0.5,
          stream: true
        }
      );
      
      expect(response.success).toBe(true);
      expect(response.chunks).toBeDefined();
      expect(response.chunks.length).toBeGreaterThan(0);
      
      // Verify streaming format matches OpenAI spec
      let hasValidChunks = false;
      let hasContentChunks = false;
      
      for (const chunk of response.chunks) {
        if (chunk.startsWith('data: ') && chunk.includes('"object":')) {
          hasValidChunks = true;
          
          try {
            const data = JSON.parse(chunk.replace('data: ', ''));
            if (data.choices?.[0]?.delta?.content) {
              hasContentChunks = true;
            }
          } catch (e) {
            // Some chunks might be [DONE] or other formats
          }
        }
      }
      
      expect(hasValidChunks).toBe(true);
      expect(hasContentChunks).toBe(true);
      
      console.log(`✅ Streaming working with ${response.chunks.length} chunks`);
    }, 60000);
  });

  describe('Cline Workflow Simulation', () => {
    test('should handle multi-turn conversation like Cline', async () => {
      console.log('💬 Testing multi-turn Cline conversation...');
      
      // First request - initial code
      const firstResponse = await apiClient.chatCompletion([
        { role: 'user', content: 'Write a simple React component for a button.' }
      ], { max_tokens: 200 });
      
      expect(firstResponse.success).toBe(true);
      
      // Second request - modification (simulate Cline follow-up)
      const conversation = [
        { role: 'user', content: 'Write a simple React component for a button.' },
        firstResponse.data.choices[0].message,
        { role: 'user', content: 'Now add click handling and state management.' }
      ];
      
      const secondResponse = await apiClient.chatCompletion(conversation, { max_tokens: 300 });
      
      expect(secondResponse.success).toBe(true);
      expect(secondResponse.data.choices[0].message.content).toBeTruthy();
      
      console.log('✅ Multi-turn conversation handled correctly');
    }, 60000);

    test('should handle Cline refactoring requests', async () => {
      console.log('🔄 Testing Cline refactoring scenario...');
      
      const response = await apiClient.chatCompletion(
        testData.clineScenarios.refactoring,
        {
          model: 'gpt-4',
          max_tokens: 400,
          temperature: 0.3
        }
      );
      
      expect(response.success).toBe(true);
      
      const content = response.data.choices[0].message.content;
      
      // Should mention hooks or functional components
      const hasRefactoringContent = content.includes('useState') ||
                                   content.includes('hooks') ||
                                   content.includes('functional') ||
                                   content.includes('const');
      
      expect(hasRefactoringContent).toBe(true);
      
      console.log('✅ Refactoring request handled appropriately');
    }, 45000);

    test('should maintain performance for Cline rapid requests', async () => {
      console.log('⚡ Testing performance for rapid Cline requests...');
      
      const startTime = Date.now();
      const promises = [];
      
      // Simulate rapid requests like Cline might make
      for (let i = 0; i < 5; i++) {
        promises.push(
          apiClient.chatCompletion([
            { role: 'user', content: `Test request ${i + 1}` }
          ], { max_tokens: 20 })
        );
      }
      
      const results = await Promise.allSettled(promises);
      const endTime = Date.now();
      
      const successful = results.filter(r => 
        r.status === 'fulfilled' && r.value.success
      ).length;
      
      const totalTime = endTime - startTime;
      const averageTime = totalTime / 5;
      
      expect(successful).toBeGreaterThanOrEqual(4); // Allow 1 failure
      expect(averageTime).toBeLessThan(15000); // Under 15 seconds average
      
      console.log(`✅ Performance test: ${successful}/5 successful, ${averageTime.toFixed(0)}ms average`);
    }, 90000);
  });

  describe('VS Code Extension Requirements', () => {
    test('should provide exact OpenAI API format for Cline', async () => {
      console.log('🔌 Testing exact OpenAI API compatibility...');
      
      // Test exact format Cline expects
      const response = await apiClient.client.post('/v1/chat/completions', {
        model: 'gpt-4',
        messages: [{ role: 'user', content: 'Hello' }],
        max_tokens: 50,
        temperature: 0.7
      });
      
      expect(response.status).toBe(200);
      expect(response.data).toHaveProperty('id');
      expect(response.data).toHaveProperty('object', 'chat.completion');
      expect(response.data).toHaveProperty('created');
      expect(response.data).toHaveProperty('model');
      expect(response.data).toHaveProperty('choices');
      expect(response.data).toHaveProperty('usage');
      
      // Check choice format
      const choice = response.data.choices[0];
      expect(choice).toHaveProperty('index', 0);
      expect(choice).toHaveProperty('message');
      expect(choice.message).toHaveProperty('role', 'assistant');
      expect(choice.message).toHaveProperty('content');
      expect(choice).toHaveProperty('finish_reason');
      
      console.log('✅ Exact OpenAI format maintained for Cline compatibility');
    });

    test('should handle Cline authentication', async () => {
      console.log('🔐 Testing Cline authentication format...');
      
      // Test with Bearer token format Cline uses
      const customClient = new ApiClient();
      customClient.client.defaults.headers['Authorization'] = 'Bearer sk-dev-gerdsen-ai-local-development-key';
      
      const response = await customClient.getModels();
      
      expect(response.success).toBe(true);
      expect(response.status).toBe(200);
      
      console.log('✅ Cline Bearer token authentication working');
    });

    test('should work with Cline base URL format', async () => {
      console.log('🌐 Testing Cline base URL compatibility...');
      
      // Test accessing endpoints the way Cline does
      const endpoints = [
        '/v1/models',
        '/v1/chat/completions'
      ];
      
      for (const endpoint of endpoints) {
        const response = await apiClient.client.get(endpoint).catch(err => err.response);
        
        if (endpoint === '/v1/models') {
          expect(response.status).toBe(200);
        } else {
          // chat/completions should require POST, so expect method not allowed or similar
          expect(response.status).toBeGreaterThanOrEqual(400);
        }
      }
      
      console.log('✅ Cline endpoint access patterns working');
    });
  });

  describe('Error Handling for Cline', () => {
    test('should provide helpful errors for Cline debugging', async () => {
      console.log('🚨 Testing error handling for Cline...');
      
      // Test various error scenarios Cline might encounter
      const errorTests = [
        {
          name: 'Missing messages',
          request: { model: 'gpt-4' },
          expectedStatus: 400
        },
        {
          name: 'Invalid JSON',
          request: 'invalid json',
          expectedStatus: 400
        }
      ];
      
      for (const test of errorTests) {
        try {
          const response = await apiClient.client.post('/v1/chat/completions', test.request);
          
          // If it doesn't throw, check the response
          if (response.status >= 400) {
            expect(response.status).toBeGreaterThanOrEqual(test.expectedStatus);
          }
        } catch (error) {
          expect(error.response?.status || 500).toBeGreaterThanOrEqual(test.expectedStatus);
        }
      }
      
      console.log('✅ Error handling appropriate for Cline debugging');
    });
  });
});
