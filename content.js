console.log('Facebook Chat Cleaner content script loaded (universal, optimized)');

let isRunning = false;
let deletedCount = 0;
let port = null;

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

// Delete a single chat row (inbox)
const deleteChatRow = async (row) => {
  try {
    row.scrollIntoView({ block: 'center', behavior: 'smooth' });
    await new Promise(r => setTimeout(r, 600));
    let menuButton = findMenuButton(row);
    if (!menuButton) return false;
    menuButton.click();
    await new Promise(r => setTimeout(r, 600));
    let deleteButton = findDeleteButton();
    if (!deleteButton) return false;
    deleteButton.click();
    await new Promise(r => setTimeout(r, 600));
    const confirmButton = await waitForDeleteConfirmButton();
    if (!confirmButton) return false;
    confirmButton.click();
    await new Promise(r => setTimeout(r, 1200));
    return true;
  } catch (e) {
    return false;
  }
};

// Bulk delete from inbox (optimized)
const startDeletion = async () => {
  const seenRows = new Set();
  while (isRunning) {
    // Always re-query the rows after each deletion
    const rows = Array.from(document.querySelectorAll('[role="row"]')).filter(
      row => {
        const rowId = row.getAttribute('data-id') || row.id || row.innerHTML;
        return !seenRows.has(rowId);
      }
    );
    if (rows.length === 0) {
      // Try to scroll to load more
      const previousCount = document.querySelectorAll('[role="row"]').length;
      window.scrollTo(0, document.body.scrollHeight);
      await new Promise(r => setTimeout(r, 350)); // Even faster scroll wait
      const currentCount = document.querySelectorAll('[role="row"]').length;
      if (currentCount === previousCount) {
        console.log('No more chats to load');
        break;
      }
      continue;
    }
    const row = rows[0];
    const rowId = row.getAttribute('data-id') || row.id || row.innerHTML;
    console.log('Attempting to delete chat...');
    if (await deleteChatRow(row)) {
      deletedCount++;
      seenRows.add(rowId);
      if (port) port.postMessage({ type: 'counter', value: deletedCount });
      console.log('Chat deleted successfully');
      await new Promise(r => setTimeout(r, 150)); // Even faster post-delete wait
    } else {
      console.log('Failed to delete chat');
      seenRows.add(rowId); // Avoid infinite loop on a bad row
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
      alert('Could not find the final Delete confirmation button.');
      return false;
    }
    confirmBtn.click();
    await new Promise(r => setTimeout(r, 1200));
    return true;
  } catch (e) {
    return false;
  }
};

// Universal entry point
chrome.runtime.onConnect.addListener((messagePort) => {
  console.log('Connection established with popup');
  port = messagePort;
  port.onMessage.addListener((msg) => {
    console.log('Received message from popup:', msg);
    if (msg.action === 'start') {
      console.log('Starting deletion process...');
      isRunning = true;
      if (document.querySelectorAll('[role="row"]').length > 0) {
        startDeletion().catch(error => {
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