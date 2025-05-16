console.log('Facebook Chat Cleaner content script loaded (universal, optimized)');

let isRunning = false;
let deletedCount = 0;
let port = null;
let totalChatsProcessed = 0; // Add global counter

// Helper: Wait for an element
const waitForElement = async (selector, timeout = 5000) => {
  const start = Date.now();
  while (Date.now() - start < timeout) {
    const el = document.querySelector(selector);
    if (el) return el;
    await new Promise(r => setTimeout(r, 100));
  }
  return null;
};

// Helper: Scroll to load more chats
const scrollToLoadMore = async () => {
  const previousCount = document.querySelectorAll('[role="row"]').length;
  window.scrollTo(0, document.body.scrollHeight);
  await new Promise(r => setTimeout(r, 500)); // Increased wait time for better reliability
  const currentCount = document.querySelectorAll('[role="row"]').length;
  return currentCount > previousCount;
};

// Helper: Get all visible chat rows (excluding marketplace)
const getVisibleChatRows = () => {
  const allRows = Array.from(document.querySelectorAll('[role="row"]'));
  // Filter out marketplace row (usually the first row)
  return allRows.filter(row => {
    const text = row.textContent.toLowerCase();
    return !text.includes('marketplace');
  });
};

// Helper: Get unique identifier for a row
const getRowId = (row) => {
  return row.getAttribute('data-id') || row.id || row.innerHTML;
};

// Find menu button in a chat row
const findMenuButton = (row) => {
  const specificClassButton = row.querySelector('[class*="x1ey2m1c"], [class*="xds687c"], [class*="x17qophe"]');
  if (specificClassButton && specificClassButton.getAttribute('role') === 'button') {
    return specificClassButton;
  }
  const buttons = row.querySelectorAll('[role="button"]');
  return Array.from(buttons).find(btn => {
    const rect = btn.getBoundingClientRect();
    const hasCorrectSize = rect.width > 20 && rect.width < 50;
    const isVisible = rect.width > 0 && rect.height > 0;
    const hasThreeDots = btn.querySelector('i[data-visualcompletion="css-img"], svg[class*="x11lihq"]');
    return isVisible && (hasCorrectSize || hasThreeDots);
  });
};

// Find delete button in dropdown
const findDeleteButton = () => {
  const menuItems = document.querySelectorAll('[role="menuitem"]');
  return Array.from(menuItems).find(item => {
    const text = item.textContent.toLowerCase();
    return text.includes('delete') || text.includes('remove');
  });
};

// Wait for the confirmation dialog and button
const waitForDeleteConfirmButton = async () => {
  const selectors = [
    'div[role="dialog"] [role="button"]:not([tabindex="-1"])',
    'div[role="dialog"] button',
    'div[role="dialog"] [aria-label*="Delete"]',
    'div[role="dialog"] [data-testid*="confirmationSheetConfirm"]',
    'div[role="dialog"] [class*="layerConfirm"]',
  ];
  for (let i = 0; i < 10; i++) {
    for (const selector of selectors) {
      const btns = Array.from(document.querySelectorAll(selector));
      const btn = btns.find(b => /delete/i.test(b.textContent));
      if (btn && btn.offsetParent !== null && !btn.disabled) {
        return btn;
      }
    }
    await new Promise(r => setTimeout(r, 200));
  }
  return null;
};

// Delete a single chat row
const deleteChatRow = async (row) => {
  try {
    // Scroll the row into view
    row.scrollIntoView({ block: 'center', behavior: 'smooth' });
    await new Promise(r => setTimeout(r, 800)); // Increased wait time for better reliability

    // Click the menu button
    const menuButton = findMenuButton(row);
    if (!menuButton) {
      console.log('Menu button not found');
      return false;
    }
    menuButton.click();
    await new Promise(r => setTimeout(r, 800));

    // Click the delete button
    const deleteButton = findDeleteButton();
    if (!deleteButton) {
      console.log('Delete button not found');
      return false;
    }
    deleteButton.click();
    await new Promise(r => setTimeout(r, 800));

    // Click the confirmation button
    const confirmButton = await waitForDeleteConfirmButton();
    if (!confirmButton) {
      console.log('Confirmation button not found');
      return false;
    }
    confirmButton.click();
    await new Promise(r => setTimeout(r, 1200));

    return true;
  } catch (error) {
    console.error('Error deleting chat:', error);
    return false;
  }
};

// Main deletion process
const startDeletion = async (startChatNumber = 1) => {
  const processedRows = new Set();
  totalChatsProcessed = 0; // Reset counter when starting new deletion
  
  while (isRunning) {
    // Get current visible rows (excluding marketplace)
    const rows = getVisibleChatRows();
    
    if (rows.length === 0) {
      console.log('No chat rows found, trying to load more...');
      const loadedMore = await scrollToLoadMore();
      if (!loadedMore) {
        console.log('No more chats to load');
        break;
      }
      continue;
    }

    // Process each visible row
    for (let i = 0; i < rows.length; i++) {
      if (!isRunning) break;

      const currentRow = rows[i];
      const rowId = getRowId(currentRow);

      // Skip if already processed
      if (processedRows.has(rowId)) {
        continue;
      }

      // Calculate the actual chat number (1-based for user display)
      const actualChatNumber = totalChatsProcessed + 1;

      // If we haven't reached the target chat number yet, skip
      if (actualChatNumber < startChatNumber) {
        console.log(`Skipping chat ${actualChatNumber} (waiting for chat ${startChatNumber})`);
        totalChatsProcessed++;
        continue;
      }

      // Attempt to delete the chat
      console.log(`Processing chat ${actualChatNumber}...`);
      const success = await deleteChatRow(currentRow);

      if (success) {
        deletedCount++;
        processedRows.add(rowId);
        if (port) {
          port.postMessage({ type: 'counter', value: deletedCount });
        }
        console.log(`Successfully deleted chat ${actualChatNumber}`);
      } else {
        console.log(`Failed to delete chat ${actualChatNumber}`);
        processedRows.add(rowId); // Mark as processed to avoid infinite loop
      }

      totalChatsProcessed++;
    }

    // If we've processed all visible rows, try to load more
    const loadedMore = await scrollToLoadMore();
    if (!loadedMore) {
      console.log('No more chats to load');
      break;
    }
  }
};

// Delete current thread (single conversation)
const deleteCurrentThread = async () => {
  try {
    let menuBtn = document.querySelector('div[aria-label="Conversation information"], div[aria-label="View conversation information"]');
    if (!menuBtn) menuBtn = document.querySelector('div[aria-label="Conversation actions"], div[aria-label="More actions"]');
    if (!menuBtn) menuBtn = document.querySelector('div[aria-label="More"]');
    if (!menuBtn) return false;
    
    menuBtn.click();
    await new Promise(r => setTimeout(r, 800));
    
    let deleteBtn = Array.from(document.querySelectorAll('span, div')).find(
      el => /delete (chat|conversation)/i.test(el.textContent)
    );
    if (!deleteBtn) return false;
    
    deleteBtn.click();
    await new Promise(r => setTimeout(r, 800));
    
    const confirmBtn = await waitForDeleteConfirmButton();
    if (!confirmBtn) {
      console.log('Could not find the final Delete confirmation button.');
      return false;
    }
    
    confirmBtn.click();
    await new Promise(r => setTimeout(r, 1200));
    return true;
  } catch (error) {
    console.error('Error deleting current thread:', error);
    return false;
  }
};

// Message handling
chrome.runtime.onConnect.addListener((messagePort) => {
  console.log('Connection established with popup');
  port = messagePort;
  
  port.onMessage.addListener((msg) => {
    console.log('Received message from popup:', msg);
    
    if (msg.action === 'start') {
      console.log('Starting deletion process...');
      isRunning = true;
      const startChatNumber = msg.startChatNumber || 1;
      
      if (document.querySelectorAll('[role="row"]').length > 0) {
        startDeletion(startChatNumber).catch(error => {
          console.error('Error in deletion process:', error);
        });
      } else {
        deleteCurrentThread().then(success => {
          if (success && port) {
            deletedCount++;
            port.postMessage({ type: 'counter', value: deletedCount });
          }
        });
      }
    } else if (msg.action === 'stop') {
      console.log('Stopping deletion process...');
      isRunning = false;
    }
  });
  
  port.onDisconnect.addListener(() => {
    console.log('Popup disconnected');
    port = null;
    isRunning = false;
  });
}); 