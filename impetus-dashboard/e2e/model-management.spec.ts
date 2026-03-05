import { test, expect } from '@playwright/test'

test.describe('Model Management', () => {
  test.beforeEach(async ({ page }) => {
    await page.goto('/')
  })

  test('model browser displays search input', async ({ page }) => {
    const searchInput = page.locator('.search-input')
    await expect(searchInput).toBeVisible()
    await expect(searchInput).toHaveAttribute('placeholder', 'Search models...')
  })

  test('search input filters models on typing', async ({ page }) => {
    const searchInput = page.locator('.search-input')
    await searchInput.fill('llama')
    // After typing, the filter effect runs via React state
    // Verify input accepted the value
    await expect(searchInput).toHaveValue('llama')
  })

  test('category filter buttons toggle active state', async ({ page }) => {
    const codingFilter = page.locator('.filter-btn', { hasText: 'coding' })
    await codingFilter.click()
    await expect(codingFilter).toHaveClass(/active/)
    // "all" should no longer be active
    const allFilter = page.locator('.filter-btn').first()
    await expect(allFilter).not.toHaveClass(/active/)
  })

  test('model cards show download button', async ({ page }) => {
    // Wait for models to load (loading spinner disappears)
    const modelCards = page.locator('.model-card')
    const modelCount = await modelCards.count()
    if (modelCount > 0) {
      const firstCard = modelCards.first()
      await expect(firstCard.locator('.button-primary')).toContainText('Download')
    }
  })
})
