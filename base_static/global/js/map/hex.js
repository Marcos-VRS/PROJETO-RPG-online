// Hex math pra grid flat-top, baseado em Red Blob Games:
// https://www.redblobgames.com/grids/hexagons/
//
// Coordenadas axiais (Q, R). Convenção flat-top:
// - Q cresce pra leste/sudeste alternando.
// - R cresce pra sudoeste.
// - Cada hex tem 6 vizinhos:
//      [+1,0], [+1,-1], [0,-1], [-1,0], [-1,+1], [0,+1]
//
// size = "raio" do hex (distância do centro a um vértice). Hex flat-top:
// - largura horizontal (esquerda→direita) = 2 × size
// - altura vertical (topo→base) = √3 × size
// - colunas horizontalmente espaçadas em 3/2 × size
// - linhas verticalmente espaçadas em √3 × size (com offset de meia em colunas ímpares)
window.rd6Hex = (function () {
    "use strict";

    var SQRT3 = Math.sqrt(3);

    // === Axial → Pixel (centro do hex) ===
    function axialToPixel(q, r, size, originX, originY) {
        // Flat-top: x = size * 3/2 * q ; y = size * √3 * (r + q/2)
        var x = size * 1.5 * q + (originX || 0);
        var y = size * SQRT3 * (r + q / 2) + (originY || 0);
        return { x: x, y: y };
    }

    // === Pixel → Axial (rounded) ===
    function pixelToAxial(px, py, size, originX, originY) {
        var x = (px - (originX || 0));
        var y = (py - (originY || 0));
        var q = (2 / 3) * x / size;
        var r = (-1 / 3) * x / size + (SQRT3 / 3) * y / size;
        return axialRound(q, r);
    }

    // Arredondamento que respeita a geometria hex (não pode só Math.round)
    function axialRound(qf, rf) {
        var sf = -qf - rf;
        var q = Math.round(qf);
        var r = Math.round(rf);
        var s = Math.round(sf);

        var dq = Math.abs(q - qf);
        var dr = Math.abs(r - rf);
        var ds = Math.abs(s - sf);

        if (dq > dr && dq > ds) {
            q = -r - s;
        } else if (dr > ds) {
            r = -q - s;
        }
        return { q: q, r: r };
    }

    // === Vértices de um hex flat-top (6 pontos pra desenhar polígono) ===
    function hexCorners(cx, cy, size) {
        var corners = [];
        for (var i = 0; i < 6; i++) {
            var angle = Math.PI / 3 * i; // 60° spacing, começa em 0 (leste) = flat-top
            corners.push({
                x: cx + size * Math.cos(angle),
                y: cy + size * Math.sin(angle),
            });
        }
        return corners;
    }

    // === Distância entre 2 hexes (em hexes) ===
    function distance(q1, r1, q2, r2) {
        return (
            Math.abs(q1 - q2)
            + Math.abs(q1 + r1 - q2 - r2)
            + Math.abs(r1 - r2)
        ) / 2;
    }

    // === Vizinhos (6 direções pra flat-top) ===
    var DIRECTIONS = [
        { q: +1, r:  0 }, { q: +1, r: -1 }, { q:  0, r: -1 },
        { q: -1, r:  0 }, { q: -1, r: +1 }, { q:  0, r: +1 },
    ];

    function neighbor(q, r, direction) {
        var d = DIRECTIONS[direction % 6];
        return { q: q + d.q, r: r + d.r };
    }

    // === Iterar hexes visíveis num retângulo de pixels ===
    // Útil pra desenhar só o grid que aparece na viewport.
    function hexesInPixelRect(x0, y0, x1, y1, size, originX, originY) {
        // Bbox em axial. Margem +1 pra cobrir bordas.
        var tl = pixelToAxial(x0, y0, size, originX, originY);
        var tr = pixelToAxial(x1, y0, size, originX, originY);
        var bl = pixelToAxial(x0, y1, size, originX, originY);
        var br = pixelToAxial(x1, y1, size, originX, originY);

        var qMin = Math.min(tl.q, tr.q, bl.q, br.q) - 1;
        var qMax = Math.max(tl.q, tr.q, bl.q, br.q) + 1;
        var rMin = Math.min(tl.r, tr.r, bl.r, br.r) - 1;
        var rMax = Math.max(tl.r, tr.r, bl.r, br.r) + 1;

        var result = [];
        for (var q = qMin; q <= qMax; q++) {
            for (var r = rMin; r <= rMax; r++) {
                result.push({ q: q, r: r });
            }
        }
        return result;
    }

    return {
        axialToPixel: axialToPixel,
        pixelToAxial: pixelToAxial,
        hexCorners: hexCorners,
        distance: distance,
        neighbor: neighbor,
        DIRECTIONS: DIRECTIONS,
        hexesInPixelRect: hexesInPixelRect,
    };
})();
