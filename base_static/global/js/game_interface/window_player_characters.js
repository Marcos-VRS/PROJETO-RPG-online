document.addEventListener("DOMContentLoaded", function () {
    // Para os botões dentro do container
    document.querySelectorAll(".personagem-container-gm button").forEach(button => {
        button.addEventListener("click", function () {
            const characterName = this.textContent.trim();

            if (characterName.toUpperCase() === "DADOS") {
                abrirJanela("dados");
            } else {
                abrirJanela("personagem_secundario");
                get_character_gm(characterName);
            }
        });
    });

    // Para os <a> da lista de personagens
    document.querySelectorAll(".lista-personagens .menu-button-gm").forEach(link => {
        link.addEventListener("click", function () {
            const characterName = this.textContent.trim();
            abrirJanela("personagem_secundario");
            get_character_gm(characterName);
        });
    });
});

function get_character_gm(name) {
    console.log(`Buscando personagem: ${name}`);
    const safeName = encodeURIComponent(name);
    console.log(`Nome Seguro: ${safeName}`);

    fetch(`/api/character/?nome=${safeName}`)
        .then(response => response.json())
        .then(data => {
            console.log("Resposta da API:", data);
            const window = document.getElementById("janela-personagem_secundario");

            let skillsList = '';
            data.skills.forEach(skill => {
                skillsList += `
                    <li class="li-gm">
                        <span class="medievalsharp-regular">${skill.nome}: NH ${skill.nh}</span>&nbsp;&nbsp; 
                        =>&nbsp;&nbsp;BÔNUS:
                        <input class="input-inc" type="number" id="bonus-${skill.nome}" value="0">
                        &nbsp;&nbsp;&nbsp;&nbsp;REDUTOR:&nbsp;&nbsp;
                        <input class="input-inc" type="number" id="redutor-${skill.nome}" value="0">
                        <button class="menu-button" onclick="rollAttribute(${skill.nh}, '${skill.nome}', \`${safeName}\`)">Rolar</button><br><br>
                    </li>
                `;
            });

            let ataque_meleeList = '';
            data.maneuvers_melee.forEach(m => {
                ataque_meleeList += `
                    <li class="li-gm">
                        <span class="medievalsharp-regular">${m.nome}: ${m.damage} NH:${m.nh}</span>&nbsp;&nbsp; 
                        =>&nbsp;&nbsp;BÔNUS:
                        <input class="input-inc" type="number" id="bonus-${m.nome}" value="0">
                        &nbsp;&nbsp;&nbsp;&nbsp;REDUTOR:&nbsp;&nbsp;
                        <input class="input-inc" type="number" id="redutor-${m.nome}" value="0">
                        <button class="menu-button" onclick="rollAttack(${m.nh}, '${m.nome}', '${m.damage}', \`${safeName}\`)">Rolar</button><br><br>
                    </li>
                `;
            });

            let ataque_rangedList = '';
            data.maneuvers_ranged.forEach(r => {
                ataque_rangedList += `
                    <li class="li-gm">
                        <span class="medievalsharp-regular">${r.nome}: ${r.damage} NH:${r.nh}</span>&nbsp;&nbsp; 
                        =>&nbsp;&nbsp;BÔNUS:
                        <input class="input-inc" type="number" id="bonus-${r.nome}" value="0">
                        &nbsp;&nbsp;&nbsp;&nbsp;REDUTOR:&nbsp;&nbsp;
                        <input class="input-inc" type="number" id="redutor-${r.nome}" value="0">
                        <button class="menu-button" onclick="rollAttack(${r.nh}, '${r.nome}', '${r.damage}', \`${safeName}\`)">Rolar</button><br><br>
                    </li>
                `;
            });

            let defesaList = '';
            data.maneuvers_defense.forEach(def => {
                defesaList += `
                    <li class="li-gm">
                        <span class="medievalsharp-regular">${def.nome}: NH:${def.nh}</span>&nbsp;&nbsp; 
                        =>&nbsp;&nbsp;BÔNUS:
                        <input class="input-inc" type="number" id="bonus-${def.nome}" value="0">
                        &nbsp;&nbsp;&nbsp;&nbsp;REDUTOR:&nbsp;&nbsp;
                        <input class="input-inc" type="number" id="redutor-${def.nome}" value="0">
                        <button class="menu-button" onclick="rollAttribute(${def.nh}, '${def.nome}', \`${safeName}\`)">Rolar</button><br><br>
                    </li>
                `;
            });

            // Atualiza a janela com os dados do personagem
            window.innerHTML = `
                <button class="fechar menu-button" onclick="fecharJanela()">×</button>
                <h2 class="nome-personagem-player" data-nome="${data.nome_personagem}" >${data.nome_personagem}</h2>
                <ul>
                    <div class="ficha-parte-box">
                        <h3 class="titulo-ficha-gm">ATRIBUTOS</h3>
                        ${["ST", "DX", "IQ", "HT"].map(attr => `
                            <li class="li-gm">
                                <span class="medievalsharp-regular">${attr}: ${data.atributos[attr]}</span>&nbsp;&nbsp;
                                =>&nbsp;&nbsp;BÔNUS:
                                <input class="input-inc" type="number" id="bonus-${attr}" value="0">
                                &nbsp;&nbsp;&nbsp;&nbsp;REDUTOR:&nbsp;&nbsp;
                                <input class="input-inc" type="number" id="redutor-${attr}" value="0">
                                <button class="menu-button" onclick="rollAttribute(${data.atributos[attr]}, '${attr}', \`${safeName}\`)">Rolar</button><br><br>
                            </li>
                        `).join("")}
                    </div>

                    <div class="ficha-parte-box">
                        <h3 class="titulo-ficha-gm">SUBATRIBUTOS</h3>
                        ${["hp", "fp", "speed"].map(sa => `
                            <li class="li-gm"><span class="medievalsharp-regular">${sa.toUpperCase()}: ${data.sub_attributes[sa]}</span></li>
                        `).join("")}
                        ${["dodge", "parry_unarmed", "parry_weapon", "will", "perception"].map(sa => `
                            <li class="li-gm">
                                <span class="medievalsharp-regular">${sa.replace("_", " ").toUpperCase()}: ${data.sub_attributes[sa]}</span>&nbsp;&nbsp;
                                =>&nbsp;&nbsp;BÔNUS:
                                <input class="input-inc" type="number" id="bonus-${sa.toUpperCase()}" value="0">
                                &nbsp;&nbsp;&nbsp;&nbsp;REDUTOR:&nbsp;&nbsp;
                                <input class="input-inc" type="number" id="redutor-${sa.toUpperCase()}" value="0">
                                <button class="menu-button" onclick="rollAttribute(${data.sub_attributes[sa]}, '${sa.toUpperCase()}', \`${safeName}\`)">Rolar</button><br><br>
                            </li>
                        `).join("")}
                    </div>

                    <div class="ficha-parte-box">
                        <h3 class="titulo-ficha-gm">PERÍCIAS</h3>
                        ${skillsList}
                    </div>

                    <div class="ficha-parte-box">
                        <h3 class="titulo-ficha-gm">ATAQUES</h3>
                        ${ataque_meleeList}
                        ${ataque_rangedList}
                    </div>

                    <div class="ficha-parte-box">
                        <h3 class="titulo-ficha-gm">DEFESAS</h3>
                        ${defesaList}
                    </div>
                </ul>
            `;
        })
        .catch(error => console.error("Erro ao carregar ficha do personagem:", error));
}
