# Facebook Chat Cleaner

A Chrome extension to **bulk delete Facebook Messenger conversations** or delete the current thread, with maximum speed and reliability.

## Features
- **Bulk delete**: Removes all visible chats from your Messenger inbox automatically.
- **Selective deletion**: Start deleting from any chat number in your inbox.
- **Thread delete**: Deletes the currently open conversation if you are inside a thread.
- **Fast**: Optimized for speed with minimal waits.
- **Universal**: Works on both [messenger.com](https://www.messenger.com/) and [facebook.com/messages/](https://www.facebook.com/messages/).
- **Popup UI**: Start/stop the process and see a live counter.

## How it works
- On the **inbox page**, it loops through all chat rows, opens the menu, clicks delete, confirms, and moves to the next chat.
  - You can specify which chat to start from (e.g., start from the 5th chat)
  - The extension will skip all chats before your specified number
- On a **thread page**, it opens the conversation menu, clicks delete, and confirms.
- The extension uses smart selectors and minimal waits for maximum speed.

## Installation
1. **Clone or download this repo**
2. Go to `chrome://extensions/` in Chrome
3. Enable **Developer mode** (top right)
4. Click **Load unpacked** and select this folder

## Usage
1. Go to [messenger.com](https://www.messenger.com/) or [facebook.com/messages/](https://www.facebook.com/messages/)
2. (For thread delete) You can also open a specific conversation (URL contains `/t/`)
3. Click the **Facebook Chat Cleaner** extension icon
4. (Optional) Enter a chat number to start from:
   - Leave empty to start from the first chat
   - Enter a number (e.g., "5") to start deleting from that chat
   - The number corresponds to the position in your inbox (1 = first chat)
5. Click **Start Deleting Chats**
6. Watch the counter update as chats are deleted
7. Click **Stop** at any time to pause

## Files
- `manifest.json` — Chrome extension manifest
- `popup.html` — Extension popup UI
- `popup.js` — Popup logic and communication
- `content.js` — Main deletion logic (bulk and thread modes)
- `README.md` — This file

## Code & Functions

### content.js (Main Deletion Logic)
- **waitForElement(selector, timeout)**: Waits for a DOM element to appear.
- **scrollToLoadMore()**: Scrolls the inbox to load more chats.
- **getVisibleChatRows()**: Returns all visible chat rows, excluding Marketplace.
- **findMenuButton(row)**: Finds the menu button in a chat row.
- **findDeleteButton()**: Finds the delete/remove button in the dropdown menu.
- **waitForDeleteConfirmButton()**: Waits for the confirmation button in the delete dialog.
- **deleteChatRow(row)**: Automates the process of deleting a single chat row.
- **startDeletion(startChatNumber)**: Main loop to delete all chats, starting from a given chat number.
- **deleteCurrentThread()**: Deletes the currently open conversation (thread mode).
- **chrome.runtime.onConnect.addListener**: Handles messages from the popup (start/stop actions, counter updates).

### popup.js (Popup UI Logic)
- Handles UI controls: Start/Stop buttons, status display, and chat number input.
- Connects to the content script in the active Facebook tab.
- Sends start/stop commands and receives live counter updates.
- Provides user feedback and error handling in the popup.

### popup.html (Popup UI)
- Simple UI with input for starting chat number, Start/Stop buttons, and a live status/counter.

### manifest.json
- Declares permissions, content scripts, and popup for the Chrome extension.

## Notes
- **Speed**: The extension is tuned for maximum speed. If you experience missed deletions, you can increase the waits in `content.js`.
- **Safety**: Use at your own risk. This extension automates UI actions and may be affected by Facebook UI changes.
- **Privacy**: No data is sent anywhere. All actions happen locally in your browser.

## Contributing
Pull requests and issues are welcome!

## License
MIT
