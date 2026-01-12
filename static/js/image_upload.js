document.getElementById("upload").addEventListener("change", async function () {

    const fileInput = this;
    if (!fileInput.files || !fileInput.files[0]) return;

    // Preview image
    const reader = new FileReader();
    reader.onload = function (e) {
        document.getElementById("imageResult").src = e.target.result;
    };
    reader.readAsDataURL(fileInput.files[0]);

    // Prepare form data
    const formData = new FormData();
    formData.append("image", fileInput.files[0]);

    // Show loading
    const loading = document.getElementById("loadingMessage");
    if (loading) loading.style.display = "block";

    try {
        const response = await fetch("/prediction", {
            method: "POST",
            body: formData
        });

        if (!response.ok) {
            throw new Error("Upload failed");
        }

        // Enable texture panel ONLY after server upload
        const texturePanel = document.querySelector(".texture-panel");
        if (texturePanel) {
            texturePanel.classList.remove("disabled");
        }

    } catch (err) {
        alert("Upload failed. Please try again.");
        console.error(err);
    } finally {
        if (loading) loading.style.display = "none";
    }
});
