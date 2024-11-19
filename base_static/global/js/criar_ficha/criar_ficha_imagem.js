
function previewImagem(event) {
    var input = event.target;
    var reader = new FileReader();

    reader.onload = function () {
        var miniatura = document.getElementById('miniatura_imagem');
        miniatura.src = reader.result;
        miniatura.style.display = 'block';
    };

    if (input.files && input.files[0]) {
        reader.readAsDataURL(input.files[0]);
    }
}