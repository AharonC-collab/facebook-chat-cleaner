// Get UI elements
const startButton = document.getElementById('startDelete');
const stopButton = document.getElementById('stopDelete');
const counter = document.getElementById('counter');
const status = document.getElementById('status');
const startChatInput = document.getElementById('startChat');
let port = null;

// Helper function to update status
const updateStatus = (message, isError = false) => {
    const count = counter ? counter.textContent : '0';
    status.innerHTML = `${message}<br>Deleted: <span class="counter">${count}</span> chats`;
    status.style.color = isError ? '#ff0000' : '#666';
};

// Start deletion process
startButton.addEventListener('click', async () => {
    try {
        console.log('Start button clicked');
        updateStatus('Connecting to Facebook tab...');
        
        const tabs = await chrome.tabs.query({ active: true, currentWindow: true });
        console.log('Found tabs:', tabs);
        
        if (!tabs || !tabs[0]) {
            throw new Error('No active tab found');
        }

        const tab = tabs[0];
        if (!tab.url.includes('facebook.com/messages')) {
            updateStatus('Please open Facebook Messages first!', true);
            return;
        }

        // Get starting chat number
        const startChatNumber = startChatInput.value ? parseInt(startChatInput.value) : 1;
        if (startChatNumber < 1) {
            updateStatus('Please enter a valid chat number (1 or higher)', true);
            return;
        }

        // Disable start button and enable stop button
        startButton.disabled = true;
        stopButton.disabled = false;
        
        // Connect to content script
        port = chrome.tabs.connect(tab.id, { name: 'fb-cleaner' });
        console.log('Port created');
        
        // Send start message with starting chat number
        port.postMessage({ 
            action: 'start',
            startChatNumber: startChatNumber
        });
        console.log('Start message sent with start chat number:', startChatNumber);
        
        // Listen for updates
        port.onMessage.addListener((msg) => {
            console.log('Received message:', msg);
            if (msg.type === 'counter') {
                counter.textContent = msg.value;
                updateStatus('Deleting chats...');
            }
        });

        // Listen for disconnection
        port.onDisconnect.addListener(() => {
            console.log('Port disconnected');
            port = null;
            startButton.disabled = false;
            stopButton.disabled = true;
            updateStatus('Connection lost. Click Start to try again.', true);
        });

        updateStatus('Started deleting chats...');
        
    } catch (error) {
        console.error('Error:', error);
        updateStatus('Error: ' + error.message, true);
        startButton.disabled = false;
        stopButton.disabled = true;
    }
});

// Stop deletion process
stopButton.addEventListener('click', () => {
    try {
        console.log('Stop button clicked');
        if (port) {
            port.postMessage({ action: 'stop' });
            port.disconnect();
            port = null;
        }
        startButton.disabled = false;
        stopButton.disabled = true;
        updateStatus('Stopped.');
    } catch (error) {
        console.error('Error stopping:', error);
        updateStatus('Error while stopping: ' + error.message, true);
    }
});

// Initialize button states
stopButton.disabled = true;
updateStatus('Ready to start.'); 