document.addEventListener("DOMContentLoaded", () => {

  document.querySelectorAll(".texture-thumb").forEach(img => {

    img.addEventListener("click", async () => {

      const textureName = img.dataset.texture;
      console.log("Texture clicked:", textureName);

      try {
        const response = await fetch("/result_textured", {
          method: "POST",
          headers: {
            "Content-Type": "application/json"
          },
          body: JSON.stringify({ texture: textureName })
        });

        const data = await response.json();

        if (response.ok && data.state === "success") {
          const image = document.querySelector("#imageResult");
          image.src = data.room_path + "?t=" + new Date().getTime();
        } else {
          alert(data.msg || "Texture could not be applied");
        }

      } catch (err) {
        console.error("Texture request failed:", err);
        alert("Network error while applying texture");
      }
    });

  });

});
