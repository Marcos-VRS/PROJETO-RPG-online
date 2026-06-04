// MapCanvas: gerencia 3 camadas de canvas (imagem, grid, overlay) com
// uma transformação compartilhada (pan + zoom).
//
// Camadas:
//   layer 0: imagem do mapa (background)
//   layer 1: grid hexagonal (desenhado on-demand quando habilitado)
//   layer 2: overlay (tokens, desenhos, cursor) — Fase 3+
//
// Coordenadas:
//   - "world": pixels da imagem original (1:1 com a arte que o GM subiu)
//   - "screen": pixels do viewport
//   - Transformação: screen = world × scale + offset
//
// Fase 1 (esta): só carrega imagem + pan + zoom. Grid e overlay vazios.
window.rd6Map = window.rd6Map || {};

(function () {
    "use strict";

    function MapCanvas(rootEl, opts) {
        this.root = rootEl;
        this.imageUrl = opts.imageUrl || null;
        this.image = null;        // HTMLImageElement carregado
        this.imageReady = false;

        // Transform (world → screen)
        this.scale = 1.0;
        this.offsetX = 0;
        this.offsetY = 0;

        // Limites de zoom
        this.minScale = 0.1;
        this.maxScale = 5.0;

        // Estado de drag
        this._dragging = false;
        this._dragStartX = 0;
        this._dragStartY = 0;
        this._dragOriginX = 0;
        this._dragOriginY = 0;

        this._setupCanvases();
        this._attachEvents();
        if (this.imageUrl) this.loadImage(this.imageUrl);
    }

    MapCanvas.prototype._setupCanvases = function () {
        // Cria 3 canvases empilhados absolutamente. Root deve ser position:relative.
        this.canvasImage = this._createLayer("rd6-map-canvas-image", 1);
        this.canvasGrid = this._createLayer("rd6-map-canvas-grid", 2);
        this.canvasOverlay = this._createLayer("rd6-map-canvas-overlay", 3);

        this.ctxImage = this.canvasImage.getContext("2d");
        this.ctxGrid = this.canvasGrid.getContext("2d");
        this.ctxOverlay = this.canvasOverlay.getContext("2d");

        this._resizeCanvases();
    };

    MapCanvas.prototype._createLayer = function (id, zIndex) {
        var c = document.createElement("canvas");
        c.id = id;
        c.className = "rd6-map-layer";
        c.style.position = "absolute";
        c.style.left = "0";
        c.style.top = "0";
        c.style.zIndex = String(zIndex);
        // Pointer-events só no overlay (topo); imagem e grid não recebem mouse.
        c.style.pointerEvents = (zIndex === 3) ? "auto" : "none";
        this.root.appendChild(c);
        return c;
    };

    MapCanvas.prototype._resizeCanvases = function () {
        var w = this.root.clientWidth;
        var h = this.root.clientHeight;
        // Suporte a high-DPI: backing store = w × dpr, mas CSS = w.
        var dpr = window.devicePixelRatio || 1;
        [this.canvasImage, this.canvasGrid, this.canvasOverlay].forEach(function (c) {
            c.width = Math.floor(w * dpr);
            c.height = Math.floor(h * dpr);
            c.style.width = w + "px";
            c.style.height = h + "px";
        });
        // Escala automática do contexto pra desenhar em coordenadas CSS
        [this.ctxImage, this.ctxGrid, this.ctxOverlay].forEach(function (ctx) {
            ctx.setTransform(dpr, 0, 0, dpr, 0, 0);
        });
        this.viewportWidth = w;
        this.viewportHeight = h;
    };

    MapCanvas.prototype._attachEvents = function () {
        var self = this;

        // Wheel = zoom (com cursor como centro de zoom)
        this.canvasOverlay.addEventListener("wheel", function (e) {
            e.preventDefault();
            var rect = self.canvasOverlay.getBoundingClientRect();
            var mx = e.clientX - rect.left;
            var my = e.clientY - rect.top;

            var dir = e.deltaY < 0 ? 1 : -1;
            var factor = dir > 0 ? 1.12 : 1 / 1.12;
            var newScale = Math.min(self.maxScale, Math.max(self.minScale, self.scale * factor));
            if (newScale === self.scale) return;

            // Pra zoom no cursor: world ponto sob o cursor não muda
            var worldX = (mx - self.offsetX) / self.scale;
            var worldY = (my - self.offsetY) / self.scale;
            self.scale = newScale;
            self.offsetX = mx - worldX * self.scale;
            self.offsetY = my - worldY * self.scale;
            self.renderAll();
        }, { passive: false });

        // Pan = botão DIREITO (2) ou meio (1). Esquerdo (0) fica livre pra
        // token/desenho/régua sem competir com o pan.
        this.canvasOverlay.addEventListener("mousedown", function (e) {
            if (e.button !== 2 && e.button !== 1) return;
            self._dragging = true;
            self._dragStartX = e.clientX;
            self._dragStartY = e.clientY;
            self._dragOriginX = self.offsetX;
            self._dragOriginY = self.offsetY;
            self.canvasOverlay.style.cursor = "grabbing";
            e.preventDefault();
        });

        // Desabilita o menu de contexto (botão direito vira pan, não menu).
        this.canvasOverlay.addEventListener("contextmenu", function (e) {
            e.preventDefault();
        });

        document.addEventListener("mousemove", function (e) {
            if (!self._dragging) return;
            var dx = e.clientX - self._dragStartX;
            var dy = e.clientY - self._dragStartY;
            self.offsetX = self._dragOriginX + dx;
            self.offsetY = self._dragOriginY + dy;
            self.renderAll();
        });

        document.addEventListener("mouseup", function () {
            if (!self._dragging) return;
            self._dragging = false;
            self.canvasOverlay.style.cursor = "default";
        });

        // Resize do viewport
        window.addEventListener("resize", function () {
            self._resizeCanvases();
            self.renderAll();
        });

        // Cursor inicial (default crosshair/seta; pan é botão direito)
        this.canvasOverlay.style.cursor = "default";
    };

    MapCanvas.prototype.loadImage = function (url) {
        var self = this;
        this.imageReady = false;
        if (!url) {
            this.image = null;
            this.renderAll();
            return;
        }
        var img = new Image();
        img.crossOrigin = "anonymous"; // pra Cloudflare Tunnel não bloquear
        img.onload = function () {
            self.image = img;
            self.imageReady = true;
            // Auto-fit: centraliza imagem e ajusta zoom pra caber.
            self.fitToViewport();
            self.renderAll();
        };
        img.onerror = function () {
            console.error("rd6Map: falha ao carregar imagem", url);
            self.image = null;
            self.imageReady = false;
            self.renderAll();
        };
        img.src = url;
        this.imageUrl = url;
    };

    MapCanvas.prototype.fitToViewport = function () {
        if (!this.imageReady) return;
        var iw = this.image.naturalWidth;
        var ih = this.image.naturalHeight;
        if (!iw || !ih) return;
        var sx = this.viewportWidth / iw;
        var sy = this.viewportHeight / ih;
        this.scale = Math.min(sx, sy, 1.0); // não amplia além de 1× ao abrir
        this.offsetX = (this.viewportWidth - iw * this.scale) / 2;
        this.offsetY = (this.viewportHeight - ih * this.scale) / 2;
    };

    MapCanvas.prototype.renderAll = function () {
        this._renderImage();
        this._renderGrid();
        this._composeOverlay();
    };

    // === Composite do overlay ===
    // Vários layers (drawings + tokens) precisam compartilhar o canvas overlay.
    // Cada layer registra-se com mc.addOverlayLayer(layer), onde layer tem .paint(ctx).
    // O composite limpa e chama os paints em ordem registrada.

    MapCanvas.prototype.addOverlayLayer = function (layer) {
        if (!this._overlayLayers) this._overlayLayers = [];
        this._overlayLayers.push(layer);
        this._composeOverlay();
    };

    MapCanvas.prototype._composeOverlay = function () {
        var ctx = this.ctxOverlay;
        this._clear(ctx);
        if (!this._overlayLayers) return;
        for (var i = 0; i < this._overlayLayers.length; i++) {
            var l = this._overlayLayers[i];
            if (l && typeof l.paint === "function") l.paint(ctx);
        }
    };

    // === Grid hexagonal (Fase 2) ===

    MapCanvas.prototype.setGridConfig = function (cfg) {
        // cfg: {enabled, size_px, offset_x, offset_y, color, opacity}
        this.gridConfig = cfg || null;
        this.renderAll();
    };

    MapCanvas.prototype._renderGrid = function () {
        var ctx = this.ctxGrid;
        this._clear(ctx);
        var cfg = this.gridConfig;
        if (!cfg || !cfg.enabled) return;
        // Grid desenha mesmo sem imagem (não bloqueia no load inicial).

        // O grid existe no "mundo" (coordenadas da imagem), então usa o mesmo
        // transform que a imagem. Tamanho do hex é em pixels da imagem;
        // o scale do canvas vai aplicar zoom.
        ctx.save();
        ctx.translate(this.offsetX, this.offsetY);
        ctx.scale(this.scale, this.scale);

        // Calcula bbox visível em coordenadas world pra só desenhar o que aparece
        var topLeft = this.screenToWorld(0, 0);
        var bottomRight = this.screenToWorld(this.viewportWidth, this.viewportHeight);

        var size = cfg.size_px;
        var hexes = window.rd6Hex.hexesInPixelRect(
            topLeft.x, topLeft.y, bottomRight.x, bottomRight.y,
            size, cfg.offset_x, cfg.offset_y
        );

        ctx.strokeStyle = cfg.color || "#000000";
        ctx.lineWidth = Math.max(1 / this.scale, 0.5);  // 1px em screen
        ctx.globalAlpha = (cfg.opacity == null) ? 0.4 : cfg.opacity;

        for (var i = 0; i < hexes.length; i++) {
            var h = hexes[i];
            var center = window.rd6Hex.axialToPixel(h.q, h.r, size, cfg.offset_x, cfg.offset_y);
            var corners = window.rd6Hex.hexCorners(center.x, center.y, size);
            ctx.beginPath();
            ctx.moveTo(corners[0].x, corners[0].y);
            for (var j = 1; j < 6; j++) {
                ctx.lineTo(corners[j].x, corners[j].y);
            }
            ctx.closePath();
            ctx.stroke();
        }

        ctx.restore();
    };

    MapCanvas.prototype._renderImage = function () {
        var ctx = this.ctxImage;
        this._clear(ctx);
        if (!this.imageReady) {
            // Sem imagem ainda: desenha fundo escuro neutro
            ctx.fillStyle = "#1a1a1a";
            ctx.fillRect(0, 0, this.viewportWidth, this.viewportHeight);
            return;
        }
        ctx.save();
        ctx.translate(this.offsetX, this.offsetY);
        ctx.scale(this.scale, this.scale);
        ctx.drawImage(this.image, 0, 0);
        ctx.restore();
    };

    MapCanvas.prototype._clear = function (ctx) {
        ctx.clearRect(0, 0, this.viewportWidth, this.viewportHeight);
    };

    // === API pública pra Fase 2+ ===

    // Converte coordenada de tela pra coordenada world (pixels da imagem).
    MapCanvas.prototype.screenToWorld = function (screenX, screenY) {
        return {
            x: (screenX - this.offsetX) / this.scale,
            y: (screenY - this.offsetY) / this.scale,
        };
    };

    MapCanvas.prototype.worldToScreen = function (worldX, worldY) {
        return {
            x: worldX * this.scale + this.offsetX,
            y: worldY * this.scale + this.offsetY,
        };
    };

    // Expor pro escopo global
    window.rd6Map.MapCanvas = MapCanvas;
})();
