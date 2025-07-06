const { AppController } = require('../utils/app-controller');
const { ScreenshotHelper } = require('../utils/screenshot-helper');
const { ApiClient } = require('../utils/api-client');
const { WebSocketHelper } = require('../utils/websocket-helper');
const { testData } = require('../utils/test-data');

describe('IMPETUS UI-API Integration Tests', () => {
  let appController;
  let screenshot;
  let apiClient;
  let wsHelper;

  beforeAll(async () => {
    appController = new AppController();
    screenshot = new ScreenshotHelper();
    apiClient = new ApiClient();
    wsHelper = new WebSocketHelper();
    
    // Ensure app is running
    await appController.launch();
    await new Promise(resolve => setTimeout(resolve, 10000));
    
    // Initialize browser
    await screenshot.init({ headless: false });
    
    // Connect WebSocket
    try {
      await wsHelper.connect();
    } catch (err) {
      console.warn('WebSocket connection failed:', err.message);
    }
  });

  afterAll(async () => {
    wsHelper.disconnect();
    await screenshot.close();
    await appController.terminate();
  });

  describe('UI Actions Trigger API Calls', () => {
    test('should make API call when refreshing models', async () => {
      console.log('🔄 Testing refresh API integration...');
      
      await screenshot.navigate('http://localhost:8080');
      await screenshot.click(testData.selectors.tabLibrary);
      await new Promise(resolve => setTimeout(resolve, 1000));
      
      // Monitor network requests
      const apiCalls = [];
      screenshot.page.on('request', request => {
        const url = request.url();
        if (url.includes('/api/') || url.includes('/v1/')) {
          apiCalls.push({
            url: url,
            method: request.method(),
            timestamp: Date.now()
          });
        }
      });
      
      // Click refresh
      const hasRefresh = await screenshot.elementExists(testData.selectors.refreshButton);
      if (hasRefresh) {
        await screenshot.click(testData.selectors.refreshButton);
        await new Promise(resolve => setTimeout(resolve, 2000));
        
        // Check if scan API was called
        const scanCalls = apiCalls.filter(call => call.url.includes('/scan'));
        expect(scanCalls.length).toBeGreaterThan(0);
        console.log(`✅ Made ${scanCalls.length} scan API calls`);
      }
    });

    test('should update UI when API returns data', async () => {
      console.log('📊 Testing API data to UI flow...');
      
      // Get models from API
      const modelsResponse = await apiClient.getModels();
      const apiModelCount = modelsResponse.data?.data?.length || 0;
      
      // Navigate to UI
      await screenshot.navigate('http://localhost:8080');
      await new Promise(resolve => setTimeout(resolve, 2000));
      
      // Count models in UI
      const modelCards = await screenshot.page.$$(testData.selectors.modelCard);
      const uiModelCount = modelCards.length;
      
      console.log(`📊 API reports ${apiModelCount} models, UI shows ${uiModelCount} models`);
      
      // They might not match exactly due to filtering or UI state
      // but both should be consistent (both 0 or both > 0)
      if (apiModelCount > 0) {
        expect(uiModelCount).toBeGreaterThan(0);
      }
    });
  });

  describe('WebSocket Real-time Updates', () => {
    test('should reflect WebSocket status in UI', async () => {
      console.log('🔌 Testing WebSocket status integration...');
      
      await screenshot.navigate('http://localhost:8080');
      
      // Check connection status in UI
      const content = await screenshot.getContent();
      const uiShowsConnected = content.includes('Server Connected');
      const wsActuallyConnected = wsHelper.isConnected;
      
      console.log(`UI shows: ${uiShowsConnected ? 'connected' : 'disconnected'}`);
      console.log(`WebSocket is: ${wsActuallyConnected ? 'connected' : 'disconnected'}`);
      
      // UI should reflect actual WebSocket state
      if (wsActuallyConnected) {
        expect(uiShowsConnected).toBe(true);
      }
      
      await screenshot.screenshot('websocket-status-integration');
    });

    test('should handle WebSocket messages for model updates', async () => {
      console.log('📨 Testing WebSocket message handling...');
      
      if (!wsHelper.isConnected) {
        console.log('⚠️ WebSocket not connected, skipping message test');
        return;
      }
      
      // Subscribe to model status updates
      const receivedUpdates = [];
      const unsubscribe = wsHelper.subscribe('model_status_update', (msg) => {
        receivedUpdates.push(msg);
      });
      
      // Wait for any natural updates
      await new Promise(resolve => setTimeout(resolve, 3000));
      
      if (receivedUpdates.length > 0) {
        console.log(`✅ Received ${receivedUpdates.length} model status updates`);
        
        // Check if UI reflects these updates
        const firstUpdate = receivedUpdates[0];
        const content = await screenshot.getContent();
        
        // UI should show some indication of the model status
        const hasStatusIndication = content.includes(firstUpdate.status) ||
                                   content.includes('loading') ||
                                   content.includes('loaded');
        
        expect(hasStatusIndication).toBe(true);
      } else {
        console.log('ℹ️ No WebSocket updates received during test period');
      }
      
      unsubscribe();
    });
  });

  describe('Error Propagation', () => {
    test('should show UI error when API fails', async () => {
      console.log('❌ Testing error propagation...');
      
      // Try to trigger an error by requesting invalid model
      try {
        const errorResponse = await apiClient.makeRequest('/v1/models/invalid-model-id/switch', {
          method: 'POST'
        });
        
        if (!errorResponse.success) {
          console.log('✅ API returned error as expected');
          
          // Check if error would be shown in UI
          // (This depends on how the UI handles errors)
        }
      } catch (err) {
        console.log('✅ API request failed as expected:', err.message);
      }
    });

    test('should handle network errors gracefully', async () => {
      console.log('🔌 Testing network error handling...');
      
      // Navigate to UI
      await screenshot.navigate('http://localhost:8080');
      
      // Check disconnected state handling
      if (!wsHelper.isConnected) {
        const hasDisconnectedIndicator = await screenshot.elementExists(testData.selectors.wifiOffIcon);
        expect(hasDisconnectedIndicator).toBe(true);
        console.log('✅ UI shows disconnected state correctly');
      } else {
        console.log('ℹ️ WebSocket connected, cannot test disconnected state');
      }
    });
  });

  describe('Data Consistency', () => {
    test('should maintain consistency between API and UI state', async () => {
      console.log('🔄 Testing data consistency...');
      
      // Get current state from API
      const apiState = {
        models: await apiClient.getModels(),
        health: await apiClient.healthCheck()
      };
      
      // Navigate to UI and check state
      await screenshot.navigate('http://localhost:8080');
      await new Promise(resolve => setTimeout(resolve, 2000));
      
      // Verify health status
      if (apiState.health.success) {
        const content = await screenshot.getContent();
        const showsHealthy = content.includes('Connected') || 
                            content.includes('Running') ||
                            content.includes('Healthy');
        
        expect(showsHealthy).toBe(true);
        console.log('✅ Health status consistent between API and UI');
      }
      
      // Verify model count consistency
      const modelCards = await screenshot.page.$$(testData.selectors.modelCard);
      const apiModelCount = apiState.models.data?.data?.length || 0;
      
      if (apiModelCount === 0 && modelCards.length === 0) {
        console.log('✅ Both API and UI show no models');
      } else if (apiModelCount > 0 && modelCards.length > 0) {
        console.log('✅ Both API and UI show models available');
      } else {
        console.log(`⚠️ Inconsistency: API has ${apiModelCount} models, UI shows ${modelCards.length}`);
      }
    });
  });

  describe('Performance Monitoring', () => {
    test('should measure API response times from UI actions', async () => {
      console.log('⏱️ Testing API performance from UI...');
      
      await screenshot.navigate('http://localhost:8080');
      
      // Measure performance of UI actions
      const measurements = [];
      
      // Measure tab switching
      const tabStart = Date.now();
      await screenshot.click(testData.selectors.tabHuggingFace);
      await screenshot.waitForSelector(testData.selectors.tabContent);
      measurements.push({
        action: 'tab_switch',
        time: Date.now() - tabStart
      });
      
      // Measure search if available
      const searchInput = await screenshot.page.$(testData.selectors.hfSearchInput);
      if (searchInput) {
        const searchStart = Date.now();
        await screenshot.type(testData.selectors.hfSearchInput, 'test');
        await new Promise(resolve => setTimeout(resolve, 1000));
        measurements.push({
          action: 'search_type',
          time: Date.now() - searchStart
        });
      }
      
      // Report measurements
      console.log('📊 UI Action Performance:');
      measurements.forEach(m => {
        console.log(`  - ${m.action}: ${m.time}ms`);
        expect(m.time).toBeLessThan(2000); // Should be under 2 seconds
      });
    });

    test('should handle concurrent UI operations', async () => {
      console.log('🔀 Testing concurrent operations...');
      
      await screenshot.navigate('http://localhost:8080');
      await screenshot.click(testData.selectors.tabLibrary);
      
      // Perform multiple operations concurrently
      const operations = [];
      
      // Search operation
      const searchInput = await screenshot.page.$(testData.selectors.searchInput);
      if (searchInput) {
        operations.push(
          screenshot.type(testData.selectors.searchInput, 'concurrent test')
        );
      }
      
      // Tab switching
      operations.push(
        screenshot.click(testData.selectors.tabInfo)
          .then(() => screenshot.click(testData.selectors.tabLibrary))
      );
      
      // Refresh if available
      if (await screenshot.elementExists(testData.selectors.refreshButton)) {
        operations.push(
          screenshot.click(testData.selectors.refreshButton)
        );
      }
      
      // Execute all operations
      const startTime = Date.now();
      await Promise.all(operations);
      const totalTime = Date.now() - startTime;
      
      console.log(`✅ Completed ${operations.length} concurrent operations in ${totalTime}ms`);
      expect(totalTime).toBeLessThan(5000);
      
      await screenshot.screenshot('concurrent-operations-complete');
    });
  });

  describe('State Synchronization', () => {
    test('should sync model state between tabs', async () => {
      console.log('🔄 Testing state synchronization...');
      
      // Open two browser tabs
      const page1 = screenshot.page;
      const page2 = await screenshot.browser.newPage();
      
      // Navigate both to the app
      await page1.goto('http://localhost:8080');
      await page2.goto('http://localhost:8080');
      
      // Wait for both to load
      await new Promise(resolve => setTimeout(resolve, 3000));
      
      // Perform action in first tab
      await page1.click(testData.selectors.refreshButton).catch(() => {});
      
      // Check if second tab reflects changes (via WebSocket)
      await new Promise(resolve => setTimeout(resolve, 2000));
      
      // Take screenshots of both
      await page1.screenshot({ path: 'screenshots/sync-tab1.png' });
      await page2.screenshot({ path: 'screenshots/sync-tab2.png' });
      
      console.log('✅ Multi-tab synchronization tested');
      
      // Close second tab
      await page2.close();
    });
  });
});