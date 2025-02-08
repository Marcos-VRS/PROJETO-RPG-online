document.addEventListener("DOMContentLoaded", function () {
    var inputImagem = document.querySelector('input[type="file"]');
    var miniatura = document.getElementById("miniatura_imagem");

    if (inputImagem) {
        inputImagem.addEventListener("change", function (event) {
            var reader = new FileReader();
            var file = event.target.files[0];

            if (file) {
                reader.onload = function () {
                    miniatura.src = reader.result;
                    miniatura.style.display = "block";
                };
                reader.readAsDataURL(file);
            }
        });
    }
});
