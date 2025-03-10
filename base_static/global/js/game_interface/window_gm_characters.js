document.addEventListener("DOMContentLoaded", function () {
    document.querySelectorAll(".personagem-container-gm button").forEach(button => {
        button.addEventListener("click", function () {
            const characterName = this.textContent;

            // Verifica se o nome do botão é "Dados"
            if (characterName === "DADOS") {
                abrirJanela("dados")
            } else {
                // Caso não seja "Dados", abre a ficha do personagem
                abrirJanela("personagem_gm");
                get_character_gm(characterName);
            }
        });
    });
});

function get_character_gm(name) {
    console.log(`Buscando personagem: ${name}`); // 🟢 Debug no console do navegador
    const safeName = encodeURIComponent(name);
    console.log(`Nome Seguro: ${safeName}`);
    fetch(`/api/character/?nome=${safeName}`)
        .then(response => response.json())
        .then(data => {
            console.log("Resposta da API:", data); // 🟢 Verifica se a API respondeu

            const window = document.getElementById("janela-personagem_gm");

            // Acessa as perícias do personagem e usa forEach para iterar sobre elas
            let skillsList = '';
            data.skills.forEach(function (skill) {
                skillsList += `
                    <li class="li-gm">
                        <span class="medievalsharp-regular">${skill.nome}: NH ${skill.nh}</span>&nbsp;&nbsp; 
                        =>&nbsp;&nbsp;BÔNUS:
                        <input class="input-inc" type="number" id="bonus-${skill.nome}" value="0">
                        &nbsp;&nbsp;&nbsp;&nbsp;REDUTOR:&nbsp;&nbsp;
                        <input class="input-inc" type="number" id="redutor-${skill.nome}" value="0">
                        <button class="menu-button" onclick="rollAttribute(${skill.nh}, '${skill.nome}', \`${encodeURIComponent(name)}\`)">Rolar</button><br><br>
                    </li>
                `;
            });

            let ataque_meleeList = '';
            data.maneuvers_melee.forEach(function (maneuvers_melee) {
                ataque_meleeList += `
                    <li class="li-gm" >
                        <span class="medievalsharp-regular">${maneuvers_melee.nome}: ${maneuvers_melee.damage}  NH:${maneuvers_melee.nh}</span>&nbsp;&nbsp; 
                        =>&nbsp;&nbsp;BÔNUS:
                        <input class="input-inc" type="number" id="bonus-${maneuvers_melee.nome}" value="0">
                        &nbsp;&nbsp;&nbsp;&nbsp;REDUTOR:&nbsp;&nbsp;
                        <input class="input-inc" type="number" id="redutor-${maneuvers_melee.nome}" value="0">
                        <button class="menu-button" onclick="rollAttack(${maneuvers_melee.nh}, '${maneuvers_melee.nome}', '${maneuvers_melee.damage}', \`${encodeURIComponent(name)}\`)">Rolar</button><br><br>
                    </li>
                `;
            });

            let ataque_rangedList = '';
            data.maneuvers_ranged.forEach(function (maneuvers_ranged) {
                ataque_rangedList += `
                    <li class="li-gm" >
                        <span class="medievalsharp-regular">${maneuvers_ranged.nome}: ${maneuvers_ranged.damage}  NH:${maneuvers_ranged.nh}</span>&nbsp;&nbsp; 
                        =>&nbsp;&nbsp;BÔNUS:
                        <input class="input-inc" type="number" id="bonus-${maneuvers_ranged.nome}" value="0">
                        &nbsp;&nbsp;&nbsp;&nbsp;REDUTOR:&nbsp;&nbsp;
                        <input class="input-inc" type="number" id="redutor-${maneuvers_ranged.nome}" value="0">
                        <button class="menu-button" onclick="rollAttack(${maneuvers_ranged.nh}, '${maneuvers_ranged.nome}', '${maneuvers_ranged.damage}', \`${encodeURIComponent(name)}\`)">Rolar</button><br><br>
                    </li>
                `;
            });

            let defesaList = '';
            data.maneuvers_defense.forEach(function (defense) {
                defesaList += `
                    <li class="li-gm" >
                        <span class="medievalsharp-regular">${defense.nome}:  NH:${defense.nh}</span>&nbsp;&nbsp; 
                        =>&nbsp;&nbsp;BÔNUS:
                        <input class="input-inc" type="number" id="bonus-${defense.nome}" value="0">
                        &nbsp;&nbsp;&nbsp;&nbsp;REDUTOR:&nbsp;&nbsp;
                        <input class="input-inc" type="number" id="redutor-${defense.nome}" value="0">
                        <button class="menu-button" onclick="rollAttribute(${defense.nh}, '${defense.nome}', \`${encodeURIComponent(name)}\`)">Rolar</button><br><br>
                    </li>
                `;
            });

            // Acessa os atributos do personagem a partir do objeto 'data'
            window.innerHTML = `
                <button class="fechar menu-button" onclick="fecharJanela()">×</button>
                <h2 class="nome-personagem-gm">${data.nome_personagem}</h2>
                <ul>
                    <div class="ficha-parte-box">
                        <h3 class="titulo-ficha-gm">ATRIBUTOS</h3>
                        <li class="li-gm" >
                            <span class="medievalsharp-regular">ST: ${data.atributos.ST}</span>&nbsp;&nbsp; 
                            =>&nbsp;&nbsp;BÔNUS:
                            <input class="input-inc" type="number" id="bonus-ST" value="0">
                            &nbsp;&nbsp;&nbsp;&nbsp;REDUTOR:&nbsp;&nbsp;
                            <input class="input-inc" type="number" id="redutor-ST" value="0">
                            <button class="menu-button" onclick="rollAttribute(${data.atributos.ST}, 'ST', \`${encodeURIComponent(name)}\`)">Rolar</button><br><br>
                        </li>
                        <li class="li-gm" >
                            <span class="medievalsharp-regular">DX: ${data.atributos.DX}</span>&nbsp;&nbsp;
                            =>&nbsp;&nbsp;BÔNUS:
                            <input class="input-inc" type="number" id="bonus-DX" value="0">
                            &nbsp;&nbsp;&nbsp;&nbsp;REDUTOR:&nbsp;&nbsp;
                            <input class="input-inc" type="number" id="redutor-DX" value="0">
                            <button class="menu-button" onclick="rollAttribute(${data.atributos.DX}, 'DX', \`${encodeURIComponent(name)}\`)">Rolar</button><br><br>
                        </li>
                        <li class="li-gm" >
                            <span class="medievalsharp-regular">IQ: ${data.atributos.IQ}</span>&nbsp;&nbsp;
                            =>&nbsp;&nbsp;BÔNUS:
                            <input class="input-inc" type="number" id="bonus-IQ" value="0">
                            &nbsp;&nbsp;&nbsp;&nbsp;REDUTOR:&nbsp;&nbsp;
                            <input class="input-inc" type="number" id="redutor-IQ" value="0">
                            <button class="menu-button" onclick="rollAttribute(${data.atributos.IQ}, 'IQ', \`${encodeURIComponent(name)}\`)">Rolar</button><br><br>
                        </li>
                        <li class="li-gm" >
                            <span class="medievalsharp-regular">HT: ${data.atributos.HT}</span>&nbsp;&nbsp;
                            =>&nbsp;&nbsp;BÔNUS:
                            <input class="input-inc" type="number" id="bonus-HT" value="0">
                            &nbsp;&nbsp;&nbsp;&nbsp;REDUTOR:&nbsp;&nbsp;
                            <input class="input-inc" type="number" id="redutor-HT" value="0">
                            <button class="menu-button" onclick="rollAttribute(${data.atributos.HT}, 'HT', \`${encodeURIComponent(name)}\`)">Rolar</button><br><br>
                        </li>
                    </div>
                    
                    <div class="ficha-parte-box">

                        <h3 class="titulo-ficha-gm">SUBATRIBUTOS</h3>
                        <li class="li-gm" >
                            <span class="medievalsharp-regular">HP: ${data.sub_attributes.hp}</span>
                        </li>
                        
                        <li class="li-gm" >
                            <span class="medievalsharp-regular">FP: ${data.sub_attributes.fp}</span>
                        </li>
                        
                        <li class="li-gm" >
                            <span class="medievalsharp-regular">SPEED: ${data.sub_attributes.speed}</span>
                        </li>
                        
                        <li class="li-gm" >
                            <span class="medievalsharp-regular">DODGE: ${data.sub_attributes.dodge}</span>&nbsp;&nbsp;
                            =>&nbsp;&nbsp;BÔNUS:
                            <input class="input-inc" type="number" id="bonus-DODGE" value="0">
                            &nbsp;&nbsp;&nbsp;&nbsp;REDUTOR:&nbsp;&nbsp;
                            <input class="input-inc" type="number" id="redutor-DODGE" value="0">
                            <button class="menu-button" onclick="rollAttribute(${data.sub_attributes.dodge}, 'DODGE', \`${encodeURIComponent(name)}\`)">Rolar</button><br><br>
                        </li>

                        <li class="li-gm" >
                            <span class="medievalsharp-regular">PARRY UNARMED: ${data.sub_attributes.parry_unarmed}</span>&nbsp;&nbsp;
                            =>&nbsp;&nbsp;BÔNUS:
                            <input class="input-inc" type="number" id="bonus-PARRY UNARMED" value="0">
                            &nbsp;&nbsp;&nbsp;&nbsp;REDUTOR:&nbsp;&nbsp;
                            <input class="input-inc" type="number" id="redutor-PARRY UNARMED" value="0">
                            <button class="menu-button" onclick="rollAttribute(${data.sub_attributes.parry_unarmed}, 'PARRY UNARMED', \`${encodeURIComponent(name)}\`)">Rolar</button><br><br>
                        </li>

                        <li class="li-gm" >
                            <span class="medievalsharp-regular">PARRY WEAPON: ${data.sub_attributes.parry_weapon}</span>&nbsp;&nbsp;
                            =>&nbsp;&nbsp;BÔNUS:
                            <input class="input-inc" type="number" id="bonus-PARRY WEAPON" value="0">
                            &nbsp;&nbsp;&nbsp;&nbsp;REDUTOR:&nbsp;&nbsp;
                            <input class="input-inc" type="number" id="redutor-PARRY WEAPON" value="0">
                            <button class="menu-button" onclick="rollAttribute(${data.sub_attributes.parry_weapon}, 'PARRY WEAPON', \`${encodeURIComponent(name)}\`)">Rolar</button><br><br>
                        </li>

                        <li class="li-gm" >
                            <span class="medievalsharp-regular">WILL: ${data.sub_attributes.will}</span>&nbsp;&nbsp;
                            =>&nbsp;&nbsp;BÔNUS:
                            <input class="input-inc" type="number" id="bonus-WILL" value="0">
                            &nbsp;&nbsp;&nbsp;&nbsp;REDUTOR:&nbsp;&nbsp;
                            <input class="input-inc" type="number" id="redutor-WILL" value="0">
                            <button class="menu-button" onclick="rollAttribute(${data.sub_attributes.will}, 'WILL', \`${encodeURIComponent(name)}\`)">Rolar</button><br><br>
                        </li>

                        <li class="li-gm" >
                            <span class="medievalsharp-regular">PER: ${data.sub_attributes.perception}</span>&nbsp;&nbsp;
                            =>&nbsp;&nbsp;BÔNUS:
                            <input class="input-inc" type="number" id="bonus-PERCEPTION" value="0">
                            &nbsp;&nbsp;&nbsp;&nbsp;REDUTOR:&nbsp;&nbsp;
                            <input class="input-inc" type="number" id="redutor-PERCEPTION" value="0">
                            <button class="menu-button" onclick="rollAttribute(${data.sub_attributes.perception}, 'PERCEPTION', \`${encodeURIComponent(name)}\`)">Rolar</button><br><br>
                        </li>
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