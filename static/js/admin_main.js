// static/js/admin_main.js
document.addEventListener('DOMContentLoaded', function() {
    console.log("Admin JS Loaded");

    // Image preview for file inputs in forms
    const imageInputs = document.querySelectorAll('input[type="file"][name="image"]'); // More specific selector
    imageInputs.forEach(input => {
        input.addEventListener('change', function(event) {
            const file = event.target.files[0];
            const previewContainerId = event.target.id + '-preview-container'; // Assumes input has an ID
            const previewContainer = document.getElementById(previewContainerId);
            
            if (previewContainer) {
                // Clear previous preview
                previewContainer.innerHTML = ''; 
                
                if (file && file.type.startsWith('image/')) {
                    const img = document.createElement('img');
                    // CSS in admin_style.css will style .image-preview-container img
                    
                    const reader = new FileReader();
                    reader.onload = function(e) {
                        img.src = e.target.result;
                        previewContainer.appendChild(img);
                    }
                    reader.readAsDataURL(file);
                }
            }
        });
    });

    // Sidebar toggle for mobile (if you add the button)
    // const sidebarToggle = document.getElementById('sidebarToggle');
    // const adminSidebar = document.querySelector('.admin-sidebar');
    // if (sidebarToggle && adminSidebar) {
    //     sidebarToggle.addEventListener('click', function() {
    //         adminSidebar.classList.toggle('open');
    //     });
    // }
});