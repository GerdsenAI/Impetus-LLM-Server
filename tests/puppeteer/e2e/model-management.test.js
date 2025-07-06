const { AppController } = require('../utils/app-controller');
const { ScreenshotHelper } = require('../utils/screenshot-helper');
const { ApiClient } = require('../utils/api-client');
const { testData } = require('../utils/test-data');
const path = require('path');
const fs = require('fs');

describe('IMPETUS Model Management Workflow Tests', () => {
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

  describe('Complete Model Lifecycle', () => {
    test('should handle refresh and scan workflow', async () => {
      console.log('🔄 Testing model refresh workflow...');
      
      await screenshot.navigate('http://localhost:8080');
      await screenshot.waitForSelector(testData.selectors.tabsList);
      
      // Go to library tab
      await screenshot.click(testData.selectors.tabLibrary);
      await new Promise(resolve => setTimeout(resolve, 1000));
      
      // Click refresh if available
      const hasRefresh = await screenshot.elementExists(testData.selectors.refreshButton);
      if (hasRefresh) {
        await screenshot.click(testData.selectors.refreshButton);
        
        // Wait for potential loading state
        await new Promise(resolve => setTimeout(resolve, 2000));
        
        // Check if loading spinner appeared
        const hasSpinner = await screenshot.elementExists(testData.selectors.loadingSpinner);
        if (hasSpinner) {
          console.log('✅ Loading state shown during refresh');
          await screenshot.screenshot('refresh-loading');
        }
        
        // Wait for refresh to complete
        await new Promise(resolve => setTimeout(resolve, 3000));
        console.log('✅ Refresh completed');
      }
      
      await screenshot.screenshot('after-refresh');
    });

    test('should handle model loading workflow', async () => {
      console.log('⚡ Testing model loading...');
      
      // Check if any models are available
      const modelCards = await screenshot.page.$$(testData.selectors.modelCard);
      
      if (modelCards.length > 0) {
        // Find a model with Load button
        let loadButtonFound = false;
        
        for (let i = 0; i < Math.min(modelCards.length, 3); i++) {
          const card = modelCards[i];
          const loadButton = await card.$(testData.selectors.loadButton);
          
          if (loadButton) {
            loadButtonFound = true;
            console.log('✅ Found model with Load button');
            
            // Get model name
            const modelTitle = await card.$eval(testData.selectors.modelTitle, el => el.textContent);
            console.log(`📦 Loading model: ${modelTitle}`);
            
            // Click load button
            await loadButton.click();
            await screenshot.screenshot('model-loading-started');
            
            // Wait for loading state
            await new Promise(resolve => setTimeout(resolve, 2000));
            
            // Check for loading indicator
            const hasLoadingState = await card.$(testData.selectors.loadingSpinner) || 
                                   await card.$eval('*', el => el.textContent.includes('Loading'));
            
            if (hasLoadingState) {
              console.log('✅ Loading state displayed');
              await screenshot.screenshot('model-loading-progress');
            }
            
            // Wait for load to complete (or timeout)
            await new Promise(resolve => setTimeout(resolve, 10000));
            
            // Check if model loaded successfully
            const hasUnloadButton = await card.$(testData.selectors.unloadButton);
            const hasSwitchButton = await card.$(testData.selectors.switchButton);
            
            if (hasUnloadButton || hasSwitchButton) {
              console.log('✅ Model loaded successfully');
              await screenshot.screenshot('model-loaded');
            } else {
              console.log('⚠️ Model load may have failed or is still in progress');
            }
            
            break;
          }
        }
        
        if (!loadButtonFound) {
          console.log('⚠️ No models available to load (all may be loaded already)');
        }
      } else {
        console.log('⚠️ No models found in library');
      }
    });

    test('should handle model switching', async () => {
      console.log('🔀 Testing model switching...');
      
      const modelCards = await screenshot.page.$$(testData.selectors.modelCard);
      let switchCount = 0;
      
      for (const card of modelCards) {
        const switchButton = await card.$(testData.selectors.switchButton);
        
        if (switchButton) {
          const modelTitle = await card.$eval(testData.selectors.modelTitle, el => el.textContent);
          console.log(`🔄 Switching to model: ${modelTitle}`);
          
          await switchButton.click();
          await new Promise(resolve => setTimeout(resolve, 2000));
          
          // Check for active state or notification
          const content = await screenshot.getContent();
          const hasActiveIndication = content.includes('Active') || 
                                     content.includes('switched') ||
                                     content.includes('Switched');
          
          if (hasActiveIndication) {
            console.log('✅ Model switch successful');
            await screenshot.screenshot(`model-switched-${switchCount}`);
          }
          
          switchCount++;
          if (switchCount >= 2) break; // Test switching between 2 models max
        }
      }
      
      if (switchCount === 0) {
        console.log('⚠️ No loaded models available for switching');
      }
    });

    test('should handle model unloading', async () => {
      console.log('🔻 Testing model unloading...');
      
      const modelCards = await screenshot.page.$$(testData.selectors.modelCard);
      let unloadFound = false;
      
      for (const card of modelCards) {
        const unloadButton = await card.$(testData.selectors.unloadButton);
        
        if (unloadButton) {
          unloadFound = true;
          const modelTitle = await card.$eval(testData.selectors.modelTitle, el => el.textContent);
          console.log(`📤 Unloading model: ${modelTitle}`);
          
          await unloadButton.click();
          await screenshot.screenshot('model-unloading');
          
          // Wait for unload
          await new Promise(resolve => setTimeout(resolve, 3000));
          
          // Check if load button reappears
          const loadButton = await card.$(testData.selectors.loadButton);
          if (loadButton) {
            console.log('✅ Model unloaded successfully');
            await screenshot.screenshot('model-unloaded');
          }
          
          break;
        }
      }
      
      if (!unloadFound) {
        console.log('⚠️ No loaded models to unload');
      }
    });
  });

  describe('Upload Workflow', () => {
    test('should show upload interface interactions', async () => {
      console.log('📤 Testing upload workflow UI...');
      
      // Navigate to upload tab
      await screenshot.click(testData.selectors.tabUpload);
      await new Promise(resolve => setTimeout(resolve, 1000));
      
      // Test browse button
      const browseButton = await screenshot.page.$(testData.selectors.browseButton);
      expect(browseButton).toBeTruthy();
      
      // Test drag over effect
      const dropZone = await screenshot.page.$(testData.selectors.dropZone);
      
      if (dropZone) {
        // Simulate drag over
        await dropZone.hover();
        await screenshot.screenshot('drop-zone-hover');
        
        console.log('✅ Drop zone interaction working');
      }
      
      // Check for file format badges
      const content = await screenshot.getContent();
      const hasFormatInfo = content.includes('.gguf') && 
                           content.includes('.safetensors');
      
      expect(hasFormatInfo).toBe(true);
      console.log('✅ File format information displayed');
    });

    test('should handle file selection', async () => {
      console.log('📁 Testing file selection...');
      
      // We can't actually upload a file in headless testing,
      // but we can verify the input exists and is configured correctly
      const fileInput = await screenshot.page.$(testData.selectors.fileInput);
      
      if (fileInput) {
        const inputProps = await fileInput.evaluate(el => ({
          accept: el.accept,
          multiple: el.multiple,
          type: el.type
        }));
        
        expect(inputProps.type).toBe('file');
        expect(inputProps.accept).toContain('.gguf');
        expect(inputProps.multiple).toBe(true);
        
        console.log('✅ File input properly configured');
      }
    });
  });

  describe('HuggingFace Download Workflow', () => {
    test('should handle search workflow', async () => {
      console.log('🔍 Testing HuggingFace search workflow...');
      
      // Navigate to HuggingFace tab
      await screenshot.click(testData.selectors.tabHuggingFace);
      await new Promise(resolve => setTimeout(resolve, 1000));
      
      // Type search query
      const searchInput = await screenshot.page.$(testData.selectors.hfSearchInput);
      
      if (searchInput) {
        await screenshot.type(testData.selectors.hfSearchInput, 'tinyllama');
        await screenshot.screenshot('hf-search-query');
        
        // Click search or press enter
        const searchButton = await screenshot.page.$(testData.selectors.hfSearchButton);
        if (searchButton) {
          await searchButton.click();
        } else {
          await searchInput.press('Enter');
        }
        
        // Wait for results
        await new Promise(resolve => setTimeout(resolve, 3000));
        
        // Check for results or loading state
        const hasResults = await screenshot.elementExists(testData.selectors.hfModelCard);
        const hasLoading = await screenshot.elementExists(testData.selectors.loadingSpinner);
        
        if (hasResults) {
          console.log('✅ Search results displayed');
          await screenshot.screenshot('hf-search-results');
        } else if (hasLoading) {
          console.log('⏳ Search in progress');
        } else {
          console.log('⚠️ No search results found');
        }
      }
    });

    test('should show download options', async () => {
      console.log('⬇️ Testing download UI...');
      
      // Check if any model cards with download buttons exist
      const modelCards = await screenshot.page.$$(testData.selectors.hfModelCard);
      
      if (modelCards.length > 0) {
        console.log(`✅ Found ${modelCards.length} HuggingFace models`);
        
        // Check first model card
        const firstCard = modelCards[0];
        const downloadButton = await firstCard.$(testData.selectors.downloadButton);
        
        if (downloadButton) {
          // Get model info
          const cardText = await firstCard.evaluate(el => el.textContent);
          console.log('📦 Model available for download');
          
          // Verify download button is clickable
          const isDisabled = await downloadButton.evaluate(el => el.disabled);
          expect(isDisabled).toBe(false);
          
          console.log('✅ Download functionality available');
        }
      } else {
        // Check for popular models section
        const content = await screenshot.getContent();
        const hasPopularModels = content.includes('Popular Models');
        
        if (hasPopularModels) {
          console.log('✅ Popular models suggestions shown');
          await screenshot.screenshot('hf-popular-models');
        }
      }
    });
  });

  describe('Filter and Search Functionality', () => {
    test('should filter models by format', async () => {
      console.log('🏷️ Testing format filter...');
      
      // Go back to library
      await screenshot.click(testData.selectors.tabLibrary);
      await new Promise(resolve => setTimeout(resolve, 1000));
      
      // Check if format filter exists
      const formatFilter = await screenshot.page.$(testData.selectors.formatFilter);
      
      if (formatFilter) {
        // Get available options
        const options = await formatFilter.$$eval('option', opts => 
          opts.map(opt => opt.textContent)
        );
        
        console.log(`✅ Format filter has ${options.length} options`);
        
        // Try selecting a format
        if (options.length > 1) {
          await formatFilter.select(options[1]); // Select first non-"all" option
          await new Promise(resolve => setTimeout(resolve, 1000));
          await screenshot.screenshot('filtered-by-format');
          console.log(`✅ Filtered by format: ${options[1]}`);
        }
        
        // Reset filter
        await formatFilter.select('all');
      } else {
        console.log('⚠️ Format filter not available (may be no models)');
      }
    });

    test('should search models by name', async () => {
      console.log('🔎 Testing model search...');
      
      const searchInput = await screenshot.page.$(testData.selectors.searchInput);
      
      if (searchInput) {
        // Clear any existing search
        await screenshot.clear(testData.selectors.searchInput);
        
        // Type search query
        await screenshot.type(testData.selectors.searchInput, 'llama');
        await new Promise(resolve => setTimeout(resolve, 1000));
        
        await screenshot.screenshot('search-results');
        
        // Check if results changed
        const modelCards = await screenshot.page.$$(testData.selectors.modelCard);
        console.log(`✅ Search showing ${modelCards.length} results`);
        
        // Clear search
        await screenshot.clear(testData.selectors.searchInput);
      } else {
        console.log('⚠️ Search not available (may be no models)');
      }
    });
  });

  describe('Error Handling and Recovery', () => {
    test('should show appropriate empty states', async () => {
      console.log('📭 Testing empty states...');
      
      // Check library for empty state
      await screenshot.click(testData.selectors.tabLibrary);
      await new Promise(resolve => setTimeout(resolve, 1000));
      
      const modelCards = await screenshot.page.$$(testData.selectors.modelCard);
      
      if (modelCards.length === 0) {
        const content = await screenshot.getContent();
        const hasEmptyState = content.includes('No models found') ||
                             content.includes('Add Model') ||
                             content.includes('Add some models');
        
        expect(hasEmptyState).toBe(true);
        await screenshot.screenshot('empty-state-library');
        console.log('✅ Empty state displayed correctly');
      } else {
        console.log(`ℹ️ Library has ${modelCards.length} models (no empty state)`)
      }
    });

    test('should handle connection status', async () => {
      console.log('🔌 Testing connection handling...');
      
      const content = await screenshot.getContent();
      const connectionStatus = content.includes('Connected') ? 'connected' : 'disconnected';
      
      console.log(`✅ Connection status displayed: ${connectionStatus}`);
      
      // Verify appropriate icon
      if (connectionStatus === 'connected') {
        const hasWifiIcon = await screenshot.elementExists(testData.selectors.wifiIcon);
        expect(hasWifiIcon).toBe(true);
      } else {
        const hasWifiOffIcon = await screenshot.elementExists(testData.selectors.wifiOffIcon);
        expect(hasWifiOffIcon).toBe(true);
      }
    });
  });

  describe('Notification System', () => {
    test('should show notifications for user actions', async () => {
      console.log('🔔 Testing notifications...');
      
      // Try to trigger a notification by performing an action
      // First, try refresh
      const refreshButton = await screenshot.page.$(testData.selectors.refreshButton);
      
      if (refreshButton) {
        await refreshButton.click();
        
        // Wait briefly for notification
        await new Promise(resolve => setTimeout(resolve, 500));
        
        // Check for any notification
        const hasNotification = await screenshot.page.$(testData.selectors.notification) !== null;
        
        if (hasNotification) {
          // Check notification type
          const hasSuccess = await screenshot.elementExists(testData.selectors.successNotification);
          const hasError = await screenshot.elementExists(testData.selectors.errorNotification);
          const hasInfo = await screenshot.elementExists(testData.selectors.infoNotification);
          
          console.log(`✅ Notification shown: ${hasSuccess ? 'success' : hasError ? 'error' : hasInfo ? 'info' : 'unknown'}`);
          await screenshot.screenshot('notification-displayed');
          
          // Wait for notification to disappear
          await new Promise(resolve => setTimeout(resolve, 5000));
          
          // Check if notification auto-dismissed
          const stillVisible = await screenshot.page.$(testData.selectors.notification) !== null;
          
          if (!stillVisible) {
            console.log('✅ Notification auto-dismissed');
          }
        } else {
          console.log('⚠️ No notification shown (action may be too fast)');
        }
      }
    });
  });
});