// Drawings layer: linhas/retângulos/círculos colaborativos no overlay.
//
// Cada usuário (player ou GM) pode desenhar; cada desenho carrega
// author_id + author_color. Schema completo em TABLETOP_MAP_PLAN.md §3.3.
//
// API publica:
//   window.rd6Drawings.attach(mapCanvas, opts)
//     opts: {
//       drawings: array inicial,
//       userId: ...,
//       userIsGm: ...,
//       userColor: cor padrão deste usuário,
//       onAdd: (drawing) => void,    (envia WS)
//       onRemove: (drawing_id) => void,
//     }
window.rd6Drawings = (function () {
    "use strict";

    function DrawingsLayer(mapCanvas, opts) {
        this.mc = mapCanvas;
        this.opts = opts || {};
        this.drawings = opts.drawings || [];
        this.selectedId = null;
        this.mode = "none";  // none | line | rect | circle
        this.strokeColor = opts.userColor || "#3b82f6";
        this.strokeWidth = 3;
        this.layer = "visible";
        this._inProgress = null;  // {kind, points: [...]}
        this._attachEvents();
    }

    DrawingsLayer.prototype.setMode = function (m) {
        this.mode = m;  // "none" | "line" | "rect" | "circle"
        var overlay = this.mc.canvasOverlay;
        overlay.style.cursor = (m === "none") ? "default" : "crosshair";
    };

    DrawingsLayer.prototype.setStrokeColor = function (c) {
        this.strokeColor = c;
    };
    DrawingsLayer.prototype.setStrokeWidth = function (n) {
        this.strokeWidth = n;
    };
    DrawingsLayer.prototype.setLayer = function (l) {
        if (["visible", "gm_only", "overlay"].indexOf(l) >= 0) this.layer = l;
    };

    DrawingsLayer.prototype.setDrawings = function (drawings) {
        this.drawings = drawings || [];
        this.render();
    };

    DrawingsLayer.prototype.addDrawing = function (d) {
        var i = this._indexOf(d.id);
        if (i >= 0) this.drawings[i] = d;
        else this.drawings.push(d);
        this.render();
    };

    DrawingsLayer.prototype.removeDrawing = function (id) {
        this.drawings = this.drawings.filter(function (d) { return d.id !== id; });
        if (this.selectedId === id) this.selectedId = null;
        this.render();
    };

    DrawingsLayer.prototype.clearAll = function () {
        this.drawings = [];
        this.selectedId = null;
        this.render();
    };

    DrawingsLayer.prototype._indexOf = function (id) {
        for (var i = 0; i < this.drawings.length; i++) {
            if (this.drawings[i].id === id) return i;
        }
        return -1;
    };

    // === Render ===

    DrawingsLayer.prototype._visibleDrawings = function () {
        var showOverlay = window.rd6ShowOverlayLayer !== false;
        var self = this;
        return this.drawings.filter(function (d) {
            var l = d.layer || "visible";
            if (!self.opts.userIsGm && l === "gm_only") return false;
            if (!showOverlay && l === "overlay") return false;
            return true;
        });
    };

    // render() pede composite ao MapCanvas (drawings + tokens compartilham canvas)
    DrawingsLayer.prototype.render = function () {
        this.mc._composeOverlay();
    };

    // paint() é chamado pelo composite — não limpa, só desenha.
    DrawingsLayer.prototype.paint = function (ctx) {
        var renderable = this._visibleDrawings();
        var LAYER_ORDER = { "visible": 0, "gm_only": 1, "overlay": 2 };
        var sorted = renderable.slice().sort(function (a, b) {
            return LAYER_ORDER[a.layer || "visible"] - LAYER_ORDER[b.layer || "visible"];
        });

        ctx.save();
        ctx.translate(this.mc.offsetX, this.mc.offsetY);
        ctx.scale(this.mc.scale, this.mc.scale);

        for (var i = 0; i < sorted.length; i++) {
            this._drawOne(ctx, sorted[i]);
        }
        if (this._inProgress) {
            ctx.save();
            ctx.setLineDash([6, 4]);
            this._drawOne(ctx, this._inProgress);
            ctx.restore();
            this._drawMeasure(ctx, this._inProgress);
        }
        ctx.restore();
    };

    // metros por pixel: hexes adjacentes (1 m) distam √3 × size pixels.
    DrawingsLayer.prototype._metersPerPx = function () {
        var g = (this.opts.getGridSize && this.opts.getGridSize()) || 50;
        return 1 / (Math.sqrt(3) * g);
    };

    // Réguas de medida durante o desenho (círculo = raio; retângulo = L e A).
    DrawingsLayer.prototype._drawMeasure = function (ctx, d) {
        if (!d || !d.points || d.points.length < 2) return;
        var mpp = this._metersPerPx();
        function fmt(px) {
            var m = px * mpp;
            return (m >= 10 ? m.toFixed(0) : m.toFixed(1)) + " m";
        }
        if (d.kind === "circle") {
            var cx = d.points[0][0], cy = d.points[0][1];
            var ex = d.points[1][0], ey = d.points[1][1];
            var dx = ex - cx, dy = ey - cy;
            var rpx = Math.sqrt(dx * dx + dy * dy);
            // linha-régua do raio (centro → borda)
            ctx.save();
            ctx.strokeStyle = "#ffd700";
            ctx.lineWidth = 1.5 / this.mc.scale;
            ctx.setLineDash([5 / this.mc.scale, 3 / this.mc.scale]);
            ctx.beginPath();
            ctx.moveTo(cx, cy);
            ctx.lineTo(ex, ey);
            ctx.stroke();
            ctx.restore();
            this._measureLabel(ctx, (cx + ex) / 2, (cy + ey) / 2, "R " + fmt(rpx));
        } else if (d.kind === "rect") {
            var x0 = Math.min(d.points[0][0], d.points[1][0]);
            var y0 = Math.min(d.points[0][1], d.points[1][1]);
            var x1 = Math.max(d.points[0][0], d.points[1][0]);
            var y1 = Math.max(d.points[0][1], d.points[1][1]);
            var wpx = x1 - x0, hpx = y1 - y0;
            this._measureLabel(ctx, (x0 + x1) / 2, y0, "↔ " + fmt(wpx));  // largura, topo
            this._measureLabel(ctx, x0, (y0 + y1) / 2, "↕ " + fmt(hpx));  // altura, lado
        }
    };

    DrawingsLayer.prototype._measureLabel = function (ctx, x, y, text) {
        ctx.save();
        var fs = 13 / this.mc.scale;
        ctx.font = "bold " + fs + "px sans-serif";
        var pad = 6 / this.mc.scale;
        var w = ctx.measureText(text).width + pad * 2;
        var h = 18 / this.mc.scale;
        ctx.fillStyle = "rgba(0,0,0,0.82)";
        ctx.fillRect(x - w / 2, y - h / 2, w, h);
        ctx.fillStyle = "#ffd700";
        ctx.textAlign = "center";
        ctx.textBaseline = "middle";
        ctx.fillText(text, x, y);
        ctx.restore();
    };

    DrawingsLayer.prototype._drawOne = function (ctx, d) {
        var w = (d.stroke_width || 3) / this.mc.scale;
        ctx.strokeStyle = d.stroke_color || "#ff0000";
        ctx.lineWidth = Math.max(w, 0.5);
        ctx.globalAlpha = d.layer === "gm_only" ? 0.7 : 1.0;
        if (d.kind === "line") {
            ctx.beginPath();
            ctx.moveTo(d.points[0][0], d.points[0][1]);
            for (var i = 1; i < d.points.length; i++) {
                ctx.lineTo(d.points[i][0], d.points[i][1]);
            }
            ctx.stroke();
        } else if (d.kind === "rect" && d.points.length >= 2) {
            var x = Math.min(d.points[0][0], d.points[1][0]);
            var y = Math.min(d.points[0][1], d.points[1][1]);
            var rw = Math.abs(d.points[1][0] - d.points[0][0]);
            var rh = Math.abs(d.points[1][1] - d.points[0][1]);
            if (d.fill_color) {
                ctx.fillStyle = d.fill_color;
                ctx.fillRect(x, y, rw, rh);
            }
            ctx.strokeRect(x, y, rw, rh);
        } else if (d.kind === "circle" && d.points.length >= 2) {
            var cx = d.points[0][0], cy = d.points[0][1];
            var dx = d.points[1][0] - cx, dy = d.points[1][1] - cy;
            var r = Math.sqrt(dx * dx + dy * dy);
            ctx.beginPath();
            ctx.arc(cx, cy, r, 0, Math.PI * 2);
            if (d.fill_color) {
                ctx.fillStyle = d.fill_color;
                ctx.fill();
            }
            ctx.stroke();
        }
        ctx.globalAlpha = 1.0;
    };

    // === Eventos ===

    DrawingsLayer.prototype._attachEvents = function () {
        var self = this;
        var overlay = this.mc.canvasOverlay;
        if (!overlay) return;

        overlay.addEventListener("mousedown", function (e) {
            if (e.button !== 0) return;
            if (self.mode === "none") return;  // sem modo de desenho ativo
            var rect = overlay.getBoundingClientRect();
            var w = self.mc.screenToWorld(e.clientX - rect.left, e.clientY - rect.top);
            self._inProgress = {
                kind: self.mode,
                points: [[w.x, w.y], [w.x, w.y]],
                stroke_color: self.strokeColor,
                stroke_width: self.strokeWidth,
                layer: self.layer,
            };
            e.stopPropagation();
            e.preventDefault();
        });

        document.addEventListener("mousemove", function (e) {
            if (!self._inProgress) return;
            var rect = overlay.getBoundingClientRect();
            var w = self.mc.screenToWorld(e.clientX - rect.left, e.clientY - rect.top);
            // Pra line/rect/circle: atualiza segundo ponto
            if (self._inProgress.kind === "line") {
                // Polyline real: adiciona pontos enquanto arrasta
                self._inProgress.points.push([w.x, w.y]);
                // Limita ao máximo 200 pontos
                if (self._inProgress.points.length > 200) {
                    self._inProgress.points = self._inProgress.points.slice(-200);
                }
            } else {
                self._inProgress.points[1] = [w.x, w.y];
            }
            self.render();
        });

        document.addEventListener("mouseup", function (e) {
            if (!self._inProgress) return;
            var d = self._inProgress;
            self._inProgress = null;
            // Despreza se foi click sem arrasto (line precisa de 2+ pontos diferentes)
            if (d.points.length < 2) return;
            var firstP = d.points[0];
            var lastP = d.points[d.points.length - 1];
            var dx = lastP[0] - firstP[0];
            var dy = lastP[1] - firstP[1];
            if (Math.abs(dx) < 2 && Math.abs(dy) < 2) {
                self.render();
                return;
            }
            // Envia WS — server gera id e broadcasta
            if (self.opts.onAdd) {
                self.opts.onAdd({
                    kind: d.kind,
                    points: d.points,
                    stroke_color: d.stroke_color,
                    stroke_width: d.stroke_width,
                    layer: d.layer,
                });
            }
        });
    };

    return {
        attach: function (mapCanvas, opts) {
            return new DrawingsLayer(mapCanvas, opts);
        },
    };
})();
