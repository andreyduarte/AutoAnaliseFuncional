document.addEventListener('DOMContentLoaded', function() {
    // JavaScript para o botão de ocultar/mostrar legenda
    const toggleLegendButton = document.getElementById('toggleLegendButton');
    if (toggleLegendButton) {
        toggleLegendButton.addEventListener('click', function() {
            var legend = document.getElementById('legendInfoBox');
            if (legend.style.display === 'none') {
                legend.style.display = 'block';
                this.innerHTML = '<i class="fas fa-eye"></i>'; // Show eye icon
            } else {
                legend.style.display = 'none';
                this.innerHTML = '<i class="fas fa-eye-slash"></i>'; // Show eye-slash icon
            }
        });
        // Initialize legend state - start hidden, button shows eye-slash
        var legend = document.getElementById('legendInfoBox');
        if(legend){
            legend.style.display = 'none';
            toggleLegendButton.innerHTML = '<i class="fas fa-eye-slash"></i>';
        }
    }

    // Lógica para o contador de caracteres no textarea
    const analysisTextarea = document.getElementById('analysisTextarea');
    const charCountNetwork = document.getElementById('charCountNetwork');
    if (analysisTextarea && charCountNetwork) {
        const maxLengthNetwork = analysisTextarea.getAttribute('maxlength');

        function updateCharCountNetwork() {
            const currentLength = analysisTextarea.value.length;
            charCountNetwork.innerText = `${currentLength}/${maxLengthNetwork} caracteres`;
        }

        analysisTextarea.addEventListener('input', updateCharCountNetwork);
        updateCharCountNetwork(); // Initial call to set the count
    }

    // JavaScript para o botão de abrir/fechar a sidebar como overlay
    const sidebarToggle = document.getElementById('sidebarToggle');
    if (sidebarToggle) {
        sidebarToggle.addEventListener('click', function() {
            var sidebar = document.getElementById('sidebar');
            var icon = this.querySelector('i');

            sidebar.classList.toggle('collapsed');
            if (sidebar.classList.contains('collapsed')) {
                icon.classList.remove('fa-times');
                icon.classList.add('fa-bars');
            } else {
                icon.classList.remove('fa-bars');
                icon.classList.add('fa-times');
            }
        });
        // Initialize sidebar state - starts visible (not collapsed), icon is fa-times
        var sidebar = document.getElementById('sidebar');
        var icon = sidebarToggle.querySelector('i');
        if (sidebar && !sidebar.classList.contains('collapsed')) { // Should be visible by default
             icon.classList.remove('fa-bars');
             icon.classList.add('fa-times');
        } else if (sidebar && sidebar.classList.contains('collapsed')) { // If somehow it starts collapsed
            icon.classList.remove('fa-times');
            icon.classList.add('fa-bars');
        }
    }

    // Lógica para mostrar o overlay de carregamento
    const updateForm = document.getElementById('updateForm');
    const loadingOverlay = document.getElementById('loadingOverlay');
    if (updateForm && loadingOverlay) {
        updateForm.addEventListener('submit', function() {
            loadingOverlay.classList.add('visible');
        });
    }

    // Funções globais para controlar o overlay, pois network events são em outro arquivo
    window.hideLoadingOverlay = function() {
        if (loadingOverlay) {
            loadingOverlay.classList.remove('visible');
        }
    }

    window.showLoadingOverlay = function() {
        if (loadingOverlay) {
            loadingOverlay.classList.add('visible');
        }
    }

    // Esconder o overlay se a página for carregada e a rede já estiver pronta (ex: via cache do navegador)
    // Esta parte depende da 'network' object, será chamada de network_graph.js
    // window.addEventListener('load', function() {
    //     if (typeof network !== 'undefined' && network.getPositions && network.getPositions().length > 0) {
    //         hideLoadingOverlay();
    //     }
    //     // initializeTimeline(); // This will be called from network_graph.js after stabilization
    // });
});
