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

        // Mouse drag = pan (botão do meio, ou esquerdo se nada selecionado)
        this.canvasOverlay.addEventListener("mousedown", function (e) {
            // Botão do meio (1) ou esquerdo (0). Direito reserva pra menu de contexto futuro.
            if (e.button !== 0 && e.button !== 1) return;
            self._dragging = true;
            self._dragStartX = e.clientX;
            self._dragStartY = e.clientY;
            self._dragOriginX = self.offsetX;
            self._dragOriginY = self.offsetY;
            self.canvasOverlay.style.cursor = "grabbing";
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
            self.canvasOverlay.style.cursor = "grab";
        });

        // Resize do viewport
        window.addEventListener("resize", function () {
            self._resizeCanvases();
            self.renderAll();
        });

        // Cursor inicial
        this.canvasOverlay.style.cursor = "grab";
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
        // Grid e overlay ficam vazios em Fase 1; outras fases preencherão
        this._clear(this.ctxGrid);
        this._clear(this.ctxOverlay);
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
