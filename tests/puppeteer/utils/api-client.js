const axios = require('axios');

class ApiClient {
  constructor(baseUrl = 'http://localhost:8080') {
    this.baseUrl = baseUrl;
    this.apiKey = 'sk-dev-gerdsen-ai-local-development-key';
    
    // Configure axios instance
    this.client = axios.create({
      baseURL: baseUrl,
      timeout: 30000,
      headers: {
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${this.apiKey}`
      }
    });
  }

  /**
   * Test basic server health
   */
  async healthCheck() {
    try {
      const response = await this.client.get('/api/health');
      return {
        success: true,
        data: response.data,
        status: response.status
      };
    } catch (error) {
      return {
        success: false,
        error: error.message,
        status: error.response?.status || 0
      };
    }
  }

  /**
   * Get list of available models (OpenAI compatible)
   */
  async getModels() {
    try {
      const response = await this.client.get('/v1/models');
      return {
        success: true,
        data: response.data,
        status: response.status
      };
    } catch (error) {
      return {
        success: false,
        error: error.message,
        status: error.response?.status || 0
      };
    }
  }

  /**
   * Send chat completion request (OpenAI compatible)
   */
  async chatCompletion(messages, options = {}) {
    const payload = {
      model: options.model || 'gpt-4',
      messages: messages,
      stream: options.stream || false,
      max_tokens: options.max_tokens || 150,
      temperature: options.temperature || 0.7,
      ...options
    };

    try {
      if (options.stream) {
        return this.streamingChatCompletion(payload);
      } else {
        const response = await this.client.post('/v1/chat/completions', payload);
        return {
          success: true,
          data: response.data,
          status: response.status
        };
      }
    } catch (error) {
      return {
        success: false,
        error: error.message,
        status: error.response?.status || 0,
        data: error.response?.data || null
      };
    }
  }

  /**
   * Handle streaming chat completion
   */
  async streamingChatCompletion(payload) {
    return new Promise((resolve, reject) => {
      const chunks = [];
      let hasError = false;

      const config = {
        method: 'POST',
        url: `${this.baseUrl}/v1/chat/completions`,
        data: payload,
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${this.apiKey}`,
          'Accept': 'text/event-stream'
        },
        responseType: 'stream',
        timeout: 30000
      };

      axios(config)
        .then(response => {
          response.data.on('data', (chunk) => {
            const lines = chunk.toString().split('\n');
            for (const line of lines) {
              if (line.trim() && line.startsWith('data: ')) {
                chunks.push(line);
              }
            }
          });

          response.data.on('end', () => {
            if (!hasError) {
              resolve({
                success: true,
                chunks: chunks,
                status: response.status
              });
            }
          });

          response.data.on('error', (error) => {
            hasError = true;
            reject({
              success: false,
              error: error.message,
              status: 0
            });
          });
        })
        .catch(error => {
          hasError = true;
          reject({
            success: false,
            error: error.message,
            status: error.response?.status || 0
          });
        });
    });
  }

  /**
   * Test completions endpoint (legacy OpenAI)
   */
  async completion(prompt, options = {}) {
    const payload = {
      model: options.model || 'gpt-4',
      prompt: prompt,
      max_tokens: options.max_tokens || 150,
      temperature: options.temperature || 0.7,
      ...options
    };

    try {
      const response = await this.client.post('/v1/completions', payload);
      return {
        success: true,
        data: response.data,
        status: response.status
      };
    } catch (error) {
      return {
        success: false,
        error: error.message,
        status: error.response?.status || 0
      };
    }
  }

  /**
   * Get hardware information
   */
  async getHardwareInfo() {
    try {
      const response = await this.client.get('/api/hardware/detect');
      return {
        success: true,
        data: response.data,
        status: response.status
      };
    } catch (error) {
      return {
        success: false,
        error: error.message,
        status: error.response?.status || 0
      };
    }
  }

  /**
   * Get loaded models from server
   */
  async getLoadedModels() {
    try {
      const response = await this.client.get('/api/models');
      return {
        success: true,
        data: response.data,
        status: response.status
      };
    } catch (error) {
      return {
        success: false,
        error: error.message,
        status: error.response?.status || 0
      };
    }
  }

  /**
   * Test server performance with multiple concurrent requests
   */
  async performanceTest(requestCount = 10, concurrent = 5) {
    const testMessage = [{ role: 'user', content: 'Hello, this is a test message.' }];
    const startTime = Date.now();
    const results = [];

    // Create batches of concurrent requests
    const batches = [];
    for (let i = 0; i < requestCount; i += concurrent) {
      const batch = [];
      for (let j = 0; j < concurrent && (i + j) < requestCount; j++) {
        batch.push(this.chatCompletion(testMessage, { max_tokens: 10 }));
      }
      batches.push(batch);
    }

    // Execute batches sequentially
    for (const batch of batches) {
      const batchResults = await Promise.allSettled(batch);
      results.push(...batchResults);
    }

    const endTime = Date.now();
    const totalTime = endTime - startTime;

    // Analyze results
    const successful = results.filter(r => r.status === 'fulfilled' && r.value.success).length;
    const failed = results.length - successful;

    return {
      totalRequests: requestCount,
      successful: successful,
      failed: failed,
      totalTime: totalTime,
      averageTime: totalTime / requestCount,
      requestsPerSecond: (requestCount / totalTime) * 1000
    };
  }

  /**
   * Validate OpenAI API compatibility
   */
  async validateOpenAICompatibility() {
    const results = {
      models: false,
      chatCompletions: false,
      streaming: false,
      errorHandling: false
    };

    try {
      // Test models endpoint
      const modelsResponse = await this.getModels();
      results.models = modelsResponse.success && 
                      modelsResponse.data.object === 'list' &&
                      Array.isArray(modelsResponse.data.data);

      // Test chat completions
      const chatResponse = await this.chatCompletion([
        { role: 'user', content: 'Test message' }
      ], { max_tokens: 5 });
      results.chatCompletions = chatResponse.success &&
                               chatResponse.data.choices &&
                               Array.isArray(chatResponse.data.choices);

      // Test streaming
      const streamResponse = await this.chatCompletion([
        { role: 'user', content: 'Stream test' }
      ], { stream: true, max_tokens: 5 });
      results.streaming = streamResponse.success &&
                         Array.isArray(streamResponse.chunks) &&
                         streamResponse.chunks.length > 0;

      // Test error handling with invalid request
      const errorResponse = await this.chatCompletion([
        { role: 'invalid', content: 'Test' }
      ]);
      results.errorHandling = !errorResponse.success && errorResponse.status >= 400;

    } catch (error) {
      console.error('OpenAI compatibility test error:', error);
    }

    return results;
  }
}

module.exports = { ApiClient };
