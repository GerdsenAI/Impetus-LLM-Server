import { test, expect } from '@playwright/test'

test.describe('Dashboard', () => {
  test.beforeEach(async ({ page }) => {
    await page.goto('/')
  })

  test('page loads with correct title', async ({ page }) => {
    await expect(page).toHaveTitle('Impetus LLM Server - Dashboard')
  })

  test('header displays app name and subtitle', async ({ page }) => {
    const header = page.locator('.header')
    await expect(header).toBeVisible()
    await expect(header.locator('.header-title')).toContainText('Impetus LLM Server')
    await expect(header.locator('.header-subtitle')).toContainText('Premium Apple Silicon ML Platform')
  })

  test('connection status indicator is visible', async ({ page }) => {
    const headerRight = page.locator('.header-right')
    await expect(headerRight).toBeVisible()
  })

  test('hardware monitor section is visible', async ({ page }) => {
    const dashboard = page.locator('.dashboard-grid')
    await expect(dashboard).toBeVisible()
    // First card contains HardwareMonitor
    const cards = dashboard.locator('.card')
    await expect(cards.first()).toBeVisible()
  })

  test('performance metrics section is visible', async ({ page }) => {
    const cards = page.locator('.dashboard-grid .card')
    // Second card contains PerformanceMetrics
    await expect(cards.nth(1)).toBeVisible()
  })

  test('model browser section is visible', async ({ page }) => {
    await expect(page.locator('.model-browser')).toBeVisible()
    await expect(page.locator('.section-title')).toContainText('Model Browser')
  })

  test('model browser has category filter buttons', async ({ page }) => {
    const filters = page.locator('.category-filters .filter-btn')
    // Categories: all, general, coding, chat, efficient, specialized
    await expect(filters).toHaveCount(6)
    // "all" filter is active by default
    await expect(filters.first()).toHaveClass(/active/)
  })
})
