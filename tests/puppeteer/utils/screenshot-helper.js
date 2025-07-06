const puppeteer = require('puppeteer');
const fs = require('fs').promises;
const path = require('path');

class ScreenshotHelper {
  constructor() {
    this.screenshotDir = path.join(__dirname, '..', 'screenshots');
    this.browser = null;
    this.page = null;
  }

  /**
   * Initialize browser and page
   */
  async init(options = {}) {
    this.browser = await puppeteer.launch({
      headless: options.headless !== false,
      args: ['--no-sandbox', '--disable-setuid-sandbox'],
      defaultViewport: { width: 1280, height: 800 }
    });
    
    this.page = await this.browser.newPage();
    
    // Setup console logging
    this.page.on('console', msg => {
      console.log(`🌐 Browser Console [${msg.type()}]:`, msg.text());
    });
    
    // Setup error handling
    this.page.on('pageerror', error => {
      console.error('🚨 Page Error:', error.message);
    });

    // Ensure screenshot directory exists
    await this.ensureScreenshotDir();
  }

  /**
   * Ensure screenshot directory exists
   */
  async ensureScreenshotDir() {
    try {
      await fs.access(this.screenshotDir);
    } catch (error) {
      await fs.mkdir(this.screenshotDir, { recursive: true });
    }
  }

  /**
   * Navigate to URL
   */
  async navigate(url) {
    if (!this.page) {
      throw new Error('Page not initialized. Call init() first.');
    }
    
    console.log(`🔗 Navigating to: ${url}`);
    await this.page.goto(url, { 
      waitUntil: 'networkidle2',
      timeout: 30000 
    });
  }

  /**
   * Take screenshot
   */
  async screenshot(filename, options = {}) {
    if (!this.page) {
      throw new Error('Page not initialized. Call init() first.');
    }

    const timestamp = new Date().toISOString().replace(/[:.]/g, '-');
    const fullFilename = `${timestamp}-${filename}.png`;
    const filepath = path.join(this.screenshotDir, fullFilename);
    
    await this.page.screenshot({
      path: filepath,
      fullPage: options.fullPage || false,
      ...options
    });
    
    console.log(`📸 Screenshot saved: ${fullFilename}`);
    return filepath;
  }

  /**
   * Wait for element
   */
  async waitForElement(selector, timeout = 10000) {
    if (!this.page) {
      throw new Error('Page not initialized. Call init() first.');
    }
    
    return await this.page.waitForSelector(selector, { timeout });
  }

  /**
   * Check if element exists
   */
  async elementExists(selector) {
    if (!this.page) {
      return false;
    }
    
    const element = await this.page.$(selector);
    return element !== null;
  }

  /**
   * Get page content
   */
  async getContent() {
    if (!this.page) {
      throw new Error('Page not initialized. Call init() first.');
    }
    
    return await this.page.content();
  }

  /**
   * Get page title
   */
  async getTitle() {
    if (!this.page) {
      throw new Error('Page not initialized. Call init() first.');
    }
    
    return await this.page.title();
  }

  /**
   * Click element
   */
  async click(selector) {
    if (!this.page) {
      throw new Error('Page not initialized. Call init() first.');
    }
    
    await this.waitForElement(selector);
    await this.page.click(selector);
  }

  /**
   * Type in element
   */
  async type(selector, text) {
    if (!this.page) {
      throw new Error('Page not initialized. Call init() first.');
    }
    
    await this.waitForElement(selector);
    await this.page.type(selector, text);
  }

  /**
   * Evaluate JavaScript on page
   */
  async evaluate(fn, ...args) {
    if (!this.page) {
      throw new Error('Page not initialized. Call init() first.');
    }
    
    return await this.page.evaluate(fn, ...args);
  }

  /**
   * Close browser
   */
  async close() {
    if (this.browser) {
      await this.browser.close();
      this.browser = null;
      this.page = null;
    }
  }
}

module.exports = { ScreenshotHelper };
