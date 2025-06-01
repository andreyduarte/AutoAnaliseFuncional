// Ensure this script runs after network_graph.js has defined globals like nodes, network, nodeColors
// and after Flask data (timelineData) is available on window.

// Make functions global so network_graph.js can call initializeTimeline
function initializeTimeline() {
    console.log("Timeline JS: Initializing timeline. Timeline data:", window.timelineData);
    const timelineRange = document.getElementById('timelineRange');
    const timelineLabel = document.getElementById('timelineLabel');

    if (!timelineRange || !timelineLabel) {
        console.error("Timeline elements not found.");
        return;
    }

    // Ensure window.nodes and window.nodeColors are available
    if (typeof window.nodes === 'undefined' || typeof window.nodeColors === 'undefined') {
        console.error("Vis.js nodes or nodeColors not initialized before timeline script.");
        return;
    }

    if (window.timelineData && window.timelineData.length > 0) {
        timelineRange.min = 0;
        timelineRange.max = window.timelineData.length - 1;
        timelineRange.value = window.timelineData.length - 1; // Start at the end
        timelineLabel.innerText = window.timelineData.length;
        updateNodeVisibility(timelineRange.max); // Update with the last index
    } else {
        timelineRange.min = 0;
        timelineRange.max = 0;
        timelineRange.value = 0;
        timelineLabel.innerText = '0';
        // If no timeline, all nodes should be visible by default (ensure hidden is false)
        // This part is crucial if there's no timeline data.
        let updates = [];
        window.nodes.forEach(function(node) {
            let nodeType = node.group; // Assuming group property holds the type like "sujeito"
            let targetColor = window.nodeColors[nodeType] || '#999999'; // Default color if type unknown
            updates.push({
                id: node.id,
                hidden: false,
                color: { background: targetColor, border: targetColor }
            });
        });
        if(updates.length > 0) {
            window.nodes.update(updates);
        }
    }
}

function updateNodeVisibility(sliderValueIndex) {
    // Ensure window.nodes and window.nodeColors are available
    if (typeof window.nodes === 'undefined' || typeof window.nodeColors === 'undefined' || typeof window.timelineData === 'undefined') {
        console.error("Vis.js nodes, nodeColors, or timelineData not initialized for updateNodeVisibility.");
        return;
    }

    var visibleNodeIds = new Set();
    // Iterate from 0 up to and including sliderValueIndex
    for (var i = 0; i <= sliderValueIndex; i++) {
        if (window.timelineData[i] !== undefined) {
            visibleNodeIds.add(window.timelineData[i]);
        }
    }

    var updates = [];
    window.nodes.forEach(function(node) {
        var isVisible = visibleNodeIds.has(node.id);
        // console.log(`Node ${node.id} (type: ${node.group}) visibility: ${isVisible}`);
        var nodeType = node.group;
        var targetColor = window.nodeColors[nodeType] || '#999999'; // Default color

        updates.push({
            id: node.id,
            hidden: !isVisible,
            // Also re-apply color in case it was changed or to ensure consistency
            color: {
                background: targetColor,
                border: targetColor
            }
        });
    });

    if (updates.length > 0) {
        window.nodes.update(updates);
    }
    // Optional: network.fit() if you want the view to adjust.
    // Be careful, it can be jarring if called too often.
    // if (window.network) window.network.fit();
}

document.addEventListener('DOMContentLoaded', function() {
    const timelineRange = document.getElementById('timelineRange');
    const timelineLabel = document.getElementById('timelineLabel');

    if (timelineRange && timelineLabel) {
        timelineRange.addEventListener('input', function() {
            var sliderValue = parseInt(this.value);
            // timelineLabel.innerText shows the number of visible nodes (index + 1)
            timelineLabel.innerText = (window.timelineData && window.timelineData.length > 0) ? (sliderValue + 1).toString() : '0';
            updateNodeVisibility(sliderValue);
        });
    }

    // Initial call to initializeTimeline is now handled by network_graph.js
    // after network stabilization, or if no nodes/physics.
    // This ensures that 'nodes' and 'network' objects are ready.
    // However, if network_graph.js fails or vis.js is not loaded, this won't run.
    // We added a call in network_graph.js for this.
});
