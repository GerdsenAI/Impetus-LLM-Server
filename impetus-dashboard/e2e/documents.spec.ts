import { test, expect } from '@playwright/test'

test.describe('Document Upload', () => {
  test.beforeEach(async ({ page }) => {
    await page.goto('/')
  })

  test('document upload section is visible', async ({ page }) => {
    const docContainer = page.locator('.doc-upload-container')
    await expect(docContainer).toBeVisible()
    await expect(docContainer.locator('h3')).toContainText('Document Upload')
  })

  test('text area accepts input', async ({ page }) => {
    const textarea = page.locator('.doc-upload-textarea')
    await expect(textarea).toBeVisible()
    await textarea.fill('Test document content for ingestion')
    await expect(textarea).toHaveValue('Test document content for ingestion')
  })

  test('ingest button is present and disabled when textarea is empty', async ({ page }) => {
    const ingestBtn = page.locator('.doc-upload-btn')
    await expect(ingestBtn).toBeVisible()
    await expect(ingestBtn).toContainText('Ingest')
    await expect(ingestBtn).toBeDisabled()
  })

  test('ingest button enables when text is entered', async ({ page }) => {
    const textarea = page.locator('.doc-upload-textarea')
    await textarea.fill('Some content')
    const ingestBtn = page.locator('.doc-upload-btn')
    await expect(ingestBtn).toBeEnabled()
  })

  test('collections section shows empty state', async ({ page }) => {
    const collectionsHeading = page.locator('.doc-collections h4')
    await expect(collectionsHeading).toContainText('Collections')
  })
})
