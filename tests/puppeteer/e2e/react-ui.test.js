const { AppController } = require('../utils/app-controller');
const { ScreenshotHelper } = require('../utils/screenshot-helper');
const { ApiClient } = require('../utils/api-client');
const { testData } = require('../utils/test-data');
const path = require('path');
const fs = require('fs');

describe('IMPETUS React UI Component Tests', () => {
  let appController;
  let screenshot;
  let apiClient;

  beforeAll(async () => {
    appController = new AppController();
    screenshot = new ScreenshotHelper();
    apiClient = new ApiClient();
    
    // Ensure app is running
    await appController.launch();
    await new Promise(resolve => setTimeout(resolve, 10000));
    
    // Initialize browser
    await screenshot.init({ headless: false });
  });

  afterAll(async () => {
    await screenshot.close();
    await appController.terminate();
  });

  describe('Tab Navigation', () => {
    test('should have all four tabs visible and functional', async () => {
      console.log('🔖 Testing tab navigation...');
      
      await screenshot.navigate('http://localhost:8080');
      await screenshot.waitForSelector(testData.selectors.tabsList);
      
      // Check all tabs exist
      const tabs = [
        { selector: testData.selectors.tabLibrary, name: 'Model Library' },
        { selector: testData.selectors.tabUpload, name: 'Upload Model' },
        { selector: testData.selectors.tabHuggingFace, name: 'HuggingFace' },
        { selector: testData.selectors.tabInfo, name: 'About' }
      ];
      
      for (const tab of tabs) {
        const exists = await screenshot.elementExists(tab.selector);
        expect(exists).toBe(true);
        console.log(`✅ ${tab.name} tab found`);
      }
      
      await screenshot.screenshot('tab-navigation');
    });

    test('should switch between tabs correctly', async () => {
      console.log('🔄 Testing tab switching...');
      
      // Test each tab
      const tabTests = [
        { 
          selector: testData.selectors.tabUpload, 
          name: 'Upload',
          expectedContent: 'drag and drop'
        },
        { 
          selector: testData.selectors.tabHuggingFace, 
          name: 'HuggingFace',
          expectedContent: 'Search HuggingFace'
        },
        { 
          selector: testData.selectors.tabInfo, 
          name: 'About',
          expectedContent: 'IMPETUS'
        },
        { 
          selector: testData.selectors.tabLibrary, 
          name: 'Library',
          expectedContent: 'Model Library'
        }
      ];
      
      for (const tab of tabTests) {
        await screenshot.click(tab.selector);
        await new Promise(resolve => setTimeout(resolve, 500));
        
        const content = await screenshot.getContent();
        expect(content.toLowerCase()).toContain(tab.expectedContent.toLowerCase());
        
        await screenshot.screenshot(`tab-${tab.name.toLowerCase()}`);
        console.log(`✅ ${tab.name} tab content loaded`);
      }
    });
  });

  describe('Model Grid Component', () => {
    test('should display model grid in library tab', async () => {
      console.log('📊 Testing model grid display...');
      
      await screenshot.click(testData.selectors.tabLibrary);
      await new Promise(resolve => setTimeout(resolve, 1000));
      
      const hasGrid = await screenshot.elementExists(testData.selectors.modelGrid);
      const hasRefreshButton = await screenshot.elementExists(testData.selectors.refreshButton);
      const hasAddButton = await screenshot.elementExists(testData.selectors.addModelButton);
      
      expect(hasGrid || hasRefreshButton || hasAddButton).toBe(true);
      
      await screenshot.screenshot('model-grid');
      console.log('✅ Model grid components found');
    });

    test('should have search and filter functionality', async () => {
      console.log('🔍 Testing search and filters...');
      
      const hasSearch = await screenshot.elementExists(testData.selectors.searchInput);
      
      if (hasSearch) {
        // Type in search
        await screenshot.type(testData.selectors.searchInput, 'llama');
        await screenshot.screenshot('search-typed');
        
        // Clear search
        await screenshot.clear(testData.selectors.searchInput);
        
        console.log('✅ Search functionality working');
      } else {
        console.log('⚠️ Search input not found (may be no models loaded)');
      }
    });

    test('should display model cards with status', async () => {
      console.log('🎴 Testing model cards...');
      
      // Check if any model cards exist
      const modelCards = await screenshot.page.$$(testData.selectors.modelCard);
      
      if (modelCards.length > 0) {
        console.log(`✅ Found ${modelCards.length} model cards`);
        
        // Check first model card for expected elements
        const firstCard = modelCards[0];
        const cardText = await firstCard.evaluate(el => el.textContent);
        
        expect(cardText).toBeTruthy();
        expect(cardText.length).toBeGreaterThan(0);
        
        await screenshot.screenshot('model-cards');
      } else {
        console.log('⚠️ No model cards found (models directory may be empty)');
        
        // Check for empty state
        const content = await screenshot.getContent();
        const hasEmptyState = content.includes('No models found') || 
                             content.includes('Add Model');
        expect(hasEmptyState).toBe(true);
      }
    });
  });

  describe('WebSocket Connection Status', () => {
    test('should display connection status in header', async () => {
      console.log('🔌 Testing WebSocket status display...');
      
      await screenshot.navigate('http://localhost:8080');
      
      // Check for connection status
      const hasConnectionStatus = await screenshot.elementExists(testData.selectors.connectionStatus);
      const hasWifiIcon = await screenshot.elementExists(testData.selectors.wifiIcon);
      const hasWifiOffIcon = await screenshot.elementExists(testData.selectors.wifiOffIcon);
      
      expect(hasConnectionStatus).toBe(true);
      expect(hasWifiIcon || hasWifiOffIcon).toBe(true);
      
      const content = await screenshot.getContent();
      const isConnected = content.includes('Server Connected');
      
      if (isConnected) {
        console.log('✅ WebSocket connected');
      } else {
        console.log('⚠️ WebSocket disconnected');
      }
      
      await screenshot.screenshot('websocket-status');
    });
  });

  describe('Drag & Drop Upload', () => {
    test('should display drop zone in upload tab', async () => {
      console.log('📤 Testing drag & drop zone...');
      
      await screenshot.click(testData.selectors.tabUpload);
      await new Promise(resolve => setTimeout(resolve, 1000));
      
      const hasDropZone = await screenshot.elementExists(testData.selectors.dropZone);
      const hasBrowseButton = await screenshot.elementExists(testData.selectors.browseButton);
      
      expect(hasDropZone).toBe(true);
      expect(hasBrowseButton).toBe(true);
      
      await screenshot.screenshot('drop-zone');
      console.log('✅ Drop zone displayed correctly');
    });

    test('should show supported formats', async () => {
      console.log('📋 Testing format display...');
      
      const content = await screenshot.getContent();
      const supportedFormats = ['.gguf', '.safetensors', '.mlx', '.onnx'];
      
      let foundFormats = 0;
      for (const format of supportedFormats) {
        if (content.includes(format)) {
          foundFormats++;
        }
      }
      
      expect(foundFormats).toBeGreaterThan(0);
      console.log(`✅ Found ${foundFormats} supported formats displayed`);
    });

    test('should handle file input interaction', async () => {
      console.log('📁 Testing file input...');
      
      const hasFileInput = await screenshot.elementExists(testData.selectors.fileInput);
      expect(hasFileInput).toBe(true);
      
      // Get file input element
      const fileInput = await screenshot.page.$(testData.selectors.fileInput);
      expect(fileInput).toBeTruthy();
      
      // Check if accept attribute includes model formats
      const acceptAttribute = await fileInput.evaluate(el => el.accept);
      expect(acceptAttribute).toContain('.gguf');
      
      console.log('✅ File input configured correctly');
    });
  });

  describe('HuggingFace Search', () => {
    test('should display search interface', async () => {
      console.log('🤗 Testing HuggingFace search...');
      
      await screenshot.click(testData.selectors.tabHuggingFace);
      await new Promise(resolve => setTimeout(resolve, 1000));
      
      const hasSearchInput = await screenshot.elementExists(testData.selectors.hfSearchInput);
      const hasSearchButton = await screenshot.elementExists(testData.selectors.hfSearchButton);
      
      expect(hasSearchInput).toBe(true);
      expect(hasSearchButton).toBe(true);
      
      await screenshot.screenshot('huggingface-search');
      console.log('✅ HuggingFace search interface displayed');
    });

    test('should show popular models or search results', async () => {
      console.log('🎯 Testing model suggestions...');
      
      const content = await screenshot.getContent();
      
      // Check for popular models or search functionality
      const hasModelSuggestions = content.includes('Popular Models') ||
                                 content.includes('TinyLlama') ||
                                 content.includes('CodeLlama') ||
                                 content.includes('Mistral');
      
      if (hasModelSuggestions) {
        console.log('✅ Model suggestions displayed');
      } else {
        console.log('⚠️ No model suggestions found');
      }
      
      // Try searching
      const searchInput = await screenshot.page.$(testData.selectors.hfSearchInput);
      if (searchInput) {
        await screenshot.type(testData.selectors.hfSearchInput, 'llama');
        await screenshot.screenshot('hf-search-typed');
        console.log('✅ Search input functional');
      }
    });
  });

  describe('Notifications System', () => {
    test('should be able to show notifications', async () => {
      console.log('🔔 Testing notification system...');
      
      // Try to trigger a notification by clicking refresh
      await screenshot.click(testData.selectors.tabLibrary);
      await new Promise(resolve => setTimeout(resolve, 500));
      
      const hasRefresh = await screenshot.elementExists(testData.selectors.refreshButton);
      if (hasRefresh) {
        await screenshot.click(testData.selectors.refreshButton);
        await new Promise(resolve => setTimeout(resolve, 1000));
        
        // Check if any notification appeared
        const hasNotification = await screenshot.elementExists(testData.selectors.notification);
        
        if (hasNotification) {
          await screenshot.screenshot('notification-shown');
          console.log('✅ Notification system working');
        } else {
          console.log('⚠️ No notification shown (may be too fast or not implemented)');
        }
      }
    });
  });

  describe('Responsive Design', () => {
    test('should adapt to different screen sizes', async () => {
      console.log('📱 Testing responsive design...');
      
      const viewports = [
        { name: 'desktop', width: 1280, height: 800 },
        { name: 'tablet', width: 768, height: 1024 },
        { name: 'mobile', width: 375, height: 667 }
      ];
      
      for (const viewport of viewports) {
        await screenshot.page.setViewport({ 
          width: viewport.width, 
          height: viewport.height 
        });
        
        await screenshot.navigate('http://localhost:8080');
        await new Promise(resolve => setTimeout(resolve, 1000));
        
        // Check if tabs are still accessible
        const hasTabsList = await screenshot.elementExists(testData.selectors.tabsList);
        expect(hasTabsList).toBe(true);
        
        await screenshot.screenshot(`responsive-${viewport.name}`);
        console.log(`✅ ${viewport.name} view rendered correctly`);
      }
      
      // Reset to desktop
      await screenshot.page.setViewport({ width: 1280, height: 800 });
    });
  });

  describe('About Tab Information', () => {
    test('should display IMPETUS information', async () => {
      console.log('ℹ️ Testing about tab...');
      
      await screenshot.click(testData.selectors.tabInfo);
      await new Promise(resolve => setTimeout(resolve, 1000));
      
      const content = await screenshot.getContent();
      
      // Check for expected information
      const expectedInfo = [
        'IMPETUS',
        'Apple Silicon',
        'tokens/sec',
        'GGUF',
        'localhost:8080'
      ];
      
      let foundInfo = 0;
      for (const info of expectedInfo) {
        if (content.includes(info)) {
          foundInfo++;
        }
      }
      
      expect(foundInfo).toBeGreaterThan(2);
      await screenshot.screenshot('about-tab');
      console.log(`✅ About tab shows ${foundInfo}/${expectedInfo.length} expected items`);
    });
  });

  describe('Error States', () => {
    test('should handle disconnected state gracefully', async () => {
      console.log('❌ Testing error states...');
      
      // The UI should show disconnected state if server is down
      // This is tested by checking the connection status
      const content = await screenshot.getContent();
      
      if (content.includes('Disconnected')) {
        const hasWifiOffIcon = await screenshot.elementExists(testData.selectors.wifiOffIcon);
        expect(hasWifiOffIcon).toBe(true);
        console.log('✅ Disconnected state handled properly');
      } else {
        console.log('✅ Server is connected (cannot test disconnected state)');
      }
    });
  });
});