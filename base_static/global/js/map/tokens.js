// Tokens layer: renderiza tokens no overlay canvas + drag-and-drop com
// snap automatico ao hex (Shift = movimento livre).
//
// Token shape: ver TABLETOP_MAP_PLAN.md §3.2.
//
// API publica:
//   window.rd6Tokens.attach(mapCanvas, opts)
//     opts: {
//       tokens: array inicial,
//       userId: id do user logado,
//       userIsGm: bool,
//       getGridSize: () => N (consulta o tamanho do hex atual),
//       getGridOffset: () => {x, y},
//       getCurrentTurnId: () => char_id ou null,
//       onTokenMove: (token_id, hex_x, hex_y) => void  (envia WS),
//       canMoveToken: (token) => bool  (regra de turno),
//     }
window.rd6Tokens = (function () {
    "use strict";

    function TokensLayer(mapCanvas, opts) {
        this.mc = mapCanvas;
        this.opts = opts || {};
        this.tokens = opts.tokens || [];
        this.selectedId = null;
        this._dragging = null;       // {token, startWorldX, startWorldY, dx, dy}
        this._imageCache = {};       // url -> HTMLImageElement
        this._attachEvents();
    }

    TokensLayer.prototype.setTokens = function (tokens) {
        this.tokens = tokens || [];
        this.render();
    };

    TokensLayer.prototype.upsertToken = function (token) {
        var i = this._indexOf(token.id);
        if (i >= 0) this.tokens[i] = token;
        else this.tokens.push(token);
        this.render();
    };

    TokensLayer.prototype.removeToken = function (tokenId) {
        this.tokens = this.tokens.filter(function (t) { return t.id !== tokenId; });
        if (this.selectedId === tokenId) this.selectedId = null;
        this.render();
    };

    TokensLayer.prototype._indexOf = function (id) {
        for (var i = 0; i < this.tokens.length; i++) {
            if (this.tokens[i].id === id) return i;
        }
        return -1;
    };

    // === Hit testing ===

    TokensLayer.prototype._tokenAt = function (worldX, worldY) {
        // Itera reverso (último desenhado = mais ao topo na pilha)
        var grid = this._gridSize();
        var ofs = this._gridOffset();
        var renderable = this._visibleTokens();
        for (var i = renderable.length - 1; i >= 0; i--) {
            var t = renderable[i];
            var center = window.rd6Hex.axialToPixel(t.hex_x, t.hex_y, grid, ofs.x, ofs.y);
            var scale = t.size_scale || 1.0;
            var r = grid * 0.85 * scale;
            var dx = worldX - center.x;
            var dy = worldY - center.y;
            if (dx * dx + dy * dy <= r * r) {
                return t;
            }
        }
        return null;
    };

    TokensLayer.prototype._gridSize = function () {
        return (this.opts.getGridSize && this.opts.getGridSize()) || 50;
    };

    TokensLayer.prototype._gridOffset = function () {
        var f = this.opts.getGridOffset;
        return f ? f() : { x: 0, y: 0 };
    };

    // === Event handlers no canvas overlay ===

    TokensLayer.prototype._attachEvents = function () {
        var self = this;
        var overlay = this.mc.canvasOverlay;
        if (!overlay) return;

        // Capture: true faz tokens.js rodar ANTES do canvas.js (que tambem
        // escuta mousedown no overlay pra pan). Se pegamos um token,
        // stopImmediatePropagation impede o canvas.js de iniciar pan.
        overlay.addEventListener("mousedown", function (e) {
            if (e.button !== 0) return;  // só botão esquerdo
            var rect = overlay.getBoundingClientRect();
            var sx = e.clientX - rect.left;
            var sy = e.clientY - rect.top;
            var w = self.mc.screenToWorld(sx, sy);
            var t = self._tokenAt(w.x, w.y);
            if (!t) {
                // Click no vazio: deselect; deixa o canvas fazer pan
                if (self.selectedId) {
                    self.selectedId = null;
                    if (self.opts.onSelect) self.opts.onSelect(null);
                    self.render();
                }
                return;
            }
            // Permissao
            var canMove = self.opts.canMoveToken ? self.opts.canMoveToken(t) : true;
            self.selectedId = t.id;
            if (self.opts.onSelect) self.opts.onSelect(t);
            self.render();
            // Sempre bloqueia pan quando clica num token (mesmo sem permissao,
            // pra player so selecionar sem panico).
            e.stopImmediatePropagation();
            e.preventDefault();
            if (!canMove) return;
            // Inicia drag
            self._dragging = {
                token: t,
                startWorldX: w.x,
                startWorldY: w.y,
                origHexX: t.hex_x,
                origHexY: t.hex_y,
                tempDX: 0,
                tempDY: 0,
            };
        }, true);  // capture phase

        document.addEventListener("mousemove", function (e) {
            if (!self._dragging) return;
            var rect = overlay.getBoundingClientRect();
            var sx = e.clientX - rect.left;
            var sy = e.clientY - rect.top;
            var w = self.mc.screenToWorld(sx, sy);
            self._dragging.tempDX = w.x - self._dragging.startWorldX;
            self._dragging.tempDY = w.y - self._dragging.startWorldY;
            self.render();
        });

        document.addEventListener("mouseup", function (e) {
            if (!self._dragging) return;
            var d = self._dragging;
            var rect = overlay.getBoundingClientRect();
            var sx = e.clientX - rect.left;
            var sy = e.clientY - rect.top;
            var w = self.mc.screenToWorld(sx, sy);
            var grid = self._gridSize();
            var ofs = self._gridOffset();

            // Snap (default) ou movimento livre (Shift)
            var newHexX, newHexY;
            if (e.shiftKey) {
                // Free: arredondar pra hex mais proximo do delta total
                // (mantemos snap mesmo no Shift; "free" seria pixel exato,
                //  mas no atual scheme do token, x/y são hex coords. Próximo
                //  passo seria adicionar offset_px no token pra free move.)
                var axial = window.rd6Hex.pixelToAxial(w.x, w.y, grid, ofs.x, ofs.y);
                newHexX = axial.q;
                newHexY = axial.r;
            } else {
                // Snap ao hex sob o mouse
                var ax = window.rd6Hex.pixelToAxial(w.x, w.y, grid, ofs.x, ofs.y);
                newHexX = ax.q;
                newHexY = ax.r;
            }

            self._dragging = null;
            if (newHexX === d.origHexX && newHexY === d.origHexY) {
                self.render();
                return;
            }
            // Optimistic: aplica localmente. Server vai validar e re-broadcast.
            d.token.hex_x = newHexX;
            d.token.hex_y = newHexY;
            self.render();
            if (self.opts.onTokenMove) {
                self.opts.onTokenMove(d.token.id, newHexX, newHexY);
            }
        });
    };

    // === Render ===
    //
    // Camadas (ordem de desenho, do fundo pro topo):
    //  1. layer="visible" (todos veem)
    //  2. layer="gm_only" (só GM vê — semi-transparente pra distinguir)
    //  3. layer="overlay" (acima de tudo: névoa, weather, etc.)

    TokensLayer.prototype._visibleTokens = function () {
        // Defesa em profundidade: player nunca renderiza gm_only.
        // Tambem respeita o toggle "Mostrar sobreposicao" do GM.
        var showOverlay = window.rd6ShowOverlayLayer !== false;  // default true
        return this.tokens.filter(function (t) {
            var l = t.layer || "visible";
            if (!this.opts.userIsGm && l === "gm_only") return false;
            if (!showOverlay && l === "overlay") return false;
            return true;
        }, this);
    };

    // render() delega ao composite do MapCanvas pra coordenar com drawings layer.
    TokensLayer.prototype.render = function () {
        this.mc._composeOverlay();
    };

    // paint() é chamado pelo composite — NÃO limpa o canvas, só desenha em cima.
    TokensLayer.prototype.paint = function (ctx) {
        var renderable = this._visibleTokens();
        if (!renderable.length) return;

        var grid = this._gridSize();
        var ofs = this._gridOffset();
        var currentTurnId = this.opts.getCurrentTurnId
            ? this.opts.getCurrentTurnId()
            : null;

        // Ordena por camada → z_index
        var LAYER_ORDER = { "visible": 0, "gm_only": 1, "overlay": 2 };
        var sorted = renderable.slice().sort(function (a, b) {
            var la = LAYER_ORDER[a.layer || "visible"];
            var lb = LAYER_ORDER[b.layer || "visible"];
            if (la !== lb) return la - lb;
            return (a.z_index || 0) - (b.z_index || 0);
        });

        ctx.save();
        ctx.translate(this.mc.offsetX, this.mc.offsetY);
        ctx.scale(this.mc.scale, this.mc.scale);

        for (var i = 0; i < sorted.length; i++) {
            var t = sorted[i];
            var center = window.rd6Hex.axialToPixel(t.hex_x, t.hex_y, grid, ofs.x, ofs.y);
            // Se está sendo arrastado, mostra preview deslocado
            if (this._dragging && this._dragging.token.id === t.id) {
                center.x += this._dragging.tempDX;
                center.y += this._dragging.tempDY;
            }
            // gm_only fica semi-transparente pra GM distinguir
            var alpha = 1.0;
            if (t.layer === "gm_only") alpha = 0.65;
            else if (t.layer === "overlay") alpha = 0.85;
            ctx.globalAlpha = alpha;
            this._drawToken(ctx, t, center.x, center.y, grid, t.id === currentTurnId);
            ctx.globalAlpha = 1.0;
        }
        ctx.restore();
    };

    TokensLayer.prototype._drawToken = function (ctx, t, cx, cy, grid, isCurrentTurn) {
        // Raio segue o grid mas pode ser escalado via size_scale (default 1.0).
        // size_scale=2 = token ocupa um hex de 2× raio (~aparente +1 hex de SM).
        var scale = t.size_scale || 1.0;
        var r = grid * 0.8 * scale;

        // Selected: glow
        if (t.id === this.selectedId) {
            ctx.save();
            ctx.shadowColor = "#ffd700";
            ctx.shadowBlur = 20;
            ctx.beginPath();
            ctx.arc(cx, cy, r, 0, Math.PI * 2);
            ctx.strokeStyle = "#ffd700";
            ctx.lineWidth = 2;
            ctx.stroke();
            ctx.restore();
        }
        // Current turn: borda vermelha pulsante
        if (isCurrentTurn) {
            ctx.save();
            ctx.beginPath();
            ctx.arc(cx, cy, r + 4, 0, Math.PI * 2);
            ctx.strokeStyle = "#c44d3d";
            ctx.lineWidth = 3;
            ctx.stroke();
            ctx.restore();
        }

        // Avatar (image ou inicial)
        ctx.save();
        ctx.beginPath();
        ctx.arc(cx, cy, r, 0, Math.PI * 2);
        ctx.closePath();
        ctx.clip();

        var img = t.image_url ? this._getCachedImage(t.image_url) : null;
        if (img && img.complete && img.naturalWidth > 0) {
            ctx.drawImage(img, cx - r, cy - r, r * 2, r * 2);
        } else {
            // Fundo colorido + inicial
            ctx.fillStyle = t.color || "#c9a55c";
            ctx.fillRect(cx - r, cy - r, r * 2, r * 2);
            ctx.fillStyle = "#000";
            ctx.font = "bold " + Math.floor(r * 0.9) + "px sans-serif";
            ctx.textAlign = "center";
            ctx.textBaseline = "middle";
            var initial = (t.label || "?").charAt(0).toUpperCase();
            ctx.fillText(initial, cx, cy);
        }
        ctx.restore();

        // Borda
        ctx.beginPath();
        ctx.arc(cx, cy, r, 0, Math.PI * 2);
        ctx.strokeStyle = t.color || "#c9a55c";
        ctx.lineWidth = 2;
        ctx.stroke();

        // Facing arrow (seta na borda)
        var facing = t.facing || 0;
        var angle = Math.PI / 3 * facing;  // 0=leste, 1=sudeste, etc.
        var fx = cx + Math.cos(angle) * r;
        var fy = cy + Math.sin(angle) * r;
        ctx.beginPath();
        ctx.arc(fx, fy, 4, 0, Math.PI * 2);
        ctx.fillStyle = "#ffd700";
        ctx.fill();
        ctx.strokeStyle = "#000";
        ctx.lineWidth = 1;
        ctx.stroke();

        // Label embaixo
        if (t.label) {
            ctx.fillStyle = "rgba(0,0,0,0.7)";
            ctx.fillRect(cx - r, cy + r + 2, r * 2, 14);
            ctx.fillStyle = "#fff";
            ctx.font = "11px sans-serif";
            ctx.textAlign = "center";
            ctx.textBaseline = "middle";
            ctx.fillText(t.label.substring(0, 20), cx, cy + r + 9);
        }
    };

    TokensLayer.prototype._getCachedImage = function (url) {
        if (this._imageCache[url]) return this._imageCache[url];
        var img = new Image();
        img.crossOrigin = "anonymous";
        var self = this;
        img.onload = function () { self.render(); };
        img.onerror = function () { /* mantém placeholder */ };
        img.src = url;
        this._imageCache[url] = img;
        return img;
    };

    return {
        attach: function (mapCanvas, opts) {
            return new TokensLayer(mapCanvas, opts);
        },
    };
})();
