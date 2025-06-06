// static/js/progress_logger.js

let pollingIntervalId = null;
let lastReceivedMessageIndex = -1; // To track last message shown

// (Keep existing addProgressMessage, clearProgressLog, showLoadingOverlayWithProgress, hideLoadingOverlay functions)
// Make sure addProgressMessage can be called by the polling function.

function addProgressMessage(message, type = 'info') {
    const logList = document.getElementById('progressLogList');
    if (!logList) {
        console.error('Progress log list element not found.');
        return;
    }
    const listItem = document.createElement('li');
    listItem.classList.add('log-message', `log-message-${type}`);
    const timestamp = new Date().toLocaleTimeString();
    listItem.textContent = `[${timestamp}] ${message}`;
    logList.appendChild(listItem);
    const logContainer = document.getElementById('progressLogContainer');
    if (logContainer) {
        logContainer.scrollTop = logContainer.scrollHeight;
    }
}

function clearProgressLog() {
    const logList = document.getElementById('progressLogList');
    if (logList) {
        logList.innerHTML = '';
    }
    lastReceivedMessageIndex = -1; // Reset message tracking
}

function showLoadingOverlayWithProgress() {
    const overlay = document.getElementById('loadingOverlay');
    if (overlay) {
        overlay.classList.add('visible');
    }
    clearProgressLog(); // Clear old logs when overlay is shown
    // Initial message can be added here or by the caller
}

function hideLoadingOverlay() {
    const overlay = document.getElementById('loadingOverlay');
    if (overlay) {
        overlay.classList.remove('visible');
    }
    stopPollingProgress(); // Ensure polling stops when overlay is hidden
}

async function pollProgress(taskId) {
    try {
        const response = await fetch(`/analysis_progress/${taskId}`);
        if (!response.ok) {
            // Don't stop polling on a single failed fetch, server might be temporarily busy
            // or task not yet registered. Could add a counter for max retries on network errors.
            console.error(`Error fetching progress: ${response.statusText}`);
            // addProgressMessage(`Error fetching progress: ${response.statusText}`, 'error');
            return;
        }
        const data = await response.json();

        // Process messages
        if (data.messages && data.messages.length > lastReceivedMessageIndex) {
            for (let i = lastReceivedMessageIndex + 1; i < data.messages.length; i++) {
                const msgObj = data.messages[i]; // Assuming messages are {text: "...", type: "info/error"}
                if (msgObj && msgObj.text) {
                     addProgressMessage(msgObj.text, msgObj.type || 'info');
                } else if (typeof msgObj === 'string') { // Handle simple string messages
                    addProgressMessage(msgObj, 'info');
                }
            }
            lastReceivedMessageIndex = data.messages.length - 1;
        }

        if (data.status === 'complete' || data.status === 'error' || data.status === 'finished') {
            stopPollingProgress();
            if (data.status === 'complete' || data.status === 'finished') {
                // Optionally add a final success message if not already sent by backend
                // addProgressMessage("Analysis complete!", "success");
                // Depending on UX, might hide overlay after a short delay or let user close it
                // setTimeout(hideLoadingOverlay, 2000);
            } else if (data.status === 'error') {
                // Optionally add a final error message if not already sent by backend
                // addProgressMessage("Analysis failed. Please check logs.", "error");
                // Keep overlay visible for errors usually
            }
            // If the main analysis request itself handles redirection or content update upon completion,
            // hiding the overlay here might be redundant or premature.
            // For now, we just stop polling. The calling page/form submission logic
            // should handle what happens after 'complete' or 'error' (e.g., page redirect or final UI update).
        }
    } catch (error) {
        console.error('Polling request failed:', error);
        // addProgressMessage('Failed to connect to server for progress updates.', 'error');
        // Consider stopping polling if multiple consecutive errors occur
    }
}

function startPollingProgress(taskId) {
    if (pollingIntervalId) {
        stopPollingProgress(); // Stop any existing polling
    }
    clearProgressLog(); // Clear previous logs
    lastReceivedMessageIndex = -1; // Reset for new task

    // Call immediately for the first update, then set interval
    pollProgress(taskId);
    pollingIntervalId = setInterval(() => pollProgress(taskId), 2000); // Poll every 2 seconds
    console.log(`Started polling for taskId: ${taskId}`);
}

function stopPollingProgress() {
    if (pollingIntervalId) {
        clearInterval(pollingIntervalId);
        pollingIntervalId = null;
        console.log("Stopped polling.");
    }
}

// (Keep the example simulation functions commented out or remove them,
// as real progress will come from the backend)
/*
// Example of how to simulate progress (for demonstration purposes)
// function simulateProgress() {
//     showLoadingOverlayWithProgress();
//     addProgressMessage('Verificando dados de entrada...', 'info');
//     ...
// }
*/
