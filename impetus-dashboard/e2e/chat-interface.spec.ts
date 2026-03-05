import { test, expect } from '@playwright/test'

test.describe('Chat Interface', () => {
  test.beforeEach(async ({ page }) => {
    await page.goto('/')
  })

  test('chat section is visible with heading', async ({ page }) => {
    const chatContainer = page.locator('.chat-container')
    await expect(chatContainer).toBeVisible()
    await expect(chatContainer.locator('h3')).toContainText('Chat')
  })

  test('empty state message is shown when no messages', async ({ page }) => {
    const emptyState = page.locator('.chat-empty')
    await expect(emptyState).toContainText('Send a message to start chatting')
  })

  test('model selector shows "No models loaded" by default', async ({ page }) => {
    const modelSelect = page.locator('.chat-model-select')
    await expect(modelSelect).toBeVisible()
    await expect(modelSelect).toContainText('No models loaded')
  })

  test('RAG toggle button is visible and defaults to OFF', async ({ page }) => {
    const ragToggle = page.locator('.chat-rag-toggle')
    await expect(ragToggle).toBeVisible()
    await expect(ragToggle).toContainText('RAG OFF')
    await expect(ragToggle).not.toHaveClass(/active/)
  })

  test('chat input is disabled when no model is loaded', async ({ page }) => {
    const chatInput = page.locator('.chat-input')
    await expect(chatInput).toBeDisabled()
    await expect(chatInput).toHaveAttribute('placeholder', 'Load a model first to chat')
  })

  test('send button is disabled when input is empty', async ({ page }) => {
    const sendBtn = page.locator('.chat-send-btn')
    await expect(sendBtn).toBeDisabled()
  })

  test('RAG toggle switches to ON when clicked', async ({ page }) => {
    const ragToggle = page.locator('.chat-rag-toggle')
    await ragToggle.click()
    await expect(ragToggle).toContainText('RAG ON')
    await expect(ragToggle).toHaveClass(/active/)
  })
})
