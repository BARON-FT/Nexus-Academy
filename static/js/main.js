document.addEventListener('DOMContentLoaded', () => {
    // --- Gestion du formulaire d'inscription ---
    const inscriptionForm = document.getElementById('inscription-form');
    if (inscriptionForm) {
        const fileInput = document.getElementById('proof-upload');
        const fileLabel = document.getElementById('file-label-text');
        const originalLabelText = fileLabel ? fileLabel.textContent : '';
        const submitBtn = inscriptionForm.querySelector('button[type="submit"]');
        const alertBox = document.getElementById('alert-box');

        // Mettre à jour le label du fichier
        fileInput.addEventListener('change', () => {
            if (fileInput.files.length > 0) {
                fileLabel.textContent = fileInput.files[0].name;
            } else {
                fileLabel.textContent = originalLabelText;
            }
        });

        // Intercepter la soumission du formulaire
        inscriptionForm.addEventListener('submit', async (e) => {
            e.preventDefault();
            
            const formData = new FormData(inscriptionForm);
            const originalBtnText = submitBtn.textContent;
            
            // UI de chargement
            submitBtn.disabled = true;
            submitBtn.textContent = 'Envoi en cours...';
            alertBox.style.display = 'none';
            alertBox.className = 'alert';

            try {
                const response = await fetch(inscriptionForm.action, {
                    method: 'POST',
                    body: formData,
                });

                const result = await response.json();

                if (response.ok) {
                    alertBox.className = 'alert success';
                    alertBox.textContent = result.message;
                    inscriptionForm.reset();
                    fileLabel.textContent = originalLabelText;
                } else {
                    throw new Error(result.error || 'Une erreur est survenue.');
                }
            } catch (error) {
                alertBox.className = 'alert error';
                alertBox.textContent = error.message;
            } finally {
                alertBox.style.display = 'block';
                submitBtn.disabled = false;
                submitBtn.textContent = originalBtnText;
            }
        });
    }
});