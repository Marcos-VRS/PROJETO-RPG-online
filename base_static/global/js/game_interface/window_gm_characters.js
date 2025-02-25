document.addEventListener("DOMContentLoaded", function () {
    document.querySelectorAll(".personagem-container-gm button").forEach(button => {
        button.addEventListener("click", function () {
            const characterName = this.textContent;
            abrirJanela("personagem_gm");
            get_character_gm(characterName);
        });
    });
});



function get_character_gm(name) {
    console.log(`Buscando personagem: ${name}`); // 🟢 Debug no console do navegador
    fetch(`/api/character/?nome=${encodeURIComponent(name)}`)
        .then(response => response.json())
        .then(data => {
            console.log("Resposta da API:", data); // 🟢 Verifica se a API respondeu
            const window = document.getElementById("janela-personagem_gm");

            // Acessa as perícias do personagem e usa forEach para iterar sobre elas
            let skillsList = '';
            data.skills.forEach(function (skill) {
                skillsList += `
                    <li>
                        ${skill.nome}: NH ${skill.nh}
                        BÔNUS:
                        <input type="number" id="bonus-${skill.nome}" value="0">
                        REDUTOR:
                        <input type="number" id="redutor-${skill.nome}" value="0">
                        <button onclick="rollAttribute(${skill.nh}, '${skill.nome}','${encodeURIComponent(name)}')">Rolar</button><br><br>
                    </li>
                `;
            });

            let ataque_meleeList = '';
            data.maneuvers_melee.forEach(function (maneuvers_melee) {
                ataque_meleeList += `
                    <li>
                        ${maneuvers_melee.nome}: ${maneuvers_melee.damage}  NH:${maneuvers_melee.nh}
                        BÔNUS:
                        <input type="number" id="bonus-${maneuvers_melee.nome}" value="0">
                        REDUTOR:
                        <input type="number" id="redutor-${maneuvers_melee.nome}" value="0">
                        <button onclick="rollAttack(${maneuvers_melee.nh}, '${maneuvers_melee.nome}','${maneuvers_melee.damage}','${encodeURIComponent(name)}')">Rolar</button><br><br>
                    </li>
                `;

            });

            let ataque_rangedList = '';
            data.maneuvers_ranged.forEach(function (maneuvers_ranged) {
                ataque_rangedList += `
                    <li>
                        ${maneuvers_ranged.nome}: ${maneuvers_ranged.damage}  NH:${maneuvers_ranged.nh}
                        BÔNUS:
                        <input type="number" id="bonus-${maneuvers_ranged.nome}" value="0">
                        REDUTOR:
                        <input type="number" id="redutor-${maneuvers_ranged.nome}" value="0">
                        <button onclick="rollAttack(${maneuvers_ranged.nh}, '${maneuvers_ranged.nome}','${maneuvers_ranged.damage}','${encodeURIComponent(name)}')">Rolar</button><br><br>
                    </li>
                `;
            });

            let defesaList = '';
            data.maneuvers_defense.forEach(function (defense) {
                defesaList += `
                    <li>
                        ${defense.nome}:  NH:${defense.nh}
                        BÔNUS:
                        <input type="number" id="bonus-${defense.nome}" value="0">
                        REDUTOR:
                        <input type="number" id="redutor-${defense.nome}" value="0">
                        <button onclick="rollAttribute(${defense.nh}, '${defense.nome}','${encodeURIComponent(name)}')">Rolar</button><br><br>
                    </li>
                `;
            });


            // Acessa os atributos do personagem a partir do objeto 'data'
            window.innerHTML = `
                <button class="fechar" onclick="fecharJanela()">×</button>
                <h2>${data.nome_personagem}</h2>
                <ul>
                    <li>
                        ST: ${data.atributos.ST} 
                        BÔNUS:
                        <input type="number" id="bonus-ST" value="0">
                        REDUTOR:
                        <input type="number" id="redutor-ST" value="0">
                        <button onclick="rollAttribute(${data.atributos.ST}, 'ST','${encodeURIComponent(name)}')">Rolar</button><br><br>
                    </li>
                    <li>
                        DX: ${data.atributos.DX}
                        BÔNUS:
                        <input type="number" id="bonus-DX" value="0">
                        REDUTOR:
                        <input type="number" id="redutor-DX" value="0">
                        <button onclick="rollAttribute(${data.atributos.DX}, 'DX','${encodeURIComponent(name)}')">Rolar</button><br><br>
                    </li>
                    <li>
                        IQ: ${data.atributos.IQ}
                        BÔNUS:
                        <input type="number" id="bonus-IQ" value="0">
                        REDUTOR:
                        <input type="number" id="redutor-IQ" value="0">
                        <button onclick="rollAttribute(${data.atributos.IQ}, 'IQ','${encodeURIComponent(name)}')">Rolar</button><br><br>
                    </li>
                    <li>
                        HT: ${data.atributos.HT}
                        BÔNUS:
                        <input type="number" id="bonus-HT" value="0">
                        REDUTOR:
                        <input type="number" id="redutor-HT" value="0">
                        <button onclick="rollAttribute(${data.atributos.HT}, 'HT','${encodeURIComponent(name)}')">Rolar</button><br><br>
                    </li>

                    <li>
                        HP: ${data.sub_attributes.hp}
                    </li>
                    
                    <li>
                        FP: ${data.sub_attributes.fp}
                    </li>
                    
                    <li>
                        SPEED: ${data.sub_attributes.speed}
                    </li>
                    
                    <li>
                        DODGE: ${data.sub_attributes.dodge}
                        BÔNUS:
                        <input type="number" id="bonus-DODGE" value="0">
                        REDUTOR:
                        <input type="number" id="redutor-HT" value="0">
                        <button onclick="rollAttribute(${data.sub_attributes.dodge}, 'DODGE','${encodeURIComponent(name)}')">Rolar</button><br><br>
                    </li>

                    <li>
                        PARRY UNARMED: ${data.sub_attributes.parry_unarmed}
                        BÔNUS:
                        <input type="number" id="bonus-PARRY UNARMED" value="0">
                        REDUTOR:
                        <input type="number" id="redutor-PARRY UNARMED" value="0">
                        <button onclick="rollAttribute(${data.sub_attributes.parry_unarmed}, 'PARRY UNARMED','${encodeURIComponent(name)}')">Rolar</button><br><br>
                    </li>

                    <li>
                        PARRY WEAPON: ${data.sub_attributes.parry_weapon}
                        BÔNUS:
                        <input type="number" id="bonus-PARRY WEAPON" value="0">
                        REDUTOR:
                        <input type="number" id="redutor-PARRY WEAPON" value="0">
                        <button onclick="rollAttribute(${data.sub_attributes.parry_weapon}, 'PARRY WEAPON','${encodeURIComponent(name)}')">Rolar</button><br><br>
                    </li>

                    <li>
                        WILL: ${data.sub_attributes.will}
                        BÔNUS:
                        <input type="number" id="bonus-WILL" value="0">
                        REDUTOR:
                        <input type="number" id="redutor-WILL" value="0">
                        <button onclick="rollAttribute(${data.sub_attributes.will}, 'WILL','${encodeURIComponent(name)}')">Rolar</button><br><br>
                    </li>

                    <li>
                        PER: ${data.sub_attributes.perception}
                        BÔNUS:
                        <input type="number" id="bonus-PERCEPTION" value="0">
                        REDUTOR:
                        <input type="number" id="redutor-PERCEPTION" value="0">
                        <button onclick="rollAttribute(${data.sub_attributes.perception}, 'PERCEPTION','${encodeURIComponent(name)}')">Rolar</button><br><br>
                    </li>

                    <h3>Perícias</h3>
                    ${skillsList}
                    

                    <h3>Ataques</h3>
                    ${ataque_meleeList}
                    ${ataque_rangedList}
                    
                    <h3>Defesas</h3>
                    ${defesaList}


                    
                    
                    
                    
                   




                </ul>
            `;
        })
        .catch(error => console.error("Erro ao carregar ficha do personagem:", error));
}
