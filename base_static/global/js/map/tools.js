// Ferramentas do mapa (Fase 5 polimentos): hex highlight sob cursor,
// régua de distância, highlight de reach do token selecionado.
//
// Registra-se como overlay layer (paint) no MapCanvas. Tudo client-side,
// efêmero (não persiste, não usa WS).
//
// API: window.rd6Tools.attach(mapCanvas, opts)  → instância vira window.rd6MapTools
//   opts: { getGridSize, getGridOffset, getSelectedToken }
// (factory = rd6Tools, igual ao padrão rd6Tokens/rd6Drawings; a INSTÂNCIA
//  criada no boot é window.rd6MapTools)
window.rd6Tools = (function () {
    "use strict";

    function MapTools(mc, opts) {
        this.mc = mc;
        this.opts = opts || {};
        this.hoverHex = null;       // {q, r} sob o cursor
        this.rulerMode = false;
        this.rulerStart = null;     // world {x, y}
        this.rulerEnd = null;
        this._attach();
    }

    MapTools.prototype._gridSize = function () {
        return (this.opts.getGridSize && this.opts.getGridSize()) || 50;
    };
    MapTools.prototype._gridOffset = function () {
        var f = this.opts.getGridOffset;
        return f ? f() : { x: 0, y: 0 };
    };

    MapTools.prototype.setRulerMode = function (on) {
        this.rulerMode = !!on;
        if (!on) { this.rulerStart = null; this.rulerEnd = null; }
        this.mc.canvasOverlay.style.cursor = on ? "crosshair" : "default";
        // Feedback visual: destaca os botões de régua via body class.
        document.body.classList.toggle("rd6-ruler-active", this.rulerMode);
        this.mc._composeOverlay();
    };
    MapTools.prototype.toggleRuler = function () {
        this.setRulerMode(!this.rulerMode);
    };

    MapTools.prototype._attach = function () {
        var self = this;
        var overlay = this.mc.canvasOverlay;
        if (!overlay) return;

        overlay.addEventListener("mousemove", function (e) {
            var rect = overlay.getBoundingClientRect();
            var w = self.mc.screenToWorld(e.clientX - rect.left, e.clientY - rect.top);
            var grid = self._gridSize();
            var ofs = self._gridOffset();
            self.hoverHex = window.rd6Hex.pixelToAxial(w.x, w.y, grid, ofs.x, ofs.y);
            if (self.rulerMode && self.rulerStart) {
                self.rulerEnd = w;
            }
            self.mc._composeOverlay();
        });

        overlay.addEventListener("mousedown", function (e) {
            if (!self.rulerMode || e.button !== 0) return;
            var rect = overlay.getBoundingClientRect();
            var w = self.mc.screenToWorld(e.clientX - rect.left, e.clientY - rect.top);
            self.rulerStart = w;
            self.rulerEnd = w;
            e.stopImmediatePropagation();
            e.preventDefault();
        }, true);

        document.addEventListener("keydown", function (e) {
            var tag = document.activeElement && document.activeElement.tagName;
            if (tag === "INPUT" || tag === "TEXTAREA" || tag === "SELECT") return;
            if (e.key === "r" || e.key === "R") {
                self.toggleRuler();
            } else if (e.key === "Escape") {
                if (self.rulerMode) self.setRulerMode(false);
            }
        });
    };

    // paint() chamado pelo composite do MapCanvas
    MapTools.prototype.paint = function (ctx) {
        var grid = this._gridSize();
        var ofs = this._gridOffset();

        ctx.save();
        ctx.translate(this.mc.offsetX, this.mc.offsetY);
        ctx.scale(this.mc.scale, this.mc.scale);

        // 1. Reach do token selecionado (Reach 1 fixo na v1; usa token.reach se houver)
        var sel = this.opts.getSelectedToken ? this.opts.getSelectedToken() : null;
        if (sel) {
            var reaches = (sel.reach && sel.reach.length) ? sel.reach : [1];
            var maxReach = Math.max.apply(null, reaches);
            var ring = window.rd6Hex.hexesWithin(sel.hex_x, sel.hex_y, maxReach);
            ctx.fillStyle = "rgba(80, 200, 120, 0.18)";
            for (var i = 0; i < ring.length; i++) {
                if (ring[i].q === sel.hex_x && ring[i].r === sel.hex_y) continue;
                this._fillHex(ctx, ring[i].q, ring[i].r, grid, ofs);
            }
        }

        // 2. Hex sob o cursor
        if (this.hoverHex) {
            ctx.strokeStyle = "rgba(255, 215, 0, 0.8)";
            ctx.lineWidth = 2 / this.mc.scale;
            this._strokeHex(ctx, this.hoverHex.q, this.hoverHex.r, grid, ofs);
        }

        // 3. Régua
        if (this.rulerMode && this.rulerStart && this.rulerEnd) {
            ctx.strokeStyle = "#ffd700";
            ctx.lineWidth = 2 / this.mc.scale;
            ctx.setLineDash([8 / this.mc.scale, 4 / this.mc.scale]);
            ctx.beginPath();
            ctx.moveTo(this.rulerStart.x, this.rulerStart.y);
            ctx.lineTo(this.rulerEnd.x, this.rulerEnd.y);
            ctx.stroke();
            ctx.setLineDash([]);

            // Distância em hexes (e metros = mesmo número)
            var a = window.rd6Hex.pixelToAxial(this.rulerStart.x, this.rulerStart.y, grid, ofs.x, ofs.y);
            var b = window.rd6Hex.pixelToAxial(this.rulerEnd.x, this.rulerEnd.y, grid, ofs.x, ofs.y);
            var dist = window.rd6Hex.distance(a.q, a.r, b.q, b.r);
            var midX = (this.rulerStart.x + this.rulerEnd.x) / 2;
            var midY = (this.rulerStart.y + this.rulerEnd.y) / 2;
            this._label(ctx, midX, midY, dist + " hex · " + dist + " m");
        }

        ctx.restore();
    };

    MapTools.prototype._fillHex = function (ctx, q, r, grid, ofs) {
        var c = window.rd6Hex.axialToPixel(q, r, grid, ofs.x, ofs.y);
        var corners = window.rd6Hex.hexCorners(c.x, c.y, grid);
        ctx.beginPath();
        ctx.moveTo(corners[0].x, corners[0].y);
        for (var i = 1; i < 6; i++) ctx.lineTo(corners[i].x, corners[i].y);
        ctx.closePath();
        ctx.fill();
    };

    MapTools.prototype._strokeHex = function (ctx, q, r, grid, ofs) {
        var c = window.rd6Hex.axialToPixel(q, r, grid, ofs.x, ofs.y);
        var corners = window.rd6Hex.hexCorners(c.x, c.y, grid);
        ctx.beginPath();
        ctx.moveTo(corners[0].x, corners[0].y);
        for (var i = 1; i < 6; i++) ctx.lineTo(corners[i].x, corners[i].y);
        ctx.closePath();
        ctx.stroke();
    };

    MapTools.prototype._label = function (ctx, x, y, text) {
        ctx.save();
        var fs = 14 / this.mc.scale;
        ctx.font = "bold " + fs + "px sans-serif";
        var w = ctx.measureText(text).width + 10 / this.mc.scale;
        var h = 20 / this.mc.scale;
        ctx.fillStyle = "rgba(0,0,0,0.8)";
        ctx.fillRect(x - w / 2, y - h / 2, w, h);
        ctx.fillStyle = "#ffd700";
        ctx.textAlign = "center";
        ctx.textBaseline = "middle";
        ctx.fillText(text, x, y);
        ctx.restore();
    };

    return {
        attach: function (mc, opts) { return new MapTools(mc, opts); },
    };
})();
