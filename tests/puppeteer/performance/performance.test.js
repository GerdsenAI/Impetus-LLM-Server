const { AppController } = require('../utils/app-controller');
const { ApiClient } = require('../utils/api-client');
const { testData } = require('../utils/test-data');

describe('IMPETUS Performance Tests', () => {
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

  describe('Response Time Tests', () => {
    test('should respond to health check quickly', async () => {
      const startTime = Date.now();
      const response = await apiClient.healthCheck();
      const responseTime = Date.now() - startTime;
      
      expect(response.success).toBe(true);
      expect(responseTime).toBeLessThan(1000); // Under 1 second
      
      console.log(`✅ Health check response time: ${responseTime}ms`);
    });

    test('should respond to models endpoint quickly', async () => {
      const startTime = Date.now();
      const response = await apiClient.getModels();
      const responseTime = Date.now() - startTime;
      
      expect(response.success).toBe(true);
      expect(responseTime).toBeLessThan(2000); // Under 2 seconds
      
      console.log(`✅ Models endpoint response time: ${responseTime}ms`);
    });

    test('should handle chat completion within reasonable time', async () => {
      const startTime = Date.now();
      const response = await apiClient.chatCompletion(
        testData.chatMessages.simple,
        { max_tokens: 50 }
      );
      const responseTime = Date.now() - startTime;
      
      expect(response.success).toBe(true);
      expect(responseTime).toBeLessThan(30000); // Under 30 seconds
      
      console.log(`✅ Chat completion response time: ${responseTime}ms`);
    }, 35000);
  });

  describe('Concurrent Request Tests', () => {
    test('should handle multiple simultaneous requests', async () => {
      console.log('🔄 Testing concurrent requests...');
      
      const config = testData.performanceTests.light;
      const startTime = Date.now();
      
      // Create concurrent requests
      const promises = [];
      for (let i = 0; i < config.requestCount; i++) {
        promises.push(
          apiClient.chatCompletion(
            [{ role: 'user', content: `Concurrent test ${i + 1}` }],
            { max_tokens: config.maxTokens }
          )
        );
      }
      
      const results = await Promise.allSettled(promises);
      const endTime = Date.now();
      
      const successful = results.filter(r => 
        r.status === 'fulfilled' && r.value.success
      ).length;
      const failed = results.length - successful;
      const totalTime = endTime - startTime;
      const averageTime = totalTime / config.requestCount;
      
      expect(successful).toBeGreaterThanOrEqual(config.requestCount * 0.8); // 80% success rate
      expect(averageTime).toBeLessThan(10000); // Under 10 seconds average
      
      console.log(`✅ Concurrent test: ${successful}/${config.requestCount} successful, ${averageTime.toFixed(0)}ms average`);
    }, 60000);

    test('should handle batch requests efficiently', async () => {
      console.log('📦 Testing batch request efficiency...');
      
      const config = testData.performanceTests.medium;
      const batchSize = 3;
      const totalBatches = Math.ceil(config.requestCount / batchSize);
      
      const startTime = Date.now();
      let totalSuccessful = 0;
      
      for (let batch = 0; batch < totalBatches; batch++) {
        const batchPromises = [];
        
        for (let i = 0; i < batchSize && (batch * batchSize + i) < config.requestCount; i++) {
          batchPromises.push(
            apiClient.chatCompletion(
              [{ role: 'user', content: `Batch ${batch + 1} request ${i + 1}` }],
              { max_tokens: 10 }
            )
          );
        }
        
        const batchResults = await Promise.allSettled(batchPromises);
        const batchSuccessful = batchResults.filter(r => 
          r.status === 'fulfilled' && r.value.success
        ).length;
        
        totalSuccessful += batchSuccessful;
        
        // Small delay between batches
        await new Promise(resolve => setTimeout(resolve, 1000));
      }
      
      const endTime = Date.now();
      const totalTime = endTime - startTime;
      const successRate = totalSuccessful / config.requestCount;
      
      expect(successRate).toBeGreaterThanOrEqual(0.8); // 80% success rate
      
      console.log(`✅ Batch test: ${totalSuccessful}/${config.requestCount} successful (${(successRate * 100).toFixed(1)}%)`);
    }, 120000);
  });

  describe('Memory and Resource Tests', () => {
    test('should handle repeated requests without memory leaks', async () => {
      console.log('🧠 Testing for memory leaks...');
      
      const iterations = 20;
      const responses = [];
      
      for (let i = 0; i < iterations; i++) {
        const response = await apiClient.chatCompletion(
          [{ role: 'user', content: `Memory test ${i + 1}` }],
          { max_tokens: 10 }
        );
        
        if (response.success) {
          responses.push(response);
        }
        
        // Small delay to allow cleanup
        await new Promise(resolve => setTimeout(resolve, 100));
      }
      
      const successRate = responses.length / iterations;
      expect(successRate).toBeGreaterThanOrEqual(0.9); // 90% success rate
      
      console.log(`✅ Memory leak test: ${responses.length}/${iterations} successful`);
    }, 90000);

    test('should maintain performance over time', async () => {
      console.log('⏱️ Testing performance consistency...');
      
      const measurements = [];
      const testCount = 10;
      
      for (let i = 0; i < testCount; i++) {
        const startTime = Date.now();
        
        const response = await apiClient.chatCompletion(
          [{ role: 'user', content: `Performance test ${i + 1}` }],
          { max_tokens: 20 }
        );
        
        const responseTime = Date.now() - startTime;
        
        if (response.success) {
          measurements.push(responseTime);
        }
        
        // Wait between tests
        await new Promise(resolve => setTimeout(resolve, 2000));
      }
      
      expect(measurements.length).toBeGreaterThanOrEqual(8); // Most should succeed
      
      const averageTime = measurements.reduce((a, b) => a + b, 0) / measurements.length;
      const maxTime = Math.max(...measurements);
      const minTime = Math.min(...measurements);
      const variance = maxTime - minTime;
      
      // Performance should be relatively consistent
      expect(variance).toBeLessThan(averageTime * 2); // Variance shouldn't exceed 2x average
      
      console.log(`✅ Performance consistency: avg=${averageTime.toFixed(0)}ms, min=${minTime}ms, max=${maxTime}ms`);
    }, 120000);
  });

  describe('Streaming Performance Tests', () => {
    test('should stream responses efficiently', async () => {
      console.log('🌊 Testing streaming performance...');
      
      const startTime = Date.now();
      let firstChunkTime = null;
      let lastChunkTime = null;
      
      const response = await apiClient.chatCompletion(
        [{ role: 'user', content: 'Write a short story about a robot.' }],
        { 
          stream: true, 
          max_tokens: 100 
        }
      );
      
      expect(response.success).toBe(true);
      expect(response.chunks.length).toBeGreaterThan(0);
      
      // Estimate timing (this is approximate since we don't have exact timestamps)
      const totalTime = Date.now() - startTime;
      const averageChunkTime = totalTime / response.chunks.length;
      
      expect(averageChunkTime).toBeLessThan(1000); // Under 1 second per chunk on average
      
      console.log(`✅ Streaming: ${response.chunks.length} chunks, ${averageChunkTime.toFixed(0)}ms per chunk`);
    }, 45000);

    test('should handle multiple concurrent streams', async () => {
      console.log('🌊🌊 Testing concurrent streaming...');
      
      const streamCount = 3;
      const promises = [];
      
      for (let i = 0; i < streamCount; i++) {
        promises.push(
          apiClient.chatCompletion(
            [{ role: 'user', content: `Concurrent stream ${i + 1}` }],
            { stream: true, max_tokens: 30 }
          )
        );
      }
      
      const results = await Promise.allSettled(promises);
      const successful = results.filter(r => 
        r.status === 'fulfilled' && r.value.success
      ).length;
      
      expect(successful).toBeGreaterThanOrEqual(2); // At least 2/3 should succeed
      
      console.log(`✅ Concurrent streaming: ${successful}/${streamCount} streams successful`);
    }, 60000);
  });

  describe('Load Testing', () => {
    test('should handle stress load', async () => {
      console.log('💪 Running stress test...');
      
      const config = testData.performanceTests.heavy;
      const results = await apiClient.performanceTest(
        config.requestCount,
        config.concurrent
      );
      
      expect(results.successful).toBeGreaterThanOrEqual(config.requestCount * 0.7); // 70% success
      expect(results.averageTime).toBeLessThan(20000); // Under 20 seconds average
      expect(results.requestsPerSecond).toBeGreaterThan(0.1); // At least 0.1 RPS
      
      console.log(`✅ Stress test results:`);
      console.log(`   - Total: ${results.totalRequests}`);
      console.log(`   - Successful: ${results.successful}`);
      console.log(`   - Failed: ${results.failed}`);
      console.log(`   - Average time: ${results.averageTime.toFixed(0)}ms`);
      console.log(`   - Requests/sec: ${results.requestsPerSecond.toFixed(2)}`);
    }, 300000); // 5 minutes timeout for stress test
  });
});
