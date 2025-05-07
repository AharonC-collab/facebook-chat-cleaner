# Facebook Chat Cleaner

A Chrome extension to **bulk delete Facebook Messenger conversations** or delete the current thread, with maximum speed and reliability.

## Features
- **Bulk delete**: Removes all visible chats from your Messenger inbox automatically.
- **Thread delete**: Deletes the currently open conversation if you are inside a thread.
- **Fast**: Optimized for speed with minimal waits.
- **Universal**: Works on both [messenger.com](https://www.messenger.com/) and [facebook.com/messages/](https://www.facebook.com/messages/).
- **Popup UI**: Start/stop the process and see a live counter.

## How it works
- On the **inbox page**, it loops through all chat rows, opens the menu, clicks delete, confirms, and moves to the next chat.
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
4. Click **Start Deleting Chats**
5. Watch the counter update as chats are deleted
6. Click **Stop** at any time to pause

## Files
- `manifest.json` — Chrome extension manifest
- `popup.html` — Extension popup UI
- `popup.js` — Popup logic and communication
- `content.js` — Main deletion logic (bulk and thread modes)
- `README.md` — This file

## Notes
- **Speed**: The extension is tuned for maximum speed. If you experience missed deletions, you can increase the waits in `content.js`.
- **Safety**: Use at your own risk. This extension automates UI actions and may be affected by Facebook UI changes.
- **Privacy**: No data is sent anywhere. All actions happen locally in your browser.
- **Page Refreshes**: Sometimes a page refresh may be needed before using the extension. This is because:
  - Facebook Messenger uses dynamic content loading
  - The extension needs all UI elements to be properly loaded
  - If you see "Connection lost" message, refresh the page and try again
  - Wait a few seconds after page load before starting deletion

## Contributing
Pull requests and issues are welcome!

## License
MIT
