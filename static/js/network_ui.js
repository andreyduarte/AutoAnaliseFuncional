// In static/js/network_ui.js
document.addEventListener('DOMContentLoaded', function () {
    const updateButton = document.getElementById('updateGraphButton'); // ID from network.html
    const analysisForm = document.getElementById('updateForm'); // ID from network.html

    if (analysisForm) {
        analysisForm.addEventListener('submit', function(event) {
            showLoadingOverlayWithProgress();
            addProgressMessage('Enviando nova solicitação de análise do gráfico...', 'info');
            // Polling will be started on page load if taskId is present
        });
    }

    // On page load, check for a task ID
    // This would be set by the server if a graph update is already in progress
    // when the network page is loaded/reloaded.
    if (typeof window.networkAnalysisTaskId !== 'undefined' && window.networkAnalysisTaskId) {
        showLoadingOverlayWithProgress();
        addProgressMessage('Atualização de gráfico anterior detectada. Buscando progresso...', 'info');
        startPollingProgress(window.networkAnalysisTaskId);
    }

    // Existing UI logic for sidebar, legend, char counter (keep as is)

    const sidebar = document.getElementById('sidebar');
    const sidebarToggle = document.getElementById('sidebarToggle');

    if (sidebarToggle && sidebar) {
        sidebarToggle.addEventListener('click', () => {
            sidebar.classList.toggle('visible');
            // Change icon based on sidebar visibility
            const icon = sidebarToggle.querySelector('i');
            if (sidebar.classList.contains('visible')) {
                icon.classList.remove('fa-bars');
                icon.classList.add('fa-times');
            } else {
                icon.classList.remove('fa-times');
                icon.classList.add('fa-bars');
            }
        });
    }

    const legendInfoBox = document.getElementById('legendInfoBox');
    const toggleLegendButton = document.getElementById('toggleLegendButton');

    if (toggleLegendButton && legendInfoBox) {
        toggleLegendButton.addEventListener('click', () => {
            const isHidden = legendInfoBox.style.display === 'none';
            legendInfoBox.style.display = isHidden ? '' : 'none';
            const icon = toggleLegendButton.querySelector('i');
            if (isHidden) {
                icon.classList.remove('fa-eye');
                icon.classList.add('fa-eye-slash');
            } else {
                icon.classList.remove('fa-eye-slash');
                icon.classList.add('fa-eye');
            }
        });
        // Initialize legend state - start hidden, button shows eye-slash
        // This initialization was in the original file and seems reasonable.
        legendInfoBox.style.display = 'none';
        toggleLegendButton.querySelector('i').classList.remove('fa-eye');
        toggleLegendButton.querySelector('i').classList.add('fa-eye-slash');
    }

    // Lógica para o contador de caracteres no textarea da página de network
    const analysisTextareaNetwork = document.getElementById('analysisTextarea');
    const charCountNetwork = document.getElementById('charCountNetwork');

    if (analysisTextareaNetwork && charCountNetwork) {
        const maxLengthNetwork = analysisTextareaNetwork.getAttribute('maxlength');

        function updateCharCountNetwork() {
            const currentLength = analysisTextareaNetwork.value.length;
            charCountNetwork.innerText = `${currentLength}/${maxLengthNetwork} caracteres`;
        }

        analysisTextareaNetwork.addEventListener('input', updateCharCountNetwork);
        // Initialize counter
        updateCharCountNetwork();
    }
});
