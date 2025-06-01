// Ensure this script runs after the DOM is fully loaded and Flask data is available
document.addEventListener('DOMContentLoaded', function() {
    if (typeof vis === 'undefined') {
        console.error("Vis.js library is not loaded.");
        return;
    }

    // Data from Flask, set in network.html
    // window.nodesData, window.edgesData, window.timelineData

    console.log("Graph JS: Nodes data", window.nodesData);
    console.log("Graph JS: Edges data", window.edgesData);

    // Cria os datasets para o Vis.js
    window.nodes = new vis.DataSet(window.nodesData || []);
    window.edges = new vis.DataSet(window.edgesData || []);

    // Define as cores dos nós com base na legenda
    window.nodeColors = {
        "sujeito": '#FFD700', // Gold
        "acao": '#ADD8E6', // Light Blue
        "estimulo": '#90EE90', // Light Green
        "hipotese": '#a753f5' // Purple
    };

    // Pega o container da rede
    var container = document.getElementById('mynetwork');
    if (!container) {
        console.error("Network container #mynetwork not found.");
        return;
    }

    // Provê os dados para a rede
    var data = {
        nodes: window.nodes,
        edges: window.edges
    };

    var options = {
        nodes: {
            borderWidth: 2,
            size: 20,
            font: {
                size: 12,
                face: 'Inter, sans-serif',
                color: '#333333',
            },
            shadow: {
                enabled: true,
                size: 5,
                x: 2,
                y: 2
            },
            widthConstraint: {
                maximum: 150
            }
        },
        edges: {
            width: 1.5,
            smooth: {
                enabled: true,
                type: "horizontal",
                roundness: 1
            },
            arrows: {
              to: { enabled: true, scaleFactor: 0.8, type: 'arrow' }
            },
            font: {
                size: 10,
                face: 'Inter, sans-serif',
                align: 'horizontal',
                strokeWidth: 3,
                strokeColor: '#ffffff'
            },
            color: {
                inherit: 'from'
            },
            shadow: true,
            widthConstraint: {
                maximum: 150
            }
        },
        layout: {
            hierarchical: false,
            improvedLayout: true,
        },
        interaction: {
            hover: false,
            navigationButtons: false,
            keyboard: {
                enabled: true,
                speed: {x: 10, y: 10, zoom: 0.05},
                bindToWindow: true
            },
            tooltipDelay: 250,
            dragNodes: true,
            zoomView: true,
            dragView: true
        },
        physics: {
            enabled: true,
            solver: 'barnesHut',
            barnesHut: {
                gravitationalConstant: -5000,
                centralGravity: 0.20,
                springLength: 150,
                springConstant: 0.01,
                damping: 0.9,
                avoidOverlap: 0.5
            },
            stabilization: {
                enabled: true,
                iterations: 1000,
                updateInterval: 25,
                onlyDynamicEdges: false,
                fit: true
            }
        },
    };

    window.network = new vis.Network(container, data, options);

    // Esconder o overlay quando a rede estiver estabilizada
    window.network.on("stabilizationIterationsDone", function () {
        if (window.network && typeof window.network.fit === 'function') {
            window.network.fit();
        }
        if (typeof window.hideLoadingOverlay === 'function') {
            window.hideLoadingOverlay();
        }
        // Initialize timeline after stabilization
        if (typeof initializeTimeline === 'function') {
            initializeTimeline();
        } else {
            console.warn("initializeTimeline function not found after stabilization.");
        }
    });

    // Esconder o overlay se a página for carregada e a rede já estiver pronta (ex: via cache do navegador)
    // This is now part of the DOMContentLoaded to ensure network is defined.
    if (window.network && typeof window.network.getPositions === 'function' && window.network.getPositions().length > 0) {
        if (typeof window.hideLoadingOverlay === 'function') {
            window.hideLoadingOverlay();
        }
    }
    // Call initializeTimeline on load as well, in case stabilization doesn't run (e.g. static network)
    // However, it's better called after stabilization or if network is already drawn.
    // The stabilizationIterationsDone event is more reliable for this.
    // If there are no nodes, stabilizationIterationsDone might not fire.
    if (window.nodesData && window.nodesData.length === 0) {
        if (typeof initializeTimeline === 'function') {
            console.log("No nodes, initializing timeline directly.");
            initializeTimeline();
        }
         if (typeof window.hideLoadingOverlay === 'function') { // Hide loading if no nodes.
            window.hideLoadingOverlay();
        }
    } else if (window.nodesData && window.nodesData.length > 0 && (!window.network.physics || !window.network.physics.enabled)) {
        // If physics is disabled, stabilizationIterationsDone might not fire.
        if (typeof initializeTimeline === 'function') {
            console.log("Physics disabled, initializing timeline directly.");
            initializeTimeline();
        }
         if (typeof window.hideLoadingOverlay === 'function') {
            window.hideLoadingOverlay();
        }
    }


});
