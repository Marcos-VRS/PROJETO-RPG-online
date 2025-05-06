function filtrarAtaque() {
    let input = document.getElementById('search-attack').value.toLowerCase();

    let assets = [
        ...document.querySelectorAll('.ficha-parte-box-ataque'),
        ...document.querySelectorAll('.ficha-parte-box-ataque-ranged')
    ];

    console.log(input, assets);

    assets.forEach(asset => {
        let nomeAsset = asset.querySelector('.medievalsharp-large')?.textContent.trim().toLowerCase() || '';

        if (nomeAsset.includes(input)) {
            asset.style.visibility = "visible";
            asset.style.position = "static";
        } else {
            asset.style.visibility = "hidden";
            asset.style.position = "absolute";
        }
    });
}
